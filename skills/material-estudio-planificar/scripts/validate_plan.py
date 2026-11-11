#!/usr/bin/env python3
"""Validate the portable study plan shape and semantic invariants without dependencies."""
import argparse
from datetime import date, timedelta
import json
import math
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]


def matches_type(value, expected):
    """JSON booleans are not numbers, despite Python's integer subclassing."""
    return {
        'object': lambda: isinstance(value, dict),
        'array': lambda: isinstance(value, list),
        'string': lambda: isinstance(value, str),
        'integer': lambda: type(value) is int or (type(value) is float and math.isfinite(value) and value.is_integer()),
        'number': lambda: type(value) in (int, float),
        'boolean': lambda: type(value) is bool,
        'null': lambda: value is None,
    }[expected]()


def check_shape(value, schema, path='$'):
    """Validate only the schema vocabulary used by the bundled contract."""
    errors = []
    if type(value) is float and not math.isfinite(value):
        return [f'{path}: non-finite number']
    if 'anyOf' in schema:
        candidates = [check_shape(value, candidate, path) for candidate in schema['anyOf']]
        if all(candidates):
            return [f'{path}: does not match an allowed shape']
        return []
    if 'const' in schema and value != schema['const']:
        errors.append(f'{path}: expected {schema["const"]!r}')
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{path}: not an allowed value')
    expected = schema.get('type')
    if expected:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(matches_type(value, choice) for choice in choices):
            return errors + [f'{path}: expected {expected}']
    if value is None:
        return errors
    if isinstance(value, dict):
        props = schema.get('properties', {})
        for key in schema.get('required', []):
            if key not in value:
                errors.append(f'{path}.{key}: missing required field')
        if schema.get('additionalProperties') is False:
            for key in value.keys() - props.keys():
                errors.append(f'{path}.{key}: unknown field')
        for key in value.keys() & props.keys():
            errors.extend(check_shape(value[key], props[key], f'{path}.{key}'))
    elif isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            errors.append(f'{path}: too few items')
        if schema.get('uniqueItems') and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errors.append(f'{path}: duplicate items')
        for index, item in enumerate(value):
            errors.extend(check_shape(item, schema.get('items', {}), f'{path}[{index}]'))
    elif isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or not value.strip():
            errors.append(f'{path}: empty string')
        if schema.get('pattern') and re.search(schema['pattern'], value) is None:
            errors.append(f'{path}: invalid format')
        if schema.get('format') == 'date':
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except ValueError:
                errors.append(f'{path}: invalid calendar date')
    elif type(value) in (int, float):
        if 'minimum' in schema and value < schema['minimum']:
            errors.append(f'{path}: below minimum')
        if 'maximum' in schema and value > schema['maximum']:
            errors.append(f'{path}: above maximum')
    return errors


def check_schedule_defaults(plan):
    """Enforce versioned defaults and explicit provenance without consulting today's clock."""
    errors = []
    schedule = plan['schedule']
    provenance = schedule['provenance']
    mode = schedule['mode']
    start = schedule['start_date']
    exam = schedule['exam_date']
    deadline = schedule['deadline_date']
    if mode == 'dated':
        if start is None or exam is None or deadline is None:
            errors.append('$.schedule: dated mode requires start, exam, and completion deadline')
        if provenance['start_date'] == 'not_applicable' or provenance['exam_date'] != 'provided' or provenance['deadline_date'] == 'not_applicable':
            errors.append('$.schedule.provenance: dated dates must have applicable provenance')
        if provenance['start_date'] == 'default_today' and start != plan['generated_on']:
            errors.append('$.schedule.start_date: default_today must equal execution-local generated_on')
        if exam and exam <= plan['generated_on']:
            errors.append('$.schedule.exam_date: exam must be after the execution-local date')
        if exam and deadline and deadline >= exam:
            errors.append('$.schedule.deadline_date: completion must precede exam')
        if exam and provenance['deadline_date'] == 'derived_before_exam':
            exam_day = date.fromisoformat(exam)
            expected = (exam_day - timedelta(days=1)).isoformat() if exam_day > date.min else None
            if deadline != expected:
                errors.append('$.schedule.deadline_date: derived deadline must be the day before exam')
    else:
        if any(value is not None for value in [start, exam, deadline]):
            errors.append('$.schedule: explicit undated mode requires null date fields')
        if any(provenance[key] != 'not_applicable' for key in ['start_date', 'exam_date', 'deadline_date']):
            errors.append('$.schedule.provenance: undated dates must be not_applicable')
    if provenance['weekends_allowed'] == 'default' and schedule['weekends_allowed'] is not True:
        errors.append('$.schedule.weekends_allowed: default is true')
    capacity = schedule['daily_budget_minutes']
    basis = provenance['daily_budget_minutes']
    if basis == 'default' and capacity != 180:
        errors.append('$.schedule.daily_budget_minutes: default is 180')
    if (capacity is None) != (basis == 'explicit_uncapped'):
        errors.append('$.schedule.daily_budget_minutes: null requires explicit_uncapped, and conversely')
    return errors


def validate_plan(plan):
    """Inspect shape and invariants without mutating input or publishing lifecycle changes."""
    version = plan.get('schema_version') if isinstance(plan, dict) else None
    schema_name = {'1.0': 'plan-v1.0.schema.json', '1.2': 'plan-v1.2.schema.json'}.get(version, 'plan.schema.json')
    schema = json.loads((ROOT / 'assets' / schema_name).read_text(encoding='utf-8'))
    errors = check_shape(plan, schema)
    if errors:
        return errors
    try:
        ZoneInfo(plan['timezone'])
    except (ZoneInfoNotFoundError, ValueError):
        errors.append('$.timezone: unknown IANA timezone')
    schedule = plan['schedule']
    start = schedule['start_date']
    deadline = schedule['deadline_date']
    if version in ('1.2', '1.3'):
        errors.extend(check_schedule_defaults(plan))
    if start and deadline and start > deadline:
        errors.append('$.schedule: start is after deadline')
    sources = [source['id'] for source in plan['sources']]
    if len(set(sources)) != len(sources):
        errors.append('$.sources: duplicate source IDs')
    source_ids = set(sources)
    session_ids = set()
    previous_date = None
    required = optional = 0
    daily_totals = {}
    for index, row in enumerate(plan['sessions']):
        path = f'$.sessions[{index}]'
        if row['id'] in session_ids:
            errors.append(f'{path}.id: duplicate session ID')
        session_ids.add(row['id'])
        current_date = row['study_date']
        if version in ('1.2', '1.3') and schedule['mode'] == 'dated' and current_date is None:
            errors.append(f'{path}.study_date: dated plans require a date for every row')
        if version in ('1.2', '1.3') and schedule['mode'] == 'undated' and current_date is not None:
            errors.append(f'{path}.study_date: undated mode requires null row dates')
        if current_date:
            if version in ('1.2', '1.3') and schedule['exam_date'] and current_date >= schedule['exam_date']:
                errors.append(f'{path}.study_date: study must finish before exam date')
            if start and current_date < start:
                errors.append(f'{path}.study_date: before start')
            if deadline and current_date > deadline:
                errors.append(f'{path}.study_date: after deadline')
            if previous_date and current_date < previous_date:
                errors.append(f'{path}.study_date: out of chronological order')
            previous_date = current_date
            if date.fromisoformat(current_date).weekday() >= 5 and schedule['weekends_allowed'] is not True:
                errors.append(f'{path}.study_date: weekend permission not granted')
        if row['kind'] == 'buffer' and not row['optional']:
            errors.append(f'{path}: buffer must be optional')
        references = set()
        for ref in row['source_refs']:
            if ref['source_id'] not in source_ids:
                errors.append(f'{path}.source_refs: unknown source ID')
            if ref['source_id'] in references:
                errors.append(f'{path}.source_refs: duplicate source reference')
            references.add(ref['source_id'])
            if ref['pages']:
                for page in ref['pages']:
                    if page['start'] > page['end']:
                        errors.append(f'{path}.source_refs: inverted page range')
        total = sum(row[key] for key in ('study_practice_minutes', 'exam_minutes', 'correction_minutes', 'break_minutes'))
        if total != row['total_minutes']:
            errors.append(f'{path}.total_minutes: does not equal components')
        if current_date:
            daily_totals[current_date] = daily_totals.get(current_date, 0) + total
        budget = schedule['session_budget_minutes']
        if budget is not None and total > budget:
            errors.append(f'{path}: exceeds requested session budget')
        if row['optional']:
            optional += total
        else:
            required += total
    if version in ('1.2', '1.3') and schedule['daily_budget_minutes'] is not None:
        for day, minutes in daily_totals.items():
            if minutes > schedule['daily_budget_minutes']:
                errors.append(f'$.schedule: daily total on {day} exceeds plan daily capacity, including optional work')
    expected = {'required_minutes': required, 'optional_minutes': optional, 'including_optional_minutes': required + optional}
    if plan['totals'] != expected:
        errors.append('$.totals: does not equal session sums')
    return errors


def reject_constant(value):
    raise ValueError(f'non-finite JSON number: {value}')


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def load_plan(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject_constant, object_pairs_hook=reject_duplicates)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan')
    args = parser.parse_args()
    try:
        errors = validate_plan(load_plan(args.plan))
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Valid portable study plan.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

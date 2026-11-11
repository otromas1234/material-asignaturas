"""Small strict validator for precisely the bundled JSON Schema keywords, not a general engine."""
import json
import math
from pathlib import Path, PurePosixPath
import re
from datetime import datetime

REPOSITORY = 'otromas1234/material-asignaturas'
BRANCH = 'main'
ASSETS = Path(__file__).resolve().parents[1] / 'assets'


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def load_json(text):
    def reject(value):
        raise ValidationError('Non-finite JSON number: ' + value)
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, 'Duplicate JSON key: ' + key)
            out[key] = value
        return out
    try:
        return json.loads(text, parse_constant=reject, object_pairs_hook=unique)
    except (ValueError, TypeError) as exc:
        raise ValidationError(str(exc)) from exc


def validate_schema(data, schema, location='$'):
    supported = {'$schema', 'type', 'required', 'properties', 'additionalProperties',
                 'items', 'minItems', 'minLength', 'pattern', 'minimum', 'enum', 'const',
                 'anyOf', 'format'}
    require(not set(schema) - supported, 'Unsupported schema keyword')
    if 'anyOf' in schema:
        for option in schema['anyOf']:
            try:
                validate_schema(data, option, location)
                return
            except ValidationError:
                pass
        raise ValidationError(location + ': no permitted nullable/union shape')
    kind = schema.get('type')
    valid = {'object': lambda: isinstance(data, dict),
             'array': lambda: isinstance(data, list),
             'string': lambda: isinstance(data, str),
             'number': lambda: type(data) in (int, float) and math.isfinite(data),
             'integer': lambda: type(data) in (int, float) and math.isfinite(data) and int(data) == data,
             'boolean': lambda: type(data) is bool, 'null': lambda: data is None}
    if kind:
        require(valid[kind](), location + ': expected ' + kind)
    if 'const' in schema:
        require(type(data) is type(schema['const']) and data == schema['const'], location + ': wrong constant')
    if 'enum' in schema:
        require(data in schema['enum'], location + ': invalid enum')
    if kind == 'object':
        require(set(schema.get('required', [])).issubset(data), location + ': missing property')
        if schema.get('additionalProperties') is False:
            require(not set(data) - set(schema['properties']), location + ': unknown property')
        for key, value in data.items():
            if key in schema.get('properties', {}):
                validate_schema(value, schema['properties'][key], location + '.' + key)
    if kind == 'array':
        require(len(data) >= schema.get('minItems', 0), location + ': too few entries')
        for index, value in enumerate(data):
            validate_schema(value, schema['items'], location + '[' + str(index) + ']')
    if kind == 'string':
        require(len(data) >= schema.get('minLength', 0), location + ': empty string')
        if 'pattern' in schema:
            require(re.search(schema['pattern'], data) is not None, location + ': invalid pattern')
        if schema.get('format') == 'date-time':
            try:
                timestamp = datetime.fromisoformat(data.replace('Z', '+00:00'))
                require(timestamp.tzinfo is not None and 'T' in data, location + ': offset required')
            except ValueError as exc:
                raise ValidationError(location + ': invalid timestamp') from exc
    if kind in ('number', 'integer') and 'minimum' in schema:
        require(data >= schema['minimum'], location + ': below minimum')


def validate_named(data, name):
    validate_schema(data, load_json((ASSETS / (name + '.schema.json')).read_text()))


def slug(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value), 'Unsafe or ambiguous slug')
    return value


def safe_path(value, prefix=None):
    require(isinstance(value, str) and value and '\\' not in value and ':' not in value and '\x00' not in value, 'Unsafe path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(p not in ('', '.', '..') for p in value.split('/')), 'Unsafe path')
    require(path.as_posix() == value, 'Noncanonical path')
    if prefix:
        require(value.startswith(prefix) and len(value) > len(prefix), 'Path outside authorized subject/destination')
    return value


def validate_snapshot(snapshot, subject=None):
    validate_named(snapshot, 'snapshot')
    tag = snapshot['tag']
    safe_path(tag)
    require(re.fullmatch(r'plan/[a-z0-9]+(?:-[a-z0-9]+)*/\d{8}-[a-zA-Z0-9-]+', tag), 'Exact material tag required')
    if subject:
        require(tag.startswith('plan/' + slug(subject) + '/'), 'Snapshot subject mismatch')


def unique_ids(rows, key='id'):
    ids = [row[key] for row in rows]
    require(len(set(ids)) == len(ids), 'Duplicate IDs: ' + key)
    return set(ids)


def validate_reference(ref, subject):
    validate_named(ref, 'profile-reference')
    safe_path(ref['path'], 'asignaturas/' + slug(subject) + '/examenes-referencia/')
    require(len(set(ref['included_locators'])) == len(ref['included_locators']), 'Duplicate included locators')
    excluded = [row['locator'] for row in ref['excluded_locators']]
    require(len(set(excluded)) == len(excluded), 'Duplicate excluded locators')
    require(not set(excluded) & set(ref['included_locators']), 'Included/excluded overlap')
    require((ref['read_status'] == 'partial') == bool(excluded), 'Partial reading requires exclusions; complete reading forbids them')

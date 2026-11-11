"""Regression tests for the portable contract and matching Markdown."""
from copy import deepcopy
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_plan import load_plan, validate_plan
from render_plan import render_plan


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_plan(ROOT / 'assets/example-plan.json')
        # Retain the original regression suite against the archived 1.0 contract.
        self.plan['schema_version'] = '1.0'
        self.plan.pop('source_snapshot')
        self.plan.pop('lifecycle_status', None)
        for row in self.plan['sessions']:
            row.pop('practice_prompt', None)
        for key in ['mode', 'exam_date', 'daily_budget_minutes', 'provenance']:
            self.plan['schedule'].pop(key)

    def assert_invalid(self):
        self.assertTrue(validate_plan(self.plan))

    def test_example_is_valid(self):
        self.assertEqual(validate_plan(self.plan), [])

    def test_numeric_dates(self):
        result = render_plan(self.plan)
        self.assertIn('26/10/2026', result)
        self.assertNotIn('2026-10-26', result)

    def test_exact_headers(self):
        header = render_plan(self.plan).splitlines()[2]
        self.assertEqual(header, '| Asignatura | Unidad | Sesión | Impartido | Día de estudio | Contenido | Páginas | Estudio y práctica | Examen y corrección | Pausa | Objetivo para comprobar lo aprendido |')

    def test_required_and_optional_totals(self):
        result = render_plan(self.plan)
        self.assertIn('Tiempo requerido estimado: 3 h 0 min', result)
        self.assertIn('Reserva opcional: 1 h 0 min', result)
        self.assertIn('Total con opcionales: 4 h 0 min', result)

    def test_exam_and_correction_combined(self):
        self.assertIn('| 60 min | 20 min | 10 min |', render_plan(self.plan))

    def test_invalid_calendar_date(self):
        self.plan['sessions'][0]['study_date'] = '2026-02-30'
        self.assert_invalid()

    def test_non_padded_date(self):
        self.plan['sessions'][0]['study_date'] = '2026-1-2'
        self.assert_invalid()

    def test_duplicate_session_ids(self):
        self.plan['sessions'][1]['id'] = self.plan['sessions'][0]['id']
        self.assert_invalid()

    def test_duplicate_source_ids(self):
        self.plan['sources'].append(deepcopy(self.plan['sources'][0]))
        self.assert_invalid()

    def test_missing_field(self):
        del self.plan['sessions'][0]['exam_minutes']
        self.assert_invalid()

    def test_unknown_field(self):
        self.plan['sessions'][0]['score'] = 50
        self.assert_invalid()

    def test_unknown_source(self):
        self.plan['sessions'][0]['source_refs'][0]['source_id'] = 'unknown'
        self.assert_invalid()

    def test_duplicate_reference(self):
        refs = self.plan['sessions'][0]['source_refs']
        refs.append(deepcopy(refs[0]))
        self.assert_invalid()

    def test_inverted_pages(self):
        self.plan['sessions'][0]['source_refs'][0]['pages'] = [{'start': 3, 'end': 1}]
        self.assert_invalid()

    def test_zero_page(self):
        self.plan['sessions'][0]['source_refs'][0]['pages'] = [{'start': 0, 'end': 1}]
        self.assert_invalid()

    def test_row_total_mismatch(self):
        self.plan['sessions'][0]['total_minutes'] = 12
        self.assert_invalid()

    def test_plan_total_mismatch(self):
        self.plan['totals']['required_minutes'] += 1
        self.assert_invalid()

    def test_missing_exam(self):
        self.plan['sessions'][0]['exam_minutes'] = 0
        self.assert_invalid()

    def test_missing_correction(self):
        self.plan['sessions'][0]['correction_minutes'] = 0
        self.assert_invalid()

    def test_boolean_is_not_number(self):
        for section, key in [('initial_knowledge', 'percent'), ('schedule', 'session_budget_minutes')]:
            with self.subTest(key=key):
                p = deepcopy(self.plan)
                p[section][key] = True
                self.assertTrue(validate_plan(p))
        self.plan['sessions'][0]['study_practice_minutes'] = True
        self.assert_invalid()

    def test_markdown_escaping(self):
        self.plan['sessions'][0]['content'] = '<script>|a\nb*_[x]`'
        result = render_plan(self.plan)
        self.assertIn('&lt;script&gt;&#124;a<br>b&#42;&#95;&#91;x&#93;&#96;', result)
        self.assertEqual(len(result.splitlines()[4].split('|')), 13)

    def test_unverified_pages(self):
        self.assertIn('Sin verificar', render_plan(self.plan))

    def test_taught_independent_of_knowledge(self):
        self.plan['initial_knowledge']['percent'] = 25
        self.plan['sessions'][0]['taught_status'] = 'not_taught'
        self.assertEqual(validate_plan(self.plan), [])
        self.assertIn('| No | 26/10/2026 |', render_plan(self.plan))

    def test_invalid_taught_state(self):
        self.plan['sessions'][0]['taught_status'] = 'learned'
        self.assert_invalid()

    def test_no_weekend_permission(self):
        for permission in [False, None]:
            self.plan['schedule']['weekends_allowed'] = permission
            self.assert_invalid()

    def test_same_date_multiple_subjects(self):
        self.plan['sessions'][1]['study_date'] = '2026-10-26'
        self.plan['sessions'][1]['subject'] = 'Biología'
        self.assertEqual(validate_plan(self.plan), [])

    def test_undated(self):
        self.plan['schedule']['start_date'] = None
        self.plan['schedule']['deadline_date'] = None
        for row in self.plan['sessions']:
            row['study_date'] = None
        self.assertEqual(validate_plan(self.plan), [])
        result = render_plan(self.plan)
        self.assertIn('Sin fecha', result)
        self.assertIn('Hay trabajo sin fecha', result)

    def test_date_bounds(self):
        self.plan['sessions'][0]['study_date'] = '2026-10-25'
        self.assert_invalid()
        self.plan['sessions'][0]['study_date'] = '2026-11-21'
        self.assert_invalid()

    def test_inverted_schedule_bounds(self):
        self.plan['schedule']['start_date'] = '2026-12-01'
        self.assert_invalid()

    def test_chronological_order(self):
        self.plan['sessions'][0], self.plan['sessions'][1] = self.plan['sessions'][1], self.plan['sessions'][0]
        self.assert_invalid()

    def test_budget_includes_everything(self):
        self.plan['schedule']['session_budget_minutes'] = 90
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['schedule']['session_budget_minutes'] = 89
        self.assert_invalid()

    def test_no_fixed_budget(self):
        row = self.plan['sessions'][0]
        row['study_practice_minutes'] += 30
        row['total_minutes'] += 30
        self.plan['totals']['required_minutes'] += 30
        self.plan['totals']['including_optional_minutes'] += 30
        self.assertEqual(validate_plan(self.plan), [])

    def test_buffer_is_optional(self):
        self.plan['sessions'][-1]['optional'] = False
        self.assert_invalid()

    def test_invalid_timezone(self):
        self.plan['timezone'] = 'Not/AZone'
        self.assert_invalid()

    def test_reject_non_finite_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text('{"x": NaN}')
            with self.assertRaises(ValueError):
                load_plan(path)

    def test_reject_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text('{"x": 1, "x": 2}')
            with self.assertRaises(ValueError):
                load_plan(path)

    def test_cli_validation_before_write(self):
        self.plan['sessions'][0]['exam_minutes'] = 0
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'bad.json'
            output = Path(tmp) / 'out.md'
            source.write_text(json.dumps(self.plan))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/render_plan.py'), str(source), '--output', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_cli_no_input_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'plan.json'
            source.write_text(json.dumps(self.plan))
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/render_plan.py'), str(source), '--output', str(source)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, source.read_bytes())

    def test_integral_float_integer_fields(self):
        def as_floats(value):
            if type(value) is int:
                return float(value)
            if isinstance(value, dict):
                return {key: as_floats(item) for key, item in value.items()}
            if isinstance(value, list):
                return [as_floats(item) for item in value]
            return value
        self.plan['schedule']['session_budget_minutes'] = 90
        self.plan['sessions'][0]['source_refs'][0]['pages'] = [{'start': 1, 'end': 2}]
        integral_plan = as_floats(self.plan)
        self.assertEqual(validate_plan(integral_plan), [])
        self.assertEqual(render_plan(integral_plan), render_plan(self.plan))
        integral_plan['sessions'][0]['exam_minutes'] = 15.5
        self.assertTrue(validate_plan(integral_plan))

    def test_whitespace_schema_and_api_agree(self):
        schema_name = 'plan-v1.0.schema.json' if self.plan['schema_version'] == '1.0' else 'plan.schema.json'
        schema = json.loads((ROOT / 'assets' / schema_name).read_text())
        pattern = schema['properties']['title']['pattern']
        self.assertIsNone(re.search(pattern, '  \t\n'))
        self.plan['title'] = '  \t\n'
        self.assert_invalid()
        self.plan['title'] = ' A title '
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['sources'][0]['locator'] = ' '
        self.assert_invalid()

    def test_nonfinite_direct_api(self):
        for value in [float('nan'), float('inf'), float('-inf')]:
            with self.subTest(value=value):
                self.plan['initial_knowledge']['percent'] = value
                self.assert_invalid()
                with self.assertRaises(ValueError):
                    render_plan(self.plan)

    def test_cli_no_hardlink_input_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'plan.json'
            output = Path(tmp) / 'alias.md'
            source.write_text(json.dumps(self.plan))
            os.link(source, output)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/render_plan.py'), str(source), '--output', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, source.read_bytes())
            self.assertEqual(before, output.read_bytes())

    def test_schema_adversarial_parity(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('Optional independent jsonschema package unavailable')
        schema_name = 'plan-v1.0.schema.json' if self.plan['schema_version'] == '1.0' else 'plan.schema.json'
        schema = json.loads((ROOT / 'assets' / schema_name).read_text())
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        variants = []
        integral = deepcopy(self.plan)
        integral['revision'] = 1.0
        variants.append((integral, True))
        for value in [True, 1.5]:
            variant = deepcopy(self.plan)
            variant['revision'] = value
            variants.append((variant, False))
        blank = deepcopy(self.plan)
        blank['title'] = ' '
        variants.append((blank, False))
        for variant, expected in variants:
            self.assertEqual(not list(validator.iter_errors(variant)), expected)
            self.assertEqual(not validate_plan(variant), expected)

    def test_schema_matches_example(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('Optional independent jsonschema package unavailable')
        schema_name = 'plan-v1.0.schema.json' if self.plan['schema_version'] == '1.0' else 'plan.schema.json'
        schema = json.loads((ROOT / 'assets' / schema_name).read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(self.plan)



class DefaultsTests(unittest.TestCase):
    """Version 1.2 defaults are explicit, dated, and plan-local."""
    def setUp(self):
        self.plan = load_plan(ROOT / 'assets/example-plan.json')
        self.plan['schema_version'] = '1.2'
        self.plan['source_snapshot'] = None
        for row in self.plan['sessions']:
            row.pop('practice_prompt', None)

    def assert_invalid(self):
        self.assertTrue(validate_plan(self.plan))

    def recalculate(self):
        for row in self.plan['sessions']:
            row['total_minutes'] = sum(row[key] for key in ['study_practice_minutes', 'exam_minutes', 'correction_minutes', 'break_minutes'])
        required = sum(row['total_minutes'] for row in self.plan['sessions'] if not row['optional'])
        optional = sum(row['total_minutes'] for row in self.plan['sessions'] if row['optional'])
        self.plan['totals'] = {'required_minutes': required, 'optional_minutes': optional, 'including_optional_minutes': required + optional}

    def same_day(self):
        self.plan['sessions'][1]['study_date'] = self.plan['sessions'][0]['study_date']
        self.plan['sessions'][1]['subject'] = 'Otra asignatura en el mismo plan'

    def test_new_example_valid_and_uncapped_daily_default(self):
        self.assertEqual(self.plan['schema_version'], '1.2')
        self.assertEqual(validate_plan(self.plan), [])
        schedule = self.plan['schedule']
        self.assertEqual(schedule['start_date'], self.plan['generated_on'])
        self.assertTrue(schedule['weekends_allowed'])
        self.assertIsNone(schedule['daily_budget_minutes'])
        self.assertEqual(schedule['provenance']['daily_budget_minutes'], 'explicit_uncapped')
        self.assertIsNone(schedule['session_budget_minutes'])

    def test_two_sessions_same_day_pass_without_fixed_daily_cap(self):
        self.same_day()
        self.assertEqual(validate_plan(self.plan), [])

    def test_same_day_over_former_default_cap_passes_when_uncapped(self):
        self.same_day()
        self.plan['sessions'][1]['study_practice_minutes'] += 1
        self.recalculate()
        self.assertEqual(validate_plan(self.plan), [])

    def test_optional_work_counts_when_capacity_is_explicit(self):
        self.same_day()
        self.plan['sessions'][-1]['study_date'] = self.plan['sessions'][0]['study_date']
        self.plan['schedule']['daily_budget_minutes'] = 180
        self.plan['schedule']['provenance']['daily_budget_minutes'] = 'provided'
        self.assert_invalid()
        self.plan['schedule']['daily_budget_minutes'] = 240
        self.assertEqual(validate_plan(self.plan), [])

    def test_daily_custom_capacity(self):
        self.plan['schedule']['daily_budget_minutes'] = 89
        self.plan['schedule']['provenance']['daily_budget_minutes'] = 'provided'
        self.assert_invalid()
        self.plan['schedule']['daily_budget_minutes'] = 90
        self.assertEqual(validate_plan(self.plan), [])

    def test_uncapped_requires_explicit_provenance(self):
        self.same_day()
        self.plan['sessions'][-1]['study_date'] = self.plan['sessions'][0]['study_date']
        self.plan['schedule']['daily_budget_minutes'] = None
        self.plan['schedule']['provenance']['daily_budget_minutes'] = 'provided'
        self.assert_invalid()
        self.plan['schedule']['provenance']['daily_budget_minutes'] = 'explicit_uncapped'
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['schedule']['daily_budget_minutes'] = 240
        self.assert_invalid()

    def test_uncapped_capacity_cannot_claim_numeric_value(self):
        self.plan['schedule']['daily_budget_minutes'] = 181
        self.assert_invalid()

    def test_session_budget_is_separate(self):
        self.same_day()
        self.plan['schedule']['session_budget_minutes'] = 90
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['schedule']['session_budget_minutes'] = 89
        self.assert_invalid()

    def test_missing_exam_field(self):
        del self.plan['schedule']['exam_date']
        self.assert_invalid()

    def test_null_exam_for_dated_request(self):
        self.plan['schedule']['exam_date'] = None
        self.assert_invalid()

    def test_invalid_exam_date(self):
        self.plan['schedule']['exam_date'] = '2026-02-30'
        self.assert_invalid()

    def test_past_and_same_day_exam(self):
        for value in ['2026-10-25', '2026-10-26', '0001-01-01']:
            with self.subTest(value=value):
                self.plan['schedule']['exam_date'] = value
                self.assert_invalid()

    def test_exam_day_is_not_study_day(self):
        self.plan['sessions'][-1]['study_date'] = self.plan['schedule']['exam_date']
        self.assert_invalid()

    def test_completion_deadline_precedes_exam(self):
        self.plan['schedule']['provenance']['deadline_date'] = 'provided'
        self.plan['schedule']['deadline_date'] = self.plan['schedule']['exam_date']
        self.assert_invalid()

    def test_derived_deadline_must_be_previous_day(self):
        self.plan['schedule']['deadline_date'] = '2026-11-18'
        self.assert_invalid()
        self.plan['schedule']['provenance']['deadline_date'] = 'provided'
        self.plan['sessions'][-1]['study_date'] = '2026-11-18'
        self.assertEqual(validate_plan(self.plan), [])

    def test_dated_rows_cannot_silently_be_undated(self):
        self.plan['sessions'][0]['study_date'] = None
        self.assert_invalid()

    def test_explicit_undated_breakdown(self):
        schedule = self.plan['schedule']
        schedule['mode'] = 'undated'
        for key in ['start_date', 'exam_date', 'deadline_date']:
            schedule[key] = None
            schedule['provenance'][key] = 'not_applicable'
        for row in self.plan['sessions']:
            row['study_date'] = None
        self.assertEqual(validate_plan(self.plan), [])
        self.assertIn('Sin fecha', render_plan(self.plan))
        self.assertNotIn('Fecha de examen aportada:', render_plan(self.plan))
        self.plan['sessions'][0]['study_date'] = '2026-10-26'
        self.assert_invalid()

    def test_default_weekends_and_explicit_false(self):
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['schedule']['weekends_allowed'] = False
        self.assert_invalid()
        self.plan['schedule']['provenance']['weekends_allowed'] = 'provided'
        self.assert_invalid()  # Example includes a Saturday.
        self.plan['sessions'][1]['study_date'] = '2026-10-30'
        self.assertEqual(validate_plan(self.plan), [])

    def test_explicit_start_overrides_today_default(self):
        self.plan['schedule']['start_date'] = '2026-10-25'
        self.assert_invalid()
        self.plan['schedule']['provenance']['start_date'] = 'provided'
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['schedule']['start_date'] = '2026-10-27'
        self.assert_invalid()  # The first row must also be moved when replanning.

    def test_execution_local_date_is_recorded_not_hardcoded(self):
        # Saved artifacts validate against their recorded execution, not the machine clock.
        self.plan['generated_on'] = '2027-01-04'
        schedule = self.plan['schedule']
        schedule['start_date'] = '2027-01-04'
        schedule['exam_date'] = '2027-02-01'
        schedule['deadline_date'] = '2027-01-31'
        for index, row in enumerate(self.plan['sessions']):
            row['study_date'] = ['2027-01-04', '2027-01-09', '2027-01-30'][index]
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['schedule']['start_date'] = '2026-10-26'
        self.assert_invalid()

    def test_required_provenance(self):
        del self.plan['schedule']['provenance']
        self.assert_invalid()

    def test_render_defaults_and_exam_are_distinct(self):
        output = render_plan(self.plan)
        self.assertIn('Fecha de examen aportada: 20/11/2026', output)
        self.assertIn('Fecha objetivo de finalización: 19/11/2026', output)
        self.assertIn('Capacidad diaria: sin límite diario por petición explícita', output)
        self.assertIn('Fines de semana: incluidos', output)
        self.assertIn('inicio=default_today', output)

    def test_unknown_version_rejected(self):
        self.plan['schema_version'] = '9.0'
        self.assert_invalid()

    def test_skill_instruction_defaults_and_questions(self):
        skill = (ROOT / 'SKILL.md').read_text()
        rules = (ROOT / 'references/planning-rules.md').read_text()
        self.assertIn('one question at a time, then STOP', skill)
        self.assertIn('today at execution', skill)
        self.assertIn('weekends to allowed', skill)
        self.assertIn('former 180-minute cap by default', skill)
        self.assertIn('never hardcode', skill)
        self.assertIn('repository-root absolute path', skill)
        self.assertIn('direct GitHub blob URL', skill)
        self.assertIn('A bare relative locator is insufficient in the prompt', (ROOT / 'references/data-contract.md').read_text())
        self.assertIn('explicit request for an undated content breakdown', rules)

    def test_new_schema_example_independent_when_available(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('Optional independent jsonschema package unavailable')
        plan = load_plan(ROOT / 'assets/example-plan.json')
        schema = json.loads((ROOT / 'assets/plan.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(plan)

    def test_source_snapshot_is_required(self):
        self.plan.pop('source_snapshot')
        self.assert_invalid()

    def test_portable_snapshot_must_be_null(self):
        self.assertIsNone(self.plan['source_snapshot'])
        self.assertEqual(validate_plan(self.plan), [])

    def test_github_snapshot_requires_exact_object(self):
        self.plan['source_snapshot'] = {'repository': 'otromas1234/material-asignaturas', 'tag': 'materials-2026-10-28'}
        self.assertEqual(validate_plan(self.plan), [])
        self.plan['source_snapshot']['branch'] = 'main'
        self.assert_invalid()

    def test_v1_1_is_not_a_supported_compatibility_version(self):
        self.plan['schema_version'] = '1.1'
        self.assert_invalid()

    def test_markdown_renders_snapshot_from_json(self):
        output = render_plan(self.plan)
        self.assertIn('Snapshot de materiales: no aplica (exportación portable).', output)
        self.plan['source_snapshot'] = {'repository': 'otromas1234/material-asignaturas', 'tag': 'materials-2026-10-28'}
        output = render_plan(self.plan)
        self.assertIn('Snapshot de materiales: otromas1234/material-asignaturas@materials-2026-10-28.', output)
        self.assertEqual(output.count('materials-2026-10-28'), 1)

    def test_markdown_derives_source_references_from_json(self):
        output = render_plan(self.plan)
        source = self.plan['sources'][0]
        self.assertIn(source['title'], output)
        if source['locator'] is not None:
            self.assertIn(source['locator'], output)
        else:
            self.assertIn('ubicación no especificada', output)


class PracticePromptSchemaTests(unittest.TestCase):
    """The new producer contract requires one prompt per scoped session."""

    def setUp(self):
        self.plan = load_plan(ROOT / 'assets/example-plan.json')
        self.plan['schema_version'] = '1.2'
        for row in self.plan['sessions']:
            row.pop('practice_prompt', None)

    def test_current_example_is_v1_3_and_session_scoped(self):
        example = load_plan(ROOT / 'assets/example-plan.json')
        self.assertEqual(example['schema_version'], '1.3')
        self.assertEqual(validate_plan(example), [])
        for row in example['sessions']:
            prompt = row['practice_prompt']
            self.assertIn('material-estudio-practicar', prompt)
            self.assertIn(row['subject'], prompt)
            self.assertIn(row['id'], prompt)
            self.assertIn(row['content'], prompt)
            self.assertIn('EXCLUSIVAMENTE', prompt)
            self.assertIn('/asignaturas/historia/contenidos/example-unit.txt', prompt)
            self.assertIn('example-owner/example-materials', prompt)
            self.assertIn('plan/historia/20261026-synthetic', prompt)
            self.assertIn('https://github.com/example-owner/example-materials/blob/plan/historia/20261026-synthetic/asignaturas/historia/contenidos/example-unit.txt', prompt)
            for other in example['sessions']:
                if other['id'] != row['id']:
                    self.assertNotIn(other['id'], prompt)
                    self.assertNotIn(other['content'], prompt)

    def test_v1_2_rejects_unrecognized_prompt(self):
        self.plan['sessions'][0]['practice_prompt'] = 'Only this session.'
        self.assertTrue(any('practice_prompt' in error for error in validate_plan(self.plan)))

    def test_v1_2_without_prompts_remains_valid(self):
        self.assertEqual(validate_plan(self.plan), [])

    def test_v1_3_requires_nonempty_prompt_in_every_session_kind(self):
        self.plan['schema_version'] = '1.3'
        for row in self.plan['sessions']:
            row['practice_prompt'] = f'Only {row["id"]}: {row["content"]}'
        self.assertEqual(validate_plan(self.plan), [])
        for index, row in enumerate(self.plan['sessions']):
            with self.subTest(kind=row['kind']):
                candidate = deepcopy(self.plan)
                del candidate['sessions'][index]['practice_prompt']
                self.assertTrue(any('practice_prompt' in error for error in validate_plan(candidate)))
                for invalid in ['', '  \n', None, 17]:
                    candidate = deepcopy(self.plan)
                    candidate['sessions'][index]['practice_prompt'] = invalid
                    self.assertTrue(any('practice_prompt' in error for error in validate_plan(candidate)))

    def test_v1_3_markdown_renders_exact_prompt_for_each_session(self):
        self.plan['schema_version'] = '1.3'
        prompts = [
            'Examine <unit>|[a] & b\\nOnly block-1; never block-2.',
            'Use ``` literal code and review content only.',
            'Optional buffer only; do not include other sessions.',
        ]
        for row, prompt in zip(self.plan['sessions'], prompts):
            row['practice_prompt'] = prompt
        output = render_plan(self.plan)
        self.assertEqual(output.count('Prompt de práctica de examen'), 3)
        for row, prompt in zip(self.plan['sessions'], prompts):
            self.assertIn(row['id'], output)
            self.assertIn(prompt, output)
        self.assertLess(output.index(prompts[0]), output.index(prompts[1]))
        self.assertLess(output.index(prompts[1]), output.index(prompts[2]))

    def test_v1_2_markdown_has_no_prompt_section(self):
        self.assertNotIn('Prompt de práctica de examen', render_plan(self.plan))


class LifecycleTests(unittest.TestCase):
    """Validation is observational; publication remains an LLM contract, not an API."""
    def setUp(self):
        self.plan = load_plan(ROOT / 'assets/example-plan.json')
        self.plan.pop('lifecycle_status', None)

    def test_legacy_absence_is_valid_without_inserting_active(self):
        before = deepcopy(self.plan)
        self.assertEqual(validate_plan(self.plan), [])
        self.assertEqual(self.plan, before)
        self.assertNotIn('lifecycle_status', self.plan)

    def test_explicit_active_and_deleted_are_valid_without_mutation(self):
        for status in ['active', 'deleted']:
            with self.subTest(status=status):
                self.plan['lifecycle_status'] = status
                before = deepcopy(self.plan)
                self.assertEqual(validate_plan(self.plan), [])
                self.assertEqual(self.plan, before)

    def test_invalid_lifecycle_is_rejected_without_mutation(self):
        for status in ['archived', 'Active', '', None, True, 1, [], {}]:
            with self.subTest(status=status):
                self.plan['lifecycle_status'] = status
                before = deepcopy(self.plan)
                errors = validate_plan(self.plan)
                self.assertTrue(any('$.lifecycle_status' in error for error in errors))
                self.assertEqual(self.plan, before)

    def test_schema_lifecycle_is_optional_and_closed(self):
        schema = json.loads((ROOT / 'assets/plan.schema.json').read_text())
        self.assertNotIn('lifecycle_status', schema['required'])
        self.assertEqual(schema['properties']['lifecycle_status'], {
            'type': 'string', 'enum': ['active', 'deleted']})
        self.assertIs(schema['additionalProperties'], False)

    def test_cli_validation_preserves_deleted_file_and_creates_no_artifacts(self):
        self.plan['lifecycle_status'] = 'deleted'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'plan.json'
            path.write_text(json.dumps(self.plan), encoding='utf-8')
            before = path.read_bytes()
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/validate_plan.py'), str(path)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(tmp).iterdir()), [path])

    def test_render_preserves_deleted_input(self):
        self.plan['lifecycle_status'] = 'deleted'
        before = deepcopy(self.plan)
        self.assertIn(self.plan['title'], render_plan(self.plan))
        self.assertEqual(self.plan, before)

    def test_publication_guidance_contract_not_executable_publisher(self):
        # Instruction checks do not prove actual remote side effects.
        skill = (ROOT / 'SKILL.md').read_text()
        rules = (ROOT / 'references/planning-rules.md').read_text()
        contract = (ROOT / 'references/data-contract.md').read_text()
        self.assertIn('lifecycle_status: active', skill)
        for phrase in ['Every newly published version', 'reads, validation, and no-op',
                       'zero writes or commits', 'not published', 'no executable publisher',
                       'manual/contract verification']:
            self.assertIn(phrase, rules)
        self.assertIn('absence means active', contract)

if __name__ == '__main__':
    unittest.main()

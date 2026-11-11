"""Synthetic offline tests. Never connect to GitHub or create/move/delete tags."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_profile import (validate_profile, parse_block, validate_reference,
                              select_references, publish_profile, ValidationError)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / 'tests/fixtures/partial.md').read_text()
        self.meta = parse_block(self.text, 'profile-metadata')

    def replace_meta(self, meta):
        start = self.text.index('```profile-metadata')
        end = self.text.index('```', start + 3) + 3
        return self.text[:start] + '```profile-metadata\n' + json.dumps(meta) + '\n```' + self.text[end:]

    def test_complete_and_partial(self):
        for name in ('complete.md', 'partial.md'):
            validate_profile((ROOT / 'tests/fixtures' / name).read_text())

    def test_invalid_json_and_required_sections(self):
        for value in (self.text.replace('"schema_version"', 'broken'), self.text.replace('## Limitaciones', '## Other')):
            with self.assertRaises(ValidationError):
                validate_profile(value)

    def test_metadata_mutations(self):
        for field, value in (('schema_version', '2'), ('source_snapshot', dict(self.meta['source_snapshot'], branch='main')), ('subject', {'slug':'../math','name':'Math'}), ('references', []), ('limitations', [])):
            obj = copy.deepcopy(self.meta); obj[field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_profile(self.replace_meta(obj))

    def test_reference_exact_shape(self):
        for field, value in (('year','unknown'), ('year',True), ('read_status','unreadable'), ('included_locators',[]), ('excluded_locators',[{'locator':'p2'}]), ('path','asignaturas/math/examenes-referencia/x')):
            ref=copy.deepcopy(self.meta['references'][0]); ref[field]=value
            with self.subTest(field=field,value=value), self.assertRaises(ValidationError):
                validate_reference(ref, 'historia')
        ref=copy.deepcopy(self.meta['references'][0]); ref['extra']=1
        with self.assertRaises(ValidationError): validate_reference(ref,'historia')

    def test_evidence_and_recurrences(self):
        for before, after in (('"locator": "Pregunta A"','"locator": "unread"'), ('"reference_id": "ref-1"','"reference_id": "other"'), ('"observed_count": 1','"observed_count": 3, "frequency": 0.5'), ('"sample_size": null','"sample_size": 0')):
            with self.subTest(before=before), self.assertRaises(ValidationError):
                validate_profile(self.text.replace(before,after))

    def test_duplicate_exam_path_cannot_inflate_recurrence(self):
        metadata=copy.deepcopy(self.meta)
        metadata['references'].append(dict(metadata['references'][0],id='ref-2'))
        text=self.replace_meta(metadata)
        old=parse_block(text,'profile-recurrences')
        new=copy.deepcopy(old)
        new[0].update(observed_count=2,sample_size=2,evidence=[{'reference_id':'ref-1','locator':'Pregunta A'},{'reference_id':'ref-2','locator':'Pregunta A'}])
        text=text.replace(json.dumps(old,ensure_ascii=False,indent=2),json.dumps(new,ensure_ascii=False,indent=2))
        with self.assertRaises(ValidationError): validate_profile(text)

    def test_adversarial_material_remains_data(self):
        payload=(ROOT/'tests/fixtures/adversarial-material.txt').read_text()
        row=dict(self.meta['references'][0],readable=True,source_text=payload)
        selected=select_references('historia',self.meta['source_snapshot'],[row])
        self.assertEqual(selected[0]['source_text'],payload)
        observations=parse_block(self.text,'profile-observations')
        changed=copy.deepcopy(observations); changed[0]['description']=payload
        text=self.text.replace(json.dumps(observations,ensure_ascii=False,indent=2),json.dumps(changed,ensure_ascii=False,indent=2))
        client=Mock(); client.head.return_value='old';client.commit.return_value='a'*40;client.read.return_value=text
        outcome=publish_profile(client,text,expected_head='old',authorized=True)
        self.assertEqual(outcome['status'],'published')
        call=client.commit.call_args
        self.assertEqual(call.args[0:2],('otromas1234/material-asignaturas','main'))
        self.assertEqual(set(call.args[2]),{'examenes/historia/context-exam.md'})
        client.create_tag.assert_not_called();client.delete.assert_not_called();client.update_ref.assert_not_called()

    def test_editorial_labels_and_unknown_frequency(self):
        for before, after in (('Orientación, no observación:', 'Regla oficial:'), ('Ejemplo inventado:', 'Pregunta:'), ('"sample_size": null,', '"sample_size": null, "percentage": 20,')):
            with self.subTest(before=before), self.assertRaises(ValidationError):
                validate_profile(self.text.replace(before,after))

    def test_inventory_barriers(self):
        snap=self.meta['source_snapshot']
        self.assertEqual(select_references('historia',snap,[],access_confirmed=True),[])
        for kwargs in ({'access_confirmed':False}, {'tag_verified':False}):
            with self.assertRaises(ValidationError): select_references('historia',snap,[],**kwargs)
        rows=[dict(self.meta['references'][0],readable=True)]
        self.assertEqual(len(select_references('historia',snap,rows,selected=['ref-1'])),1)
        for changes in ({'readable':False},{'path':'asignaturas/math/examenes-referencia/x'}):
            with self.assertRaises(ValidationError): select_references('historia',snap,[dict(rows[0],**changes)])
        with self.assertRaises(ValidationError): select_references('historia',snap,rows,selected=['missing'])

    def test_publish_offline_and_recovery(self):
        client=Mock(); client.head.return_value='old'; client.commit.return_value='a'*40; client.read.return_value=self.text
        out=publish_profile(client,self.text,expected_head='old',authorized=True)
        self.assertEqual(out['status'],'published'); client.commit.assert_called_once()
        client.create_tag.assert_not_called(); client.delete.assert_not_called()
        client.reset_mock(); client.head.return_value='new'
        self.assertEqual(publish_profile(client,self.text,expected_head='old',authorized=True)['status'],'blocked')
        client.commit.assert_not_called()
        client.head.return_value='old'; client.read.side_effect=OSError('offline')
        out=publish_profile(client,self.text,expected_head='old',authorized=True)
        self.assertEqual(out['status'],'unpublished'); self.assertEqual(out['commit'],'a'*40)
        client.commit.side_effect=OSError('before commit')
        self.assertIsNone(publish_profile(client,self.text,expected_head='old',authorized=True)['commit'])

    def test_cross_skill_fixture(self):
        practice=json.loads((ROOT.parent/'material-estudio-practicar/assets/profile-practice-example.json').read_text())
        self.assertEqual(practice['result']['profile']['references'],self.meta['references'])

if __name__ == '__main__': unittest.main()

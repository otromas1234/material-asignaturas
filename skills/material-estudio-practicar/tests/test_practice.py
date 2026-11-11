"""Offline synthetic tests only: no GitHub I/O or tag mutations permitted."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_practice import (ValidationError,validate_data,validate_directory,
                               resolve_context,publish_practice,practice_path)
from render_practice import render

class PracticeTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'assets/practice-example.json').read_text())

    def test_fixtures_general_and_profile(self):
        validate_data(self.data)
        validate_data(json.loads((ROOT/'assets/profile-practice-example.json').read_text()))

    def test_result_required_extra_types(self):
        for key in self.data['result']:
            obj=copy.deepcopy(self.data); del obj['result'][key]
            with self.subTest(key=key),self.assertRaises(ValidationError): validate_data(obj)
        for key,value in (('extra',1),('practice_mode','unknown'),('corrected_at','2026-10-30'),('source_refs',[]),('profile',{})):
            obj=copy.deepcopy(self.data); obj['result'][key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError): validate_data(obj)

    def test_nonfinite_and_score_invariants(self):
        for val in (float('nan'),float('inf'),-1,5,True):
            obj=copy.deepcopy(self.data); obj['result']['questions'][0]['score']=val
            with self.subTest(val=val),self.assertRaises(ValidationError): validate_data(obj)
        for key in ('total','max','assessed_total','assessed_max'):
            obj=copy.deepcopy(self.data); obj['result']['score'][key]=99
            with self.subTest(key=key),self.assertRaises(ValidationError): validate_data(obj)
        obj=copy.deepcopy(self.data); obj['result']['questions'][0]['rubric'][0]['awarded_score']=0
        with self.assertRaises(ValidationError): validate_data(obj)

    def test_identity_snapshot_and_ids(self):
        for part,key,value in (('submission','student',{'id':'other','name':'Other'}),('result','source_snapshot',{'repository':'other/repo','tag':'x'}),('exam','practice_id','../escape'),('exam','created_at','2026-02-30T12:00:00+01:00')):
            obj=copy.deepcopy(self.data); obj[part][key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError): validate_data(obj)
        obj=copy.deepcopy(self.data); obj['submission']['answers'][0]['question_id']='other'
        with self.assertRaises(ValidationError): validate_data(obj)

    def test_context_absence_not_access_failure(self):
        exam=self.data['exam']; sources=[{'id':'src-1','path':exam['source_refs'][0]['path'],'locators':['Intercambio'],'text':'Fuente real simulada sobre intercambio.'}]
        kwargs=dict(subject='historia',snapshot=exam['source_snapshot'],source_refs=exam['source_refs'],sources=sources,profile_status='absent')
        self.assertIsNone(resolve_context(**kwargs)['profile'])
        for change in ({'access_confirmed':False},{'tag_verified':False},{'sources':[]},{'profile_status':'access_error'},{'sources':[dict(sources[0],text='')]},{'sources':[dict(sources[0],locators=['Missing'])]}):
            with self.subTest(change=change),self.assertRaises(ValidationError): resolve_context(**dict(kwargs,**change))
        profile=json.loads((ROOT/'assets/profile-practice-example.json').read_text())['exam']['profile']
        self.assertEqual(resolve_context(**dict(kwargs,profile_status='present',profile=profile))['profile'],profile)
        profile['source_snapshot']['tag']='different'
        with self.assertRaises(ValidationError): resolve_context(**dict(kwargs,profile_status='present',profile=profile))
        with self.assertRaises(ValidationError): resolve_context(**dict(kwargs,plan_snapshot=dict(exam['source_snapshot'],tag='old')))

    def test_image_paths(self):
        for path in ('../x','/private/x','https://x','submission/../x','submission\\x','submission//x','submission/.gitkeep'):
            obj=copy.deepcopy(self.data); obj['submission']['answers'][0]['images']=[path]
            with self.subTest(path=path),self.assertRaises(ValidationError): validate_data(obj)

    def test_inconclusive_image_not_zero(self):
        obj=copy.deepcopy(self.data); obj['exam']['questions'][0].update(requires_image=True,response_mode='paper_image')
        obj['submission']['answers'][0]['images']=['submission/answer.png']
        q=obj['result']['questions'][0]; q.update(status='not_assessable',score=None)
        for c in q['rubric']: c['awarded_score']=None
        obj['result'].update(status='inconclusive',score={'total':None,'max':4,'assessed_total':1.5,'assessed_max':2},limitations=[{'code':'unreadable_image','question_id':'q1','image_path':'submission/answer.png','description':'No se puede interpretar la imagen.','prevents_conclusive_grading':True}])
        validate_data(obj)
        bad=copy.deepcopy(obj); bad['result']['questions'][0]['score']=0
        with self.assertRaises(ValidationError): validate_data(bad)
        bad=copy.deepcopy(obj); bad['result']['limitations']=[]
        with self.assertRaises(ValidationError): validate_data(bad)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValidationError): render(obj,Path(tmp)/'missing-image')

    def test_render_no_key_html_safe_and_draft(self):
        obj=copy.deepcopy(self.data); obj['exam']['questions'][0]['prompt']='<script>alert(1)</script> & "x"'
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'practice'; render(obj,out)
            html=(out/'exam.html').read_text(); md=(out/'exam.md').read_text()
            self.assertIn('&lt;script&gt;',html); self.assertNotIn('<script>',html)
            for text in (html,md):
                self.assertNotIn('SYNTHETIC_PRIVATE_KEY',text); self.assertNotIn('awarded_score',text)
                self.assertIn('ni pretende imitar',text)
            self.assertNotIn('<form',html); self.assertNotIn('src=',html)
            from html import unescape
            self.assertIn('SYNTHETIC_PRIVATE_KEY',unescape((out/'result.md').read_text()))
            validate_directory(out)
            with self.assertRaises(ValidationError): render(obj,out)
        obj['submission'].update(status='draft',submitted_at=None); obj['result']=None
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'draft'; render(obj,out)
            self.assertFalse((out/'result.json').exists()); validate_directory(out)
        obj['result']=self.data['result']
        with self.assertRaises(ValidationError): validate_data(obj)

    def test_graded_question_cannot_have_applicable_blocking_limitation(self):
        obj=copy.deepcopy(self.data)
        obj['exam']['questions'][0].update(requires_image=True,response_mode='paper_image')
        obj['submission']['answers'][0]['images']=['submission/q1.png']
        obj['result']['questions'][1].update(status='not_assessable',score=None)
        for criterion in obj['result']['questions'][1]['rubric']: criterion['awarded_score']=None
        obj['result'].update(status='inconclusive',score={'total':None,'max':4,'assessed_total':1.5,'assessed_max':2},limitations=[
            {'code':'unreadable_image','question_id':'q1','image_path':'submission/q1.png','description':'Imagen de q1 ilegible.','prevents_conclusive_grading':True},
            {'code':'missing_capability','question_id':'q2','image_path':None,'description':'No se puede evaluar q2.','prevents_conclusive_grading':True}])
        with self.assertRaises(ValidationError): validate_data(obj)
        obj['result']['limitations'][0]['question_id']=None
        with self.assertRaises(ValidationError): validate_data(obj)

    def test_safe_retry_reconciles_by_sha_without_duplicate_commit(self):
        client=Mock();client.private=False;client.head.return_value='old';client.commit.return_value='c'*40
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'practice';render(self.data,out)
            files={practice_path(self.data['exam'])+'/'+p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file()}
            client.read.side_effect=OSError('verification unavailable after commit')
            initial=publish_practice(client,out,authorized=True,expected_head='old')
            self.assertEqual(initial['status'],'unpublished');self.assertEqual(initial['commit'],'c'*40)
            client.commit.assert_called_once()
            client.read.reset_mock()
            client.read.side_effect=lambda repo,path,sha:files[path] if sha=='c'*40 else b'wrong revision'
            retry=publish_practice(client,out,authorized=True,expected_head='new-head',known_commit=initial['commit'])
            self.assertEqual(retry['status'],'published');self.assertEqual(retry['commit'],'c'*40)
            client.commit.assert_called_once()
            self.assertEqual({call.args[1] for call in client.read.call_args_list},set(files))
            self.assertTrue(all(call.args[2]=='c'*40 for call in client.read.call_args_list))
            client.read.side_effect=lambda repo,path,sha:b'mismatch'
            failed=publish_practice(client,out,authorized=True,known_commit=initial['commit'])
            self.assertEqual(failed['status'],'unpublished');client.commit.assert_called_once()
            client.create_tag.assert_not_called();client.delete.assert_not_called()

    def test_profile_reference_loss_rejected(self):
        obj=json.loads((ROOT/'assets/profile-practice-example.json').read_text())
        expected=copy.deepcopy(obj['exam']['profile']['references'])
        self.assertEqual(obj['result']['profile']['references'],expected)
        obj['result']['profile']['references'][0]['excluded_locators']=[]
        with self.assertRaises(ValidationError): validate_data(obj)

    def test_batch_collision_and_submission_folder(self):
        self.assertEqual(practice_path(self.data['exam']),'alumnos/synthetic-student/asignaturas/historia/examenes/20261030-1200-synthetic')
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'practice'; render(self.data,out)
            self.assertEqual({x.name for x in out.iterdir()},{'exam.md','exam.html','submission.json','submission','result.json','result.md'})
            self.assertTrue((out/'submission/.gitkeep').exists())
            (out/'exam.md').write_text('tampered')
            with self.assertRaises(ValidationError): validate_directory(out)

    def test_schema_parity_and_exact_shared_contract(self):
        from contract import validate_named, validate_schema, load_json
        other=ROOT.parent/'material-estudio-perfil-examen/assets/profile-reference.schema.json'
        self.assertEqual((ROOT/'assets/profile-reference.schema.json').read_bytes(),other.read_bytes())
        for name,part in (('exam','exam'),('submission','submission'),('result','result')):
            validate_named(self.data[part],name)
            schema=load_json((ROOT/'assets'/f'{name}.schema.json').read_text())
            for key in schema['required']:
                broken=copy.deepcopy(self.data[part]); del broken[key]
                with self.assertRaises(ValidationError): validate_schema(broken,schema)
        obj=copy.deepcopy(self.data); obj['exam']['questions'][0]['requires_image']='yes'
        with self.assertRaises(ValidationError): validate_data(obj)

    def test_response_modes_and_empty_answer(self):
        for mode in ('chat','paper_image','graph_text','graph_image'):
            obj=copy.deepcopy(self.data)
            obj['exam']['questions'][0].update(response_mode=mode,requires_image=mode in ('paper_image','graph_image'))
            validate_data(obj)
        obj=copy.deepcopy(self.data)
        obj['submission']['answers'][0]['text']=None
        obj['result']['questions'][0]['score']=0
        for criterion in obj['result']['questions'][0]['rubric']: criterion['awarded_score']=0
        obj['result']['score'].update(total=1.5,assessed_total=1.5)
        validate_data(obj)

    def test_attachment_binary_and_symlink(self):
        obj=copy.deepcopy(self.data)
        obj['submission']['answers'][0]['images']=['submission/answer.png']
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'source/submission').mkdir(parents=True)
            # Tiny deterministic image fixture, not a student image.
            import base64
            (root/'source/submission/answer.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZ2kAAAAASUVORK5CYII='))
            render(obj,root/'with-image',attachments_dir=root/'source')
            validate_directory(root/'with-image')
            (root/'source/submission/answer.png').unlink()
            (root/'source/submission/answer.png').symlink_to(root/'with-image/submission/answer.png')
            with self.assertRaises(ValidationError): render(obj,root/'bad',attachments_dir=root/'source')

    def test_pedagogical_fixture_evidence(self):
        matrix=json.loads((ROOT/'assets/evidence-matrix.json').read_text())
        self.assertEqual({row['question_id'] for row in matrix},{q['id'] for q in self.data['exam']['questions']})
        self.assertEqual({row['difficulty'] for row in matrix},{'usual','demanding'})
        self.assertEqual({c for row in matrix for c in row['key_concepts']},set(self.data['exam']['scope']['key_concepts']))
        source=(ROOT/'tests/fixtures/source.txt').read_text()
        for question in self.data['exam']['questions']:
            self.assertNotIn(question['prompt'],source)
        self.assertTrue(all(row['original'] and not row['predicts_recurrence'] for row in matrix))

    def test_publish_mock_only(self):
        client=Mock(); client.private=False; client.head.return_value='old'; client.commit.return_value='b'*40
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'practice'; render(self.data,out)
            files={p.relative_to(out).as_posix():p.read_bytes() for p in out.rglob('*') if p.is_file()}
            prefix=practice_path(self.data['exam'])+'/'
            client.read.side_effect=lambda repo,path,sha:files[path[len(prefix):]]
            self.assertEqual(publish_practice(client,out,authorized=False,expected_head='old')['status'],'unpublished'); client.commit.assert_not_called()
            self.assertEqual(publish_practice(client,out,authorized=True,expected_head='old')['status'],'published')
            client.create_tag.assert_not_called(); client.delete.assert_not_called()
            client.head.return_value='new'; client.reset_mock()
            self.assertEqual(publish_practice(client,out,authorized=True,expected_head='old')['status'],'blocked'); client.commit.assert_not_called()
            client.head.return_value='old'; client.read.side_effect=OSError('offline')
            result=publish_practice(client,out,authorized=True,expected_head='old')
            self.assertEqual(result['status'],'unpublished'); self.assertEqual(result['commit'],'b'*40)
            client.commit.side_effect=OSError('before commit')
            result=publish_practice(client,out,authorized=True,expected_head='old')
            self.assertEqual(result['status'],'unpublished'); self.assertIsNone(result['commit'])

if __name__=='__main__': unittest.main()

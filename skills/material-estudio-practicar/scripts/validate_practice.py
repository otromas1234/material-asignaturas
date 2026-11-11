"""Validate local practice artifacts and provenance. No remote I/O without an injected adapter."""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import re
import sys
from contract import (ValidationError, require, load_json, validate_named,
                      validate_reference, validate_snapshot, unique_ids,
                      safe_path, slug, REPOSITORY, BRANCH)

GENERAL_NOTICE = 'Práctica general; no está basada en exámenes del centro ni pretende imitar su estilo.'


def practice_path(exam):
    return ('alumnos/' + slug(exam['student']['id']) + '/asignaturas/' +
            slug(exam['subject']['slug']) + '/examenes/' + safe_path(exam['practice_id']))


def image_path(path):
    safe_path(path, 'submission/')
    require(path != 'submission/.gitkeep', 'Placeholder is not an image answer')
    require(Path(path).suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.heic', '.heif'), 'Unsupported image attachment extension')
    return path


def validate_source_refs(refs, subject):
    ids = unique_ids(refs)
    for ref in refs:
        safe_path(ref['path'], 'asignaturas/' + slug(subject) + '/contenidos/')
        locators = [(row['kind'], row['value']) for row in ref['locators']]
        require(len(set(locators)) == len(locators), 'Duplicate source locators')
    return ids


def validate_profile_reference(profile, snapshot, subject):
    if profile is None:
        return
    require(profile['path'] == 'examenes/' + subject + '/context-exam.md', 'Profile subject/path mismatch')
    require(profile['source_snapshot'] == snapshot, 'Incompatible profile snapshot; update profile')
    unique_ids(profile['references'])
    for ref in profile['references']:
        validate_reference(ref, subject)


def validate_provenance(data):
    subject = data['subject']['slug']
    validate_snapshot(data['source_snapshot'], subject)
    require((data['practice_mode'] == 'general') == (data['profile'] is None), 'Practice mode/profile mismatch')
    validate_profile_reference(data['profile'], data['source_snapshot'], subject)
    plan = data['plan_reference']
    if plan:
        require(plan['path'] == 'planes/' + subject + '/plan.json', 'Plan path subject mismatch')
        require(len(set(plan['session_ids'])) == len(plan['session_ids']), 'Duplicate plan sessions')
    ids = validate_source_refs(data['source_refs'], subject)
    concepts = {c for ref in data['source_refs'] for c in ref['key_concepts']}
    units = {ref['unit'] for ref in data['source_refs'] if ref['unit'] is not None}
    require(set(data['scope']['key_concepts']).issubset(concepts), 'Scope concept lacks source')
    require(set(data['scope']['units']).issubset(units), 'Scope unit lacks source')
    created = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
    require(data['practice_id'].startswith(created.strftime('%Y%m%d-%H%M-')), 'Practice ID must match local creation time')
    return ids


def validate_data(data):
    require(isinstance(data, dict) and set(data) == {'exam', 'submission', 'result'}, 'Expected exam/submission/result canonical envelope')
    exam, submission, result = data['exam'], data['submission'], data['result']
    validate_named(exam, 'exam'); validate_named(submission, 'submission')
    ids = validate_provenance(exam)
    practice_path(exam)
    qids = unique_ids(exam['questions'])
    for question in exam['questions']:
        require(set(question['source_ref_ids']).issubset(ids), 'Unknown question source')
        require(len(set(question['source_ref_ids'])) == len(question['source_ref_ids']), 'Duplicate question source')
        require(question['requires_image'] == (question['response_mode'] in ('paper_image', 'graph_image')), 'Image requirement/mode mismatch')
    for key in ('schema_version', 'practice_id', 'student', 'subject'):
        require(submission[key] == exam[key], 'Submission identity mismatch: ' + key)
    require(unique_ids(submission['answers'], 'question_id') == qids, 'Answer IDs must equal question IDs; use empty text/null for unanswered')
    for answer in submission['answers']:
        require(len(set(answer['images'])) == len(answer['images']), 'Duplicate attachment')
        for path in answer['images']:
            image_path(path)
    require((submission['status'] == 'draft') == (submission['submitted_at'] is None), 'Submission state/timestamp mismatch')
    if submission['submitted_at']:
        require(datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00')) >= datetime.fromisoformat(exam['created_at'].replace('Z', '+00:00')), 'Submission predates creation')
    if result is None:
        return data
    require(submission['status'] == 'submitted', 'No correction/key before explicit submission')
    validate_named(result, 'result')
    validate_provenance(result)
    for key in exam:
        if key != 'questions':
            require(result[key] == exam[key], 'Result/exam provenance mismatch: ' + key)
    require(datetime.fromisoformat(result['corrected_at'].replace('Z', '+00:00')) >= datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00')), 'Correction predates submission')
    require(unique_ids(result['questions'], 'question_id') == qids, 'Result question IDs mismatch')
    exam_questions = {q['id']: q for q in exam['questions']}
    attachments = {path for a in submission['answers'] for path in a['images']}
    for limit in result['limitations']:
        require(limit['question_id'] is None or limit['question_id'] in qids, 'Unknown limitation question')
        if limit['image_path'] is not None:
            image_path(limit['image_path'])
            require(limit['image_path'] in attachments, 'Limitation image absent from submission')
            if limit['question_id']:
                answer = next(a for a in submission['answers'] if a['question_id'] == limit['question_id'])
                require(limit['image_path'] in answer['images'], 'Limitation image/question mismatch')
    for row in result['review_areas']:
        require(set(row['question_ids']).issubset(qids), 'Unknown review question')
        require(set(row['source_ref_ids']).issubset(ids), 'Unknown review source')
    assessed_total = assessed_max = maximum = 0
    inconclusive = set()
    for question in result['questions']:
        public = exam_questions[question['question_id']]
        require(question['max_score'] == public['max_score'] and question['source_ref_ids'] == public['source_ref_ids'], 'Result question does not match exam')
        unique_ids(question['rubric'])
        require(math.isclose(sum(c['max_score'] for c in question['rubric']), question['max_score']), 'Rubric maxima do not sum to question max')
        for criterion in question['rubric']:
            awarded = criterion['awarded_score']
            require(awarded is None or awarded <= criterion['max_score'], 'Criterion score above maximum')
        maximum += question['max_score']
        if question['status'] == 'graded':
            require(not any(l['prevents_conclusive_grading'] and l['question_id'] in (None, question['question_id']) for l in result['limitations']), 'Graded question has an applicable blocking limitation')
            require(question['score'] is not None and question['score'] <= question['max_score'], 'Graded score missing/above max')
            require(all(c['awarded_score'] is not None for c in question['rubric']), 'Conclusive rubric incomplete')
            require(math.isclose(sum(c['awarded_score'] for c in question['rubric']), question['score']), 'Rubric sum differs from question score')
            assessed_total += question['score']; assessed_max += question['max_score']
        else:
            inconclusive.add(question['question_id'])
            require(question['score'] is None, 'Unassessable question must not be scored zero')
            require(any(l['question_id'] in (None, question['question_id']) and l['prevents_conclusive_grading'] for l in result['limitations']), 'Unassessable question needs explanatory limitation')
    blocking = any(l['prevents_conclusive_grading'] for l in result['limitations'])
    require(bool(inconclusive) == blocking, 'Blocking limitations inconsistent with assessed questions')
    require(result['status'] == ('inconclusive' if inconclusive else 'complete'), 'Result status inconsistent')
    expected = {'total': None if inconclusive else assessed_total, 'max': maximum,
                'assessed_total': assessed_total, 'assessed_max': assessed_max}
    for key, value in expected.items():
        actual = result['score'][key]
        require(actual is None if value is None else actual is not None and math.isclose(actual, value), 'Score aggregate mismatch: ' + key)
    if result['profile'] and any(ref['read_status'] == 'partial' for ref in result['profile']['references']):
        require(any(l['code'] == 'partial_profile' for l in result['limitations']), 'Preserve partial profile limitation')
    return data


def resolve_context(subject, snapshot, source_refs, sources, profile_status,
                    profile=None, access_confirmed=True, tag_verified=True,
                    plan_snapshot=None):
    """Validate independently obtained read receipts; never treat failed access as absence."""
    validate_snapshot(snapshot, subject)
    require(access_confirmed is True and tag_verified is True, 'Access/tag unresolved')
    if plan_snapshot is not None:
        require(snapshot == plan_snapshot, 'Selected plan snapshot must prevail')
    require(profile_status in ('absent', 'present'), 'Profile access failed or unresolved')
    from contract import validate_schema
    schema = load_json((Path(__file__).resolve().parents[1] / 'assets/exam.schema.json').read_text())
    validate_schema(source_refs, schema['properties']['source_refs'])
    validate_source_refs(source_refs, subject)
    receipts = {row['id']: row for row in sources}
    require(len(receipts) == len(sources), 'Duplicate source read receipts')
    for ref in source_refs:
        require(ref['id'] in receipts, 'Required source not read')
        receipt = receipts[ref['id']]
        require(receipt['path'] == ref['path'], 'Read receipt path mismatch')
        require(isinstance(receipt.get('text'), str) and receipt['text'].strip(), 'Source unreadable/incomplete')
        require({l['value'] for l in ref['locators']}.issubset(receipt['locators']), 'Scope locator not read')
    if profile_status == 'absent':
        require(profile is None, 'Confirmed absence conflicts with profile')
        return {'practice_mode': 'general', 'profile': None, 'notice': GENERAL_NOTICE}
    require(profile is not None, 'Present profile required')
    # Full profile shape is validated through the same schema used by exam/result.
    validate_schema(profile, schema['properties']['profile'])
    validate_profile_reference(profile, snapshot, subject)
    return {'practice_mode': 'profile_based', 'profile': profile, 'notice': 'Perfil observado, no predicción del examen real.'}


def validate_directory(directory):
    root = Path(directory)
    require(root.is_dir() and not root.is_symlink(), 'Practice directory missing/unsafe')
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'Symlink in artifact batch')
    md = (root / 'exam.md').read_text(encoding='utf-8')
    blocks = re.findall(r'^```exam-data\n(.*?)\n```$', md, re.M | re.S)
    require(len(blocks) == 1, 'Exam public metadata missing/ambiguous')
    result_path = root / 'result.json'
    data = {'exam': load_json(blocks[0]),
            'submission': load_json((root / 'submission.json').read_text()),
            'result': load_json(result_path.read_text()) if result_path.exists() else None}
    validate_data(data)
    from render_practice import render_texts
    texts = render_texts(data)
    for name, expected in texts.items():
        require((root / name).is_file() and (root / name).read_text(encoding='utf-8') == expected, 'Missing/tampered canonical artifact: ' + name)
    required = set(texts)
    require({p.name for p in root.iterdir()} == required | {'submission'}, 'Unexpected or stale files in batch')
    images = {path for answer in data['submission']['answers'] for path in answer['images']}
    actual = {p.relative_to(root).as_posix() for p in (root / 'submission').rglob('*') if p.is_file()}
    require(actual == (images or {'submission/.gitkeep'}), 'Attachment persistence incomplete or unexpected files')
    for path in images:
        require((root / path).stat().st_size > 0, 'Empty attachment is not persisted image')
    return data


def publish_practice(client, directory, authorized=False, expected_head=None, known_commit=None):
    data = validate_directory(directory)
    prefix = practice_path(data['exam'])
    outcome = {'status': 'unpublished', 'path': prefix, 'commit': None}
    if not authorized:
        return outcome
    try:
        require(client.private is False, 'Authorized repository must be confirmed public')
        if known_commit is not None:
            require(isinstance(known_commit, str) and re.fullmatch(r'[0-9a-f]{40}', known_commit), 'Reconciliation needs full known commit SHA')
            outcome['commit'] = known_commit
        else:
            require(expected_head and client.head(REPOSITORY, BRANCH) == expected_head, 'Concurrent change; reconcile first')
    except (OSError, ValidationError) as exc:
        return dict(outcome, status='blocked', error=str(exc))
    root = Path(directory)
    files = {prefix + '/' + p.relative_to(root).as_posix(): p.read_bytes()
             for p in root.rglob('*') if p.is_file()}
    try:
        # Reconciliation is read-only: a known possibly successful commit must never be replayed.
        commit = known_commit if known_commit is not None else client.commit(REPOSITORY, BRANCH, files, expected_head=expected_head)
        outcome['commit'] = commit
        require(re.fullmatch(r'[0-9a-f]{40}', commit or ''), 'Full SHA required')
        for path, content in files.items():
            require(client.read(REPOSITORY, path, commit) == content, 'Unverified committed artifact: ' + path)
        return dict(outcome, status='published', files=list(files))
    except (OSError, ValidationError) as exc:
        return dict(outcome, error=str(exc), recovery='Reconcile known SHA and each file before retry; never duplicate or delete.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('practice_dir')
    args = parser.parse_args()
    try:
        validate_directory(args.practice_dir)
        print('Valid exam practice batch.')
    except (OSError, ValidationError, KeyError, TypeError) as exc:
        print('Invalid practice: ' + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

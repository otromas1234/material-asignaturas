"""Validate evidence-bearing profile Markdown. No network or filesystem writes."""
import argparse
from pathlib import Path
import re
import sys
from contract import (ValidationError, require, load_json, validate_named,
                      validate_reference, validate_snapshot, unique_ids,
                      safe_path, slug, REPOSITORY, BRANCH)

SECTIONS = ('Fuentes y cobertura', 'Patrones observados', 'Recurrencias',
            'Recomendaciones de formato', 'Ejemplos originales', 'Limitaciones')
DIMENSIONS = {'question_types', 'organization', 'instructions',
              'apparent_difficulty', 'response_modes'}


def parse_block(text, name):
    blocks = re.findall(r'^```' + re.escape(name) + r'\s*\n(.*?)\n```\s*$', text, re.M | re.S)
    require(len(blocks) == 1, 'Exactly one ' + name + ' JSON block required')
    return load_json(blocks[0])


def validate_profile(text):
    require(isinstance(text, str), 'Profile must be Markdown')
    require(text.lstrip().startswith('```profile-metadata\n'), 'Metadata must lead profile')
    metadata = parse_block(text, 'profile-metadata')
    validate_named(metadata, 'profile')
    subject = metadata['subject']['slug']
    validate_snapshot(metadata['source_snapshot'], subject)
    unique_ids(metadata['references'])
    refs = {}
    exam_paths = set()
    for ref in metadata['references']:
        validate_reference(ref, subject)
        require(ref['path'] not in exam_paths, 'Duplicate canonical exam path; IDs do not create distinct exams')
        exam_paths.add(ref['path'])
        refs[ref['id']] = ref
    require(not any(r['read_status'] == 'partial' for r in refs.values()) or metadata['limitations'], 'Partial profile requires limitations')
    for section in SECTIONS:
        require(re.search(r'^## ' + re.escape(section) + r'\s*$', text, re.M), 'Missing section: ' + section)
    recommendations = re.search(r'^## Recomendaciones de formato\s*$(.*?)(?=^## |\Z)', text, re.M | re.S).group(1)
    examples = re.search(r'^## Ejemplos originales\s*$(.*?)(?=^## |\Z)', text, re.M | re.S).group(1)
    require(re.search(r'orientativ|orientación|no observación', recommendations, re.I), 'Label recommendations as guidance, not observations')
    require(re.search(r'ejemplo(?:s)? (?:inventado|original)', examples, re.I), 'Label invented examples explicitly')
    observations = parse_block(text, 'profile-observations')
    recurrences = parse_block(text, 'profile-recurrences')
    validate_named(observations, 'observations')
    validate_named(recurrences, 'recurrences')
    unique_ids(observations); unique_ids(recurrences)
    require({row['dimension'] for row in observations} == DIMENSIONS, 'Five observation dimensions required')
    for row in observations + recurrences:
        for evidence in row['evidence']:
            require(evidence['reference_id'] in refs, 'Unknown evidence reference')
            require(evidence['locator'] in refs[evidence['reference_id']]['included_locators'], 'Evidence points outside included coverage')
    for row in recurrences:
        count, sample = row['observed_count'], row['sample_size']
        require(count <= len({e['reference_id'] for e in row['evidence']}), 'Count exceeds evidenced distinct exams')
        require(sample is None or count <= sample <= len(refs), 'Inconsistent known sample')
    return metadata


def select_references(subject, snapshot, inventory, selected=None,
                      access_confirmed=True, tag_verified=True):
    slug(subject); validate_snapshot(snapshot, subject)
    require(access_confirmed is True and tag_verified is True, 'Access/tag unverified; not absence')
    unique_ids(inventory)
    selected_ids = {row['id'] for row in inventory} if selected is None else set(selected)
    require(selected_ids.issubset({row['id'] for row in inventory}), 'Selected reference absent')
    result = []
    for row in inventory:
        safe_path(row['path'], 'asignaturas/' + subject + '/examenes-referencia/')
        if row['id'] in selected_ids:
            require(row.get('readable') is True, 'Unreadable selected reference; stop analysis')
            result.append(row)
    return result


def publish_profile(client, text, expected_head, authorized=False):
    """Injected adapter only: CAS commit(repo, branch, files, expected_head), read by SHA."""
    metadata = validate_profile(text)
    path = 'examenes/' + metadata['subject']['slug'] + '/context-exam.md'
    outcome = {'status': 'unpublished', 'path': path, 'commit': None}
    if not authorized:
        return outcome
    try:
        require(expected_head and client.head(REPOSITORY, BRANCH) == expected_head, 'Concurrent change; reread before retry')
    except (OSError, ValidationError) as exc:
        return dict(outcome, status='blocked', error=str(exc))
    try:
        commit = client.commit(REPOSITORY, BRANCH, {path: text}, expected_head=expected_head)
        outcome['commit'] = commit
        require(re.fullmatch(r'[0-9a-f]{40}', commit or ''), 'Full commit SHA required')
        require(client.read(REPOSITORY, path, commit) == text, 'Committed content not verified')
        return dict(outcome, status='published')
    except (OSError, ValidationError) as exc:
        return dict(outcome, error=str(exc), recovery='Reconcile known SHA before retry; never repeat blindly.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile')
    args = parser.parse_args()
    try:
        validate_profile(Path(args.profile).read_text(encoding='utf-8'))
        print('Valid exam style profile.')
    except (OSError, ValidationError) as exc:
        print('Invalid profile: ' + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

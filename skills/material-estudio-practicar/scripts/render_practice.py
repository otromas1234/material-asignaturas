"""Derive safe static student artifacts from validated canonical data. Never generates questions."""
import argparse
from html import escape
import json
from pathlib import Path
import shutil
import sys
import tempfile
from contract import ValidationError, require, load_json
from validate_practice import validate_data, validate_directory, GENERAL_NOTICE


def pretty(data):
    return json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def md(value):
    # Escape raw HTML and prevent source-controlled Markdown links/fences/headings.
    entities = {'\\': '&#92;', '`': '&#96;', '[': '&#91;', ']': '&#93;',
                '*': '&#42;', '_': '&#95;', '#': '&#35;', '\n': '<br>'}
    return ''.join(entities.get(char, escape(char, quote=True)) for char in str(value))


def render_texts(data):
    validate_data(data)
    exam, submission, result = data['exam'], data['submission'], data['result']
    notice = GENERAL_NOTICE if exam['profile'] is None else 'Basada en patrones observados; no predice el examen real.'
    lines = ['# Examen de práctica', '', md(exam['subject']['name']), '', md(notice), '',
             'Responde en el chat por número de pregunta. Indica explícitamente cuando termines.', '',
             'Snapshot: ' + md(exam['source_snapshot']['repository']) + ' — ' + md(exam['source_snapshot']['tag']), '',
             '## Alcance', md(exam['scope']['description']), '']
    html_questions = []
    for index, question in enumerate(exam['questions'], 1):
        mode = question['response_mode'] + ('; adjuntar imagen' if question['requires_image'] else '; responder en el chat')
        lines.extend(['## ' + str(index) + '. ' + md(question['id']), md(question['prompt']), '',
                      'Modalidad: ' + md(mode) + '. Máximo: ' + str(question['max_score']) + '.',
                      'Fuentes: ' + ', '.join(md(s) for s in question['source_ref_ids']), ''])
        html_questions.append('<li><h2>' + escape(question['id']) + '</h2><p>' + escape(question['prompt']) + '</p><p>' + escape(mode) + '</p><p>Máximo: ' + str(question['max_score']) + '</p></li>')
    lines.extend(['## Fuentes curriculares', ''])
    for ref in exam['source_refs']:
        lines.append('- ' + md(ref['id']) + ': ' + md(ref['path']) + '; ' + '; '.join(md(l['kind'] + ': ' + l['value']) for l in ref['locators']))
    # Exact public exam JSON is recoverable; escape angle brackets to prevent raw HTML activation.
    public_json = pretty(exam).rstrip().replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026').replace('`', '\\u0060')
    lines.extend(['', '## Datos públicos del examen', '```exam-data', public_json, '```', ''])
    provenance = '<p>Práctica: ' + escape(exam['practice_id']) + '; alumno: ' + escape(exam['student']['name']) + '; creada: ' + escape(exam['created_at']) + '</p>'
    if exam['profile']:
        provenance += '<p>Perfil: ' + escape(exam['profile']['path'] + ' @ ' + exam['profile']['commit']) + '</p>'
    if exam['plan_reference']:
        provenance += '<p>Plan: ' + escape(exam['plan_reference']['path'] + ' @ ' + exam['plan_reference']['commit']) + '</p>'
    sources_html = '<ul>' + ''.join('<li>' + escape(ref['path']) + ': ' + escape('; '.join(l['value'] for l in ref['locators'])) + '</li>' for ref in exam['source_refs']) + '</ul>'
    html = '<!doctype html>\n<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Examen de práctica</title></head><body><main><h1>' + escape(exam['subject']['name']) + '</h1>' + provenance + '<p>' + escape(notice) + '</p><p>Responde en el chat. Declara la entrega al terminar.</p><p>' + escape(exam['source_snapshot']['repository'] + ' — ' + exam['source_snapshot']['tag']) + '</p><p>' + escape(exam['scope']['description']) + '</p><ol>' + ''.join(html_questions) + '</ol><h2>Fuentes</h2>' + sources_html + '</main></body></html>\n'
    files = {'exam.md': '\n'.join(lines), 'exam.html': html, 'submission.json': pretty(submission)}
    if result is not None:
        score = result['score']
        exam_questions = {question['id']: question for question in exam['questions']}
        answers = {answer['question_id']: answer for answer in submission['answers']}
        didactic_questions = []
        for question in result['questions']:
            public = exam_questions[question['question_id']]
            answer = answers[question['question_id']]
            student_answer = answer['text']
            if not student_answer and answer['images']:
                student_answer = 'Respuesta entregada mediante ' + str(len(answer['images'])) + (' imagen adjunta.' if len(answer['images']) == 1 else ' imágenes adjuntas.')
            elif not student_answer:
                student_answer = 'Sin respuesta entregada.'
            answer_status = question.get('answer_status')
            if answer_status is None:
                if question['status'] == 'not_assessable':
                    answer_status = 'not_assessable'
                elif question['score'] == question['max_score']:
                    answer_status = 'correct'
                elif question['score'] == 0:
                    answer_status = 'incorrect'
                else:
                    answer_status = 'partially_correct'
            didactic_questions.append({
                'question_id': question['question_id'], 'prompt': public['prompt'],
                'student_answer': student_answer, 'expected_answer': question['expected_answer'],
                'status': answer_status, 'score': question['score'], 'max_score': question['max_score'],
                'feedback': question['feedback'], 'strengths': question.get('strengths', []),
                'improvement_areas': question.get('improvement_areas', []),
            })
        didactic_report = {
            'practice_id': result['practice_id'], 'student_name': result['student']['name'],
            'subject_name': result['subject']['name'], 'created_at': result['created_at'],
            'corrected_at': result['corrected_at'], 'status': result['status'],
            'score': {'total': score['total'], 'max': score['max']}, 'questions': didactic_questions,
        }
        report = ['# Resultado de práctica', '', md(notice), '',
                  'Práctica: ' + md(result['practice_id']),
                  'Alumno: ' + md(result['student']['name']),
                  'Asignatura: ' + md(result['subject']['name']),
                  'Snapshot: ' + md(result['source_snapshot']['repository'] + ' — ' + result['source_snapshot']['tag']),
                  'Estado: ' + result['status'],
                  'Puntuación: ' + ('No concluyente' if score['total'] is None else str(score['total'])) + ' / ' + str(score['max']),
                  'Evaluado: ' + str(score['assessed_total']) + ' / ' + str(score['assessed_max']),
                  'La puntuación corresponde a esta rúbrica; no es una escala oficial del centro.', '']
        for question in result['questions']:
            didactic_question = next(item for item in didactic_questions if item['question_id'] == question['question_id'])
            report.extend(['## ' + md(question['question_id']), 'Estado: ' + question['status'],
                           'Puntuación: ' + str(question['score']) + ' / ' + str(question['max_score']),
                           'Clasificación: ' + didactic_question['status'],
                           'Enunciado: ' + md(didactic_question['prompt']),
                           'Respuesta del alumno: ' + md(didactic_question['student_answer']),
                           'Respuesta esperada: ' + md(question['expected_answer']), md(question['feedback'])])
            if didactic_question['strengths']:
                report.append('Aciertos: ' + '; '.join(md(item) for item in didactic_question['strengths']))
            if didactic_question['improvement_areas']:
                report.append('Para ampliar: ' + '; '.join(md(item) for item in didactic_question['improvement_areas']))
            for criterion in question['rubric']:
                report.append('- ' + md(criterion['id'] + ': ' + criterion['description']) + ' — ' + str(criterion['awarded_score']) + '/' + str(criterion['max_score']) + '; ' + md(criterion['feedback']))
            report.append('Fuentes: ' + ', '.join(md(s) for s in question['source_ref_ids']))
        report.extend(['', '## Áreas de repaso'])
        for area in result['review_areas']:
            report.append('- ' + md(area['concept'] + ': ' + area['recommendation']) + '; preguntas ' + ', '.join(md(x) for x in area['question_ids']))
        report.extend(['', '## Fuentes y procedencia'])
        for ref in result['source_refs']:
            report.append('- ' + md(ref['id'] + ': ' + ref['path']) + '; ' + '; '.join(md(l['kind'] + ': ' + l['value']) for l in ref['locators']))
        if result['plan_reference']:
            report.append('Plan: ' + md(result['plan_reference']['path'] + ' @ ' + result['plan_reference']['commit']))
        if result['profile']:
            report.append('Perfil: ' + md(result['profile']['path'] + ' @ ' + result['profile']['commit']))
            for ref in result['profile']['references']:
                report.append('- ' + md(ref['path']) + '; lectura: ' + ref['read_status'] + '; año: ' + str(ref['year']))
                report.append('  Incluido: ' + ', '.join(md(x) for x in ref['included_locators']))
                for item in ref['excluded_locators']:
                    report.append('  Excluido: ' + md(item['locator'] + ': ' + item['reason']))
        report.extend(['', '## Limitaciones'])
        for limit in result['limitations']:
            report.append('- ' + md(limit['code'] + ': ' + limit['description']) + ('; ' + md(limit['image_path']) if limit['image_path'] else ''))
        result_payload = dict(result)
        result_payload['didactic_report'] = didactic_report
        files.update({'result.json': pretty(result_payload), 'result.md': '\n'.join(report) + '\n'})
    return files


def render(data, output, attachments_dir=None):
    texts = render_texts(data)
    output = Path(output)
    require(not output.exists() and not output.is_symlink(), 'Output collision; select a unique practice slug/directory, never overwrite')
    images = {path for answer in data['submission']['answers'] for path in answer['images']}
    attachments = {}
    for path in images:
        require(attachments_dir is not None, 'Real attachments required; cannot fake persisted images')
        source = Path(attachments_dir) / path
        require(source.is_file() and not source.is_symlink(), 'Attachment missing or symlink')
        require(source.resolve().is_relative_to(Path(attachments_dir).resolve()), 'Attachment escapes source root')
        attachments[path] = source.read_bytes()
        require(attachments[path], 'Empty attachment')
    require(output.parent.is_dir(), 'Output parent must already exist')
    # Build/validate in an isolated sibling. Rename to a new directory only on success.
    staging = Path(tempfile.mkdtemp(prefix='.practice-', dir=output.parent))
    try:
        for name, text in texts.items():
            (staging / name).write_text(text, encoding='utf-8')
        (staging / 'submission').mkdir()
        for path, content in attachments.items():
            target = staging / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        if not attachments:
            (staging / 'submission/.gitkeep').write_text('')
        validate_directory(staging)
        require(not output.exists(), 'Concurrent output collision')
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('practice_data')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--attachments-dir')
    args = parser.parse_args()
    try:
        render(load_json(Path(args.practice_data).read_text()), Path(args.output_dir), args.attachments_dir)
        print('Rendered validated exam practice batch.')
    except (OSError, ValidationError, KeyError, TypeError) as exc:
        print('Cannot render: ' + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

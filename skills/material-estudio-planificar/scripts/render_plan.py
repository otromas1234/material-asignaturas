#!/usr/bin/env python3
"""Render validated portable study JSON to a matching Spanish Markdown table."""
import argparse
from datetime import date
import html
from pathlib import Path
import re
import sys
from validate_plan import load_plan, validate_plan

HEADERS = ['Asignatura', 'Unidad', 'Sesión', 'Impartido', 'Día de estudio', 'Contenido', 'Páginas', 'Estudio y práctica', 'Examen y corrección', 'Pausa', 'Objetivo para comprobar lo aprendido']
TAUGHT = {'taught': 'Sí', 'not_taught': 'No', 'partial': 'Parcial', 'unknown': 'Desconocido'}


def cell(value):
    """Escape raw markup and preserve literal source text inside table cells."""
    return html.escape(str(value), quote=False).replace('\\', '&#92;').replace('|', '&#124;').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>').replace('`', '&#96;').replace('*', '&#42;').replace('_', '&#95;').replace('[', '&#91;').replace(']', '&#93;')


def pages(row):
    labels = []
    multiple = len(row['source_refs']) > 1
    for ref in row['source_refs']:
        ranges = ref['pages']
        text = 'Sin verificar' if ranges is None else ', '.join(str(int(p['start'])) if p['start'] == p['end'] else f'{int(p["start"])}–{int(p["end"])}' for p in ranges)
        labels.append(f'{ref["source_id"]}: {text}' if multiple else text)
    return '; '.join(labels)


def duration(minutes):
    hours, remainder = divmod(int(minutes), 60)
    return f'{hours} h {remainder} min' if hours else f'{remainder} min'


def render_plan(plan):
    errors = validate_plan(plan)
    if errors:
        raise ValueError('\n'.join(errors))
    lines = [f'# {cell(plan["title"])}', '', '| ' + ' | '.join(HEADERS) + ' |', '|' + '|'.join(['---'] * len(HEADERS)) + '|']
    for row in plan['sessions']:
        content = row['content']
        if row['optional']:
            prefix = 'Reserva opcional' if row['kind'] == 'buffer' else 'Opcional'
            content = f'{prefix}: {content}'
        values = [row['subject'], ', '.join(row['units']), row['label'], TAUGHT[row['taught_status']], date.fromisoformat(row['study_date']).strftime('%d/%m/%Y') if row['study_date'] else 'Sin fecha', content, pages(row), f'{int(row["study_practice_minutes"])} min', f'{int(row["exam_minutes"] + row["correction_minutes"])} min', f'{int(row["break_minutes"])} min', row['objective']]
        lines.append('| ' + ' | '.join(cell(value) for value in values) + ' |')
    totals = plan['totals']
    knowledge = plan['initial_knowledge']
    basis = {'assumed': 'supuesto, no medido', 'provided_estimate': 'estimación aportada', 'provided_measured': 'medición aportada'}[knowledge['basis']]
    lines.extend(['', f'Conocimiento inicial: {knowledge["percent"]:g} % ({basis}).', '', f'Tiempo requerido estimado: {duration(totals["required_minutes"])}. Reserva opcional: {duration(totals["optional_minutes"])}. Total con opcionales: {duration(totals["including_optional_minutes"])}.', '', 'Los tiempos son estimaciones; impartido no significa aprendido. Examen y corrección suma ambas actividades.'])
    budget = plan['schedule']['session_budget_minutes']
    lines.extend(['', f'Presupuesto solicitado por sesión: {int(budget)} min, incluidas pausas y evaluación.' if budget is not None else 'Sin límite fijo por sesión solicitado.'])
    snapshot = plan.get('source_snapshot')
    snapshot_text = (f"{snapshot['repository']}@{snapshot['tag']}" if snapshot else 'no aplica (exportación portable)')
    lines.extend(['', f'Snapshot de materiales: {cell(snapshot_text)}.'])
    if plan['schema_version'] in ('1.2', '1.3'):
        schedule = plan['schedule']
        provenance = schedule['provenance']
        daily = schedule['daily_budget_minutes']
        daily_text = f'{int(daily)} min al día en este plan, sumando sesiones, evaluación, pausas y opcionales' if daily is not None else 'sin límite diario por petición explícita'
        weekend_text = 'incluidos' if schedule['weekends_allowed'] else 'excluidos'
        lines.extend(['', f'Capacidad diaria: {daily_text}.', '', f'Fines de semana: {weekend_text}.', '', f'Origen de datos: inicio={provenance["start_date"]}; examen={provenance["exam_date"]}; fecha objetivo={provenance["deadline_date"]}; fines de semana={provenance["weekends_allowed"]}; capacidad diaria={provenance["daily_budget_minutes"]}.'])
        if schedule['exam_date']:
            lines.extend(['', f'Fecha de examen aportada: {date.fromisoformat(schedule["exam_date"]).strftime("%d/%m/%Y")}.'])
    else:
        lines.extend(['', 'Contrato anterior 1.0: no se infieren fecha de examen ni capacidad diaria.'])
    if any(row['study_date'] is None for row in plan['sessions']):
        lines.extend(['', 'Hay trabajo sin fecha; no se confirma que todo quepa antes de la fecha objetivo.'])
    for label, value in [('Inicio', plan['schedule']['start_date']), ('Fecha objetivo de finalización', plan['schedule']['deadline_date'])]:
        if value:
            lines.extend(['', f'{label}: {date.fromisoformat(value).strftime("%d/%m/%Y")}.'])
    lines.extend(['', 'Fuentes:'])
    for source in plan['sources']:
        locator = f' — {cell(source["locator"])}' if source['locator'] else ' — ubicación no especificada'
        lines.append(f'- {cell(source["id"])}: {cell(source["title"])}{locator}')
    if plan['schema_version'] == '1.3':
        lines.extend(['', '## Prompts de práctica de examen por sesión'])
        for row in plan['sessions']:
            prompt = row['practice_prompt']
            fence_width = max([3] + [len(match.group()) + 1 for match in re.finditer(r'`+', prompt)])
            fence = '`' * fence_width
            lines.extend(['', f'### Sesión {cell(row["id"])} — {cell(row["label"])}', '', 'Prompt de práctica de examen:', '', f'{fence}text', prompt, fence])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan')
    parser.add_argument('--output')
    args = parser.parse_args()
    try:
        if args.output:
            source = Path(args.plan)
            destination = Path(args.output)
            if (destination.resolve() == source.resolve()
                    or (destination.exists() and destination.samefile(source))):
                raise ValueError('Output must not overwrite the JSON input, including file aliases.')
        markdown = render_plan(load_plan(args.plan))
        if args.output:
            Path(args.output).write_text(markdown, encoding='utf-8')
        else:
            print(markdown, end='')
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

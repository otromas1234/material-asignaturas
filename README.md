# Biblioteca de materiales de estudio

Repositorio privado para organizar fuentes por asignatura y las salidas consumidas por las Skills de estudio.

## Estructura

- `asignaturas/<slug>/contenidos/`: temario y fuentes curriculares.
- `asignaturas/<slug>/apoyos/`: material complementario.
- `asignaturas/<slug>/examenes-referencia/`: exámenes anteriores usados como referencia.
- `examenes/<slug>/context-exam.md`: guía de estilo generada a partir de exámenes de referencia (flujo 006).
- `planes/<slug>/`: plan JSON y Markdown generados por el planificador (flujo 005).

Los slugs usan minúsculas sin tildes ni espacios. Se incluyen `historia`, `ingles` y `matematicas` como carpetas iniciales vacías; se pueden añadir otras asignaturas siguiendo el mismo patrón. No se incluyen datos de alumnos: la ruta y los controles de privacidad de esa salida quedan sujetos al contrato de la Skill 007.

## Branch contract

All study-material Skills read and write this library on the `material-estudio` branch. Material snapshots use tags shaped as `plan/<subject-slug>/<YYYYMMDD>-<short-id>` and are created only after a material add, replacement, or deletion commit. Plan, exam-style profile, and practice-output commits do not create tags; each consumer records the material tag it used.

Practice results, when generated, belong under `alumnos/<student>/asignaturas/<subject-slug>/examenes/<exam-id>/`. The empty `alumnos/` directory is only a location placeholder; do not place student data there without a specific practice request.

# Biblioteca de materiales de estudio

Repositorio privado para organizar fuentes por asignatura y las salidas consumidas por las Skills de estudio.

## Estructura

- `asignaturas/<slug>/contenidos/`: temario y fuentes curriculares.
- `asignaturas/<slug>/apoyos/`: material complementario.
- `asignaturas/<slug>/examenes-referencia/`: exámenes anteriores usados como referencia.
- `examenes/<slug>/context-exam.md`: guía de estilo generada a partir de exámenes de referencia (flujo 006).
- `planes/<slug>/`: plan JSON y Markdown generados por el planificador (flujo 005).

Los slugs usan minúsculas sin tildes ni espacios. Se incluyen `historia`, `ingles` y `matematicas` como carpetas iniciales vacías; se pueden añadir otras asignaturas siguiendo el mismo patrón. No se incluyen datos de alumnos: la ruta y los controles de privacidad de esa salida quedan sujetos al contrato de la Skill 007.

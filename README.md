# Biblioteca de materiales de estudio

Repositorio privado para organizar fuentes por asignatura y las salidas consumidas por las Skills de estudio.

## Estructura

- `asignaturas/<slug>/contenidos/`: temario y fuentes curriculares.
- `asignaturas/<slug>/apoyos/`: material complementario.
- `asignaturas/<slug>/examenes-referencia/`: exámenes anteriores usados como referencia.
- `examenes/<slug>/context-exam.md`: guía de estilo generada a partir de exámenes de referencia (flujo 006).
- `planes/<slug>/`: plan JSON y Markdown generados por el planificador (flujo 005).

Los slugs usan minúsculas sin tildes ni espacios. Están preparadas las carpetas de `historia`, `ingles` y `matematicas`; Historia ya tiene materiales fuente y las otras asignaturas quedan listas para recibirlos. Se pueden añadir otras asignaturas siguiendo el mismo patrón. No se incluyen datos de alumnos: la ruta y los controles de privacidad de esa salida quedan sujetos al contrato de la Skill 007.

## Contrato de la rama

Todas las Skills de materiales leen y escriben esta biblioteca en la rama `material-estudio`. Los snapshots de materiales usan tags con el formato `plan/<slug-asignatura>/<YYYYMMDD>-<identificador-corto>` y se crean solo después de un commit que añade, sustituye o elimina material. Los commits de planes, perfiles de estilo y resultados de práctica no crean tags; cada consumidor registra el tag de materiales que utilizó.

Cuando se generen, los resultados de práctica se guardan en `alumnos/<alumno>/asignaturas/<slug-asignatura>/examenes/<id-examen>/`. La carpeta `alumnos/` está vacía y solo reserva la ubicación; no agregues datos de estudiantes sin una solicitud de práctica concreta.

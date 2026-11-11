# Contrato del repositorio

- Repositorio autorizado: `otromas1234/material-asignaturas`; rama fija de trabajo y consumo: `main`. No uses `development` ni otra rama para operaciones de materiales.
- El repositorio es público. Antes de publicar fuentes, confirma que el archivo no incluye datos personales de alumnos (nombre, identificador, nota, imagen identificable u otros) salvo autorización explícita de publicación.
- Antes de escribir, consulta repositorio/rama/árbol reales; la estructura esperada no demuestra que existan rutas.
- Slugs de asignatura: minúsculas, sin tildes ni espacios. Si dos asignaturas pueden resolver al mismo slug, solicita aclaración.
- Categorías: `asignaturas/<slug>/contenidos/`, `asignaturas/<slug>/apoyos/` y `asignaturas/<slug>/examenes-referencia/`.
- Rutas consumidoras: `examenes/<slug>/context-exam.md` (guía de estilo, propiedad del flujo 006) y `planes/<slug>/` (salidas 005); esta Skill no crea esas guías ni planes.
- 005 consume contenidos de un tag exacto y fija `source_snapshot.repository` y `source_snapshot.tag`; 006 consume exámenes de referencia y escribe la guía indicando el tag analizado; 007 consume contenidos, guía y snapshot seleccionado y guarda prácticas en `alumnos/<alumno>/asignaturas/<slug>/examenes/<id>/`. Mantén los nombres de rutas exactamente. Los planes, perfiles y prácticas no crean tags.
- Convención confirmada por 005: `plan/<slug-asignatura>/<YYYYMMDD>-<identificador-corto>`. El prefijo `plan` identifica snapshots de materiales; no significa que la Skill de planificación cree tags.
- Herramientas GitHub MCP disponibles en esta sesión: consultar archivo por ruta (`fetch_file`), crear archivo UTF-8 nuevo, actualizar archivo existente con blob SHA, borrar archivo con blob SHA, crear blob/tree/commit, mover una rama a un commit mediante `update_ref`, y leer metadata/diff de commit. Estas herramientas no equivalen a una prueba de escritura.
- Esta sesión no expone herramienta MCP dedicada para crear/verificar tags ni listar el árbol completo como operación específica. La creación de tags queda condicionada a un flujo Git local verificado; si no puede comprobarse acceso y SHA exacto, no crear ni declarar tag.

# Checklist de verificación operativa

## Verificado localmente con fixtures sintéticos
- [x] Tests offline; no configuración de credenciales, datos reales ni red.
- [x] Solo mocks para commits/relecturas; prohibidas escrituras GitHub y creación/movimiento/borrado de tags desde tests.
- [x] Repository/tag exactos y ausencia de `branch` en snapshot; rutas/identidades y ProfileReference compartido comprobados.
- [x] Fixtures legibles, exclusiones con motivo, año desconocido y límites explícitos. Revisar originalidad: ejemplos inventados, sin copia de fuentes sintéticas.

## En cada ejecución real (no realizado durante implementación)
- [ ] Confirmar asignatura, selección/alcance y alumno si corresponde; una sola pregunta si falta un dato esencial.
- [ ] Confirmar repositorio público autorizado, acceso y rama `main`; excluir datos personales no necesarios de exámenes/guías publicados.
- [ ] Resolver tag exacto pertinente o conservar snapshot del plan; comprobar SHA y lectura real, sin fallback a head.
- [ ] Seleccionar herramienta/Skill de formato; comprobar lectura/imagen/OCR real y declarar límites, sin servicios externos nuevos.
- [ ] Contrastar cada conclusión/pregunta con fuente y localizador; revisar cobertura, originalidad y distinción observación/recomendación/predicción.
- [ ] Validar guía/artefactos con Python instalado y verificado; revisar Markdown/HTML generado y no filtrar clave antes de entrega.
- [ ] Confirmar intención de guardar, destino, identidad, colisiones y archivos ajenos antes de escribir. Solo actualizar el mismo intento; nunca sobrescribir otro.
- [ ] Comprobar capacidad de commit atómico del lote y control concurrente contra revisión anterior, no solo un chequeo previo de head.
- [ ] Releer TODAS las rutas por SHA del commit; comparar contenido y adjuntos reales. Reportar solo lo verificado.
- [ ] Fallo parcial: comunicar SHA conocido, persistencia incompleta o estado no publicado y reconciliar antes de reintentar; no duplicar ni borrar.
- [ ] No crear/mover/borrar tags. No modificar materiales, planes, otro perfil/intento ni aplicación. No borrar archivos sin solicitud expresa.

Este checklist distingue verificación local de ejecución real. Los permisos, OCR y publicación real no se declaran probados por mocks.

# Análisis y contrato consumidor

## Lectura
Inventaría todas las referencias o el subconjunto explícito en el tag fijado. No incluyas otro temario/asignatura. Una ausencia solo se confirma tras acceso satisfactorio al árbol. Si no hay referencias, `no_references`, sin perfil ni commit; 007 continúa en modo general. Archivo totalmente ilegible bloquea el conjunto seleccionado: informa archivo y capacidad faltante y resuelve selección con la persona. Lectura parcial solo con alcance delimitado: registra cada exclusión y motivo, exclúyela de la evidencia y declara cobertura incompleta. No inventes páginas; usa encabezados, pregunta, sección o región verificable. No externalices OCR privado sin permiso.

## Perfil Markdown
Empieza con un único bloque `profile-metadata` de JSON válido conforme a `assets/profile.schema.json`. Conserva las seis secciones de la plantilla; incluye las cinco dimensiones mínimas: tipos, organización, instrucciones, dificultad aparente y formas de respuesta.

Para que la validación estructural sea reproducible, **Patrones observados** contiene `profile-observations`: lista de `{ id, dimension, description, evidence: [{ reference_id, locator }] }`. `dimension`: `question_types`, `organization`, `instructions`, `apparent_difficulty`, `response_modes`. Cada evidencia debe resolver a un localizador incluido de una referencia; describe el patrón en prosa legible junto al bloque si ayuda. El validador no verifica que la descripción sea verdadera: contrástala con la fuente.

**Recurrencias** contiene `profile-recurrences`: lista de `{ id, unit: "distinct_exams", description, observed_count, sample_size, evidence, comparability_limits }`. Cuenta exámenes legibles distintos, no menciones repetidas en una página. El recuento no puede superar las fuentes evidenciadas. Con muestra conocida: `0 <= observed_count <= sample_size <= número de referencias`. Con denominador desconocido usa `null` y no calcules porcentajes ni frecuencias relativas. La muestra limita comparabilidad y no predice aparición futura. Identifica preguntas recurrentes por paráfrasis, no copia extensa.

Recomendaciones de formato son orientativas, no observaciones; etiqueta la sección con «Orientación», «orientativa» o «no observación». Etiqueta cada ejemplo como «Ejemplo inventado» o «Ejemplo original». Ejemplos originales son inventados y se comparan con las referencias para evitar copia. Dificultad siempre aparente/orientativa. No atribuyas al centro criterios, escala o temario no documentados.

## ProfileReference compartido 006 → 007
Shape exacto (sin propiedades adicionales):

```json
{"id":"ref-1","path":"asignaturas/historia/examenes-referencia/synthetic.txt","year":null,"read_status":"partial","included_locators":["Pregunta A"],"excluded_locators":[{"locator":"Página 2","reason":"Imagen ilegible en fixture sintético"}]}
```

`year` entero o `null`; no inferir año por apariencia. `complete` exige cero exclusiones; `partial` exige exclusiones y limitación explícita en metadata. IDs únicos y rutas canónicas de examen únicas: dos IDs de una misma ruta no son dos exámenes y no pueden inflar la recurrencia. El contrato actual no tiene digest de documento, por lo que la identidad mínima verificable es la ruta exacta del snapshot. No mezclar incluido/excluido.

007 conserva **igualdad profunda** de `references`, sin convertir a `SourceRef` curricular; fija `{ path, commit, source_snapshot, references }`. Perfil y plan deben compartir exactamente repository/tag; el commit del perfil es independiente del tag material. No incrustes un SHA autorreferente en el perfil. Fixtures cruzados `tests/fixtures/partial-metadata.json` y `../material-estudio-practicar/assets/profile-practice-example.json` conservan año desconocido, lectura parcial y motivos.

## Herramientas locales
Python estándar 3.9+; sin dependencias ni red. `contract.py` soporta exactamente los keywords empleados por los schemas incluidos; no es un motor general JSON Schema. CLI valida JSON estricto (sin duplicados/NaN), estructura, evidencia/localizadores y recuentos; la revisión semántica/originalidad y las capacidades OCR/publicación siguen siendo trabajo conversacional/manual.

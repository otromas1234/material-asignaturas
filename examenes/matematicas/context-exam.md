```profile-metadata
{
  "schema_version": "1.0",
  "subject": {
    "slug": "matematicas",
    "name": "Matemáticas"
  },
  "source_snapshot": {
    "repository": "otromas1234/material-estudio",
    "tag": "plan/matematicas/20261031-6285fa20"
  },
  "references": [
    {
      "id": "ref-cd-2223",
      "path": "asignaturas/matematicas/examenes-referencia/examen-cd-1a-evaluacion-2022-23-soluciones.pdf",
      "year": 2022,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    },
    {
      "id": "ref-cd-2324",
      "path": "asignaturas/matematicas/examenes-referencia/examen-cd-1a-evaluacion-2023-24-soluciones.pdf",
      "year": 2023,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    },
    {
      "id": "ref-cd-2425",
      "path": "asignaturas/matematicas/examenes-referencia/examen-cd-1a-evaluacion-2024-25-soluciones.pdf",
      "year": 2024,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3",
        "Página 4",
        "Página 5"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    },
    {
      "id": "ref-cd-2526",
      "path": "asignaturas/matematicas/examenes-referencia/examen-cd-1a-evaluacion-2025-26-soluciones.pdf",
      "year": 2025,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    },
    {
      "id": "ref-global-2223",
      "path": "asignaturas/matematicas/examenes-referencia/examen-global-1a-evaluacion-2022-23-soluciones.pdf",
      "year": 2022,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3",
        "Página 4"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    },
    {
      "id": "ref-global-2324",
      "path": "asignaturas/matematicas/examenes-referencia/examen-global-1a-evaluacion-2023-24-soluciones.pdf",
      "year": 2023,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3",
        "Página 4"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    },
    {
      "id": "ref-global-2425",
      "path": "asignaturas/matematicas/examenes-referencia/examen-global-1a-evaluacion-2024-25-soluciones.pdf",
      "year": 2024,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3",
        "Página 4"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    },
    {
      "id": "ref-global-2526",
      "path": "asignaturas/matematicas/examenes-referencia/examen-global-1a-evaluacion-2025-26-soluciones.pdf",
      "year": 2025,
      "read_status": "partial",
      "included_locators": [
        "Página 1",
        "Página 2",
        "Página 3",
        "Página 4",
        "Página 5",
        "Página 6",
        "Página 7",
        "Página 8"
      ],
      "excluded_locators": [
        {
          "locator": "Transcripción exacta de expresiones/fórmulas en las páginas incluidas",
          "reason": "OCR de símbolos y disposición matemática no verificado visualmente; no se usa como evidencia literal."
        }
      ]
    }
  ],
  "limitations": [
    "Se consultaron los textos OCR página por página, no una inspección visual de los PDF. La extracción altera o vuelve ambiguos signos, exponentes y fracciones; las afirmaciones describen tipos de ejercicio reconocibles, no la transcripción exacta de expresiones. Los encabezados visibles en la captura incluyen «Esquema factori…» y «Material a entre…» truncados; no se infiere su contenido. No se proporcionaron hojas de ejercicios separadas: las fuentes disponibles son dos apuntes y ocho exámenes resueltos."
  ]
}
```

# Perfil de exámenes de Matemáticas

## Fuentes y cobertura

Ocho exámenes resueltos, en modalidad CD y Global, con cursos identificados por las rutas 2022-23 a 2025-26. Se revisó cada página de los textos extraídos. La evidencia se limita a páginas indicadas por observación; signos y fórmulas no se citan literalmente por la incertidumbre del OCR.

## Patrones observados

```profile-observations
[
  {
    "id": "obs-1",
    "dimension": "question_types",
    "description": "Se observan cálculos/simplificaciones de fracciones en varios exámenes y problemas contextualizados sobre fracciones de cantidades.",
    "evidence": [
      {
        "reference_id": "ref-cd-2223",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-cd-2324",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-cd-2425",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-cd-2425",
        "locator": "Página 3"
      },
      {
        "reference_id": "ref-cd-2526",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2223",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2223",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 3"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 1"
      }
    ]
  },
  {
    "id": "obs-2",
    "dimension": "organization",
    "description": "Los exámenes legibles se organizan en ejercicios numerados; algunos dividen una tarea en apartados a/b y muestran puntuación por ejercicio.",
    "evidence": [
      {
        "reference_id": "ref-cd-2223",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-cd-2425",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2223",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 1"
      }
    ]
  },
  {
    "id": "obs-3",
    "dimension": "instructions",
    "description": "Consignas visibles incluyen hallar fracción irreducible, operar y simplificar, operar radicales, indicar cociente/resto y factorizar polinomios.",
    "evidence": [
      {
        "reference_id": "ref-cd-2223",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-cd-2223",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-cd-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-cd-2526",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 3"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 4"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 2"
      }
    ]
  },
  {
    "id": "obs-4",
    "dimension": "apparent_difficulty",
    "description": "Dificultad aparente orientativa: hay procedimientos simbólicos de varios pasos y problemas contextualizados; el OCR impide valorar con precisión la carga de cálculo.",
    "evidence": [
      {
        "reference_id": "ref-cd-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-cd-2324",
        "locator": "Página 3"
      },
      {
        "reference_id": "ref-cd-2526",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 4"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 3"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 4"
      }
    ]
  },
  {
    "id": "obs-5",
    "dimension": "response_modes",
    "description": "Las soluciones muestran resultados numéricos con desarrollo de operaciones y planteamientos/resoluciones de problemas; en álgebra aparecen cociente y resto.",
    "evidence": [
      {
        "reference_id": "ref-cd-2223",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-cd-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-cd-2425",
        "locator": "Página 3"
      },
      {
        "reference_id": "ref-cd-2526",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2223",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2223",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 3"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 4"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 2"
      }
    ]
  }
]
```

## Recurrencias

Los recuentos corresponden a exámenes distintos con evidencia localizada, no a número de menciones.

```profile-recurrences
[
  {
    "id": "rec-1",
    "unit": "distinct_exams",
    "description": "Ejercicios de operaciones/simplificación con fracciones aparecen en los exámenes CD 2022-23, CD 2024-25, CD 2025-26, Global 2022-23 y Global 2024-25; no se cuenta cada apartado como examen separado.",
    "observed_count": 5,
    "sample_size": 8,
    "evidence": [
      {
        "reference_id": "ref-cd-2223",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-cd-2425",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-cd-2526",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2223",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 3"
      }
    ],
    "comparability_limits": "Conteo limitado a ejercicios reconocibles en OCR; no estima probabilidad futura ni cobertura completa."
  },
  {
    "id": "rec-2",
    "unit": "distinct_exams",
    "description": "Operaciones con radicales aparecen en los cuatro exámenes de las referencias con evidencia inequívoca: CD 2022-23, CD 2023-24, Global 2023-24 y Global 2024-25.",
    "observed_count": 4,
    "sample_size": 8,
    "evidence": [
      {
        "reference_id": "ref-cd-2223",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-cd-2324",
        "locator": "Página 1"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2425",
        "locator": "Página 4"
      }
    ],
    "comparability_limits": "Se contabiliza únicamente evidencia OCR legible de estos cuatro exámenes; la muestra parcial no permite predicción."
  },
  {
    "id": "rec-3",
    "unit": "distinct_exams",
    "description": "División o factorización de polinomios se observa en CD 2023-24, CD 2025-26, Global 2023-24 y Global 2025-26.",
    "observed_count": 4,
    "sample_size": 8,
    "evidence": [
      {
        "reference_id": "ref-cd-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-cd-2526",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2324",
        "locator": "Página 2"
      },
      {
        "reference_id": "ref-global-2526",
        "locator": "Página 2"
      }
    ],
    "comparability_limits": "Agrupación temática de ejercicios reconocibles; OCR parcial y no es una predicción."
  }
]
```

## Recomendaciones de formato

Orientación, no observación: alternar cálculo con problemas contextualizados y pedir que se comprueben los procedimientos; no es una predicción del examen siguiente.

## Ejemplos originales

Ejemplo inventado: no se incluye ninguno; no se han generado preguntas de práctica.

## Limitaciones

La calidad OCR puede alterar signos, exponentes, numeradores y denominadores. No se infieren temario oficial, dificultad oficial, criterios de calificación ni contenidos impartidos. Los rótulos «Esquema factori…» y «Material a entre…» de la captura están truncados y su alcance es desconocido. Las fuentes disponibles son apuntes y exámenes resueltos; no se recibió una hoja de ejercicios independiente.

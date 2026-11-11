```profile-metadata
{
  "schema_version": "1.0",
  "subject": {
    "slug": "historia",
    "name": "Historia sintética"
  },
  "source_snapshot": {
    "repository": "otromas1234/material-asignaturas",
    "tag": "plan/historia/20261030-fixture"
  },
  "references": [
    {
      "id": "ref-1",
      "path": "asignaturas/historia/examenes-referencia/synthetic.txt",
      "year": "unknown",
      "read_status": "partial",
      "included_locators": [
        "Pregunta A"
      ],
      "excluded_locators": [
        {
          "locator": "Página 2",
          "reason": "Imagen ilegible en fixture sintético"
        }
      ]
    }
  ],
  "limitations": [
    "Página 2 excluida; muestra parcial."
  ]
}
```

# Perfil sintético de Historia

## Fuentes y cobertura
Referencia sintética; año desconocido. Página 2 excluida por imagen ilegible.

## Patrones observados
```profile-observations
[
  {
    "id": "obs-1",
    "dimension": "question_types",
    "description": "Respuesta breve observada",
    "evidence": [
      {
        "reference_id": "ref-1",
        "locator": "Pregunta A"
      }
    ]
  },
  {
    "id": "obs-2",
    "dimension": "organization",
    "description": "Una sección visible",
    "evidence": [
      {
        "reference_id": "ref-1",
        "locator": "Pregunta A"
      }
    ]
  },
  {
    "id": "obs-3",
    "dimension": "instructions",
    "description": "Explicar con palabras propias",
    "evidence": [
      {
        "reference_id": "ref-1",
        "locator": "Pregunta A"
      }
    ]
  },
  {
    "id": "obs-4",
    "dimension": "apparent_difficulty",
    "description": "Dificultad aparente orientativa",
    "evidence": [
      {
        "reference_id": "ref-1",
        "locator": "Pregunta A"
      }
    ]
  },
  {
    "id": "obs-5",
    "dimension": "response_modes",
    "description": "Texto",
    "evidence": [
      {
        "reference_id": "ref-1",
        "locator": "Pregunta A"
      }
    ]
  }
]
```

## Recurrencias
```profile-recurrences
[
  {
    "id": "rec-1",
    "unit": "distinct_exams",
    "description": "Explicación conceptual observada; no predice próximos exámenes",
    "observed_count": 1,
    "sample_size": null,
    "evidence": [
      {
        "reference_id": "ref-1",
        "locator": "Pregunta A"
      }
    ],
    "comparability_limits": "Solo fragmento legible; denominador desconocido."
  }
]
```

## Recomendaciones de formato
Orientación, no observación: usar preguntas breves sin predecir el examen real.

## Ejemplos originales
Ejemplo inventado: explique cómo cambiaría una sociedad ficticia sin intercambio.

## Limitaciones
Año desconocido. Página 2 excluida; sin inferencia de temario ni frecuencia porcentual.

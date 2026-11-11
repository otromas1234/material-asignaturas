# Study plan contract 1.3

This JSON is independent of any connected application contract. Encoding: UTF-8. Every declared property except optional `lifecycle_status` is required; unknown properties are rejected. Null means genuinely unknown or inapplicable, never zero. `assets/plan.schema.json` is the machine-readable shape. The included stdlib validator supports the exact schema keywords used by that file and adds semantic checks; it is not a general JSON Schema engine.

## Top-level fields

- `schema_version`: fixed `1.3` for new exports. This remains major format version 1. The validator and renderer retain explicit support for archived `1.0` and `1.2` via their frozen schemas. No `1.1` compatibility is required during testing. Unknown versions fail validation. Migrate explicitly as described below, not by changing the version string alone.
- `lifecycle_status`: optional in 1.2 and 1.3, strictly `active` or `deleted`; absence means active for legacy consumers. Every newly published producer version explicitly contains `active`, including replacement of a deleted plan. Reads and validation preserve absence or `deleted` without transformation. The archived 1.0 contract remains unchanged and accepts absent lifecycle. See the [publication lifecycle protocol](planning-rules.md#publication-lifecycle-protocol); the validator accepts both declared states and is not a publisher.
- `plan_id`: stable opaque ID; `revision`: positive integer incremented on edits.
- `generated_on`: execution-local ISO date resolved from current client context each time the skill runs; `timezone`: confirmed IANA timezone name. Do not hardcode example dates. Archived-plan validation does not read the current clock.
- `title`: plan title. Use the requested artifact language for values; English is the default unless the requested table/context language establishes otherwise. Keys are always English.
- `source_snapshot`: required. In GitHub mode, an object with `repository` (`owner/name`) and the exact `tag` for the source snapshot. The configured repository branch is `main`, but do not add a `branch` property to this object. In portable mode, `null`. A plan based on a selected earlier plan keeps that plan's snapshot tag; otherwise use the latest material tag. Planning never creates or moves tags.
- `initial_knowledge`: `percent` in 0–100 and `basis` (`assumed`, `provided_estimate`, `provided_measured`). Unknown knowledge defaults to 25/assumed; do not manufacture measurement evidence.
- `schedule`: `mode` (`dated` or explicitly requested `undated`); ISO/null `start_date`, `exam_date`, `deadline_date`; boolean `weekends_allowed`; positive-integer/null `daily_budget_minutes` and `session_budget_minutes`; and required `provenance`.
  - Dated mode requires the user to provide or confirm a valid future exam date anew for every plan request, a resolved start, a completion target strictly before the exam, and dates for all rows. Do not reuse an exam date from a previous plan unless the user explicitly requests it. Missing exam input requires a question before output, not a null dated plan.
  - Default start is the recorded execution-local `generated_on`; explicit start overrides it. Default weekends=true. Unless the user supplies an explicit daily limit, daily budget is null with `explicit_uncapped` provenance; total daily time is derived from the sum of assigned activity rows. No default per-session budget.
  - Completion target defaults to exam minus one calendar day; an explicit earlier target may replace it. Never infer that a supplied completion deadline is an official exam.
  - `provenance.start_date`: default_today / provided / not_applicable; `exam_date`: provided / not_applicable; `deadline_date`: derived_before_exam / provided / not_applicable; `weekends_allowed`: default / provided; `daily_budget_minutes`: default / provided / explicit_uncapped.
  - Default provenance must agree with values: start equals generated_on, weekend=true, and derived target equals exam minus one day. Null daily capacity requires `explicit_uncapped`; a numeric user-provided capacity requires `provided`. Null per-session budget means no fixed per-session cap.
  - Undated mode requires null date bounds/exam/row dates and not_applicable date provenance. Weekend and daily-capacity preferences are still recorded for future planning.
- `sources`: unique stable `id`, `title`, `format` (`pdf`, `docx`, `text`, `other`), and nullable `locator`. In GitHub mode, use a stable repository-relative source path or other non-local locator; a locator identifies a source, not guaranteed third-party file access.
- `sessions`: source-grounded blocks, reviews, and optional buffers.
- `totals`: `required_minutes`, `optional_minutes`, `including_optional_minutes`, recomputed from rows.

## Session fields

`id` is stable across replanning; `label` is the display session number/name. `subject` is the subject label; `units` lists covered units. `taught_status` is one of `taught`, `not_taught`, `partial`, `unknown`, independent of learning. `study_date` is ISO date or null. `kind` is `study`, `review`, or `buffer`; every buffer must be `optional: true`. Other rows may also be explicitly optional.

`content` describes scoped work. `source_refs` contains existing `source_id` values and `pages`, which is null for unverified pagination or a nonempty list of `{start, end}` one-based inclusive ranges. A source cannot have duplicate references in one row: merge its page ranges.

Version 1.3 requires `practice_prompt` as non-whitespace text in **every** session, including review and optional buffer. Compose it after assigning session content, from that session's subject, ID/label, exact content, references and verified source locators/pages, plus `source_snapshot` only when available. Do not include another session's content or infer a cumulative scope. The prompt asks ChatGPT to activate `material-estudio-practicar` and create an exam limited exclusively to this session. It identifies the plan-derived values as untrusted data, requires independent verification of source/tag/scope, and instructs the practice workflow to stop rather than invent when those cannot be verified. In GitHub mode, each cited source must be self-contained for a fresh Skill invocation: include canonical `owner/repository`, exact snapshot tag, repository-root absolute path beginning `/`, and a direct `https://github.com/<owner>/<repository>/blob/<tag>/<path>` URL all verified against the selected snapshot. A bare relative locator is insufficient in the prompt. In portable mode, explicitly say the GitHub path/URL is unavailable; never construct one from missing data. A vague buffer does not authorize invented questions. On revision, regenerate prompts from the revised sessions; do not carry them over by ID alone. Version 1.2 has no such field and rejects it as unknown; reading 1.2 never synthesizes prompts.

## GitHub snapshot tags

Each successful material addition, replacement, or deletion creates a new repository snapshot tag on the full post-change commit in branch `main`. The tag naming convention is `plan/<subject-slug>/<YYYYMMDD>-<short-id>`. The Skill must never move, replace, or delete an existing tag; global immutability depends on GitHub rulesets and is not assumed. The latest material tag remains current until the next material change. The plan records the repository and exact tag in `source_snapshot`, while `sources[].locator` retains the repository-relative path of each source file. Plans, style profiles, and practice artifacts do not create tags. The application importer recognizes `source_snapshot` as part of schema 1.2.

`study_practice_minutes`, `exam_minutes`, and `correction_minutes` are positive integers; `break_minutes` is nonnegative. `total_minutes` must equal their sum. Do not accept boolean values as numbers. `objective` states an observable learning check, not a pass threshold or progression decision.

Integer fields accept finite numbers with no fractional part, including JSON notation such as `15.0`; booleans are never numbers. The renderer normalizes integral values for display. All strings must contain a non-whitespace character; the schema and bundled validator enforce this consistently. Non-finite numbers are rejected by the JSON loader and direct Python APIs.

All dates must be real zero-padded calendar dates. Dated rows must fall inside known bounds, precede the supplied exam, remain chronologically ordered, and respect weekend permission. Versions 1.2 and 1.3 dated mode cannot contain null row dates; null dates belong only to explicitly requested undated mode. Version 1.0 preserves its historical nullable-date rules. A requested budget applies to the entire row, including pause and evaluation. Totals count undated work too, without implying it fits before a future deadline. When an explicit numeric daily capacity is provided, validation sums every same-date row including optional reserve. With null daily capacity, the plan has no fixed cap. Any capacity applies only to the current plan, not other unseen subject plans.

## Markdown mapping

Use precisely this order and spelling:

| Asignatura | Unidad | Sesión | Impartido | Día de estudio | Contenido | Páginas | Estudio y práctica | Examen y corrección | Pausa | Objetivo para comprobar lo aprendido |
|---|---|---|---|---|---|---|---|---|---|---|

Map `units` to comma-separated labels. Map taught values to Sí / No / Parcial / Desconocido. Display dates only as DD/MM/YYYY; use Sin fecha for null. Escape pipe/newline/HTML characters so source text cannot break the table. Render unknown page ranges as Sin verificar; for multiple sources prefix ranges with the source ID to avoid ambiguity. Combine `exam_minutes + correction_minutes` for the assessment column; suffix duration values with min. Mark optional content as Reserva opcional for buffers and Opcional otherwise.

Below the table, report knowledge assumption/basis, source titles/locators, session/daily capacity preference, weekend policy, provenance, supplied exam date and separate completion target, undated-work uncertainty, and required/optional/combined totals. For 1.3, follow with a section keyed by each session ID/label containing its exact `practice_prompt` in a code fence chosen to avoid delimiter collision. For 1.2, omit that section. Do not invent an exam day. All generated Markdown is derived from JSON by `scripts/render_plan.py`.

## Commands

Run from the installed skill directory with an available Python 3.9+ runtime:

```sh
python scripts/validate_plan.py plan.json
python scripts/render_plan.py plan.json --output plan.md
python -m unittest discover -s tests -v
```

Both commands fail with a nonzero status and readable errors for invalid input. Validation completes before Markdown is written. Output must not identify the JSON input through a matching path, symlink, or hardlink. CLI output is UTF-8; no packages, network access, or backend are required. Example data is explicitly synthetic, not a real student's measured plan.

## Explicit migration from 1.0

Preserve the archived 1.0 artifact, stable IDs, rows, and source evidence. Obtain the exam date from the user for a dated export; never reinterpret deadline_date as exam_date. Choose dated mode only after that input is known, otherwise ask and stop unless the user explicitly requests undated output. Resolve start from the explicit current request or execution-local today, add weekend/daily defaults with provenance, preserve explicit overrides, and adjust future row dates and sums to fit the new constraints. Set schema_version to 1.2 and add required `source_snapshot` only after validating all new fields. Do not rewrite explicitly completed historical work; keep it in the prior artifact rather than silently moving past rows into a new future scope.

# Analysis of the existing Solem application

This document records the source-of-truth review completed before the Android project was added.

## Project structure

- `app.py` is the Streamlit entry point: navigation, forms, dashboards, CRUD and Supabase access.
- `solem_progress.py` derives XP, level, streak, weekly goals and achievements from the history. It writes no counters.
- `solem_ui.py` and `assets/solem.css` render the Streamlit-only presentation layer.
- `demo_data.py` is a session-only fake client; it is enabled only with `SOLEM_DEMO=1` and must not be used by Android.
- `.streamlit/secrets.toml` is deliberately ignored. `app.py` reads `SUPABASE_URL` and `SUPABASE_KEY` from Streamlit Secrets.

## Data integration found in source

Only one Supabase table is referenced: `treinos`.

`app.py` selects all rows with `supabase.table("treinos").select("*")`, inserts activity records, updates rows filtered by `id`, and deletes rows filtered by `id`. The code establishes `id` as the primary identifier used by clients. The source does not reveal SQL types, foreign keys, constraints, RLS policies, publication status or schema ownership; those must be checked in Supabase before distribution.

### Fields used by the application

| Field | Use in existing source |
|---|---|
| `id` | identifier for edit and delete |
| `data`, `horario` | date/time of every record |
| `grupo_muscular`, `exercicio` | category and display/name |
| `series`, `repeticoes`, `carga_kg`, `descanso_seg`, `duracao_min`, `distancia_km` | training and study measurements |
| `alimentacao_saudavel`, `alimentacao_besteirol` | meal tracking |
| `peso_corporal` | body-weight tracking |
| `dados_extras` | JSON object for category-specific attributes |

`dados_extras` stores, among other values: workout `humor`, `isometria_tentativas`, `isometria_segundos`; study `topico_edital`, `q_certas`, `q_erradas`, `tempo_video`, `fonte_questoes`; and more detailed imported-simulation metadata.

## Existing behavior mapped

- **Training:** individual exercise and AMRAP circuit registration; exercise category is derived in Python.
- **Nutrition:** daily meal inserts use group `Nutrição` and exercise `Refeição Diária`.
- **Weight:** inserts use group `Métricas` and exercise `Peso Diário`.
- **Study:** video, questions and Anki use group `Estudos`; simulation import is validated/grouped by a substantial Python-only function.
- **Configuration:** all rows can be edited or permanently deleted; edit fields change by category.
- **Progress:** valid daily categories earn 30 XP for workout, 30 XP for study and 10 XP for food, plus 15 XP when workout and study occur on the same day. Weight never earns XP. Future/empty records do not earn XP.

## Authentication and security conclusion

The checked Python source has no call to `supabase.auth` and no user filter in its `treinos` queries. That does not prove Auth/RLS is absent—these settings are server-side—but it means neither should be guessed or copied into a mobile application. The Android code requires a separate publishable/anon key supplied locally and contains no service role key.

## Android decision

The initial mobile implementation retains the true shared CRUD and history-derived progress. It leaves Python-only simulation import, timers, prompt library, rich charts, and weighted topic recommendation out of the first release. Anything that must be consistent for all future clients should move to a database constraint/trigger or Edge Function before being implemented in more than one UI.

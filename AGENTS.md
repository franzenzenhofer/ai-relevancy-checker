# Repository Guidelines

## Project Structure & Module Organization
- `run.py` is the CLI entrypoint; it loads `configs/*.config.json`, applies overrides, and orchestrates runs.
- `core/` holds the pipeline: config loading, GSC client/query models, prompt generation, LLM clients (`llm_openai.py`, `llm_gemini.py`), relevancy parsing, and HTML/CSV report builders.
- `configs/` contains example site configs; copy one to add a new property. Generated artifacts land in `reports/`, `exports/`, `results/`, and `logs/`; run metadata lives in `state/`.
- `tests/` currently houses the live LLM integration test (`tests/test_live_llm.py`).

## Build, Test, and Development Commands
- Create env + install deps: `python -m venv .venv && source .venv/bin/activate && pip install openai google-generativeai google-auth-oauthlib`.
- Run a standard job: `python run.py -c configs/karriere.at.config.json -n 100 --desktop`.
- Resume, retry, or regenerate: `python run.py -c <config> --continue-run <id>`, `--retry-failed <id>`, or `--report-only <id>`.
- Integration test (requires real keys): `python -m unittest tests/test_live_llm.py`; skips automatically if `OPENAI_API_KEY` or `GEMINI_API_KEY` is missing.

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indents, type hints, and dataclasses where state is grouped (`Config`, `QueryResult`).
- Keep everything config-driven; avoid hidden defaults. Use `config.apply_overrides` for runtime tweaks and prefer `pathlib.Path`.
- Functions/classes use `snake_case`/`PascalCase`; module-level constants are UPPER_SNAKE.
- Logging goes through `core.logger`; include request IDs when available and avoid printing secrets.

## Testing Guidelines
- Tests use `unittest`; name files `test_*.py` and prefer deterministic inputs. Mock LLMs unless explicitly running the live test to avoid token burn.
- When adding features that touch the pipeline, cover prompt generation, parsing, and reporting slices separately to keep failures local.

## Commit & Pull Request Guidelines
- Follow the existing short, imperative commit style (`Fix methodology section…`, `Enforce JSON domain responses…`). Keep summaries under ~72 chars.
- PRs should state scope, configs/CLI flags touched, and any behavior changes. Include a sample run command/output path or screenshots for report UI changes. Link issues when applicable.

## Security & Configuration Tips
- Keep API keys in `.env`; never commit `client_secret.json` or `token.json`. The OAuth files live one directory above the repo by design.
- Validate configs before running; `prompt_mode` must stay `ai`, and provider lists should be explicit (`openai`, `gemini`).
- Reports/CSVs may contain real query data—cleanse before sharing externally. Do not log full prompts or tokens when debugging production data.

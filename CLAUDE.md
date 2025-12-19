# CLAUDE.md

Project instructions for Claude Code when working on this codebase.

## Quick Reference

```bash
# Setup
source .venv/bin/activate

# New run with N queries
python run.py -c configs/mysite.config.json -n 100 -d

# Test single query
python run.py -c configs/mysite.config.json -q "example query" --debug

# Regenerate report from existing data (NO API calls)
python run.py -c configs/mysite.config.json --regenerate RUN_ID -d

# List all runs
python run.py -c configs/mysite.config.json --list-runs
```

## Architecture

```
run.py                          # CLI entry point
core/runner.py                  # Main execution + healthcheck
core/config.py                  # Config loading + validation
core/gsc_client.py              # Google Search Console API
core/llm_openai.py              # OpenAI client
core/llm_gemini.py              # Gemini client
core/healthcheck.py             # API key validation
core/prompt_generator.py        # Unbiased prompt generation
core/relevancy_engine.py        # Brand detection logic
core/report_generator.py        # HTML report generation
core/report_kpi.py              # KPI card generation
core/report_charts.py           # Chart generation
core/presentation_generator.py  # HTML presentation slides
core/csv_exporter.py            # CSV export
```

## Critical Rules

### NO FALLBACKS
- AI fails -> ABORT (no template fallback)
- API key fails -> ABORT (no skip)
- `prompt_mode` must be `"ai"` (RuntimeError otherwise)

### MODELS - USE LATEST ONLY
```
OpenAI:  gpt-5-mini (main), gpt-5-nano (prompts)
Gemini:  gemini-flash-latest
```

### HEALTHCHECK REQUIRED
Every run must show:
```
Pinging API keys for: openai, gemini...
API healthcheck PASSED - all providers reachable
```

### TESTING REPORT FEATURES
When testing report/visualization changes, **regenerate from existing data** (no API calls):
```bash
python run.py -c configs/mysite.config.json --regenerate RUN_ID -d
```

## Auth Files

```
.env                      # OPENAI_API_KEY, GEMINI_API_KEY
../token.json             # GSC OAuth token (gitignored)
../client_secret.json     # GSC OAuth credentials (gitignored)
```

## Key Metrics

1. **Answer Visibility**: Brand mentioned in AI answer text (True/False)
2. **Domain Rank**: Position 1-10 in domain list (None = not found)

## Config Structure

See `configs/example.config.json` for template. Required fields:
- `site_url`: GSC property URL
- `domain`: Target domain
- `brand_names`: Array of brand name variations to detect

## CLI Options

| Flag | Description |
|------|-------------|
| `-c`, `--config` | Config file (required) |
| `-n`, `--max-queries` | Number of queries |
| `-d`, `--desktop` | Copy output to Desktop |
| `-q`, `--single-query` | Test one query |
| `--regenerate RUN_ID` | Regenerate report only |
| `--run-id RUN_ID` | Add to existing run |
| `--retry-failed RUN_ID` | Retry failed queries |
| `--list-runs` | List all runs |
| `--debug` | Verbose logging |

# AI Relevancy Checker

**Measure your brand's visibility in AI-generated answers from ChatGPT and Google Gemini.**

Fetches your top search queries from Google Search Console, asks AI models to answer them, and measures whether your brand appears in the responses.

## Table of Contents

- [Quick Start](#quick-start)
- [Setup](#setup)
  - [Requirements](#requirements)
  - [API Keys](#api-keys)
  - [Google Search Console Auth](#google-search-console-authentication)
- [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Reference](#cli-reference)
- [How It Works](#how-it-works)
  - [Metrics](#metrics)
- [Output](#output)
- [Security](#security)

---

## Quick Start

> **Note:** This tool requires Google Search Console access. Complete [GSC Authentication](#google-search-console-authentication) setup before running.

```bash
# 1. Clone and install
git clone https://github.com/franzenzenhofer/ai-relevancy-checker.git
cd ai-relevancy-checker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp configs/example.config.json configs/mysite.config.json
# Edit mysite.config.json with your site details

# 3. Add API keys to .env
echo "OPENAI_API_KEY=sk-your-key" > .env
echo "GEMINI_API_KEY=AIza-your-key" >> .env

# 4. Set up GSC auth (see instructions below)
# Place client_secret.json in parent directory

# 5. Run
python run.py -c configs/mysite.config.json -n 100 -d
```

---

## Setup

### Requirements

- Python 3.10+
- OpenAI API key ([get one](https://platform.openai.com/api-keys))
- Google Gemini API key ([get one](https://aistudio.google.com/app/apikey))
- Google Search Console property access

### API Keys

Create `.env` in project root:

```
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...
```

### Google Search Console Authentication

You need two files for GSC access:
- `client_secret.json` - OAuth credentials (create once)
- `token.json` - Auth token (auto-generated on first run)

<details>
<summary><strong>Step-by-step GSC setup (click to expand)</strong></summary>

#### A. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → Name it "AI Relevancy Checker"

#### B. Enable Search Console API

1. Go to "APIs & Services" → "Library"
2. Search "Google Search Console API" → Enable

#### C. Configure OAuth Consent

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" → Create
3. Fill: App name, support email, developer email
4. Add scope: `https://www.googleapis.com/auth/webmasters.readonly`
5. Add yourself as test user

#### D. Create Credentials

1. Go to "APIs & Services" → "Credentials"
2. Create OAuth client ID → **Desktop app**
3. Download JSON → Rename to `client_secret.json`
4. Move to **parent directory** of this project

#### E. First Run

```bash
python run.py -c configs/mysite.config.json -n 1
```
Browser opens → Sign in → Grant access → `token.json` created automatically.

</details>

**Troubleshooting:**
- "Access blocked": Add yourself as test user in OAuth consent screen
- "Property not found": `site_url` must match GSC exactly
- Token expired: Delete `token.json`, run again

### File Structure

```
parent-directory/
├── client_secret.json      # GSC OAuth (gitignored)
├── token.json              # Auto-generated (gitignored)
└── ai-relevancy-checker/
    ├── .env                # API keys (gitignored)
    ├── configs/mysite.config.json  # Your config (gitignored)
    ├── reports/            # Output (gitignored)
    └── exports/            # CSV output (gitignored)
```

---

## Configuration

Copy and edit `configs/example.config.json`:

```json
{
  "site_url": "https://www.example.com/",
  "domain": "example.com",
  "brand_names": ["example.com", "www.example.com", "Example Inc"],
  "user_country": "Austria",
  "user_country_en": "Austria",
  "user_city": "Vienna"
}
```

| Field | Required | Description |
|-------|:--------:|-------------|
| `site_url` | Yes | GSC property URL (must match exactly) |
| `domain` | Yes | Domain to check visibility for |
| `brand_names` | Yes | All name variations to detect |
| `user_country` | Yes | Country for prompts (local language) |
| `user_country_en` | Yes | Country for prompts (English) |
| `user_city` | No | City for location context |
| `force_language` | No | Override detection: `de`, `en` |
| `gsc_days` | No | Days of data (default: 90) |

---

## Usage

```bash
# Basic run (100 queries, copy to Desktop)
python run.py -c configs/mysite.config.json -n 100 -d

# Test single query
python run.py -c configs/mysite.config.json -q "your query" --debug

# Regenerate report (no API calls)
python run.py -c configs/mysite.config.json --regenerate RUN_ID -d

# Add queries to existing run
python run.py -c configs/mysite.config.json --run-id RUN_ID -n 50 --offset 100

# Retry failed queries
python run.py -c configs/mysite.config.json --retry-failed RUN_ID
```

### CLI Reference

| Option | Short | Description |
|--------|:-----:|-------------|
| `--config` | `-c` | Config file path **(required)** |
| `--max-queries` | `-n` | Number of queries to process |
| `--desktop` | `-d` | Copy output to Desktop |
| `--single-query` | `-q` | Test one query |
| `--debug` | | Verbose logging |
| `--regenerate` | | Regenerate report from stored data |
| `--run-id` | | Add to existing run |
| `--continue-run` | | Resume incomplete run |
| `--retry-failed` | | Retry failed queries |
| `--list-runs` | | Show all runs |
| `--providers` | `-p` | `openai`, `gemini`, or both |
| `--offset` | | Skip first N queries |
| `--days` | | Days of GSC data |
| `--presentation` | | Generate HTML slides |

---

## How It Works

```
GSC Queries → Prompt Generator → LLMs (OpenAI + Gemini) → Report
                (unbiased)           ↓
                              Brand Detection
```

1. **Fetch** top queries by clicks from GSC
2. **Generate** natural prompts (AI doesn't know your brand)
3. **Query** both OpenAI and Gemini
4. **Detect** brand in answers + domain rankings
5. **Report** HTML dashboard + CSV export

### Metrics

| Metric | What it measures |
|--------|------------------|
| **Answer Visibility** | Brand mentioned in AI's answer text |
| **Domain Rank** | Position 1-10 when AI lists relevant sites |
| **Top-5 %** | How often you rank #1-5 |
| **Top-10 %** | How often you rank #1-10 |

**Example:**
- Query: "best pizza restaurants"
- AI Answer: "Try pizzahut.com, dominos.com..."
- If you're pizzahut.com → **Visible in answer**
- AI Domain List: `["yelp.com", "pizzahut.com", ...]`
- If you're pizzahut.com → **Rank #2**

### Models

| Purpose | OpenAI | Gemini |
|---------|--------|--------|
| Answers | gpt-5-mini | gemini-flash-latest |
| Prompts | gpt-5-nano | - |

Configurable via `openai_model`, `gemini_model` in config.

---

## Output

**HTML Report** - Interactive dashboard with:
- KPI cards (visibility %, rankings)
- Charts (pie, bar, breakdown)
- Query table with filters
- Methodology transparency

**CSV Export** - Raw data for analysis:
```
query, prompt, clicks, openai_visible, openai_rank, gemini_visible, gemini_rank...
```

Use `-d` / `--desktop` to auto-copy to Desktop.

---

## Security

Gitignored (never committed):
- `.env` - API keys
- `configs/*.config.json` - Your configs
- `client_secret.json`, `token.json` - GSC credentials
- `results/`, `reports/`, `exports/`, `state/`, `logs/`

Only `configs/example.config.json` is committed.

---

## License

MIT

---

Built by [Franz Enzenhofer](https://github.com/franzenzenhofer) with [Claude Code](https://claude.ai/code).

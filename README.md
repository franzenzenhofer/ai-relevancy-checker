# AI Relevancy Checker

**Measure your brand's visibility in AI-generated answers from ChatGPT and Google Gemini.**

This tool fetches your top search queries from Google Search Console, asks AI models to answer them, and measures whether your brand/domain appears in the responses.

## Key Features

- **Dual AI Analysis**: Tests both OpenAI (ChatGPT) and Google Gemini
- **Two Visibility Metrics**: Answer mentions + Domain ranking
- **GSC Integration**: Automatically fetches your top queries by clicks
- **Interactive Reports**: HTML reports with charts and filters
- **CSV Export**: Raw data for further analysis
- **Config-Driven**: Works with any website via JSON config
- **Desktop Output**: `--desktop` flag copies reports directly to your Desktop

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/franzenzenhofer/ai-relevancy-checker.git
cd ai-relevancy-checker
python -m venv .venv
source .venv/bin/activate
pip install openai google-generativeai google-auth-oauthlib

# 2. Create .env with your API keys
echo "OPENAI_API_KEY=sk-your-key-here" > .env
echo "GEMINI_API_KEY=AIza-your-key-here" >> .env

# 3. Create your config (copy and edit example)
cp configs/example.config.json configs/mysite.config.json
# Edit configs/mysite.config.json with your site details

# 4. Run (requires GSC setup - see below)
python run.py -c configs/mysite.config.json -n 100 --desktop
```

---

## Usage

### Basic Commands

```bash
# Run with 100 queries, output to Desktop
python run.py -c configs/mysite.config.json -n 100 --desktop

# Test a single query
python run.py -c configs/mysite.config.json -q "your search query" --debug

# List previous runs
python run.py -c configs/mysite.config.json --list-runs

# Regenerate report from existing data (no API calls)
python run.py -c configs/mysite.config.json --regenerate abc123 --desktop
```

### CLI Options - Complete Reference

#### Required
| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | **Required.** Path to config file |

#### Query Selection
| Option | Short | Description |
|--------|-------|-------------|
| `--max-queries` | `-n` | Number of queries to process (default: from config) |
| `--offset` | | Skip first N queries from GSC |
| `--days` | | Days of GSC data to fetch (default: 90) |

#### Output Control
| Option | Short | Description |
|--------|-------|-------------|
| `--desktop` | `-d` | Copy report & CSV to Desktop |
| `--name` | | Custom name for output files (e.g., "mysite-dec12") |
| `--presentation` | `-pres` | Also generate HTML slide presentation |

#### Run Management
| Option | Short | Description |
|--------|-------|-------------|
| `--list-runs` | | List all runs with ID, status, progress |
| `--run-id` | | **ADD** queries to existing run (accumulates results) |
| `--continue-run` | | **RESUME** incomplete run |
| `--regenerate` | | **REGENERATE** report from stored data (NO API calls!) |
| `--report-only` | | Alias for `--regenerate` |
| `--retry-failed` | | Retry only failed/missing queries for a run |

#### Debug & Testing
| Option | Short | Description |
|--------|-------|-------------|
| `--single-query` | `-q` | Test one query in debug mode |
| `--language` | | Language override for single query: `de` or `en` |
| `--debug` | | Enable verbose debug logging |

#### Provider & Concurrency
| Option | Short | Description |
|--------|-------|-------------|
| `--providers` | `-p` | Providers: `openai`, `gemini`, or `openai,gemini` |
| `--max-query-workers` | | Max concurrent queries (default: 50) |
| `--max-provider-workers` | | Per-query concurrency for answer/domain (default: 2) |
| `--prompt-concurrency` | | Concurrent prompt generations (default: 8) |
| `--request-delay` | | Delay between API requests in seconds |

### Common Workflows

```bash
# New run with 100 queries
python run.py -c configs/mysite.config.json -n 100 -d

# Regenerate report after code changes (NO API CALLS)
python run.py -c configs/mysite.config.json --regenerate abc123 -d

# Add 50 more queries to existing run (starting at offset 100)
python run.py -c configs/mysite.config.json --run-id abc123 -n 50 --offset 100 -d

# Retry failed queries
python run.py -c configs/mysite.config.json --retry-failed abc123 -d

# Debug single query
python run.py -c configs/mysite.config.json -q "example query" --debug
```

---

## What It Measures

### 1. Answer Visibility
> "Does the AI mention your brand in its answer?"

The tool asks AI to naturally answer your search query, then checks if your domain/brand appears in the response text.

**Example Query**: "jobs in vienna"
**AI Answer**: "You can find jobs in Vienna on karriere.at, Indeed, and LinkedIn..."
**Result**: karriere.at = **VISIBLE** in answer

### 2. Domain Ranking
> "When asked for relevant websites, does AI recommend yours?"

The tool asks: "What are the 10 most relevant domains for this query?" and checks your position.

**Example Query**: "jobs in vienna"
**AI Response**: `["indeed.com", "karriere.at", "linkedin.com", ...]`
**Result**: karriere.at = **Rank #2**

### Key Metrics in Reports

| Metric | Description |
|--------|-------------|
| **Answer Visible %** | Percentage of queries where brand appears in answer |
| **Top-5 %** | Percentage of queries where domain ranks #1-5 |
| **Top-10 %** | Percentage of queries where domain ranks #1-10 |
| **Avg Rank** | Average ranking position when present |

---

## Configuration

### Creating Your Config File

Config files live in `configs/`. Start with the example:

```bash
cp configs/example.config.json configs/mysite.config.json
```

### Config Structure

```json
{
  "site_url": "https://www.example.com/",
  "domain": "example.com",
  "brand_names": ["example.com", "www.example.com", "Example Inc"],

  "user_city": "Vienna",
  "user_city_en": "Vienna",
  "user_country": "Österreich",
  "user_country_en": "Austria",

  "language_indicators": {
    "de": ["ä", "ö", "ü", "ß", "wien", "österreich"]
  },
  "force_language": "de",

  "prompt_mode": "ai",
  "default_providers": ["openai", "gemini"],
  "gsc_days": 90,
  "max_query_workers": 50,
  "max_provider_workers": 2,
  "prompt_concurrency": 8
}
```

### Config Fields

| Field | Required | Description |
|-------|----------|-------------|
| `site_url` | Yes | Your GSC property URL |
| `domain` | Yes | Domain to check visibility for |
| `brand_names` | Yes | All variations to detect (domain, brand name, etc.) |
| `user_country` | Yes | Country for AI prompts (local language) |
| `user_country_en` | Yes | Country for AI prompts (English) |
| `user_city` | No | City for location context |
| `force_language` | No | Override language detection (`de`, `en`) |
| `gsc_days` | No | Days of GSC data to fetch (default: 90) |
| `max_query_workers` | No | Concurrent queries processed (default: 50) |
| `max_provider_workers` | No | Per-query concurrency for answer/domain (default: 2) |
| `prompt_concurrency` | No | Concurrent prompt generations (default: 8) |
| `default_providers` | No | Which AI to use (default: both) |

---

## Setup

### 1. API Keys

Create `.env` file in project root:

```bash
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...
```

Get keys from:
- OpenAI: https://platform.openai.com/api-keys
- Gemini: https://aistudio.google.com/app/apikey

### 2. Google Search Console

You need OAuth credentials to access GSC data.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable "Search Console API"
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `client_secret.json`
6. Place in **parent directory** of this project

First run will open browser for OAuth consent. Token saved to `token.json`.

### 3. File Structure

```
parent-directory/
├── client_secret.json    # OAuth credentials (gitignored)
├── token.json            # Generated after first auth (gitignored)
└── ai-relevancy-checker/
    ├── run.py
    ├── configs/
    │   ├── example.config.json  # Template config
    │   └── mysite.config.json   # Your config (gitignored)
    ├── core/
    ├── reports/          # Generated HTML reports (gitignored)
    ├── exports/          # Generated CSV files (gitignored)
    └── .env              # API keys (gitignored)
```

---

## Output

### HTML Report

Interactive report includes:
- **KPI Summary**: Answer visibility %, Top-5 %, Top-10 % per AI
- **Charts**: Pie charts, bar comparisons, visibility breakdown
- **Query Table**: Full results with filters and sorting
- **Methodology**: Complete transparency on prompts used

### CSV Export

All data in flat format for analysis:
```
run_id, query_text, hypothetical_prompt, clicks, impressions,
openai_answer_visible, openai_rank, openai_domains,
gemini_answer_visible, gemini_rank, gemini_domains, ...
```

### Desktop Output

Use `--desktop` flag to automatically copy both report and CSV to your Desktop folder.

---

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    GSC      │────▶│   Prompt    │────▶│    LLM      │
│  Top 100    │     │  Generator  │     │   OpenAI    │
│  Queries    │     │ (Unbiased)  │     │   Gemini    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌─────────────┐            │
                    │   Report    │◀───────────┘
                    │  Generator  │
                    └─────────────┘
```

1. **Fetch Queries**: Gets top queries by clicks from GSC (up to 25,000 rows)
2. **Generate Prompts**: AI creates natural user questions (unbiased, no brand info)
3. **Query LLMs**: Asks both OpenAI and Gemini to answer + list relevant domains
4. **Analyze Results**: Checks for brand presence in answers and rankings
5. **Generate Reports**: Creates HTML report with charts + CSV export

### Unbiased Prompts

**Critical**: The prompt generator does NOT know your target domain. This ensures unbiased measurement. Prompts are generated based only on the search query and user location.

---

## Models Used

| Purpose | OpenAI | Gemini |
|---------|--------|--------|
| Answer Generation | gpt-5-mini | gemini-flash-latest |
| Prompt Generation | gpt-5-nano | - |
| Domain Ranking | gpt-5-mini | gemini-flash-latest |

Configurable via config file (`openai_model`, `openai_prompt_model`, `gemini_model`).

---

## Requirements

- Python 3.10+
- OpenAI API key
- Google Gemini API key
- Google Search Console access

### Python Packages

```bash
pip install openai google-generativeai google-auth-oauthlib
```

---

## Security Notes

This tool is designed for public release. Sensitive files are gitignored:

- `.env` - API keys
- `configs/*.config.json` - Client-specific configs (except `example.config.json`)
- `token.json`, `client_secret.json` - Google OAuth credentials
- `results/`, `reports/`, `exports/` - Generated output data
- `state/`, `logs/` - Runtime state

**Before contributing**: Ensure no sensitive data is committed.

---

## License

MIT

---

## Author

Built by Franz Enzenhofer with Claude Code.

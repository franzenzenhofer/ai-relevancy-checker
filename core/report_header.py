"""Header section for HTML report."""
from html import escape
from .config import config
from .llm_openai import get_openai_prompt_system


def render_header(domain: str, timestamp: str, query_count: int, run_id: str = "") -> str:
    """Render the report header with run ID - compact design."""
    o_model = config.openai_model
    g_model = config.gemini_model
    title_prefix = config.report_text.get("title_prefix", "AI Relevancy Report")
    return f"""
<header class="report-header">
<h1>{title_prefix}: {domain}</h1>
<div class="header-stats">
<span class="stat-box"><strong>{query_count}</strong> Queries</span>
<span class="stat-box">OpenAI: <strong>{o_model}</strong></span>
<span class="stat-box">Gemini: <strong>{g_model}</strong></span>
</div>
<div class="header-meta">Run: {run_id} | {timestamp}</div>
</header>"""


def render_methodology(domain: str, ctx: str, run_id: str = "", offset: int = 0, max_queries: int = 0, cli_command: str = "") -> str:
    """Render comprehensive methodology section with FULL transparency - uses REAL prompts from source."""
    # SINGLE SOURCE OF TRUTH: Use the ACTUAL language used in prompts
    # force_language determines which city/country values are used
    lang = config.force_language or "en"
    city_de = config.user_city
    city_en = config.user_city_en
    country_de = config.user_country
    country_en = config.user_country_en
    # Use the SAME logic as prompt_generator._location_parts()
    city = city_de if lang == "de" else city_en
    country = country_de if lang == "de" else country_en
    # Build location clause same way as in llm_openai.py - EXACT SAME LOGIC
    location_phrase = city.strip() or country
    location_clause = (
        f"{city}, {country}" if city and country and city.lower() != country.lower()
        else location_phrase
    )
    # Get the REAL prompt from source - DRY, no duplication!
    prompt_system = get_openai_prompt_system(location_clause, location_phrase)
    # Use the REAL domain prompts from config
    domain_prompt_openai = config.openai_domain_json_prompt
    domain_prompt_gemini = config.gemini_domain_json_prompt
    next_offset = offset + max_queries
    methodology_heading = config.report_text.get("methodology_heading", "Methodology - Full Transparency")
    # Use actual CLI command if available, otherwise show fallback
    actual_cli = cli_command or f"python run.py --config <config> --max-queries {max_queries}"
    return f"""
<section class="section"><h2>{methodology_heading}</h2>

<details>
<summary style="cursor:pointer;font-size:1.1rem;font-weight:600;margin-bottom:0.5rem">0. CLI Commands (click to expand)</summary>
<div style="background:#f0fdf4;border:2px solid #22c55e;padding:1rem;border-radius:8px;margin-bottom:1rem">
<p style="margin:0 0 0.5rem 0;font-weight:bold;color:#166534">📋 This run:</p>
<pre class="full-text" style="background:#1e293b;color:#e2e8f0;padding:1rem;border-radius:6px;font-size:13px;margin:0">{actual_cli}</pre>
</div>
<div style="background:#fef3c7;border:2px solid #f59e0b;padding:1rem;border-radius:8px;margin-bottom:1rem">
<p style="margin:0 0 0.5rem 0;font-weight:bold;color:#92400e">▶️ ADD more queries to this run (accumulate results):</p>
<pre class="full-text" style="background:#1e293b;color:#e2e8f0;padding:1rem;border-radius:6px;font-size:13px;margin:0">python run.py --run-id {run_id} --max-queries 10 --offset {next_offset}</pre>
<p style="margin:0.5rem 0 0 0;font-size:12px;color:#92400e">This will add 10 more queries starting from position {next_offset + 1} and regenerate the report with ALL results combined.</p>
</div>
<div style="background:#f1f5f9;border:1px solid #94a3b8;padding:1rem;border-radius:8px">
<p style="margin:0 0 0.5rem 0;font-weight:bold;color:#475569">🔍 Debug a single query:</p>
<pre class="full-text" style="background:#1e293b;color:#e2e8f0;padding:1rem;border-radius:6px;font-size:13px;margin:0">python run.py --single-query "your query here" --debug</pre>
</div>
</details>

<h3>1. Models Used</h3>
<table class="query-table" style="margin-bottom:1.5rem">
<tr><th>Purpose</th><th>OpenAI Model</th><th>Gemini Model</th><th>Max Tokens</th></tr>
<tr><td>Prompt Generation</td><td>{config.openai_prompt_model}</td><td>-</td><td>8000</td></tr>
<tr><td>Answer Generation</td><td>{config.openai_model}</td><td>{config.gemini_model}</td><td>{config.max_output_tokens_answer}</td></tr>
<tr><td>Domain List</td><td>{config.openai_model}</td><td>{config.gemini_model}</td><td>{config.max_output_tokens_domains}</td></tr>
</table>

<h3>2. Target Domain & Location (Configuration)</h3>
<table class="query-table" style="margin-bottom:1.5rem">
<tr><th>Setting</th><th>Value</th><th>Purpose</th></tr>
<tr><td>Target Domain</td><td><code>{domain}</code></td><td>Domain we check visibility for</td></tr>
<tr><td>Brand Names</td><td><code>{', '.join(config.brand_names)}</code></td><td>Alternative names to detect</td></tr>
<tr><td>Force Language</td><td><code>{lang}</code></td><td>Language used in all prompts</td></tr>
<tr><td>Location (ACTUAL)</td><td><code>{location_clause}</code></td><td>EXACT location sent to LLMs</td></tr>
<tr><td>City (DE/EN)</td><td><code>{city_de}</code> / <code>{city_en}</code></td><td>City in German/English</td></tr>
<tr><td>Country (DE/EN)</td><td><code>{country_de}</code> / <code>{country_en}</code></td><td>Country in German/English</td></tr>
<tr><td>Run ID</td><td><code>{run_id}</code></td><td>Unique identifier for this run</td></tr>
</table>

<h3>3. Prompt Generation (UNBIASED)</h3>
<p>The hypothetical user prompt is generated by AI. <strong>Important:</strong> The prompt generator does NOT know the target domain - this ensures unbiased evaluation.</p>
<p><strong>System prompt for prompt generation:</strong></p>
<pre class="full-text" style="background:#f1f5f9;padding:1rem;border-radius:6px;font-size:12px">{escape(prompt_system)}</pre>

<h3>4. Answer Generation</h3>
<p><strong>System context sent to LLMs:</strong></p>
<pre class="full-text" style="background:#f1f5f9;padding:1rem;border-radius:6px;font-size:12px">{escape(ctx)}</pre>

<h3>5. Domain List Generation</h3>
<p>After the answer, we ask the LLM to list 10 relevant domains for the same question.</p>
<p><strong>OpenAI domain prompt suffix:</strong></p>
<pre class="full-text" style="background:#f1f5f9;padding:0.5rem;border-radius:6px;font-size:12px">{escape(domain_prompt_openai)}</pre>
<p><strong>Gemini domain prompt suffix:</strong></p>
<pre class="full-text" style="background:#f1f5f9;padding:0.5rem;border-radius:6px;font-size:12px">{escape(domain_prompt_gemini)}</pre>

<h3>6. Visibility Checks</h3>
<table class="query-table">
<tr><th>Column</th><th>Check</th><th>How it works</th></tr>
<tr><td><strong>Brand?</strong></td><td>Brand name mentioned in answer text</td><td>Case-insensitive substring search for domain (<code>{domain}</code>) OR any brand name (<code>{', '.join(config.brand_names)}</code>)</td></tr>
<tr><td><strong>URL?</strong></td><td>Domain URL found in answer text</td><td>Extract URLs from answer using regex, check if <code>{domain}</code> (or subdomain) appears as a URL pattern</td></tr>
<tr><td><strong>Sources</strong></td><td>Top-10 recommended sources list</td><td>AI generates JSON list of 10 relevant domains for the query</td></tr>
<tr><td><strong>Rank</strong></td><td>Position in sources list</td><td>Find <code>{domain}</code> using {config.domain_match_strategy} matching. Position 1-10 or "-" if not found.</td></tr>
</table>

<h3>7. Rate Limiting & Concurrency</h3>
<p><strong>Request delay:</strong> {config.request_delay}s between API calls<br>
<strong>Query workers:</strong> {config.max_query_workers} | <strong>Provider workers/query:</strong> {config.max_provider_workers} | <strong>Prompt concurrency:</strong> {config.prompt_concurrency}</p>

</section>"""

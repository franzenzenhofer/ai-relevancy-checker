"""HTML Presentation Generator - SUPER DRY implementation.

100% REUSE of existing report components:
- generate_kpi_cards() for all KPI boxes
- generate_pie_chart(), generate_bar_chart() for visualizations
- Color constants from report_kpi.py

Structure (21 slides):
- Section 1: Intro & Key Findings (3 slides)
- Section 2: Methodology with Examples (7 slides)
- Section 3: Data/KPIs (10 slides) - PIE CHARTS BIG + CENTERED ABOVE CARDS
- Section 4: Reference (1 slide)
"""
from datetime import datetime
from typing import List, Dict
from html import escape

from .relevancy_engine import QueryResult
from .aggregator import AggregatedKPIs
from .config import config
from .report_kpi import (
    generate_kpi_cards, OPENAI_COLOR, GEMINI_COLOR, OPENAI_LIGHT, GEMINI_LIGHT,
    OPENAI_ICON, GEMINI_ICON, GREEN, RED
)
from .report_charts import (
    generate_pie_chart, generate_bar_chart, generate_long_tail_chart,
    render_chart_legend, get_chartjs_cdn
)
from .presentation_styles import get_presentation_styles
from .llm_openai import get_openai_prompt_system


class PresentationGenerator:
    """Generates HTML presentation - 100% DRY reuse of report components."""

    def __init__(self, domain: str, run_id: str = "", cli_command: str = ""):
        self.domain = domain
        self.run_id = run_id
        self.cli_command = cli_command
        self.generated_at = datetime.now()
        self.total_slides = 0

    def generate(
        self,
        openai_results: List[QueryResult],
        gemini_results: List[QueryResult],
        kpis: AggregatedKPIs,
        system_context: str
    ) -> str:
        """Generate HTML presentation - reuses ALL report components."""
        # DRY: Generate cards ONCE - same as report
        cards = generate_kpi_cards(kpis)
        o, g = kpis.openai_stats, kpis.gemini_stats
        total = o.total_queries

        openai_sorted = sorted(openai_results, key=lambda x: x.clicks, reverse=True)
        gemini_map = {r.query_id: r for r in gemini_results}

        slides = []
        n = 1

        # SECTION 1: INTRO & KEY FINDINGS
        slides.append(self._slide_title(n, total)); n += 1
        slides.append(self._slide_executive_summary(n, o, g, kpis)); n += 1
        slides.append(self._slide_objectives(n, total)); n += 1

        # SECTION 2: METHODOLOGY WITH EXAMPLES
        slides.append(self._slide_models(n)); n += 1
        slides.append(self._slide_location(n)); n += 1
        slides.append(self._slide_prompt_generation(n)); n += 1
        slides.append(self._slide_prompt_example(n, openai_sorted)); n += 1
        slides.append(self._slide_answer_domain(n)); n += 1
        slides.append(self._slide_visibility_checks(n)); n += 1
        slides.append(self._slide_check_example(n, openai_sorted, gemini_map)); n += 1

        # SECTION 3: DATA/KPIs - DRY reuse of cards + big centered charts
        slides.append(self._slide_data_quality(n, cards)); n += 1
        slides.append(self._slide_overall_presence(n, cards, kpis)); n += 1
        slides.append(self._slide_openai_presence(n, cards, o)); n += 1
        slides.append(self._slide_gemini_presence(n, cards, g)); n += 1
        slides.append(self._slide_brand_answers(n, cards, o, g, kpis)); n += 1
        slides.append(self._slide_domain_sources(n, cards, o, g, kpis)); n += 1
        slides.append(self._slide_ranking(n, cards)); n += 1
        slides.append(self._slide_api_usage(n, cards)); n += 1
        slides.append(self._slide_long_tail(n, openai_sorted, gemini_map)); n += 1
        slides.append(self._slide_comparison_bar(n, o, g)); n += 1

        # SECTION 4: REFERENCE
        slides.append(self._slide_reference(n)); n += 1

        self.total_slides = n - 1
        return self._wrap_html(slides)

    def _slide(self, num: int, title: str, content: str, section: str = "") -> str:
        """DRY slide wrapper."""
        section_html = f'<div class="slide-section-label">{section}</div>' if section else ''
        return f'''<section class="slide" id="slide-{num}">
{section_html}
<div class="slide-header"><h2>{title}</h2></div>
<div class="slide-content">{content}</div>
<div class="slide-num">{num}</div>
</section>'''

    def _big_pie(self, chart_id: str, labels: List[str], data: List[int], colors: List[str]) -> str:
        """Render a BIG CENTERED pie chart."""
        pie = generate_pie_chart(chart_id, labels, data, colors)
        return f'<div style="display:flex;justify-content:center;margin:1rem 0"><div style="width:280px;height:280px">{pie}</div></div>'

    def _two_pies(self, id1: str, labels1, data1, colors1, id2: str, labels2, data2, colors2) -> str:
        """Render two BIG CENTERED pie charts side by side."""
        pie1 = generate_pie_chart(id1, labels1, data1, colors1)
        pie2 = generate_pie_chart(id2, labels2, data2, colors2)
        return f'''<div style="display:flex;justify-content:center;gap:3rem;margin:1rem 0">
<div style="width:240px;height:240px">{pie1}</div>
<div style="width:240px;height:240px">{pie2}</div>
</div>'''

    # === SECTION 1: INTRO ===

    def _slide_title(self, num: int, total: int) -> str:
        ts = self.generated_at.strftime("%d.%m.%Y %H:%M:%S")
        brands = ", ".join(config.brand_names)
        return self._slide(num, f"AI Relevancy Report: {self.domain}", f'''
<div style="text-align:center;padding:1.5rem 0">
<p style="font-size:1.4rem;color:#64748b;margin-bottom:1.5rem">
{total} Queries · OpenAI: {config.openai_model} · Gemini: {config.gemini_model}
</p>
<p style="color:#94a3b8;margin:0.5rem 0">Run: {self.run_id} | {ts}</p>
<div style="margin-top:1.5rem;padding:1rem;background:#f0f9ff;border:2px solid #0ea5e9;border-radius:8px;text-align:left;max-width:700px;margin-left:auto;margin-right:auto">
<p style="font-weight:600;margin-bottom:0.5rem">Brand Names Tracked:</p>
<p style="color:#0369a1;font-size:1rem">{brands}</p>
</div>
</div>
''', "INTRO")

    def _slide_executive_summary(self, num: int, o, g, kpis: AggregatedKPIs) -> str:
        overall_pct = (kpis.any_visibility / o.total_queries * 100) if o.total_queries > 0 else 0
        if overall_pct >= 80:
            assessment = ("STRONG", "#22c55e", "Excellent AI visibility!")
        elif overall_pct >= 50:
            assessment = ("MODERATE", "#f59e0b", "Room for improvement.")
        else:
            assessment = ("WEAK", "#ef4444", "Significant gaps.")
        return self._slide(num, "Key Findings – Executive Summary", f'''
<div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem">
<div>
<h3 style="margin-bottom:0.75rem">📊 Overall Results</h3>
<div style="background:#f8fafc;padding:1rem;border-radius:8px;margin-bottom:0.75rem">
<div style="font-size:2.5rem;font-weight:700;color:{assessment[1]}">{overall_pct:.0f}%</div>
<div style="color:#64748b;font-size:12px">Overall AI Visibility</div>
<div style="font-weight:600;color:{assessment[1]};margin-top:0.25rem;font-size:13px">{assessment[0]}: {assessment[2]}</div>
</div>
<ul style="color:#475569;line-height:1.6;padding-left:1.5rem;font-size:13px">
<li><strong>{kpis.any_visibility}</strong> of {o.total_queries} queries show {self.domain}</li>
<li><strong>{kpis.no_visibility}</strong> queries with NO visibility</li>
</ul>
</div>
<div>
<h3 style="margin-bottom:0.75rem">🎯 Provider Comparison</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-bottom:0.5rem">
<div style="background:{OPENAI_LIGHT};padding:0.75rem;border-radius:8px;text-align:center">
<div style="font-size:1.5rem;font-weight:700;color:{OPENAI_COLOR}">{o.answer_visible_pct:.0f}%</div>
<div style="color:#64748b;font-size:11px">OpenAI Brand</div>
</div>
<div style="background:{GEMINI_LIGHT};padding:0.75rem;border-radius:8px;text-align:center">
<div style="font-size:1.5rem;font-weight:700;color:{GEMINI_COLOR}">{g.answer_visible_pct:.0f}%</div>
<div style="color:#64748b;font-size:11px">Gemini Brand</div>
</div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem">
<div style="background:{OPENAI_LIGHT};padding:0.75rem;border-radius:8px;text-align:center">
<div style="font-size:1.5rem;font-weight:700;color:{OPENAI_COLOR}">{o.top10_pct:.0f}%</div>
<div style="color:#64748b;font-size:11px">OpenAI Sources</div>
</div>
<div style="background:{GEMINI_LIGHT};padding:0.75rem;border-radius:8px;text-align:center">
<div style="font-size:1.5rem;font-weight:700;color:{GEMINI_COLOR}">{g.top10_pct:.0f}%</div>
<div style="color:#64748b;font-size:11px">Gemini Sources</div>
</div>
</div>
</div>
</div>
<div style="background:#f0f9ff;border:2px solid #0ea5e9;padding:0.75rem;border-radius:8px;margin-top:1rem;font-size:13px">
<strong>Key Insight:</strong> {self.domain} ranks <strong>#{o.avg_rank_if_present:.1f}</strong> avg in OpenAI, <strong>#{g.avg_rank_if_present:.1f}</strong> avg in Gemini when listed.
</div>
''', "KEY FINDINGS")

    def _slide_objectives(self, num: int, total: int) -> str:
        return self._slide(num, "Objective & Data Basis", f'''
<div style="max-width:800px;margin:0 auto">
<p style="font-size:1.1rem;margin-bottom:1.5rem;text-align:center">
We tested <strong>{total} user prompts</strong> (user prompts generated based on Google Search Console top queries) to measure how often <strong>{self.domain}</strong> appears in AI responses.
</p>
<div style="background:#f0fdf4;border:2px solid #22c55e;padding:1rem;border-radius:8px;margin-bottom:1rem">
<h3 style="color:#166534;margin-bottom:0.75rem;font-size:1.1rem">Two Checks Per Query:</h3>
<ol style="margin:0;padding-left:1.5rem;line-height:2;font-size:1rem">
<li><strong>Brand in Answer</strong> – Does AI mention {self.domain} or brand names in its response?</li>
<li><strong>Domain in Source List</strong> – Does AI rank {self.domain} in its top-10 sources?</li>
</ol>
</div>
<div style="display:flex;justify-content:center;gap:3rem;margin:1rem 0">
<div style="text-align:center">
<div style="font-size:1.5rem">{OPENAI_ICON}</div>
<div style="font-weight:600;font-size:14px">OpenAI</div>
<div style="color:#64748b;font-size:12px">{config.openai_model}</div>
</div>
<div style="text-align:center">
<div style="font-size:1.5rem">{GEMINI_ICON}</div>
<div style="font-weight:600;font-size:14px">Gemini</div>
<div style="color:#64748b;font-size:12px">{config.gemini_model}</div>
</div>
</div>
</div>
''', "METHODOLOGY")

    # === SECTION 2: METHODOLOGY ===

    def _slide_models(self, num: int) -> str:
        return self._slide(num, "1. Models Used", f'''
<table class="slide-table" style="max-width:800px;margin:0 auto">
<tr><th>Purpose</th><th>OpenAI Model</th><th>Gemini Model</th><th>Max Tokens</th></tr>
<tr><td>Prompt Generation</td><td>{config.openai_prompt_model}</td><td>–</td><td>8000</td></tr>
<tr><td>Answer Generation</td><td>{config.openai_model}</td><td>{config.gemini_model}</td><td>{config.max_output_tokens_answer}</td></tr>
<tr><td>Domain List</td><td>{config.openai_model}</td><td>{config.gemini_model}</td><td>{config.max_output_tokens_domains}</td></tr>
</table>
''', "METHODOLOGY")

    def _slide_location(self, num: int) -> str:
        lang = config.force_language or "en"
        city = config.user_city if lang == "de" else config.user_city_en
        country = config.user_country if lang == "de" else config.user_country_en
        location_clause = f"{city}, {country}" if city and country else (city or country)
        brands_short = ", ".join(config.brand_names[:4])
        return self._slide(num, "2. Target Domain & Location", f'''
<div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;max-width:900px;margin:0 auto">
<div style="background:#f8fafc;padding:1rem;border-radius:8px">
<h4 style="color:#64748b;margin-bottom:0.5rem;font-size:14px">Configuration</h4>
<ul style="list-style:none;padding:0;margin:0;line-height:1.8;font-size:13px">
<li><strong>Target Domain:</strong> <code>{self.domain}</code></li>
<li><strong>Brand Names:</strong> <code style="font-size:11px">{brands_short}...</code></li>
<li><strong>Force Language:</strong> <code>{lang}</code></li>
</ul>
</div>
<div style="background:#f8fafc;padding:1rem;border-radius:8px">
<h4 style="color:#64748b;margin-bottom:0.5rem;font-size:14px">Location</h4>
<ul style="list-style:none;padding:0;margin:0;line-height:1.8;font-size:13px">
<li><strong>Location (ACTUAL):</strong> <code>{location_clause}</code></li>
<li><strong>City:</strong> <code>{config.user_city}</code> / <code>{config.user_city_en}</code></li>
<li><strong>Country:</strong> <code>{config.user_country}</code> / <code>{config.user_country_en}</code></li>
</ul>
</div>
</div>
''', "METHODOLOGY")

    def _slide_prompt_generation(self, num: int) -> str:
        lang = config.force_language or "en"
        city = config.user_city if lang == "de" else config.user_city_en
        country = config.user_country if lang == "de" else config.user_country_en
        location_phrase = city.strip() or country
        location_clause = f"{city}, {country}" if city and country and city.lower() != country.lower() else location_phrase
        prompt_system = get_openai_prompt_system(location_clause, location_phrase)
        return self._slide(num, "3. Prompt Generation (UNBIASED)", f'''
<div style="max-width:900px;margin:0 auto">
<div style="background:#fef3c7;border:2px solid #f59e0b;padding:0.75rem;border-radius:8px;margin-bottom:1rem">
<p style="margin:0;font-weight:600;color:#92400e;font-size:13px">⚠️ The prompt generator does NOT know the target domain – this ensures unbiased evaluation.</p>
</div>
<div style="background:#1e293b;padding:1rem;border-radius:8px;max-height:200px;overflow-y:auto">
<p style="color:#94a3b8;margin:0 0 0.5rem 0;font-size:11px">System Prompt (excerpt):</p>
<pre style="color:#e2e8f0;margin:0;font-size:10px;white-space:pre-wrap">{escape(prompt_system[:500])}...</pre>
</div>
</div>
''', "METHODOLOGY")

    def _slide_prompt_example(self, num: int, openai_sorted: List[QueryResult]) -> str:
        example = openai_sorted[0] if openai_sorted else None
        if not example:
            return self._slide(num, "Example: GSC → Prompt Transformation", "<p>No data available</p>", "EXAMPLE")
        return self._slide(num, "Example: GSC → Prompt Transformation", f'''
<div style="max-width:900px;margin:0 auto">
<p style="font-size:13px;color:#64748b;margin-bottom:1rem">How a real GSC query becomes an AI prompt:</p>
<div style="display:grid;grid-template-columns:1fr auto 1fr;gap:1rem;align-items:center">
<div style="background:#e0f2fe;border:2px solid #0ea5e9;padding:1rem;border-radius:8px">
<div style="font-weight:600;color:#0369a1;margin-bottom:0.5rem;font-size:12px">📊 GSC Query (Original)</div>
<div style="font-size:1.1rem;font-weight:600">{escape(example.query_text)}</div>
<div style="color:#64748b;font-size:11px;margin-top:0.5rem">{example.clicks} clicks · {example.impressions} impressions</div>
</div>
<div style="font-size:2rem;color:#64748b">→</div>
<div style="background:#f0fdf4;border:2px solid #22c55e;padding:1rem;border-radius:8px">
<div style="font-weight:600;color:#166534;margin-bottom:0.5rem;font-size:12px">🤖 AI Prompt (Generated)</div>
<div style="font-size:13px;line-height:1.5">{escape(example.hypothetical_prompt[:200])}{"..." if len(example.hypothetical_prompt) > 200 else ""}</div>
</div>
</div>
<div style="background:#f8fafc;padding:0.75rem;border-radius:8px;margin-top:1rem;font-size:12px;color:#475569">
<strong>Note:</strong> AI generates a natural user question from the keyword. Location context ({config.user_city}) is included. Domain name is NOT mentioned (unbiased).
</div>
</div>
''', "EXAMPLE")

    def _slide_answer_domain(self, num: int) -> str:
        openai_domain = config.openai_domain_json_prompt[:150]
        gemini_domain = config.gemini_domain_json_prompt[:150]
        return self._slide(num, "4-5. Answer & Domain List Generation", f'''
<div style="max-width:900px;margin:0 auto">
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
<div>
<h3 style="margin-bottom:0.5rem;font-size:14px">4. Answer Generation</h3>
<div style="background:#f8fafc;padding:0.75rem;border-radius:8px;font-size:12px">
<p style="margin:0;color:#475569">"Du bist ein hilfreicher Assistent. Antworte in 1-2 kurzen Absätzen."</p>
</div>
</div>
<div>
<h3 style="margin-bottom:0.5rem;font-size:14px">5. Domain List Generation</h3>
<div style="background:#f8fafc;padding:0.75rem;border-radius:8px;font-size:12px">
<p style="margin:0;color:#475569">"After the answer, list 10 relevant domains as JSON."</p>
</div>
</div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem">
<div style="background:#1e293b;padding:0.75rem;border-radius:8px">
<p style="color:#94a3b8;margin:0 0 0.25rem 0;font-size:10px">OpenAI domain prompt:</p>
<pre style="color:#e2e8f0;margin:0;font-size:9px;white-space:pre-wrap">{escape(openai_domain)}...</pre>
</div>
<div style="background:#1e293b;padding:0.75rem;border-radius:8px">
<p style="color:#94a3b8;margin:0 0 0.25rem 0;font-size:10px">Gemini domain prompt:</p>
<pre style="color:#e2e8f0;margin:0;font-size:9px;white-space:pre-wrap">{escape(gemini_domain)}...</pre>
</div>
</div>
</div>
''', "METHODOLOGY")

    def _slide_visibility_checks(self, num: int) -> str:
        return self._slide(num, "6. Visibility Checks", f'''
<div style="max-width:800px;margin:0 auto">
<table class="slide-table">
<tr><th>Check</th><th>What it does</th></tr>
<tr><td><strong>Brand in Answer?</strong></td><td>Case-insensitive search for '{self.domain}' or brand names in response text.</td></tr>
<tr><td><strong>Domain Rank</strong></td><td>Parse JSON domain list, find position of {self.domain} (rank 1–10 or "-").</td></tr>
</table>
<div style="background:#f8fafc;padding:1rem;border-radius:8px;margin-top:1rem">
<h4 style="margin-bottom:0.5rem;font-size:13px">Rate Limiting & Concurrency</h4>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;text-align:center;font-size:12px">
<div><strong>{config.request_delay}s</strong><br><span style="color:#64748b">delay</span></div>
<div><strong>{config.max_query_workers}</strong><br><span style="color:#64748b">query workers</span></div>
<div><strong>{config.max_provider_workers}</strong><br><span style="color:#64748b">provider workers</span></div>
<div><strong>{config.prompt_concurrency}</strong><br><span style="color:#64748b">prompt concurrency</span></div>
</div>
</div>
</div>
''', "METHODOLOGY")

    def _slide_check_example(self, num: int, openai_sorted: List[QueryResult], gemini_map: Dict[int, QueryResult]) -> str:
        example_o = None
        example_g = None
        for r in openai_sorted[:30]:
            g = gemini_map.get(r.query_id)
            if r.appears_in_answer and r.rank_if_present:
                example_o = r
                example_g = g
                break
        if not example_o:
            example_o = openai_sorted[0] if openai_sorted else None
            example_g = gemini_map.get(example_o.query_id) if example_o else None

        if not example_o:
            return self._slide(num, "Example: How Visibility Check Works", "<p>No data available</p>", "EXAMPLE")

        o_brand = "✓ YES" if example_o.appears_in_answer else "✗ NO"
        o_rank = f"#{example_o.rank_if_present}" if example_o.rank_if_present else "-"
        g_brand = "✓ YES" if (example_g and example_g.appears_in_answer) else "✗ NO"
        g_rank = f"#{example_g.rank_if_present}" if (example_g and example_g.rank_if_present) else "-"

        return self._slide(num, "Example: How Visibility Check Works", f'''
<div style="max-width:900px;margin:0 auto">
<div style="background:#e0f2fe;border:2px solid #0ea5e9;padding:0.75rem;border-radius:8px;margin-bottom:1rem">
<div style="font-size:12px;color:#0369a1;margin-bottom:0.25rem">Query:</div>
<div style="font-weight:600">{escape(example_o.query_text)}</div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
<div>
<h4 style="color:{OPENAI_COLOR};margin-bottom:0.5rem;font-size:14px">{OPENAI_ICON} OpenAI Result</h4>
<table class="slide-table" style="font-size:12px">
<tr><td><strong>Brand in answer?</strong></td><td style="color:{'#22c55e' if example_o.appears_in_answer else '#ef4444'}">{o_brand}</td></tr>
<tr><td><strong>Domain rank</strong></td><td>{o_rank}</td></tr>
<tr><td><strong>Domains found</strong></td><td style="font-size:10px">{', '.join(example_o.domains_list[:3])}...</td></tr>
</table>
</div>
<div>
<h4 style="color:{GEMINI_COLOR};margin-bottom:0.5rem;font-size:14px">{GEMINI_ICON} Gemini Result</h4>
<table class="slide-table" style="font-size:12px">
<tr><td><strong>Brand in answer?</strong></td><td style="color:{'#22c55e' if (example_g and example_g.appears_in_answer) else '#ef4444'}">{g_brand}</td></tr>
<tr><td><strong>Domain rank</strong></td><td>{g_rank}</td></tr>
<tr><td><strong>Domains found</strong></td><td style="font-size:10px">{', '.join(example_g.domains_list[:3]) if example_g else 'N/A'}...</td></tr>
</table>
</div>
</div>
</div>
''', "EXAMPLE")

    # === SECTION 3: DATA/KPIs - DRY REUSE OF CARDS ===

    def _slide_data_quality(self, num: int, cards: dict) -> str:
        return self._slide(num, "KPI 0: Data Quality", f'''
<p class="slide-explanation">"Can we trust this data? API success rate for this analysis run."</p>
<div class="kpi-row" style="justify-content:center;gap:1rem;margin:1.5rem 0">
{cards['dq_both']}
{cards['dq_openai']}
{cards['dq_gemini']}
{cards['dq_missing']}
</div>
''', "DATA")

    def _slide_overall_presence(self, num: int, cards: dict, kpis: AggregatedKPIs) -> str:
        # BIG PIE CHART ABOVE, then cards below
        pie = self._big_pie("pres_pie_a", ["Present", "Not Present"],
                           [kpis.any_visibility, kpis.no_visibility], [GREEN, RED])
        return self._slide(num, "KPI A: Overall Presence", f'''
<p class="slide-explanation">"Is {self.domain} detectable ANYWHERE?"</p>
{pie}
<div class="kpi-row" style="justify-content:center;gap:1.5rem;margin-top:1rem">
{cards['a_present']}
{cards['a_not_present']}
</div>
''', "DATA")

    def _slide_openai_presence(self, num: int, cards: dict, o) -> str:
        # BIG PIE for OpenAI
        visible = o.total_visibility_count
        blind = o.total_queries - visible
        pie = self._big_pie("pres_pie_openai", ["Visible", "Blind"], [visible, blind], [OPENAI_COLOR, OPENAI_LIGHT])
        return self._slide(num, f"KPI B1: {OPENAI_ICON} OpenAI Presence", f'''
<p class="slide-explanation">"Does OpenAI know about {self.domain}?"</p>
{pie}
<div class="kpi-row" style="justify-content:center;gap:1.5rem;margin-top:1rem">
{cards['b_openai_pres']}
{cards['b_openai_blind']}
</div>
''', "DATA")

    def _slide_gemini_presence(self, num: int, cards: dict, g) -> str:
        # BIG PIE for Gemini
        visible = g.total_visibility_count
        blind = g.total_queries - visible
        pie = self._big_pie("pres_pie_gemini", ["Visible", "Blind"], [visible, blind], [GEMINI_COLOR, GEMINI_LIGHT])
        return self._slide(num, f"KPI B2: {GEMINI_ICON} Gemini Presence", f'''
<p class="slide-explanation">"Does Gemini know about {self.domain}?"</p>
{pie}
<div class="kpi-row" style="justify-content:center;gap:1.5rem;margin-top:1rem">
{cards['b_gemini_pres']}
{cards['b_gemini_blind']}
</div>
''', "DATA")

    def _slide_brand_answers(self, num: int, cards: dict, o, g, kpis: AggregatedKPIs) -> str:
        # Two pies side by side
        pies = self._two_pies(
            "pres_pie_c1", ["Mentions", "Silent"], [o.answer_visible_count, o.total_queries - o.answer_visible_count], [OPENAI_COLOR, OPENAI_LIGHT],
            "pres_pie_c2", ["Mentions", "Silent"], [g.answer_visible_count, g.total_queries - g.answer_visible_count], [GEMINI_COLOR, GEMINI_LIGHT]
        )
        return self._slide(num, "KPI C: Brand in Answers", f'''
<p class="slide-explanation">"Does AI mention your brand? This is what users SEE."</p>
{pies}
<div class="kpi-row" style="justify-content:center;gap:1rem;margin-top:1rem">
{cards['c_openai']}
{cards['c_gemini']}
</div>
<div class="kpi-row" style="justify-content:center;gap:0.5rem;margin-top:0.75rem">
{cards['c_both']}
{cards['c_neither']}
</div>
''', "DATA")

    def _slide_domain_sources(self, num: int, cards: dict, o, g, kpis: AggregatedKPIs) -> str:
        # Two pies side by side
        pies = self._two_pies(
            "pres_pie_e1", ["Ranked", "Not"], [o.top10_count, o.total_queries - o.top10_count], [OPENAI_COLOR, OPENAI_LIGHT],
            "pres_pie_e2", ["Ranked", "Not"], [g.top10_count, g.total_queries - g.top10_count], [GEMINI_COLOR, GEMINI_LIGHT]
        )
        return self._slide(num, "KPI E: Domain in Source Lists", f'''
<p class="slide-explanation">"Does AI rank {self.domain} in its top-10 sources?"</p>
{pies}
<div class="kpi-row" style="justify-content:center;gap:1rem;margin-top:1rem">
{cards['e_openai']}
{cards['e_gemini']}
</div>
<div class="kpi-row" style="justify-content:center;gap:0.5rem;margin-top:0.75rem">
{cards['e_both']}
{cards['e_neither']}
</div>
''', "DATA")

    def _slide_ranking(self, num: int, cards: dict) -> str:
        return self._slide(num, "KPI F: Ranking Position", f'''
<p class="slide-explanation">"When in top-10, what position? (#1 is best)"</p>
<div class="kpi-row" style="justify-content:center;gap:2rem;margin:2rem 0">
{cards['f_openai']}
{cards['f_gemini']}
</div>
<p style="text-align:center;font-size:12px;color:#64748b">↓ Lower is better (#1 = top authority)</p>
''', "DATA")

    def _slide_api_usage(self, num: int, cards: dict) -> str:
        return self._slide(num, "KPI G: API Usage", f'''
<p class="slide-explanation">"Token consumption for cost tracking."</p>
<div class="kpi-row" style="justify-content:center;gap:2rem;margin:2rem 0">
{cards['g_openai']}
{cards['g_gemini']}
</div>
''', "DATA")

    def _slide_long_tail(self, num: int, openai_sorted: List[QueryResult], gemini_map: Dict[int, QueryResult]) -> str:
        # OpenAI long tail
        o_clicks = [r.clicks for r in openai_sorted]
        o_answer = [r.appears_in_answer for r in openai_sorted]
        o_domain = [r.appears_in_top10 for r in openai_sorted]
        o_queries = [r.query_text for r in openai_sorted]
        o_chart = generate_long_tail_chart("pres_lt_openai", "OpenAI", o_clicks, o_answer, o_domain, o_queries)

        # Gemini long tail
        g_clicks, g_answer, g_domain, g_queries = [], [], [], []
        for r in openai_sorted:
            g = gemini_map.get(r.query_id)
            g_clicks.append(r.clicks)
            g_answer.append(g.appears_in_answer if g else False)
            g_domain.append(g.appears_in_top10 if g else False)
            g_queries.append(r.query_text)
        g_chart = generate_long_tail_chart("pres_lt_gemini", "Gemini", g_clicks, g_answer, g_domain, g_queries)

        return self._slide(num, "Long Tail Analysis", f'''
<p class="slide-explanation">"How does visibility vary across high vs low traffic queries?"</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
<div>
<h4 style="text-align:center;color:{OPENAI_COLOR};font-size:13px">{OPENAI_ICON} OpenAI</h4>
{o_chart}
</div>
<div>
<h4 style="text-align:center;color:{GEMINI_COLOR};font-size:13px">{GEMINI_ICON} Gemini</h4>
{g_chart}
</div>
</div>
{render_chart_legend()}
''', "DATA")

    def _slide_comparison_bar(self, num: int, o, g) -> str:
        # Domain Share = when AI mentions domains, what % include our target
        bar = generate_bar_chart("pres_bar_cmp", ["Brand in Answer", "Domain Share", "Domain in Top-10"], [
            {"label": "OpenAI", "data": [o.answer_visible_pct, o.target_share_when_any_pct, o.top10_pct], "backgroundColor": OPENAI_COLOR},
            {"label": "Gemini", "data": [g.answer_visible_pct, g.target_share_when_any_pct, g.top10_pct], "backgroundColor": GEMINI_COLOR}
        ])
        return self._slide(num, "Provider Comparison", f'''
<p class="slide-explanation">"Side-by-side: OpenAI vs Gemini visibility metrics."</p>
<div style="max-width:600px;margin:2rem auto">
{bar}
</div>
''', "DATA")

    # === SECTION 4: REFERENCE ===

    def _slide_reference(self, num: int) -> str:
        return self._slide(num, f"Full Report: {self.domain}", f'''
<div style="text-align:center;padding:1.5rem 0">
<p style="font-size:1.3rem;margin-bottom:1rem">AI Relevancy Report: {self.domain}</p>
<p style="color:#64748b;margin-bottom:1.5rem">Run: {self.run_id}</p>
<div style="background:#f0f9ff;border:2px solid #0ea5e9;padding:1.5rem;border-radius:8px;max-width:500px;margin:0 auto;text-align:left">
<h3 style="color:#0369a1;margin-bottom:0.75rem;font-size:14px">Full Report Contains:</h3>
<ul style="line-height:1.8;color:#475569;font-size:13px;padding-left:1.5rem">
<li>Summary KPIs with all metrics</li>
<li>Methodology – Full Transparency</li>
<li>Detailed Results for ALL queries</li>
<li>Expandable AI responses</li>
<li>Filters by visibility status</li>
</ul>
</div>
<p style="margin-top:1.5rem;color:#94a3b8;font-size:12px">
Generated: {self.generated_at.strftime("%d.%m.%Y %H:%M:%S")}
</p>
</div>
''', "REFERENCE")

    # === HTML WRAPPER ===

    def _wrap_html(self, slides: list) -> str:
        return f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Relevancy Presentation - {self.domain}</title>
{get_presentation_styles()}
{get_chartjs_cdn()}
</head>
<body>
<div class="presentation">{''.join(slides)}</div>
<nav class="slide-nav">
<button class="nav-btn" onclick="prevSlide()" id="prev-btn">← Previous</button>
<span class="nav-counter">Slide <span id="current">1</span> of {self.total_slides}</span>
<button class="nav-btn" onclick="nextSlide()" id="next-btn">Next →</button>
</nav>
<script>
let current = 1, total = {self.total_slides};
function goToSlide(n) {{
  current = Math.max(1, Math.min(n, total));
  document.getElementById('slide-' + current).scrollIntoView({{behavior:'smooth'}});
  document.getElementById('current').textContent = current;
  document.getElementById('prev-btn').disabled = current === 1;
  document.getElementById('next-btn').disabled = current === total;
}}
function nextSlide() {{ goToSlide(current + 1); }}
function prevSlide() {{ goToSlide(current - 1); }}
document.addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight' || e.key === ' ') {{ nextSlide(); e.preventDefault(); }}
  if (e.key === 'ArrowLeft') prevSlide();
  if (e.key === 'Home') goToSlide(1);
  if (e.key === 'End') goToSlide(total);
}});
document.addEventListener('DOMContentLoaded', () => {{
  document.getElementById('prev-btn').disabled = true;
}});
</script>
</body>
</html>'''

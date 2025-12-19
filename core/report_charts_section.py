"""Charts section - pie charts with KPI cards below, matching KPI hierarchy."""
from typing import List, Dict
from .aggregator import AggregatedKPIs
from .relevancy_engine import QueryResult
from .config import config
from .report_charts import (
    generate_pie_chart, generate_bar_chart, generate_long_tail_chart, render_chart_legend
)
# DRY: Import card generator and colors (cards generated ONCE, used everywhere)
from .report_kpi import (
    generate_kpi_cards,
    OPENAI_COLOR, OPENAI_LIGHT, GEMINI_COLOR, GEMINI_LIGHT,
    GREEN, YELLOW, RED, OPENAI_ICON, GEMINI_ICON
)

ICONS = f"{OPENAI_ICON}{GEMINI_ICON}"


def _pie(chart_id: str, labels: list, data: list, colors: list) -> str:
    """DRY helper for pie chart."""
    return generate_pie_chart(chart_id, labels, data, colors)


def _viz_card(pie_html: str, kpi_html: str) -> str:
    """DRY helper: pie chart on top, KPI card below."""
    return f'''<div class="viz-card">
<div class="viz-pie">{pie_html}</div>
<div class="viz-kpi">{kpi_html}</div>
</div>'''


def render_charts_section(
    kpis: AggregatedKPIs,
    openai_sorted: List[QueryResult],
    gemini_map: Dict[int, QueryResult],
    cards: dict = None,
) -> str:
    """Render visualizations: pie chart + KPI card below, following KPI hierarchy.

    DRY: Uses cards dict from generate_kpi_cards() - same cards as KPI section.
    """
    # DRY: Generate cards ONCE if not provided (or reuse from KPI section)
    if cards is None:
        cards = generate_kpi_cards(kpis)

    o, g = kpis.openai_stats, kpis.gemini_stats

    # Long tail charts
    long_tail_oa = _render_long_tail_chart("lt_openai", "OpenAI", openai_sorted, None)
    long_tail_ga = _render_long_tail_chart("lt_gemini", "Gemini", openai_sorted, gemini_map)
    legend = render_chart_legend()

    # Bar chart - metrics matching sections C, D, E
    # Domain Share = when AI mentions domains, what % include our target (NOT any_domain_pct)
    bar = generate_bar_chart("bar1", ["Brand in Answer", "Domain Share", "Domain in Top-10"], [
        {"label": "OpenAI", "data": [o.answer_visible_pct, o.target_share_when_any_pct, o.top10_pct], "backgroundColor": OPENAI_COLOR},
        {"label": "Gemini", "data": [g.answer_visible_pct, g.target_share_when_any_pct, g.top10_pct], "backgroundColor": GEMINI_COLOR}
    ])

    return f"""
<section class="section"><h2>Visualizations</h2>
<style>
.viz-section {{ margin-bottom: 1.5rem; }}
.viz-section h4 {{ color: #1e293b; margin: 0 0 0.75rem; font-size: 1rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }}
.viz-row {{ display: flex; flex-wrap: wrap; gap: 1.5rem; justify-content: center; }}
.viz-card {{ display: flex; flex-direction: column; align-items: center; text-align: center; }}
.viz-pie {{ margin-bottom: 1rem; display: flex; justify-content: center; }}
.viz-kpi {{ display: flex; justify-content: center; }}
</style>

<div class="viz-section">
<h4>A. Overall Presence</h4>
<div class="viz-row">
{_viz_card(
    _pie("pie_a1", ["Present", "Not Present"], [kpis.any_visibility, kpis.no_visibility], [GREEN, RED]),
    cards['a_present']
)}
</div>
</div>

<div class="viz-section">
<h4>B. Provider Presence</h4>
<div class="viz-row">
{_viz_card(
    _pie("pie_b1", ["Present", "Blind"], [o.total_visibility_count, o.total_queries - o.total_visibility_count], [OPENAI_COLOR, OPENAI_LIGHT]),
    cards['b_openai_pres']
)}
{_viz_card(
    _pie("pie_b2", ["Present", "Blind"], [g.total_visibility_count, g.total_queries - g.total_visibility_count], [GEMINI_COLOR, GEMINI_LIGHT]),
    cards['b_gemini_pres']
)}
</div>
</div>

<div class="viz-section">
<h4>C. Brand in Answers</h4>
<div class="viz-row">
{_viz_card(
    _pie("pie_c1", ["Mentions", "No"], [o.answer_visible_count, o.total_queries - o.answer_visible_count], [OPENAI_COLOR, OPENAI_LIGHT]),
    cards['c_openai']
)}
{_viz_card(
    _pie("pie_c2", ["Mentions", "No"], [g.answer_visible_count, g.total_queries - g.answer_visible_count], [GEMINI_COLOR, GEMINI_LIGHT]),
    cards['c_gemini']
)}
</div>
</div>

<div class="viz-section">
<h4>D. Domain Mentions in Answers</h4>
<div class="viz-row">
{_viz_card(
    _pie("pie_d1", ["Mentions", "No"], [o.answers_with_any_domain, o.total_queries - o.answers_with_any_domain], [OPENAI_COLOR, OPENAI_LIGHT]),
    cards['d_openai_dom']
)}
{_viz_card(
    _pie("pie_d2", ["Mentions", "No"], [g.answers_with_any_domain, g.total_queries - g.answers_with_any_domain], [GEMINI_COLOR, GEMINI_LIGHT]),
    cards['d_gemini_dom']
)}
{_viz_card(
    _pie("pie_d3", ["Target", "Other"], [o.answers_with_target_when_any, max(o.answers_with_any_domain - o.answers_with_target_when_any, 0)], [OPENAI_COLOR, OPENAI_LIGHT]),
    cards['d_openai_share']
)}
{_viz_card(
    _pie("pie_d4", ["Target", "Other"], [g.answers_with_target_when_any, max(g.answers_with_any_domain - g.answers_with_target_when_any, 0)], [GEMINI_COLOR, GEMINI_LIGHT]),
    cards['d_gemini_share']
)}
</div>
</div>

<div class="viz-section">
<h4>E. Domain in Source Lists</h4>
<div class="viz-row">
{_viz_card(
    _pie("pie_e1", ["Top-10", "No"], [o.top10_count, o.total_queries - o.top10_count], [OPENAI_COLOR, OPENAI_LIGHT]),
    cards['e_openai']
)}
{_viz_card(
    _pie("pie_e2", ["Top-10", "No"], [g.top10_count, g.total_queries - g.top10_count], [GEMINI_COLOR, GEMINI_LIGHT]),
    cards['e_gemini']
)}
</div>
</div>

<div class="viz-section">
<h4>Comparison</h4>
<div class="viz-row">
<div class="viz-card" style="width:100%;max-width:500px"><div class="chart-title">{ICONS}Visibility Comparison (%)</div>{bar}</div>
</div>
</div>

<div class="long-tail-section">
<h3>Long Tail Clicks & Visibility</h3>
<p class="chart-help">Hover over dots to see the query text. X-axis = query rank by clicks (1 = highest clicks).</p>
<div class="chart-container-full"><div class="chart-title" style="color:{OPENAI_COLOR}">{OPENAI_ICON}OpenAI - Long Tail</div>{long_tail_oa}</div>
<div class="chart-container-full"><div class="chart-title" style="color:{GEMINI_COLOR}">{GEMINI_ICON}Gemini - Long Tail</div>{long_tail_ga}</div>
{legend}
</div>
</section>"""


def _render_long_tail_chart(chart_id: str, title: str, openai_sorted: List[QueryResult], gemini_map):
    clicks = [r.clicks for r in openai_sorted]
    query_texts = [r.query_text for r in openai_sorted]
    if "OpenAI" in title:
        answer_flags = [r.appears_in_answer for r in openai_sorted]
        domain_flags = [r.appears_in_top10 for r in openai_sorted]
    else:
        answer_flags = []
        domain_flags = []
        for r in openai_sorted:
            g = gemini_map.get(r.query_id) if gemini_map else None
            answer_flags.append(bool(g and g.appears_in_answer))
            domain_flags.append(bool(g and g.appears_in_top10))
    return generate_long_tail_chart(chart_id, title, clicks, answer_flags, domain_flags, query_texts)

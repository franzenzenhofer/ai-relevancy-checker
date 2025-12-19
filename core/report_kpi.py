"""KPI summary section for HTML report - restructured with correct terminology."""
from datetime import datetime, timedelta
from .aggregator import AggregatedKPIs
from .config import config

OPENAI_COLOR = "#10a37f"
OPENAI_LIGHT = "#10a37f40"
GEMINI_COLOR = "#4285f4"
GEMINI_LIGHT = "#4285f440"
GREEN = "#22c55e"
YELLOW = "#f59e0b"
RED = "#ef4444"
RED_COLOR = "#dc2626"
RED_BG = "#fee2e2"
RED_BORDER = "#ef4444"
GREEN_COLOR = "#166534"
GREEN_BG = "#dcfce7"
GREEN_BORDER = "#22c55e"
YELLOW_COLOR = "#92400e"
YELLOW_BG = "#fef3c7"
YELLOW_BORDER = "#f59e0b"
GRAY_COLOR = "#94a3b8"
GRAY_BG = "#f1f5f9"
GRAY_BORDER = "#cbd5e1"

OPENAI_ICON = '<img src="https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg" alt="OpenAI" style="width:18px;height:18px;vertical-align:middle">'
GEMINI_ICON = '<img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" alt="Gemini" style="width:18px;height:18px;vertical-align:middle">'


def _kpi_box(value, ratio_text: str, label: str, detail: str, bg: str, border: str, color: str, icon: str = "") -> str:
    """Render a KPI box with icon ABOVE the value, all centered."""
    icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ''
    return f'''<div class="kpi-box" style="background:{bg};border-color:{border}">
{icon_html}
<div class="kpi-value" style="color:{color}">{value}</div>
<div class="kpi-ratio" style="color:{color}">{ratio_text}</div>
<div class="kpi-label">{label}</div>
<div class="kpi-detail">{detail}</div>
</div>'''


def _small_kpi_box(value, ratio_text: str, label: str, bg: str, border: str, color: str, icon: str = "", direction: str = "") -> str:
    """Render a smaller KPI box for comparison metrics.

    direction: "up" for ↑ Higher is better, "down" for ↓ Lower is better, "" for none
    """
    icon_html = f'<span style="margin-right:4px">{icon}</span>' if icon else ''
    direction_html = ""
    if direction == "up":
        direction_html = '<div style="font-size:8px;margin-top:2px">↑ Higher is better</div>'
    elif direction == "down":
        direction_html = '<div style="font-size:8px;margin-top:2px">↓ Lower is better</div>'
    return f'''<div class="kpi-box" style="background:{bg};border-color:{border};min-width:100px;padding:0.4rem 0.6rem">
<div class="kpi-value" style="color:{color};font-size:1.4rem">{icon_html}{value}</div>
<div class="kpi-ratio" style="color:{color};font-size:0.75rem">{ratio_text}</div>
<div class="kpi-label" style="font-size:9px">{label}</div>
{direction_html}
</div>'''


def _ratio_text(count: int, total: int) -> str:
    pct = (count / total * 100) if total else 0
    return f'{count} of {total} · {pct:.0f}%'


def _comparison_ratio(count: int, queries_with_both: int) -> str:
    """Ratio text for comparison KPIs (only counts queries where both providers have data)."""
    pct = (count / queries_with_both * 100) if queries_with_both else 0
    return f'{count} of {queries_with_both} · {pct:.0f}%'


def _blind_box(count: int, total: int, label: str, detail: str, icon: str) -> str:
    """Render a BLIND box with conditional coloring.

    - 0 count: GREEN (no blindness is perfect)
    - Below 10%: YELLOW/ORANGE (low failure rate, minor concern)
    - 10% or above: RED (significant issue)
    """
    pct = (count / total * 100) if total else 0
    ratio = _ratio_text(count, total)

    if count == 0:
        bg, border, color = GREEN_BG, GREEN_BORDER, GREEN_COLOR
        detail_text = f"{detail}.<br>✓ Perfect - detected everywhere!"
    elif pct < 10:
        bg, border, color = YELLOW_BG, YELLOW_BORDER, YELLOW_COLOR
        detail_text = f"{detail} in {count} queries.<br>Low rate - minor concern."
    else:
        bg, border, color = RED_BG, RED_BORDER, RED_COLOR
        detail_text = f"{detail} in {count} queries.<br>↓ Lower is better."

    return _kpi_box(count, ratio, label, detail_text, bg, border, color, icon)


def generate_kpi_cards(kpis: AggregatedKPIs) -> dict:
    """Generate all KPI cards ONCE - single source of truth for DRY reuse."""
    o, g = kpis.openai_stats, kpis.gemini_stats
    domain = config.domain
    total = o.total_queries
    both = kpis.queries_with_both_providers

    # Helper for 3-tier color on "bad" metrics
    def _neither_colors(count, base):
        pct = (count / base * 100) if base else 0
        if count == 0:
            return GREEN_BG, GREEN_BORDER, GREEN_COLOR
        elif pct < 10:
            return YELLOW_BG, YELLOW_BORDER, YELLOW_COLOR
        return RED_BG, RED_BORDER, RED_COLOR

    cards = {}

    # 0. DATA QUALITY
    api_success = o.total_queries + g.total_queries
    api_total = total * 2
    cards['dq_both'] = _kpi_box(
        f"{(api_success / api_total * 100) if api_total else 0:.0f}%",
        f"{api_success}/{api_total} successful", "BOTH SUCCESS",
        f"Combined API success rate.<br>{'✓ Full data - all queries completed!' if api_success == api_total else '↑ Higher is better.'}",
        GREEN_BG if api_success == api_total else YELLOW_BG,
        GREEN_BORDER if api_success == api_total else YELLOW_BORDER,
        GREEN_COLOR if api_success == api_total else YELLOW_COLOR,
        f"{OPENAI_ICON}{GEMINI_ICON}")
    cards['dq_openai'] = _kpi_box(
        o.total_queries, f"{o.total_queries}/{total} · 100%", "OpenAI SUCCESS",
        f"All {o.total_queries} OpenAI queries completed.<br>✓ No failures.",
        GREEN_BG, GREEN_BORDER, GREEN_COLOR, OPENAI_ICON)
    cards['dq_gemini'] = _kpi_box(
        g.total_queries, f"{g.total_queries}/{total} · {(g.total_queries/total*100) if total else 0:.0f}%", "Gemini SUCCESS",
        f"{g.total_queries} of {total} Gemini queries completed.<br>{'✓ No failures.' if g.total_queries == total else f'⚠ {total - g.total_queries} failed.'}",
        GREEN_BG if g.total_queries == total else YELLOW_BG,
        GREEN_BORDER if g.total_queries == total else YELLOW_BORDER,
        GREEN_COLOR if g.total_queries == total else YELLOW_COLOR, GEMINI_ICON)
    missing = kpis.openai_failed + kpis.gemini_failed
    cards['dq_missing'] = _kpi_box(
        missing, f"{missing}/{api_total}", "TOTAL MISSING",
        f"Missing API responses.<br>{'✓ None missing - full data!' if missing == 0 else '↓ Lower is better.'}",
        GREEN_BG if missing == 0 else RED_BG,
        GREEN_BORDER if missing == 0 else RED_BORDER,
        GREEN_COLOR if missing == 0 else RED_COLOR,
        f"{OPENAI_ICON}{GEMINI_ICON}")

    # A. OVERALL PRESENCE
    cards['a_present'] = _kpi_box(
        kpis.any_visibility, _ratio_text(kpis.any_visibility, total), "PRESENT (any AI)",
        f"{domain} detected in {kpis.any_visibility} queries.<br>↑ Higher is better.",
        GREEN_BG, GREEN_BORDER, GREEN_COLOR, f"{OPENAI_ICON}{GEMINI_ICON}")
    no_vis_bg, no_vis_border, no_vis_color = _neither_colors(kpis.no_visibility, total)
    cards['a_not_present'] = _kpi_box(
        kpis.no_visibility, _ratio_text(kpis.no_visibility, total), "NOT PRESENT",
        f"{domain} undetectable in {kpis.no_visibility} queries.<br>{'✓ Perfect - detected everywhere!' if kpis.no_visibility == 0 else '↓ Lower is better.'}",
        no_vis_bg, no_vis_border, no_vis_color, f"{OPENAI_ICON}{GEMINI_ICON}")

    # B. PROVIDER PRESENCE
    cards['b_openai_pres'] = _kpi_box(
        o.total_visibility_count, _ratio_text(o.total_visibility_count, o.total_queries), "OpenAI PRESENCE",
        f"OpenAI detects {domain} in {o.total_visibility_count} queries.<br>(brand mentioned OR domain ranked)<br>↑ Higher is better.",
        f"{OPENAI_COLOR}15", OPENAI_COLOR, OPENAI_COLOR, OPENAI_ICON)
    cards['b_openai_blind'] = _blind_box(
        o.total_queries - o.total_visibility_count, o.total_queries, "OpenAI BLIND",
        f"OpenAI doesn't detect {domain}", OPENAI_ICON)
    cards['b_gemini_pres'] = _kpi_box(
        g.total_visibility_count, _ratio_text(g.total_visibility_count, g.total_queries), "Gemini PRESENCE",
        f"Gemini detects {domain} in {g.total_visibility_count} queries.<br>(brand mentioned OR domain ranked)<br>↑ Higher is better.",
        f"{GEMINI_COLOR}15", GEMINI_COLOR, GEMINI_COLOR, GEMINI_ICON)
    cards['b_gemini_blind'] = _blind_box(
        g.total_queries - g.total_visibility_count, g.total_queries, "Gemini BLIND",
        f"Gemini doesn't detect {domain}", GEMINI_ICON)

    # C. BRAND IN ANSWERS
    cards['c_openai'] = _kpi_box(
        o.answer_visible_count, _ratio_text(o.answer_visible_count, o.total_queries), "OpenAI mentions brand",
        f"Your brand appears in {o.answer_visible_count} OpenAI answers.<br>↑ Higher is better.",
        f"{OPENAI_COLOR}15", OPENAI_COLOR, OPENAI_COLOR, OPENAI_ICON)
    cards['c_gemini'] = _kpi_box(
        g.answer_visible_count, _ratio_text(g.answer_visible_count, g.total_queries), "Gemini mentions brand",
        f"Your brand appears in {g.answer_visible_count} Gemini answers.<br>↑ Higher is better.",
        f"{GEMINI_COLOR}15", GEMINI_COLOR, GEMINI_COLOR, GEMINI_ICON)
    cards['c_both'] = _small_kpi_box(
        kpis.both_answer, _comparison_ratio(kpis.both_answer, both), "BOTH MENTION",
        GREEN_BG, GREEN_BORDER, GREEN_COLOR, f"{OPENAI_ICON}{GEMINI_ICON}", "up")
    c_neither_bg, c_neither_border, c_neither_color = _neither_colors(kpis.neither_answer, both)
    cards['c_neither'] = _small_kpi_box(
        kpis.neither_answer, _comparison_ratio(kpis.neither_answer, both), "NEITHER",
        c_neither_bg, c_neither_border, c_neither_color, f"{OPENAI_ICON}{GEMINI_ICON}", "down")

    # D. DOMAIN MENTIONS IN ANSWERS
    cards['d_openai_dom'] = _kpi_box(
        o.answers_with_any_domain, _ratio_text(o.answers_with_any_domain, o.total_queries), "OpenAI mentions domains",
        f"OpenAI mentions some domain in {o.answers_with_any_domain} answers.<br>Context: How often AI mentions domains.",
        f"{OPENAI_COLOR}15", OPENAI_COLOR, OPENAI_COLOR, OPENAI_ICON)
    cards['d_gemini_dom'] = _kpi_box(
        g.answers_with_any_domain, _ratio_text(g.answers_with_any_domain, g.total_queries), "Gemini mentions domains",
        f"Gemini mentions some domain in {g.answers_with_any_domain} answers.<br>Context: How often AI mentions domains.",
        f"{GEMINI_COLOR}15", GEMINI_COLOR, GEMINI_COLOR, GEMINI_ICON)
    cards['d_both'] = _small_kpi_box(
        kpis.both_any_domain, _comparison_ratio(kpis.both_any_domain, both), "BOTH MENTION",
        GREEN_BG, GREEN_BORDER, GREEN_COLOR, f"{OPENAI_ICON}{GEMINI_ICON}", "up")
    d_neither_bg, d_neither_border, d_neither_color = _neither_colors(kpis.neither_any_domain, both)
    cards['d_neither'] = _small_kpi_box(
        kpis.neither_any_domain, _comparison_ratio(kpis.neither_any_domain, both), "NEITHER",
        d_neither_bg, d_neither_border, d_neither_color, f"{OPENAI_ICON}{GEMINI_ICON}", "down")
    cards['d_openai_share'] = _kpi_box(
        o.answers_with_target_when_any, f"{o.answers_with_target_when_any}/{o.answers_with_any_domain} · {o.target_share_when_any_pct:.0f}%",
        "OpenAI: DOMAIN SHARE", f"When OpenAI mentions domains, {o.target_share_when_any_pct:.0f}% include {domain}.<br>↑ Higher is better.",
        GREEN_BG if o.target_share_when_any_pct >= 50 else f"{OPENAI_COLOR}15",
        GREEN_BORDER if o.target_share_when_any_pct >= 50 else OPENAI_COLOR,
        GREEN_COLOR if o.target_share_when_any_pct >= 50 else OPENAI_COLOR, OPENAI_ICON)
    cards['d_gemini_share'] = _kpi_box(
        g.answers_with_target_when_any, f"{g.answers_with_target_when_any}/{g.answers_with_any_domain} · {g.target_share_when_any_pct:.0f}%",
        "Gemini: DOMAIN SHARE", f"When Gemini mentions domains, {g.target_share_when_any_pct:.0f}% include {domain}.<br>↑ Higher is better.",
        GREEN_BG if g.target_share_when_any_pct >= 50 else f"{GEMINI_COLOR}15",
        GREEN_BORDER if g.target_share_when_any_pct >= 50 else GEMINI_COLOR,
        GREEN_COLOR if g.target_share_when_any_pct >= 50 else GEMINI_COLOR, GEMINI_ICON)

    # E. DOMAIN IN SOURCE LISTS
    cards['e_openai'] = _kpi_box(
        o.top10_count, _ratio_text(o.top10_count, o.total_queries), "OpenAI ranks domain",
        f"{domain} in OpenAI's top-10 list for {o.top10_count} queries.<br>↑ Higher is better.",
        f"{OPENAI_COLOR}15", OPENAI_COLOR, OPENAI_COLOR, OPENAI_ICON)
    cards['e_gemini'] = _kpi_box(
        g.top10_count, _ratio_text(g.top10_count, g.total_queries), "Gemini ranks domain",
        f"{domain} in Gemini's top-10 list for {g.top10_count} queries.<br>↑ Higher is better.",
        f"{GEMINI_COLOR}15", GEMINI_COLOR, GEMINI_COLOR, GEMINI_ICON)
    cards['e_both'] = _small_kpi_box(
        kpis.both_ranked, _comparison_ratio(kpis.both_ranked, both), "BOTH RANK",
        GREEN_BG, GREEN_BORDER, GREEN_COLOR, f"{OPENAI_ICON}{GEMINI_ICON}", "up")
    e_neither_bg, e_neither_border, e_neither_color = _neither_colors(kpis.neither_ranked, both)
    cards['e_neither'] = _small_kpi_box(
        kpis.neither_ranked, _comparison_ratio(kpis.neither_ranked, both), "NEITHER",
        e_neither_bg, e_neither_border, e_neither_color, f"{OPENAI_ICON}{GEMINI_ICON}", "down")

    # F. RANKING POSITION
    cards['f_openai'] = _kpi_box(
        f"#{o.avg_rank_if_present:.1f}", f"Based on {o.rank_count} ranked queries", "OpenAI Avg Position",
        f"Average position when ranked by OpenAI.<br>↓ Lower is better (#1 = top authority).",
        f"{OPENAI_COLOR}15", OPENAI_COLOR, OPENAI_COLOR, OPENAI_ICON)
    cards['f_gemini'] = _kpi_box(
        f"#{g.avg_rank_if_present:.1f}", f"Based on {g.rank_count} ranked queries", "Gemini Avg Position",
        f"Average position when ranked by Gemini.<br>↓ Lower is better (#1 = top authority).",
        f"{GEMINI_COLOR}15", GEMINI_COLOR, GEMINI_COLOR, GEMINI_ICON)

    # G. API USAGE
    cards['g_openai'] = _kpi_box(
        f"{o.total_tokens:,}", f"{o.avg_tokens_per_query:.0f} avg/query", "OpenAI Tokens",
        f"Total tokens: {o.total_tokens:,}<br>{o.total_queries * 2} successful API calls.",
        f"{OPENAI_COLOR}15", OPENAI_COLOR, OPENAI_COLOR, OPENAI_ICON)
    cards['g_gemini'] = _kpi_box(
        f"{g.total_tokens:,}", f"{g.avg_tokens_per_query:.0f} avg/query", "Gemini Tokens",
        f"Total tokens: {g.total_tokens:,}<br>{g.total_queries * 2} successful API calls.",
        f"{GEMINI_COLOR}15", GEMINI_COLOR, GEMINI_COLOR, GEMINI_ICON)

    return cards


def render_kpi_summary(kpis: AggregatedKPIs, cards: dict = None) -> str:
    """Render KPIs with correct terminology and logical hierarchy."""
    if cards is None:
        cards = generate_kpi_cards(kpis)

    o, g = kpis.openai_stats, kpis.gemini_stats
    domain = config.domain
    total = o.total_queries
    both = kpis.queries_with_both_providers

    end_date = datetime.now()
    start_date = end_date - timedelta(days=config.gsc_days)
    gsc_range = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
    report_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    return f"""
<div class="intro-box">
<h3>AI Visibility Report</h3>
<p><strong>Domain:</strong> <span style="color:#166534;font-size:1.1em">{domain}</span></p>
<p><strong>Brand Names Tracked:</strong> {", ".join(config.brand_names)}</p>
<p>We tested <strong>{total} prompts</strong> (user prompts generated based on Google Search Console top queries) to measure how often <strong>{domain}</strong> appears in AI responses.</p>
<p><strong>Three checks per prompt:</strong></p>
<ol>
<li><strong>Brand?</strong> Does AI mention any brand name ({", ".join(config.brand_names)}) in its answer text? <em>(Text mentions)</em></li>
<li><strong>URL?</strong> Does AI include <code>{domain}</code> as a URL/link in its answer? <em>(Direct domain reference)</em></li>
<li><strong>Sources + Rank:</strong> Does AI list <code>{domain}</code> in its top-10 recommended sources? <em>(AI's internal recommendations)</em></li>
</ol>
<p><strong>AI Models:</strong> {OPENAI_ICON} OpenAI {config.openai_model} | {GEMINI_ICON} Gemini {config.gemini_model}</p>
<p><strong>Report:</strong> {report_time} | <strong>GSC Range:</strong> {gsc_range} ({config.gsc_days} days)</p>
</div>

<div class="finding-section">
<h4>0. DATA QUALITY</h4>
<p class="finding-explanation">Can we trust this data? API success rate for this analysis run.</p>
<div class="kpi-row">
{cards['dq_both']}
{cards['dq_openai']}
{cards['dq_gemini']}
{cards['dq_missing']}
</div>
</div>

<h3>Results</h3>

<div class="finding-section">
<h4>A. OVERALL PRESENCE</h4>
<p class="finding-explanation">Is {domain} detectable ANYWHERE? (Brand in answer OR domain in source list, in EITHER AI)</p>
<div class="kpi-row">
{cards['a_present']}
{cards['a_not_present']}
</div>
</div>

<div class="finding-section">
<h4>B. PROVIDER PRESENCE</h4>
<p class="finding-explanation">Which AI knows about {domain}? (Brand in answer OR domain in source list)</p>

<p style="font-weight:600;margin:0.75rem 0 0.5rem 0;color:{OPENAI_COLOR}">B1. OpenAI Presence:</p>
<div class="kpi-row">
{cards['b_openai_pres']}
{cards['b_openai_blind']}
</div>

<p style="font-weight:600;margin:0.75rem 0 0.5rem 0;color:{GEMINI_COLOR}">B2. Gemini Presence:</p>
<div class="kpi-row">
{cards['b_gemini_pres']}
{cards['b_gemini_blind']}
</div>
</div>

<div class="finding-section">
<h4>C. BRAND IN ANSWERS</h4>
<p class="finding-explanation">Does AI mention your brand in its written response? <strong>This is what users actually SEE.</strong></p>
<p style="font-size:11px;color:{GRAY_COLOR};margin-bottom:0.5rem">Checks for: {", ".join(config.brand_names)}</p>
<div class="kpi-row">
{cards['c_openai']}
{cards['c_gemini']}
</div>
<p style="font-size:11px;color:{GRAY_COLOR};margin:0.5rem 0 0.25rem 0">Comparison ({both} queries where both AIs returned data):</p>
<div class="kpi-row" style="gap:0.5rem">
{cards['c_both']}
{cards['c_neither']}
</div>
</div>

<div class="finding-section">
<h4>D. DOMAIN MENTIONS IN ANSWERS</h4>
<p class="finding-explanation">Does AI mention ANY domain in its answer text? And when it does, does it mention {domain}?</p>

<p style="font-weight:600;margin:0.5rem 0">Part 1: Does AI mention any domain at all?</p>
<div class="kpi-row">
{cards['d_openai_dom']}
{cards['d_gemini_dom']}
</div>
<p style="font-size:11px;color:{GRAY_COLOR};margin:0.5rem 0 0.25rem 0">Comparison ({both} queries where both AIs returned data):</p>
<div class="kpi-row" style="gap:0.5rem">
{cards['d_both']}
{cards['d_neither']}
</div>

<p style="font-weight:600;margin:1rem 0 0.5rem 0">Part 2: When AI mentions domains, is {domain} included?</p>
<div class="kpi-row">
{cards['d_openai_share']}
{cards['d_gemini_share']}
</div>
</div>

<div class="finding-section">
<h4>E. DOMAIN IN SOURCE LISTS</h4>
<p class="finding-explanation">Does AI rank {domain} in its "top 10 relevant sources"? <strong>This is what AI THINKS internally</strong> (users don't see this list).</p>
<div class="kpi-row">
{cards['e_openai']}
{cards['e_gemini']}
</div>
<p style="font-size:11px;color:{GRAY_COLOR};margin:0.5rem 0 0.25rem 0">Comparison ({both} queries where both AIs returned data):</p>
<div class="kpi-row" style="gap:0.5rem">
{cards['e_both']}
{cards['e_neither']}
</div>
</div>

<div class="finding-section">
<h4>F. RANKING POSITION</h4>
<p class="finding-explanation">When {domain} IS in the top-10 list, what position? (#1 is best, #10 is worst)</p>
<div class="kpi-row">
{cards['f_openai']}
{cards['f_gemini']}
</div>
</div>

<div class="finding-section">
<h4>G. API USAGE</h4>
<p class="finding-explanation">Token consumption for cost tracking. Each query = 2 API calls (answer + domain list).</p>
<div class="kpi-row">
{cards['g_openai']}
{cards['g_gemini']}
</div>
</div>
"""

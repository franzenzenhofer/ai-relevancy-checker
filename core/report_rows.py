"""Query row rendering for HTML report."""
from html import escape
from .config import config
from .relevancy_engine import QueryResult
from .report_table import (
    render_domain_list, render_rank_badge, render_visibility,
    render_collapsible_text, is_error_response
)


def render_query_row(num: int, o: QueryResult, g, domain: str, timestamp: str) -> str:
    """Render a single query row with collapsible text."""
    o_err = is_error_response(o.answer_text)
    g_err = g and is_error_response(g.answer_text)
    no_data_text = config.report_text.get("table_headers", {}).get("no_data", "No data")

    # Unique IDs for collapsible elements
    prompt_id = f"prompt_{num}"
    o_answer_id = f"o_answer_{num}"
    g_answer_id = f"g_answer_{num}"

    # Check any visibility (answer OR domain rank in either AI)
    o_any = o.appears_in_answer or (o.rank_if_present and o.rank_if_present > 0)
    g_any = g and (g.appears_in_answer or (g.rank_if_present and g.rank_if_present > 0))
    any_vis = o_any or g_any
    any_vis_html = '<span class="visible-yes" style="font-weight:800">✓ YES</span>' if any_vis else '<span class="visible-no" style="font-weight:800">✗ NO</span>'

    # Data attributes for filtering
    o_dom_in_ans = getattr(o, 'target_domain_in_answer', False)
    g_dom_in_ans = getattr(g, 'target_domain_in_answer', False) if g else False
    return f"""<tr data-any-vis="{str(bool(any_vis)).lower()}" data-oa-answer="{str(bool(o.appears_in_answer)).lower()}"
data-oa-domain-in-answer="{str(bool(o_dom_in_ans)).lower()}"
data-oa-rank="{o.rank_if_present or 0}" data-ga-answer="{str(bool(g.appears_in_answer if g else False)).lower()}"
data-ga-domain-in-answer="{str(bool(g_dom_in_ans)).lower()}"
data-ga-rank="{g.rank_if_present if g and g.rank_if_present else 0}">
<td><span class="query-num">Q{num}</span></td>
<td><strong>{escape(o.query_text)}</strong></td>
<td>{o.clicks:,}</td>
<td>{any_vis_html}</td>
<td>{render_collapsible_text(o.hypothetical_prompt, prompt_id, highlight=False)}</td>
<td>{render_collapsible_text(o.answer_text, o_answer_id)}</td>
<td>{render_visibility(o.appears_in_answer, o_err)}</td>
<td>{render_visibility(o_dom_in_ans, o_err)}</td>
<td>{render_domain_list(o.domains_list, domain)}</td>
<td>{render_rank_badge(o.rank_if_present)}</td>
<td>{render_collapsible_text(g.answer_text, g_answer_id) if g else f'<span class="error-text">{no_data_text}</span>'}</td>
<td>{render_visibility(g.appears_in_answer, g_err) if g else '-'}</td>
<td>{render_visibility(g_dom_in_ans, g_err) if g else '-'}</td>
<td>{render_domain_list(g.domains_list, domain) if g else '-'}</td>
<td>{render_rank_badge(g.rank_if_present) if g else '-'}</td>
<td class="timestamp">{timestamp}</td>
</tr>"""


OPENAI_ICON = '<img src="https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg" alt="" style="width:14px;height:14px;vertical-align:middle;margin-right:4px">'
GEMINI_ICON = '<img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" alt="" style="width:14px;height:14px;vertical-align:middle;margin-right:4px">'


def render_table_header() -> str:
    """Render the table header with color-coded provider columns and favicons."""
    rt = config.report_text
    headers = rt.get("table_headers", {})
    th_query = headers.get("query", "Query")
    th_clicks = headers.get("gsc_clicks", "GSC Clicks")
    th_any = headers.get("any_visibility", "Any Visibility?")
    th_prompt = headers.get("prompt", "Prompt")
    th_checked = headers.get("checked", "Checked")
    # Clear column names: Brand in text, URL in text, Source list + rank
    return f"""<thead><tr>
<th>#</th><th>{th_query}</th><th>{th_clicks}</th><th style="background:#fef3c7;color:#92400e">{th_any}</th><th>{th_prompt}</th>
<th style="background:#10a37f20;color:#10a37f">{OPENAI_ICON}Answer</th>
<th style="background:#10a37f20;color:#10a37f" title="Brand name mentioned in answer text">{OPENAI_ICON}Brand?</th>
<th style="background:#10a37f20;color:#10a37f" title="Domain URL found in answer text">{OPENAI_ICON}URL?</th>
<th style="background:#10a37f20;color:#10a37f" title="Top-10 recommended sources">{OPENAI_ICON}Sources</th>
<th style="background:#10a37f20;color:#10a37f" title="Position in source list">{OPENAI_ICON}Rank</th>
<th style="background:#4285f420;color:#4285f4">{GEMINI_ICON}Answer</th>
<th style="background:#4285f420;color:#4285f4" title="Brand name mentioned in answer text">{GEMINI_ICON}Brand?</th>
<th style="background:#4285f420;color:#4285f4" title="Domain URL found in answer text">{GEMINI_ICON}URL?</th>
<th style="background:#4285f420;color:#4285f4" title="Top-10 recommended sources">{GEMINI_ICON}Sources</th>
<th style="background:#4285f420;color:#4285f4" title="Position in source list">{GEMINI_ICON}Rank</th>
<th>{th_checked}</th>
</tr></thead>"""

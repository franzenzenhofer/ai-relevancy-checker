"""HTML report generator - row-based layout with charts."""
from datetime import datetime
from typing import List

from .config import config
from .relevancy_engine import QueryResult
from .aggregator import AggregatedKPIs
from .report_styles import get_report_styles
from .report_header import render_header, render_methodology
from .report_kpi import render_kpi_summary, generate_kpi_cards
from .report_charts_section import render_charts_section
from .report_charts import get_chartjs_cdn
from .report_rows import render_query_row, render_table_header
from .report_table import get_table_javascript


class ReportGenerator:
    """Generates row-based HTML reports with charts."""

    def __init__(self, domain: str, run_id: str = "", offset: int = 0, max_queries: int = 0, cli_command: str = "") -> None:
        self.domain = domain
        self.run_id = run_id
        self.offset = offset
        self.max_queries = max_queries
        self.cli_command = cli_command
        self.generated_at = datetime.now()

    def generate(
        self, openai_results: List[QueryResult], gemini_results: List[QueryResult],
        kpis: AggregatedKPIs, system_context: str
    ) -> str:
        """Generate the full HTML report."""
        openai_sorted = sorted(openai_results, key=lambda x: x.clicks, reverse=True)
        gemini_map = {r.query_id: r for r in gemini_results}
        ts = self.generated_at.strftime("%d.%m.%Y %H:%M:%S")
        ts_row = self.generated_at.strftime("%d.%m.%Y %H:%M")

        rows = [render_query_row(i + 1, o, gemini_map.get(o.query_id), self.domain, ts_row)
                for i, o in enumerate(openai_sorted)]

        table_controls = self._render_table_controls()
        title_prefix = config.report_text.get("title_prefix", "AI Relevancy Report")
        summary_heading = config.report_text.get("summary_heading", "Summary KPIs")
        detail_heading = config.report_text.get("detail_heading", "Detailed Results (Ordered by Clicks)")

        # DRY: Generate KPI cards ONCE, use in both KPI summary and Charts section
        cards = generate_kpi_cards(kpis)

        return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_prefix} - {self.domain} - {self.run_id}</title>
{get_report_styles()}
{get_chartjs_cdn()}
{get_table_javascript()}
{self._get_filter_sort_js()}
</head>
<body>
<div class="report">
{render_header(self.domain, ts, len(openai_results), self.run_id)}
<section class="section"><h2>{summary_heading}</h2>{render_kpi_summary(kpis, cards)}</section>
{render_charts_section(kpis, openai_sorted, gemini_map, cards)}
{render_methodology(self.domain, system_context, self.run_id, self.offset, self.max_queries, self.cli_command)}
<section class="section"><h2>{detail_heading}</h2>
{table_controls}
<div style="overflow-x:auto">
<table class="query-table" id="results-table">
{render_table_header()}
<tbody>{"".join(rows)}</tbody>
</table></div></section>
</div>
</body>
</html>"""

    def _render_table_controls(self) -> str:
        """Render filter and display controls above the table."""
        rt = config.report_text
        fo = rt.get("filter_options", {})
        buttons = rt.get("buttons", {})
        qf_labels = rt.get("quick_filter_labels", {})
        qf_groups = rt.get("quick_filter_groups", {})
        return f"""
<div class="table-controls">
<div class="control-group">
<label style="color:#92400e;font-weight:700">{rt.get("any_vis_label", "Any Visibility:")}</label>
<select id="filter-any-vis" onchange="filterTable()">
<option value="all">{fo.get("all", "All")}</option>
<option value="yes">{fo.get("yes", "✓ Visible (any AI)")}</option>
<option value="no">{fo.get("no", "✗ NOT Visible (nowhere)")}</option>
</select>
</div>
<div class="control-group">
<label style="color:#10a37f;font-weight:700">OpenAI Brand:</label>
<select id="filter-openai-brand" onchange="filterTable()">
<option value="all">{fo.get("all", "All")}</option>
<option value="yes">✓ Brand in Text</option>
<option value="no">✗ No Brand</option>
</select>
</div>
<div class="control-group">
<label style="color:#10a37f;font-weight:700">OpenAI URL:</label>
<select id="filter-openai-domain-answer" onchange="filterTable()">
<option value="all">{fo.get("all", "All")}</option>
<option value="yes">✓ URL in Text</option>
<option value="no">✗ No URL</option>
</select>
</div>
<div class="control-group">
<label style="color:#10a37f;font-weight:700">OpenAI Sources:</label>
<select id="filter-openai-domain" onchange="filterTable()">
<option value="all">{fo.get("all", "All")}</option>
<option value="top5">{fo.get("domain_top5", "Top 5")}</option>
<option value="top10">{fo.get("domain_top10", "Top 6-10")}</option>
<option value="ranked">{fo.get("domain_ranked", "Any Rank")}</option>
<option value="none">{fo.get("domain_none", "Not Ranked")}</option>
</select>
</div>
<div class="control-group">
<label style="color:#4285f4;font-weight:700">Gemini Brand:</label>
<select id="filter-gemini-brand" onchange="filterTable()">
<option value="all">{fo.get("all", "All")}</option>
<option value="yes">✓ Brand in Text</option>
<option value="no">✗ No Brand</option>
</select>
</div>
<div class="control-group">
<label style="color:#4285f4;font-weight:700">Gemini URL:</label>
<select id="filter-gemini-domain-answer" onchange="filterTable()">
<option value="all">{fo.get("all", "All")}</option>
<option value="yes">✓ URL in Text</option>
<option value="no">✗ No URL</option>
</select>
</div>
<div class="control-group">
<label style="color:#4285f4;font-weight:700">Gemini Sources:</label>
<select id="filter-gemini-domain" onchange="filterTable()">
<option value="all">{fo.get("all", "All")}</option>
<option value="top5">{fo.get("domain_top5", "Top 5")}</option>
<option value="top10">{fo.get("domain_top10", "Top 6-10")}</option>
<option value="ranked">{fo.get("domain_ranked", "Any Rank")}</option>
<option value="none">{fo.get("domain_none", "Not Ranked")}</option>
</select>
</div>
</div>
<div class="table-controls">
<div class="control-group">
<label>{rt.get("quick_filters_label", "Quick Filters:")}</label>
<select id="filter-quick" onchange="applyQuickFilter()">
<option value="all">{fo.get("all", "All")}</option>
<optgroup label="{qf_groups.get('successes', '🎯 Successes')}">
<option value="both-answer">{qf_labels.get('both_answer', 'Both AI mention in answer')}</option>
<option value="both-top5">{qf_labels.get('both_top5', 'Both AI rank Top-5')}</option>
<option value="full-success">{qf_labels.get('full_success', 'Full success (answer + top5 both)')}</option>
</optgroup>
<optgroup label="{qf_groups.get('problems', '⚠️ Problems')}">
<option value="neither-answer">{qf_labels.get('neither_answer', 'Neither AI mentions in answer')}</option>
<option value="neither-ranked">{qf_labels.get('neither_ranked', 'Neither AI ranks domain')}</option>
<option value="full-fail">{qf_labels.get('full_fail', 'Full fail (no answer, no rank)')}</option>
</optgroup>
<optgroup label="{qf_groups.get('opportunities', '🔍 Opportunities')}">
<option value="openai-only-answer">{qf_labels.get('openai_only_answer', 'Only OpenAI in answer')}</option>
<option value="gemini-only-answer">{qf_labels.get('gemini_only_answer', 'Only Gemini in answer')}</option>
<option value="openai-only-ranked">{qf_labels.get('openai_only_ranked', 'Only OpenAI ranks')}</option>
<option value="gemini-only-ranked">{qf_labels.get('gemini_only_ranked', 'Only Gemini ranks')}</option>
</optgroup>
</select>
</div>
<div class="control-group">
<label>{rt.get("sort_label", "Sort by:")}</label>
<select id="sort-by" onchange="sortTable()">
<option value="clicks-desc">GSC Clicks (high→low)</option>
<option value="clicks-asc">GSC Clicks (low→high)</option>
<option value="query-asc">Query (A-Z)</option>
<option value="query-desc">Query (Z-A)</option>
</select>
</div>
<div class="control-group">
<label>{rt.get("display_label", "Display:")}</label>
<button class="toggle-btn" onclick="toggleAllText(true)">{buttons.get("expand_all", "Expand all")}</button>
<button class="toggle-btn" onclick="toggleAllText(false)">{buttons.get("collapse_all", "Collapse all")}</button>
<button class="toggle-btn" onclick="resetFilters()">{buttons.get("reset_filters", "Reset filters")}</button>
</div>
<div class="control-group">
<span id="filter-count" style="font-size:12px;color:#475569"></span>
</div>
</div>"""

    def _get_filter_sort_js(self) -> str:
        """Return JavaScript for filter and sort functionality."""
        return """
<script>
function filterTable() {
  var anyVis = document.getElementById('filter-any-vis').value;
  var oaBrand = document.getElementById('filter-openai-brand').value;
  var oaDomainAns = document.getElementById('filter-openai-domain-answer').value;
  var oaDomain = document.getElementById('filter-openai-domain').value;
  var gaBrand = document.getElementById('filter-gemini-brand').value;
  var gaDomainAns = document.getElementById('filter-gemini-domain-answer').value;
  var gaDomain = document.getElementById('filter-gemini-domain').value;
  var rows = document.querySelectorAll('#results-table tbody tr');
  var visible = 0, total = rows.length;

  rows.forEach(function(row) {
    var anyVisCell = row.dataset.anyVis === 'true';
    var oaVis = row.dataset.oaAnswer === 'true';
    var oaDomInAns = row.dataset.oaDomainInAnswer === 'true';
    var oaRank = parseInt(row.dataset.oaRank || '0');
    var gaVis = row.dataset.gaAnswer === 'true';
    var gaDomInAns = row.dataset.gaDomainInAnswer === 'true';
    var gaRank = parseInt(row.dataset.gaRank || '0');
    var show = true;

    // Any Visibility filter
    if (anyVis === 'yes' && !anyVisCell) show = false;
    if (anyVis === 'no' && anyVisCell) show = false;

    // OpenAI Brand filter
    if (oaBrand === 'yes' && !oaVis) show = false;
    if (oaBrand === 'no' && oaVis) show = false;

    // OpenAI Domain in Answer filter
    if (oaDomainAns === 'yes' && !oaDomInAns) show = false;
    if (oaDomainAns === 'no' && oaDomInAns) show = false;

    // OpenAI Source List filter
    if (oaDomain === 'top5' && (oaRank === 0 || oaRank > 5)) show = false;
    if (oaDomain === 'top10' && (oaRank <= 5 || oaRank > 10)) show = false;
    if (oaDomain === 'ranked' && oaRank === 0) show = false;
    if (oaDomain === 'none' && oaRank !== 0) show = false;

    // Gemini Brand filter
    if (gaBrand === 'yes' && !gaVis) show = false;
    if (gaBrand === 'no' && gaVis) show = false;

    // Gemini Domain in Answer filter
    if (gaDomainAns === 'yes' && !gaDomInAns) show = false;
    if (gaDomainAns === 'no' && gaDomInAns) show = false;

    // Gemini Source List filter
    if (gaDomain === 'top5' && (gaRank === 0 || gaRank > 5)) show = false;
    if (gaDomain === 'top10' && (gaRank <= 5 || gaRank > 10)) show = false;
    if (gaDomain === 'ranked' && gaRank === 0) show = false;
    if (gaDomain === 'none' && gaRank !== 0) show = false;

    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('filter-count').textContent = 'Showing ' + visible + ' of ' + total;
}

function applyQuickFilter() {
  var q = document.getElementById('filter-quick').value;
  // Reset individual filters first
  document.getElementById('filter-any-vis').value = 'all';
  document.getElementById('filter-openai-brand').value = 'all';
  document.getElementById('filter-openai-domain-answer').value = 'all';
  document.getElementById('filter-openai-domain').value = 'all';
  document.getElementById('filter-gemini-brand').value = 'all';
  document.getElementById('filter-gemini-domain-answer').value = 'all';
  document.getElementById('filter-gemini-domain').value = 'all';

  var rows = document.querySelectorAll('#results-table tbody tr');
  var visible = 0, total = rows.length;

  rows.forEach(function(row) {
    var oaVis = row.dataset.oaAnswer === 'true';
    var oaRank = parseInt(row.dataset.oaRank || '0');
    var gaVis = row.dataset.gaAnswer === 'true';
    var gaRank = parseInt(row.dataset.gaRank || '0');
    var show = true;

    if (q === 'both-answer') show = oaVis && gaVis;
    else if (q === 'both-top5') show = oaRank > 0 && oaRank <= 5 && gaRank > 0 && gaRank <= 5;
    else if (q === 'full-success') show = oaVis && gaVis && oaRank > 0 && oaRank <= 5 && gaRank > 0 && gaRank <= 5;
    else if (q === 'neither-answer') show = !oaVis && !gaVis;
    else if (q === 'neither-ranked') show = oaRank === 0 && gaRank === 0;
    else if (q === 'full-fail') show = !oaVis && !gaVis && oaRank === 0 && gaRank === 0;
    else if (q === 'openai-only-answer') show = oaVis && !gaVis;
    else if (q === 'gemini-only-answer') show = !oaVis && gaVis;
    else if (q === 'openai-only-ranked') show = oaRank > 0 && gaRank === 0;
    else if (q === 'gemini-only-ranked') show = oaRank === 0 && gaRank > 0;

    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('filter-count').textContent = 'Showing ' + visible + ' of ' + total;
}

function resetFilters() {
  document.getElementById('filter-any-vis').value = 'all';
  document.getElementById('filter-openai-brand').value = 'all';
  document.getElementById('filter-openai-domain-answer').value = 'all';
  document.getElementById('filter-openai-domain').value = 'all';
  document.getElementById('filter-gemini-brand').value = 'all';
  document.getElementById('filter-gemini-domain-answer').value = 'all';
  document.getElementById('filter-gemini-domain').value = 'all';
  document.getElementById('filter-quick').value = 'all';
  var rows = document.querySelectorAll('#results-table tbody tr');
  rows.forEach(function(row) { row.style.display = ''; });
  document.getElementById('filter-count').textContent = 'Showing ' + rows.length + ' of ' + rows.length;
}

function sortTable() {
  var sortBy = document.getElementById('sort-by').value;
  var tbody = document.querySelector('#results-table tbody');
  var rows = Array.from(tbody.querySelectorAll('tr'));
  rows.sort(function(a, b) {
    if (sortBy === 'clicks-desc' || sortBy === 'clicks-asc') {
      var aVal = parseInt(a.cells[2].textContent.replace(/,/g, '')) || 0;
      var bVal = parseInt(b.cells[2].textContent.replace(/,/g, '')) || 0;
      return sortBy === 'clicks-desc' ? bVal - aVal : aVal - bVal;
    } else {
      var aVal = a.cells[1].textContent.toLowerCase();
      var bVal = b.cells[1].textContent.toLowerCase();
      return sortBy === 'query-asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
  });
  rows.forEach(function(row) { tbody.appendChild(row); });
}

// Initialize count on page load
document.addEventListener('DOMContentLoaded', function() {
  var rows = document.querySelectorAll('#results-table tbody tr');
  document.getElementById('filter-count').textContent = 'Showing ' + rows.length + ' of ' + rows.length;
});
</script>"""

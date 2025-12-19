"""Query table rendering for HTML report."""
import re
from html import escape
from typing import Optional
from .config import config


def render_domain_list(domains: list, target_domain: str) -> str:
    """Render domain list as bullet points with highlighting."""
    if not domains:
        return '<span class="error-text">No domains returned</span>'
    items = []
    target_clean = target_domain.replace("www.", "").lower()

    def _matches(candidate: str) -> bool:
        cand = candidate.replace("www.", "").lower()
        if config.domain_match_strategy == "exact":
            return cand == target_clean
        return cand == target_clean or cand.endswith(f".{target_clean}")

    for d in domains:
        is_target = _matches(d)
        cls = ' class="highlight"' if is_target else ""
        items.append(f"<li{cls}>{d}</li>")
    return f'<ul class="domain-list">{"".join(items)}</ul>'


def render_rank_badge(rank: Optional[int]) -> str:
    """Render rank as colored badge."""
    if rank is None:
        return '<span class="rank-badge rank-none">0</span>'
    if rank <= 5:
        return f'<span class="rank-badge rank-top5">#{rank}</span>'
    if rank <= 10:
        return f'<span class="rank-badge rank-top10">#{rank}</span>'
    return f'<span class="rank-badge rank-none">#{rank}</span>'


def render_visibility(visible: bool, is_error: bool = False) -> str:
    """Render visibility status."""
    if is_error:
        return '<span class="visible-no">ERROR</span>'
    if visible:
        return '<span class="visible-yes">YES</span>'
    return '<span class="visible-no">NO</span>'


def render_collapsible_text(text: str, cell_id: str, highlight: bool = True) -> str:
    """Render text with truncation and expand/collapse functionality.

    Args:
        text: The text to render
        cell_id: Unique ID for expand/collapse functionality
        highlight: If True, highlight target domains/brands. If False, show plain text.
    """
    if not text or "[Response blocked" in text or "[Error" in text:
        return f'<span class="error-text">{text or "Empty response"}</span>'

    escaped = escape(text)
    display_text = _highlight_targets(escaped) if highlight else escaped

    if len(text) <= config.report_truncate_length:
        return f'<div class="collapsible-text full-text">{display_text}</div>'

    truncated = escape(text[:config.report_truncate_length]) + "..."
    truncated_display = _highlight_targets(truncated) if highlight else truncated

    return f'''<div class="collapsible-text" data-id="{cell_id}">
<div class="text-truncated">{truncated_display} <button class="expand-btn" onclick="toggleText('{cell_id}')">Show more</button></div>
<div class="text-full full-text" style="display:none">{display_text} <button class="expand-btn" onclick="toggleText('{cell_id}')">Show less</button></div>
</div>'''


def render_answer_text(text: str) -> str:
    """Render full answer text without truncation (legacy, kept for compatibility)."""
    if not text or "[Response blocked" in text or "[Error" in text:
        return f'<span class="error-text">{text or "Empty response"}</span>'
    return f'<div class="full-text">{_highlight_targets(escape(text))}</div>'


def is_error_response(text: str) -> bool:
    """Check if response indicates an error."""
    return not text or "[Response blocked" in text or "[Error" in text


def _highlight_targets(html_text: str) -> str:
    """Highlight occurrences of target domain/brands inside escaped HTML."""
    targets = {config.domain.replace("www.", "").lower()}
    targets.update(b.lower() for b in config.brand_names)
    for t in sorted(targets, key=len, reverse=True):
        if not t:
            continue
        pattern = re.compile(re.escape(t), re.IGNORECASE)
        html_text = pattern.sub(lambda m: f'<mark class="target-hit">{m.group(0)}</mark>', html_text)
    return html_text


def get_table_javascript() -> str:
    """Return JavaScript for expand/collapse functionality."""
    return """
<script>
function toggleText(id) {
  var container = document.querySelector('[data-id="' + id + '"]');
  var truncated = container.querySelector('.text-truncated');
  var full = container.querySelector('.text-full');
  if (truncated.style.display === 'none') {
    truncated.style.display = 'block';
    full.style.display = 'none';
  } else {
    truncated.style.display = 'none';
    full.style.display = 'block';
  }
}

function toggleAllText(show) {
  var containers = document.querySelectorAll('.collapsible-text[data-id]');
  containers.forEach(function(container) {
    var truncated = container.querySelector('.text-truncated');
    var full = container.querySelector('.text-full');
    if (show) {
      truncated.style.display = 'none';
      full.style.display = 'block';
    } else {
      truncated.style.display = 'block';
      full.style.display = 'none';
    }
  });
}
</script>"""

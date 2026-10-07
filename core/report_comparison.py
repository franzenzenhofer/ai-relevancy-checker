"""Year-over-year comparison section for the HTML report.

Compares the current run's aggregate AI-visibility KPIs against a previous
run's exported data CSV (same schema as csv_exporter). Renders a compact
delta table per provider plus a matched-query headline (queries present in
BOTH runs) so like-is-compared-with-like.
"""
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import config
from .aggregator import AggregatedKPIs, ProviderStats
from .relevancy_engine import QueryResult

TRUE_SET = {"1", "true", "yes"}

OPENAI_ICON = ('<img src="https://upload.wikimedia.org/wikipedia/commons/0/04/'
               'ChatGPT_logo.svg" alt="OpenAI" style="width:16px;height:16px;'
               'vertical-align:middle">')
GEMINI_ICON = ('<img src="https://www.gstatic.com/lamda/images/'
               'gemini_sparkle_v002_d4735304ff6292a690345.svg" alt="Gemini" '
               'style="width:16px;height:16px;vertical-align:middle">')


def _is_true(v: Optional[str]) -> bool:
    return (v or "").strip().lower() in TRUE_SET


def _has_rank(v: Optional[str]) -> bool:
    s = (v or "").strip().lower()
    return s not in ("", "0", "none")


def _norm(text: str) -> str:
    return (text or "").strip().lower()


class _Counts:
    """Accumulates provider visibility counts over a set of rows."""

    def __init__(self) -> None:
        self.n = self.answer = self.top5 = self.top10 = self.anyvis = 0

    def add(self, answer: bool, top5: bool, top10: bool, ranked: bool) -> None:
        self.n += 1
        self.answer += 1 if answer else 0
        self.top5 += 1 if top5 else 0
        self.top10 += 1 if top10 else 0
        self.anyvis += 1 if (answer or ranked) else 0

    def pct(self, attr: str) -> float:
        return (getattr(self, attr) / self.n * 100) if self.n else 0.0


def _resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute() and config._config_path:
        path = (config._config_path.parent / path).resolve()
    return path


def _load_prior(path: Path) -> Tuple[_Counts, _Counts, List[dict]]:
    """Load the previous run's CSV into per-provider counts + raw rows."""
    oc, gc, rows = _Counts(), _Counts(), []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
            if (r.get("openai_answer_visible") or "").strip() != "":
                oc.add(_is_true(r.get("openai_answer_visible")), _is_true(r.get("openai_top5")),
                       _is_true(r.get("openai_top10")), _has_rank(r.get("openai_rank")))
            if (r.get("gemini_answer_visible") or "").strip() != "":
                gc.add(_is_true(r.get("gemini_answer_visible")), _is_true(r.get("gemini_top5")),
                       _is_true(r.get("gemini_top10")), _has_rank(r.get("gemini_rank")))
    return oc, gc, rows


def _current_from_stats(s: ProviderStats) -> _Counts:
    c = _Counts()
    c.n = s.total_queries
    c.answer = s.answer_visible_count
    c.top5 = s.top5_count
    c.top10 = s.top10_count
    c.anyvis = s.total_visibility_count
    return c


def _delta_badge(now_pct: float, prior_pct: float) -> str:
    """Coloured percentage-point delta (higher is better for every metric here)."""
    d = now_pct - prior_pct
    if abs(d) < 0.05:
        return '<span style="color:#64748b;font-weight:700">±0.0pp</span>'
    if d > 0:
        return f'<span style="color:#166534;font-weight:700">▲ +{d:.1f}pp</span>'
    return f'<span style="color:#991b1b;font-weight:700">▼ {d:.1f}pp</span>'


_METRICS = [
    ("answer", "Marke im Antworttext", "Brand named in the AI answer"),
    ("top5", "Domain in Top-5-Quellen", "Domain ranked in the top-5 sources"),
    ("top10", "Domain in Top-10-Quellen", "Domain ranked in the top-10 sources"),
    ("anyvis", "Sichtbar (Antwort o. Quelle)", "Mentioned in answer OR listed as a source"),
]


def _provider_card(name: str, icon: str, accent: str, now: _Counts, prior: _Counts,
                   prior_label: str, now_label: str) -> str:
    rows = []
    for attr, label_de, tip in _METRICS:
        p, n = prior.pct(attr), now.pct(attr)
        rows.append(
            f'<tr>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #e2e8f0" title="{tip}">{label_de}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #e2e8f0;text-align:right;color:#475569">'
            f'{p:.1f}% <span style="font-size:10px;color:#94a3b8">({getattr(prior, attr)}/{prior.n})</span></td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:700">'
            f'{n:.1f}% <span style="font-size:10px;color:#94a3b8;font-weight:400">({getattr(now, attr)}/{now.n})</span></td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #e2e8f0;text-align:right">'
            f'{_delta_badge(n, p)}</td>'
            f'</tr>'
        )
    return f'''<div class="chart-container" style="border-color:{accent}">
<div class="chart-title" style="color:{accent};font-size:15px">{icon} {name}</div>
<table style="width:100%;border-collapse:collapse;font-size:12px">
<thead><tr style="background:#f1f5f9">
<th style="padding:6px 8px;text-align:left;border-bottom:2px solid #e2e8f0">Metrik</th>
<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #e2e8f0">{prior_label}</th>
<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #e2e8f0">{now_label}</th>
<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #e2e8f0">Δ</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table></div>'''


def _matched_query_headline(prior_rows: List[dict],
                            openai_results: List[QueryResult],
                            gemini_results: List[QueryResult],
                            prior_label: str, now_label: str) -> str:
    """Compare 'any AI names the brand in the answer' on queries present in BOTH runs."""
    # Prior: query_text -> (openai_answer OR gemini_answer)
    prior_any: Dict[str, bool] = {}
    for r in prior_rows:
        key = _norm(r.get("query_text", ""))
        if not key:
            continue
        prior_any[key] = _is_true(r.get("openai_answer_visible")) or _is_true(r.get("gemini_answer_visible"))

    # Current: query_text -> (openai_answer OR gemini_answer)
    cur_any: Dict[str, bool] = {}
    for r in openai_results:
        cur_any[_norm(r.query_text)] = cur_any.get(_norm(r.query_text), False) or r.appears_in_answer
    for r in gemini_results:
        cur_any[_norm(r.query_text)] = cur_any.get(_norm(r.query_text), False) or r.appears_in_answer

    shared = sorted(set(prior_any) & set(cur_any))
    if not shared:
        return ""
    p_vis = sum(1 for q in shared if prior_any[q])
    n_vis = sum(1 for q in shared if cur_any[q])
    p_pct, n_pct = p_vis / len(shared) * 100, n_vis / len(shared) * 100
    return f'''<div class="intro-box" style="margin-top:1.5rem">
<h3>Gleiche Suchanfragen im Direktvergleich</h3>
<p>{len(shared)} identische Suchanfragen kommen in beiden Auswertungen vor. Auf dieser
gleichbleibenden Basis nennt mindestens eine KI die Marke im Antworttext bei:</p>
<p style="font-size:1.15rem;font-weight:700;color:#0369a1">
{prior_label}: {p_vis}/{len(shared)} · {p_pct:.1f}% &nbsp;→&nbsp;
{now_label}: {n_vis}/{len(shared)} · {n_pct:.1f}% &nbsp;&nbsp; {_delta_badge(n_pct, p_pct)}</p>
</div>'''


def render_comparison_section(
    kpis: AggregatedKPIs,
    openai_results: List[QueryResult],
    gemini_results: List[QueryResult],
) -> str:
    """Render the YoY comparison section, or '' if no comparison CSV configured."""
    if not config.comparison_csv:
        return ""
    path = _resolve_path(config.comparison_csv)
    if not path.exists():
        raise FileNotFoundError(f"comparison_csv not found: {path}")

    prior_o, prior_g, prior_rows = _load_prior(path)
    now_o = _current_from_stats(kpis.openai_stats)
    now_g = _current_from_stats(kpis.gemini_stats)

    prior_label = config.comparison_label or "Vorperiode"
    now_label = config.comparison_current_label or "Aktuell"

    cards = (
        _provider_card("OpenAI (ChatGPT)", OPENAI_ICON, "#10a37f", now_o, prior_o, prior_label, now_label)
        + _provider_card("Google Gemini", GEMINI_ICON, "#4285f4", now_g, prior_g, prior_label, now_label)
    )
    matched = _matched_query_headline(prior_rows, openai_results, gemini_results, prior_label, now_label)

    return f'''<section class="section">
<h2>Jahresvergleich: KI-Sichtbarkeit {prior_label} → {now_label}</h2>
<p class="chart-help">Gegenüberstellung der wichtigsten GEO-Kennzahlen mit der
Vorauswertung ({prior_label}). Δ zeigt die Veränderung in Prozentpunkten (pp);
höhere Werte sind besser. Basis: je 300 Suchanfragen aus der Google Search Console.</p>
<div class="charts-grid-summary" style="grid-template-columns:repeat(2,1fr)">{cards}</div>
{matched}
</section>'''

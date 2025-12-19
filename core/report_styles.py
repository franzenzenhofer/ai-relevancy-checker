"""CSS styles for HTML report - B2B professional design."""

REPORT_STYLES = """
:root{--bg:#f8fafc;--card:#fff;--primary:#0f172a;--secondary:#475569;
--accent:#3b82f6;--success:#22c55e;--warning:#f59e0b;--danger:#ef4444;
--openai:#10a37f;--gemini:#4285f4;--border:#e2e8f0;--highlight:#fef08a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);
color:var(--primary);line-height:1.6;font-size:14px}
.report{max-width:1600px;margin:0 auto;padding:2rem}
.report-header{text-align:center;padding:1rem 1.5rem;background:#fff;border:2px solid var(--border);
color:var(--primary);margin-bottom:1.5rem}
h1{font-size:2rem;margin-bottom:0.5rem;font-weight:800;color:var(--primary)}
.header-stats{display:flex;justify-content:center;gap:1rem;flex-wrap:wrap}
.stat-box{background:#f1f5f9;padding:0.4rem 1rem;font-size:14px;border:1px solid var(--border);color:var(--primary)}
.header-meta{font-size:12px;color:var(--secondary);margin-top:0.5rem}
.section{background:var(--card);padding:1.5rem;margin-bottom:1.5rem;
box-shadow:0 1px 3px rgba(0,0,0,0.1);border:1px solid var(--border)}
h2{font-size:1.8rem;font-weight:700;margin-bottom:1rem;padding-bottom:0.5rem;border-bottom:2px solid var(--border)}
h3{font-size:1.4rem;font-weight:600;margin-bottom:0.8rem}
.kpi-row{display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1rem}
.kpi-box{flex:1;min-width:140px;padding:0.5rem 0.75rem;text-align:center;border:2px solid var(--border)}
.kpi-box.openai{background:#10a37f15;border-color:#10a37f}
.kpi-box.gemini{background:#4285f415;border-color:#4285f4}
.kpi-value{font-size:1.8rem;font-weight:800;line-height:1.1}
.kpi-sub{font-size:0.85rem;font-weight:700;opacity:0.75}
.kpi-label{font-size:10px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.7;margin-top:0.25rem}
.kpi-detail{font-size:10px;color:var(--secondary);margin-top:0.15rem}
.icon{width:16px;height:16px;display:inline-block;background-size:contain;background-repeat:no-repeat;vertical-align:middle}
.icon-openai{background-image:url("https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg")}
.icon-gemini{background-image:url("https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg")}
.kpi-ratio{font-size:0.8rem;font-weight:600;margin-top:0.1rem}
.kpi-icon{margin-bottom:0.25rem}
.charts-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1.5rem}
.charts-grid-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem;margin-bottom:1.5rem}
@media(max-width:900px){.charts-grid-summary{grid-template-columns:1fr}}
.chart-container{background:#fff;border:2px solid var(--border);padding:1rem}
.chart-title{font-size:13px;font-weight:600;margin-bottom:1rem;text-align:center}
.long-tail-section{margin-top:2rem}
.long-tail-section h3{font-size:1rem;margin-bottom:0.5rem}
.chart-help{font-size:12px;color:var(--secondary);margin-bottom:1rem}
.chart-legend{background:#f8fafc;border:2px solid var(--border);padding:1rem;margin:1.5rem auto;max-width:800px}
.legend-title{font-weight:600;font-size:13px;margin-bottom:0.5rem;text-align:center}
.legend-items{display:flex;flex-wrap:wrap;gap:1.5rem;justify-content:center}
.legend-item{display:flex;align-items:center;font-size:12px}
.legend-dot{width:12px;height:12px;margin-right:6px;flex-shrink:0}
.query-table{width:100%;border-collapse:collapse;font-size:13px}
.query-table th{background:#f1f5f9;padding:0.75rem;text-align:left;font-weight:600;
border-bottom:2px solid var(--border);position:sticky;top:0}
.query-table td{padding:0.75rem;border-bottom:1px solid var(--border);vertical-align:top}
.query-table tr:hover{background:#f8fafc}
.query-num{background:var(--primary);color:#fff;padding:2px 8px;font-size:11px}
.visible-yes{color:var(--success);font-weight:600}
.visible-no{color:var(--danger);font-weight:600}
.domain-list{list-style:none;padding:0;margin:0}
.domain-list li{padding:2px 0}
.domain-list li.highlight{background:var(--highlight);font-weight:600;padding:2px 4px}
.rank-badge{display:inline-block;padding:2px 8px;font-weight:600;font-size:12px}
.rank-top5{background:#dcfce7;color:#166534}
.rank-top10{background:#fef3c7;color:#92400e}
.rank-none{background:#fee2e2;color:#991b1b}
.error-text{color:var(--danger);font-style:italic}
.timestamp{font-size:11px;color:var(--secondary)}
.full-text{white-space:pre-wrap;word-break:break-word}
mark.target-hit{background:var(--highlight);color:var(--primary);padding:0 3px}
.legend-row{display:flex;gap:0.75rem;flex-wrap:wrap;font-size:12px;margin-top:0.75rem}
.legend-dot{width:10px;height:10px;display:inline-block;vertical-align:middle;margin-right:6px}
.legend-green{background:#16a34a}.legend-yellow{background:#b45309}.legend-blue{background:#2563eb}.legend-gray{background:#94a3b8}
.intro-box{background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:2px solid #0ea5e9;padding:1.5rem;margin-bottom:1.5rem}
.intro-box h3{color:#0369a1;margin-bottom:0.75rem;font-size:1.3rem}
.intro-box p{margin-bottom:0.5rem;color:#0c4a6e}
.intro-box ol{margin:0.5rem 0 0 1.5rem;color:#0c4a6e}
.intro-box li{margin-bottom:0.25rem}
.finding-section{margin-bottom:1.5rem}
.finding-section h4{font-size:1.1rem;color:var(--primary);margin-bottom:0.25rem;border-left:4px solid var(--accent);padding-left:0.75rem}
.finding-explanation{font-size:13px;color:var(--secondary);margin-bottom:0.75rem;padding-left:1rem}
.kpi-detail{font-size:11px;color:var(--secondary);margin-top:0.25rem}
.long-tail-chart-container{width:100%;max-width:100%;height:400px;margin:0 auto;aspect-ratio:3/1;display:block}
.chart-container-full{background:#fff;border:2px solid var(--border);padding:1rem;margin-bottom:1rem;display:flex;flex-direction:column;align-items:center}
.data-source-section{margin-bottom:2rem}
.data-kpi-row{display:flex;gap:1rem;flex-wrap:wrap}
.data-kpi{flex:1;min-width:180px;padding:1rem;text-align:center;background:#f8fafc;border:2px solid var(--border)}
.data-kpi-value{font-size:1.8rem;font-weight:800;color:var(--primary)}
.data-kpi-label{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--secondary)}
.chart-center{display:flex;justify-content:center;align-items:center}
.table-controls{display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:1rem;padding:1rem;background:#f8fafc;border:2px solid var(--border)}
.control-group{display:flex;align-items:center;gap:0.5rem}
.control-group label{font-size:12px;font-weight:600;color:var(--secondary)}
.control-group select{padding:0.4rem 0.8rem;border:1px solid var(--border);font-size:12px;background:#fff}
.toggle-btn{background:var(--accent);color:#fff;border:none;padding:0.4rem 0.8rem;cursor:pointer;font-size:12px}
.toggle-btn:hover{background:#2563eb}
.expand-btn{background:var(--accent);color:#fff;border:none;padding:2px 8px;cursor:pointer;font-size:11px;margin-left:4px}
.expand-btn:hover{background:#2563eb}
.collapsible-text{font-size:12px}
.text-truncated,.text-full{display:inline}
"""


def get_report_styles() -> str:
    """Return the CSS styles for the report."""
    return f"<style>{REPORT_STYLES}</style>"

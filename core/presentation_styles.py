"""Slide-specific CSS + print styles for PDF export - EXTENDS base report styles (DRY)."""
from .report_styles import REPORT_STYLES

SLIDE_STYLES = """
/* Presentation container */
.presentation { width: 100%; scroll-snap-type: y mandatory; }
.slide {
  position: relative;
  min-height: 100vh;
  padding: 2rem 3rem 5rem 3rem;
  background: #fff;
  border-bottom: 3px solid #e2e8f0;
  scroll-snap-align: start;
  box-sizing: border-box;
}
.slide-header { margin-bottom: 1.5rem; text-align: center; }
.slide-header h2 {
  font-size: 2rem;
  border-bottom: 3px solid #3b82f6;
  padding-bottom: 0.75rem;
  display: inline-block;
}
.slide-content { max-width: 1200px; margin: 0 auto; }
.slide-num {
  position: absolute;
  bottom: 4rem;
  right: 2rem;
  color: #94a3b8;
  font-size: 1rem;
}
.slide-explanation {
  font-size: 1.1rem;
  color: #475569;
  margin-bottom: 1.5rem;
  text-align: center;
}
.slide-section-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #64748b;
  margin-bottom: 0.5rem;
}

/* Slide-specific KPI layout - larger for presentations */
.slide .kpi-row { justify-content: center; gap: 1.5rem; }
.slide .kpi-box { min-width: 180px; padding: 1rem; }
.slide .kpi-value { font-size: 2.5rem; }
.slide .kpi-label { font-size: 12px; }
.slide .kpi-detail { font-size: 12px; }

/* Visualization row - center charts horizontally */
.slide .viz-row {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 2rem;
  margin: 1.5rem auto;
  flex-wrap: wrap;
}
.slide .viz-card {
  max-width: 250px;
  min-width: 200px;
  flex: 0 0 auto;
}

/* Table styling for methodology slides */
.slide-table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}
.slide-table th, .slide-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border: 1px solid #e2e8f0;
}
.slide-table th {
  background: #f1f5f9;
  font-weight: 600;
}
.slide-table tr:nth-child(even) { background: #f8fafc; }

/* Code blocks */
.slide-code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 8px;
  font-family: monospace;
  font-size: 13px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Long tail chart container */
.slide .long-tail-chart-container {
  height: 350px;
  margin: 1rem auto;
}

/* Navigation */
.slide-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #1e293b;
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1000;
}
.nav-btn {
  background: #3b82f6;
  color: #fff;
  border: none;
  padding: 0.5rem 1.5rem;
  cursor: pointer;
  font-size: 14px;
  border-radius: 4px;
  transition: background 0.2s;
}
.nav-btn:hover { background: #2563eb; }
.nav-btn:disabled { background: #64748b; cursor: not-allowed; }
.nav-counter { color: #fff; font-size: 14px; }
.print-btn { background: #22c55e; }
.print-btn:hover { background: #16a34a; }

/* Print CSS for PDF export - LANDSCAPE MODE for presentations! */
@media print {
  @page {
    size: A4 landscape;
    margin: 0.75cm;
  }
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    background: #fff !important;
  }
  .presentation { width: 100%; }
  .slide {
    page-break-after: always;
    page-break-inside: avoid;
    min-height: auto;
    height: auto;
    padding: 1.5rem;
    border: none;
    background: #fff !important;
  }
  .slide:last-child { page-break-after: avoid; }
  .slide-nav { display: none !important; }
  .slide-num {
    position: static;
    text-align: right;
    margin-top: 1rem;
    font-size: 10px;
  }
  .slide-header h2 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
  }
  .slide-explanation { font-size: 0.9rem; }
  /* Ensure charts print correctly */
  canvas {
    max-width: 100% !important;
    max-height: 250px !important;
  }
  .long-tail-chart-container {
    height: 200px !important;
    max-height: 200px !important;
  }
  .viz-row { gap: 1rem; }
  .viz-card { max-width: 200px; }
  .kpi-row { gap: 0.5rem; }
  .kpi-box {
    min-width: 100px;
    padding: 0.5rem;
  }
  .kpi-value { font-size: 1.5rem; }
  .slide-table { font-size: 11px; }
  .slide-code { font-size: 10px; padding: 0.5rem; }
  .chart-container-full { padding: 0.5rem; }
}
"""


def get_presentation_styles() -> str:
    """Return combined base + slide-specific styles (DRY: reuses REPORT_STYLES)."""
    return f"<style>{REPORT_STYLES}\n{SLIDE_STYLES}</style>"

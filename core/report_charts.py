"""Chart generation for HTML report using Chart.js."""
import json
from typing import List


def get_chartjs_cdn() -> str:
    """Return Chart.js CDN script tag."""
    return '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'


def generate_pie_chart(chart_id: str, labels: List[str], data: List[int], colors: List[str]) -> str:
    """Generate a pie chart."""
    colors_js = "[" + ", ".join(f"'{c}'" for c in colors) + "]"
    return f"""
<canvas id="{chart_id}" width="200" height="200"></canvas>
<script>
new Chart(document.getElementById('{chart_id}'), {{
  type: 'pie',
  data: {{
    labels: {labels},
    datasets: [{{ data: {data}, backgroundColor: {colors_js} }}]
  }},
  options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
}});
</script>"""


def generate_bar_chart(chart_id: str, labels: List[str], datasets: List[dict]) -> str:
    """Generate a bar chart."""
    datasets_js = json.dumps(datasets)
    return f"""
<canvas id="{chart_id}" width="400" height="200"></canvas>
<script>
new Chart(document.getElementById('{chart_id}'), {{
  type: 'bar',
  data: {{ labels: {labels}, datasets: {datasets_js} }},
  options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true, max: 100 }} }} }}
}});
</script>"""


def generate_long_tail_chart(
    chart_id: str,
    title: str,
    clicks: List[int],
    answer_flags: List[bool],
    domain_flags: List[bool],
    query_texts: List[str],
) -> str:
    """Generate a long-tail click chart with point colors based on visibility."""
    def color_for(idx: int) -> str:
        ans, dom = answer_flags[idx], domain_flags[idx]
        if ans and dom:
            return "#16a34a"  # green - both answer visible AND in domain list
        if dom:
            return "#f59e0b"  # amber - only in domain list
        if ans:
            return "#3b82f6"  # blue - only answer visible
        return "#9ca3af"      # gray - neither

    data = [{"x": i + 1, "y": c, "query": q} for i, (c, q) in enumerate(zip(clicks, query_texts))]
    colors = [color_for(i) for i in range(len(clicks))]
    data_js = json.dumps(data)
    colors_js = json.dumps(colors)
    x_max = len(clicks) + 1
    return f"""
<div class="long-tail-chart-container"><canvas id="{chart_id}"></canvas></div>
<script>
new Chart(document.getElementById('{chart_id}'), {{
  type: 'scatter',
  data: {{
    datasets: [{{
      label: '{title}',
      data: {data_js},
      showLine: true,
      fill: false,
      borderColor: 'rgba(99, 102, 241, 0.35)',
      tension: 0.25,
      pointRadius: 8,
      pointBackgroundColor: {colors_js},
      pointBorderColor: {colors_js},
      pointHoverRadius: 10,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          title: function(ctx) {{
            return ctx[0].raw.query;
          }},
          label: function(ctx) {{
            return 'Rank #' + ctx.raw.x + ' | Clicks: ' + ctx.raw.y.toLocaleString();
          }}
        }}
      }}
    }},
    scales: {{
      x: {{
        type: 'linear',
        min: 0,
        max: {x_max},
        title: {{ display: true, text: 'Query rank by clicks' }},
        ticks: {{ stepSize: 1, precision: 0 }}
      }},
      y: {{
        title: {{ display: true, text: 'Clicks' }},
        beginAtZero: true
      }}
    }}
  }}
}});
</script>"""


def render_chart_legend() -> str:
    """Render the legend explaining dot colors."""
    return """
<div class="chart-legend">
  <div class="legend-title">Legend:</div>
  <div class="legend-items">
    <div class="legend-item"><span class="legend-dot" style="background:#16a34a"></span> Domain in answer + top-10 list</div>
    <div class="legend-item"><span class="legend-dot" style="background:#3b82f6"></span> Domain in answer only</div>
    <div class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span> Domain in top-10 list only</div>
    <div class="legend-item"><span class="legend-dot" style="background:#9ca3af"></span> Not visible</div>
  </div>
</div>"""

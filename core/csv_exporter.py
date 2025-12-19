"""CSV export for data scientist view."""
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from .config import config
from .relevancy_engine import QueryResult


class CSVExporter:
    """Exports query results to CSV for data analysis."""

    def export(
        self, openai_results: List[QueryResult], gemini_results: List[QueryResult],
        run_id: Optional[str] = None, output_name: Optional[str] = None
    ) -> Path:
        """Export results to CSV file."""
        timestamp = datetime.now()
        rows = self._build_rows(openai_results, gemini_results, run_id, timestamp)
        if output_name:
            filename = f"{output_name}.csv"
        else:
            ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"ai_relevancy_data_{ts_str}.csv"
        filepath = config.get_export_path(filename)
        self._write_csv(rows, filepath)
        return filepath

    def _build_rows(
        self, openai_results: List[QueryResult], gemini_results: List[QueryResult],
        run_id: Optional[str], timestamp: datetime
    ) -> List[Dict]:
        """Build flat rows combining both providers."""
        o_map = {r.query_id: r for r in openai_results}
        g_map = {r.query_id: r for r in gemini_results}
        rows: List[Dict] = []
        ts_iso = timestamp.isoformat()
        query_ids = sorted(set(o_map.keys()) | set(g_map.keys()))

        for qid in query_ids:
            o_res = o_map.get(qid)
            g_res = g_map.get(qid)
            rows.append(
                {
                    "run_id": run_id or "",
                    "timestamp": ts_iso,
                    "domain": config.domain,
                    "query_id": qid,
                    "query_text": o_res.query_text if o_res else g_res.query_text if g_res else "",
                    "hypothetical_prompt": o_res.hypothetical_prompt if o_res else g_res.hypothetical_prompt if g_res else "",
                    "country_code": o_res.country_code if o_res else g_res.country_code if g_res else "",
                    "impressions": o_res.impressions if o_res else g_res.impressions if g_res else 0,
                    "clicks": o_res.clicks if o_res else g_res.clicks if g_res else 0,
                    # OpenAI metrics
                    "openai_answer_visible": int(o_res.appears_in_answer) if o_res else "",
                    "openai_top5": int(o_res.appears_in_top5) if o_res else "",
                    "openai_top10": int(o_res.appears_in_top10) if o_res else "",
                    "openai_rank": o_res.rank_if_present if o_res and o_res.rank_if_present else "",
                    "openai_domains": "|".join(o_res.domains_list) if o_res and o_res.domains_list else "",
                    "openai_tokens": o_res.tokens_used if o_res else "",
                    # Gemini metrics
                    "gemini_answer_visible": int(g_res.appears_in_answer) if g_res else "",
                    "gemini_top5": int(g_res.appears_in_top5) if g_res else "",
                    "gemini_top10": int(g_res.appears_in_top10) if g_res else "",
                    "gemini_rank": g_res.rank_if_present if g_res and g_res.rank_if_present else "",
                    "gemini_domains": "|".join(g_res.domains_list) if g_res and g_res.domains_list else "",
                    "gemini_tokens": g_res.tokens_used if g_res else "",
                }
            )
        return rows

    def _write_csv(self, rows: List[Dict], filepath: Path) -> None:
        """Write rows to CSV file."""
        if not rows:
            print("No data to export")
            return

        fieldnames = list(rows[0].keys())
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"CSV exported: {filepath} ({len(rows)} rows)")

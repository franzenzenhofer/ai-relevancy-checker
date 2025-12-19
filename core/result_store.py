"""Result storage for incremental saves and resume."""
import json
from pathlib import Path
from dataclasses import asdict
from typing import List, Optional, Tuple
from .relevancy_engine import QueryResult


class ResultStore:
    """Stores results incrementally for resume capability."""

    def __init__(self, store_dir: Path) -> None:
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, run_id: str, result: QueryResult, provider: str) -> None:
        """Save a single result."""
        path = self._get_path(run_id, result.query_id, provider)
        with open(path, "w") as f:
            json.dump(asdict(result), f, indent=2)

    def load_result(self, run_id: str, query_id: int, provider: str) -> Optional[QueryResult]:
        """Load a single result."""
        path = self._get_path(run_id, query_id, provider)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return QueryResult(**data)

    def load_all_results(self, run_id: str) -> Tuple[List[QueryResult], List[QueryResult]]:
        """Load all results for a run."""
        openai_results, gemini_results = [], []
        for p in self.store_dir.glob(f"{run_id}_*_openai.json"):
            with open(p) as f:
                openai_results.append(QueryResult(**json.load(f)))
        for p in self.store_dir.glob(f"{run_id}_*_gemini.json"):
            with open(p) as f:
                gemini_results.append(QueryResult(**json.load(f)))
        return (
            sorted(openai_results, key=lambda r: r.query_id),
            sorted(gemini_results, key=lambda r: r.query_id)
        )

    def providers_for_query(self, run_id: str, query_id: int) -> set[str]:
        """Return providers with stored results for given query."""
        providers: set[str] = set()
        for p in self.store_dir.glob(f"{run_id}_{query_id:04d}_*.json"):
            suffix = p.stem.split("_")[-1]
            providers.add(suffix)
        return providers

    def has_result(self, run_id: str, query_id: int, provider: str) -> bool:
        """Check if a result exists."""
        return self._get_path(run_id, query_id, provider).exists()

    def _get_path(self, run_id: str, query_id: int, provider: str) -> Path:
        return self.store_dir / f"{run_id}_{query_id:04d}_{provider}.json"

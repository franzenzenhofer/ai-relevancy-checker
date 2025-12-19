"""Run state management for resume capability."""
import json
import uuid
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict
from .config import config


@dataclass
class RunState:
    """State of a run that can be resumed."""
    run_id: str
    domain: str
    max_queries: int
    started_at: str
    completed_queries: List[int]
    total_queries: int
    status: str  # pending, running, completed, failed
    providers: List[str] = field(default_factory=lambda: config.default_providers)
    completed_providers: Dict[str, List[str]] = field(default_factory=dict)
    cli_command: str = ""  # Original CLI command for methodology display

    @classmethod
    def create_new(cls, domain: str, max_queries: int, total: int, providers: Optional[List[str]] = None,
                   cli_command: str = "") -> "RunState":
        return cls(
            run_id=str(uuid.uuid4())[:8],
            domain=domain,
            max_queries=max_queries,
            started_at=datetime.now().isoformat(),
            completed_queries=[],
            total_queries=total,
            status="running",
            providers=providers or config.default_providers,
            completed_providers={},
            cli_command=cli_command,
        )


class RunStateManager:
    """Manages run state persistence."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: RunState) -> Path:
        path = self.state_dir / f"run_{state.run_id}.json"
        with open(path, "w") as f:
            json.dump(asdict(state), f, indent=2)
        return path

    def load(self, run_id: str) -> Optional[RunState]:
        path = self.state_dir / f"run_{run_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return RunState(**data)

    def list_runs(self) -> List[RunState]:
        runs = []
        for p in self.state_dir.glob("run_*.json"):
            with open(p) as f:
                runs.append(RunState(**json.load(f)))
        return sorted(runs, key=lambda r: r.started_at, reverse=True)

    def mark_query_done(self, state: RunState, query_id: int) -> None:
        if query_id not in state.completed_queries:
            state.completed_queries.append(query_id)
        self.save(state)

    def mark_provider_done(self, state: RunState, query_id: int, provider: str) -> None:
        key = str(query_id)
        providers = state.completed_providers.setdefault(key, [])
        if provider not in providers:
            providers.append(provider)
        if all(p in providers for p in state.providers):
            self.mark_query_done(state, query_id)
        else:
            self.save(state)

    def mark_completed(self, state: RunState) -> None:
        state.status = "completed" if len(state.completed_queries) >= state.total_queries else "running"
        self.save(state)

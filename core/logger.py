"""Logging for AI Relevancy Checker - full request/response logging."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class RunLogger:
    """Logs all requests and responses for a run."""

    def __init__(self, log_dir: Path, run_id: str) -> None:
        self.log_dir = log_dir
        self.run_id = run_id
        self.log_file = log_dir / f"run_{run_id}.log"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._write(f"=== RUN {run_id} STARTED at {datetime.now().isoformat()} ===\n")

    def _write(self, msg: str) -> None:
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def log_query_start(self, query_id: int, query_text: str, prompt: str) -> None:
        self._write(f"\n--- QUERY {query_id}: {query_text} ---")
        self._write(f"Hypothetical prompt: {prompt}")

    def log_request(self, provider: str, request_type: str, prompt: str, system: str, request_id: str = "") -> None:
        self._write(f"\n[{provider}] {request_type} REQUEST:")
        if request_id:
            self._write(f"Request ID: {request_id}")
        self._write(f"System: {system}")
        self._write(f"Prompt: {prompt}")

    def log_response(self, provider: str, request_type: str, response: str, tokens: int, request_id: str = "") -> None:
        self._write(f"\n[{provider}] {request_type} RESPONSE ({tokens} tokens):")
        if request_id:
            self._write(f"Request ID: {request_id}")
        self._write(response)

    def log_error(self, provider: str, error: str) -> None:
        self._write(f"\n[{provider}] ERROR: {error}")

    def log_result(self, provider: str, answer_visible: bool, rank: Optional[int], domains: list) -> None:
        self._write(f"\n[{provider}] RESULT: answer_visible={answer_visible}, rank={rank}")
        self._write(f"[{provider}] Domains: {domains}")

    def log_run_complete(self) -> None:
        self._write(f"\n=== RUN {self.run_id} COMPLETED at {datetime.now().isoformat()} ===")
        print(f"Log file: {self.log_file}")


# Global logger instance
_logger: Optional[RunLogger] = None


def init_logger(log_dir: Path, run_id: str) -> RunLogger:
    global _logger
    _logger = RunLogger(log_dir, run_id)
    return _logger


def get_logger() -> Optional[RunLogger]:
    return _logger

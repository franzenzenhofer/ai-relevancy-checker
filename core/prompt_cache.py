"""Cache PromptPackets to support resumable runs."""
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from .prompt_generator import PromptPacket


class PromptCache:
    """Simple JSON cache for prompt packets."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run_id: str, packets: List[PromptPacket]) -> Path:
        path = self.cache_dir / f"{run_id}_packets.json"
        data = [asdict(p) for p in packets]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return path

    def load(self, run_id: str) -> List[PromptPacket]:
        path = self.cache_dir / f"{run_id}_packets.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        return [PromptPacket(**item) for item in data]

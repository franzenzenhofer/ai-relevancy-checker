"""Environment and .env file loading utilities."""
import os
from pathlib import Path
from typing import Optional

_dotenv_values: dict = {}


def load_dotenv() -> None:
    """Load .env file from project root if exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            _dotenv_values[key.strip()] = value.strip()


def get_env_key(key: str) -> Optional[str]:
    """Get key from .env (priority) or environment."""
    return _dotenv_values.get(key, os.environ.get(key))

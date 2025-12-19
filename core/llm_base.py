"""Base classes and constants for LLM clients."""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .config import config


@dataclass
class LLMResponse:
    """Response from an LLM."""

    text: str
    tokens_used: int
    model: str
    provider: str
    full_prompt: str = ""


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_answer(self, prompt: str, system_context: str) -> LLMResponse:
        """Generate an answer to the user prompt."""
        pass

    @abstractmethod
    def generate_relevant_domains(self, prompt: str, system_context: str) -> LLMResponse:
        """Generate a list of relevant domains for the prompt."""
        pass


def rate_limit_delay() -> None:
    """Apply rate limiting delay."""
    time.sleep(config.request_delay)


def get_domain_list_suffix() -> str:
    """Return the domain list suffix from config (no hardcoded string)."""
    return config.domain_list_suffix

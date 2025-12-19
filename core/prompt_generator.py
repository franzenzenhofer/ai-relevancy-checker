"""Prompt generation for AI Relevancy Checker - AI ONLY, NO TEMPLATE FALLBACKS!"""
import concurrent.futures
from dataclasses import dataclass
from typing import Callable, List, Optional
from .config import config
from .gsc_query import QueryRecord
# REMOVED: prompt_templates import - NO TEMPLATE FALLBACKS ALLOWED!


@dataclass
class PromptPacket:
    """Contains all data needed for LLM evaluation."""
    query_id: int
    query_text: str
    hypothetical_prompt: str
    language_code: str
    location_briefing: str
    domain: str
    brand_names: List[str]
    page_url: str
    country_code: str
    clicks: int
    impressions: int


class PromptGenerator:
    """Generates hypothetical prompts from GSC queries."""

    def __init__(self) -> None:
        self.domain = config.domain
        self.brand_names = config.brand_names
        # Location from config (single source of truth)
        self.city_de = config.user_city
        self.city_en = config.user_city_en
        self.country_de = config.user_country
        self.country_en = config.user_country_en
        # Language indicators from config (required unless force_language set)
        self._language_indicators = config.language_indicators or {}

    def detect_language(self, query: str) -> str:
        """Detect language based on query content and config indicators; fail loud on ambiguity."""
        if config.force_language:
            return config.force_language
        query_lower = query.lower()
        for lang_code, indicators in self._language_indicators.items():
            for ind in indicators:
                if ind.lower() in query_lower:
                    return lang_code
        if config.default_language:
            return config.default_language
        raise ValueError(
            "Unable to detect language for query and no default_language set. "
            "Add force_language or language_indicators/default_language to config."
        )

    def generate_prompt_ai(self, query: str, language: str, prompt_client) -> str:
        """Use the OpenAI prompt model to generate an UNBIASED hypothetical prompt.

        FAIL LOUD, FAIL EARLY, FAIL HARD - NO FALLBACK! AI generation is REQUIRED.
        """
        if prompt_client is None:
            raise RuntimeError(
                "FATAL: AI prompt generation REQUIRED! No prompt_client provided. "
                "Set PROMPT_MODE=ai (default) and ensure OpenAI API key is valid."
            )
        city, country = self._location_parts(language)
        return prompt_client.generate_hypothetical_prompt(query, language, city, country)

    def get_system_context(self, language: str) -> str:
        """Return system context from config; fail loud if missing."""
        ctx = config.answer_system_contexts.get(language)
        if not ctx:
            raise ValueError(f"No system context configured for language: {language}")
        return ctx

    def get_location_string(self, language: str) -> str:
        """Return location string for reports."""
        city, country = self._location_parts(language)
        if city and city.lower() != country.lower():
            return f"{city}, {country}"
        return country or city

    def create_packets(
        self,
        records: List[QueryRecord],
        prompt_client,
        start_query_id: int = 0,
        on_progress: Optional[Callable[[List[PromptPacket]], None]] = None,
        progress_interval: int = 10,
    ) -> List[PromptPacket]:
        """Create prompt packets with concurrent AI generation. AI generation is mandatory - no fallbacks."""
        # FAIL HARD: AI prompt generation is REQUIRED - no fallback to templates!
        if config.prompt_mode != "ai":
            raise RuntimeError(
                f"FATAL: prompt_mode must be 'ai', got '{config.prompt_mode}'. "
                "Template fallbacks are DISABLED. AI generation is MANDATORY!"
            )
        if prompt_client is None:
            raise RuntimeError(
                "FATAL: AI prompt generation REQUIRED but prompt_client is None! "
                "Ensure OpenAI API key is valid. NO FALLBACKS ALLOWED!"
            )

        total = len(records)
        packets: list[Optional[PromptPacket]] = [None] * total
        progress_interval = max(1, progress_interval)

        def build_packet(idx: int, record: QueryRecord) -> PromptPacket:
            lang = self.detect_language(record.query_text)
            ai_prompt = self.generate_prompt_ai(record.query_text, lang, prompt_client)
            location_str = self.get_location_string(lang)
            return PromptPacket(
                query_id=start_query_id + idx, query_text=record.query_text,
                hypothetical_prompt=ai_prompt, language_code=lang,
                location_briefing=location_str, domain=self.domain,
                brand_names=self.brand_names, page_url=record.page_url,
                country_code=record.country_code, clicks=record.clicks, impressions=record.impressions,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.prompt_concurrency) as executor:
            future_map = {executor.submit(build_packet, idx, r): idx for idx, r in enumerate(records)}
            completed = 0
            for future in concurrent.futures.as_completed(future_map):
                idx = future_map[future]
                packet = future.result()
                packets[idx] = packet
                completed += 1
                if on_progress and (completed % progress_interval == 0 or completed == total):
                    ready = [p for p in packets if p is not None]
                    on_progress(ready)

        return [p for p in packets if p is not None]

    def _location_parts(self, language: str) -> tuple[str, str]:
        """Return (city, country)."""
        city = (self.city_de if language == "de" else self.city_en).strip()
        country = (self.country_de if language == "de" else self.country_en).strip()
        return city, country

    # REMOVED: _generate_prompt_template - NO TEMPLATE FALLBACKS ALLOWED!

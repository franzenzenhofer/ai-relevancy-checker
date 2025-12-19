"""OpenAI client implementation."""
import json
from typing import Optional
from .config import config
from .llm_base import LLMClient, LLMResponse, rate_limit_delay

def get_openai_prompt_system(location_clause: str, location_phrase: str) -> str:
    """Return the system prompt for hypothetical prompt generation - SINGLE SOURCE OF TRUTH."""
    return config.prompt_system_template.format(location_clause=location_clause, location_phrase=location_phrase)


class OpenAIClient(LLMClient):
    """OpenAI API client using latest mini model."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or config.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)
        self.model = config.openai_model
        self.prompt_model = config.openai_prompt_model
        print(f"OpenAI client initialized with model: {self.model} (prompt model: {self.prompt_model})")

    def generate_answer(self, prompt: str, system_context: str) -> LLMResponse:
        """Generate answer using OpenAI."""
        rate_limit_delay()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_context}, {"role": "user", "content": prompt}],
            max_completion_tokens=config.max_output_tokens_answer,
        )
        text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return LLMResponse(text=text, tokens_used=tokens, model=self.model, provider="openai", full_prompt=prompt)

    def generate_relevant_domains(self, prompt: str, system_context: str) -> LLMResponse:
        """Generate list of relevant domains using OpenAI with JSON response."""
        rate_limit_delay()
        domain_prompt = f"{prompt}\n\n{config.openai_domain_json_prompt}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_context}, {"role": "user", "content": domain_prompt}],
            max_completion_tokens=config.max_output_tokens_domains,
            response_format={"type": "json_object"},
        )
        raw_text = response.choices[0].message.content or "{}"
        domains = self._parse_domains_json(raw_text)
        tokens = response.usage.total_tokens if response.usage else 0
        text = json.dumps({"domains": domains})
        return LLMResponse(text=text, tokens_used=tokens, model=self.model, provider="openai", full_prompt=domain_prompt)

    def generate_hypothetical_prompt(self, query: str, language: str, city: str, country: str) -> str:
        """Create an UNBIASED hypothetical user prompt. NO target domain info - must be neutral."""
        language_hint = "German" if language == "de" else "English"
        location_phrase = city.strip() or country
        location_clause = (
            f"{city}, {country}" if city and country and city.lower() != country.lower() else location_phrase
        )
        system_context = get_openai_prompt_system(location_clause, location_phrase)
        user_prompt = config.prompt_user_template.format(
            query=query,
            language_hint=language_hint,
            location_clause=location_clause,
            location_phrase=location_phrase,
        )
        # NO FALLBACKS - fail loud if API fails
        rate_limit_delay()
        response = self.client.chat.completions.create(
            model=self.prompt_model,
            messages=[
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=8000,
        )
        result = response.choices[0].message.content
        if not result or not result.strip():
            raise ValueError(f"Empty response from OpenAI for query: {query}")
        return result

    def ping(self) -> str:
        """Minimal request to validate API/key. Reasoning models need ~1000 tokens."""
        rate_limit_delay()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_completion_tokens=1000,
        )
        return (response.choices[0].message.content or "").strip()

    def _parse_domains_json(self, raw: str) -> list[str]:
        """Parse JSON response and return domain list; fail loud if invalid."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON from OpenAI domains response: {exc}") from exc
        domains = data.get("domains")
        if not isinstance(domains, list) or not domains:
            raise ValueError("OpenAI domains response missing non-empty 'domains' array")
        cleaned = [str(d).strip() for d in domains if str(d).strip()]
        if not cleaned:
            raise ValueError("OpenAI domains response contained no usable domains")
        return cleaned[:10]

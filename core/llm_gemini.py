"""Google Gemini client implementation."""
import json
from typing import Optional
from .config import config
from .llm_base import LLMClient, LLMResponse, rate_limit_delay

class GeminiClient(LLMClient):
    """Google Gemini API client using latest flash model."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or config.gemini_api_key
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.model_name = config.gemini_model
        self.model = genai.GenerativeModel(self.model_name)
        print(f"Gemini client initialized with model: {self.model_name}")

    def generate_answer(self, prompt: str, system_context: str) -> LLMResponse:
        rate_limit_delay()
        full_prompt = f"{system_context}\n\nUser question: {prompt}"
        response = self.model.generate_content(
            full_prompt, generation_config={"max_output_tokens": config.max_output_tokens_answer, "temperature": 0.3},
        )
        text = self._safe_get_text(response)
        tokens = self._get_token_count(response)
        return LLMResponse(text=text, tokens_used=tokens, model=self.model_name, provider="gemini", full_prompt=prompt)

    def generate_relevant_domains(self, prompt: str, system_context: str) -> LLMResponse:
        rate_limit_delay()
        domain_prompt = f"{system_context}\n\nUser question: {prompt}\n\n{config.gemini_domain_json_prompt}"
        response = self.model.generate_content(
            domain_prompt,
            generation_config={
                "max_output_tokens": config.max_output_tokens_domains,
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )
        raw_text = self._safe_get_text(response)
        domains = self._parse_domains_json(raw_text)
        tokens = self._get_token_count(response)
        text = json.dumps({"domains": domains})
        return LLMResponse(text=text, tokens_used=tokens, model=self.model_name, provider="gemini", full_prompt=domain_prompt)

    def _parse_domains_json(self, raw: str) -> list[str]:
        """Parse JSON response and return domain list; fail loud if invalid."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON from Gemini domains response: {exc}") from exc
        domains = data.get("domains")
        if not isinstance(domains, list) or not domains:
            raise ValueError("Gemini domains response missing non-empty 'domains' array")
        cleaned = [str(d).strip() for d in domains if str(d).strip()]
        if not cleaned:
            raise ValueError("Gemini domains response contained no usable domains")
        return cleaned[:10]

    def _safe_get_text(self, response) -> str:
        try:
            if response.text:
                return response.text
        except ValueError:
            pass
        # Thinking models return thought parts before (or instead of) text
        # parts; response.text raises on them. Join real text parts only.
        if response.candidates and response.candidates[0].content.parts:
            texts = [p.text for p in response.candidates[0].content.parts
                     if getattr(p, "text", None) and not getattr(p, "thought", False)]
            if texts:
                return "".join(texts)
        return "[Response blocked or empty]"

    def _get_token_count(self, response) -> int:
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            return getattr(response.usage_metadata, "total_token_count", 0)
        return 0

    def ping(self) -> str:
        """Minimal request to validate API/key."""
        rate_limit_delay()
        # No output cap: thinking models (gemini-flash-latest) burn hundreds of
        # tokens on internal reasoning first; any small cap yields an empty
        # response and a false-negative healthcheck. A ping costs ~a cent max.
        response = self.model.generate_content(
            "Respond with OK",
            generation_config={"temperature": 0.0},
        )
        return self._safe_get_text(response).strip()

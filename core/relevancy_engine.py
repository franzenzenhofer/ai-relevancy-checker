"""Relevancy scoring engine for AI Relevancy Checker."""
from dataclasses import dataclass
from typing import List, Optional

from .prompt_generator import PromptPacket
from .llm_base import LLMResponse
from .relevancy_parser import check_answer_visibility, parse_domain_list, check_domain_presence, find_domains_in_text


@dataclass
class QueryResult:
    """Results for a single query evaluation."""

    query_id: int
    query_text: str
    hypothetical_prompt: str
    system_context: str
    provider: str
    model: str
    answer_text: str
    appears_in_answer: bool
    domain_list_prompt: str
    domain_list_text: str
    domains_list: List[str]
    appears_in_top5: bool
    appears_in_top10: bool
    rank_if_present: Optional[int]
    clicks: int
    impressions: int
    country_code: str
    page_url: str
    tokens_used: int
    answer_request_id: str = ""
    domains_request_id: str = ""
    # Domain mention analysis
    domains_in_answer: List[str] = None  # All domains found in answer text
    any_domain_in_answer: bool = False  # Does answer contain ANY domain?
    target_domain_in_answer: bool = False  # Is TARGET domain mentioned in answer text?


class RelevancyEngine:
    """Evaluates domain visibility in LLM responses."""

    def __init__(self, domain: str, brand_names: List[str]) -> None:
        self.domain = domain.lower()
        self.domain_base = self.domain.replace("www.", "").split(".")[0]
        self.brand_names = [b.lower() for b in brand_names]

    def check_visibility(
        self,
        packet: PromptPacket,
        answer_response: LLMResponse,
        domains_response: LLMResponse,
        system_context: str,
        domain_list_prompt: str,
        answer_request_id: str = "",
        domains_request_id: str = "",
    ) -> QueryResult:
        """Check visibility for a single query against LLM responses."""
        appears = check_answer_visibility(
            answer_response.text, self.domain, self.domain_base, self.brand_names
        )
        domains = parse_domain_list(domains_response.text)
        top5, top10, rank = check_domain_presence(domains, self.domain, self.domain_base)
        # Find ALL domains mentioned in answer text
        domains_in_answer = find_domains_in_text(answer_response.text)
        # Check if TARGET domain is specifically mentioned in answer text
        target_clean = self.domain.replace("www.", "").lower()
        target_domain_in_answer = any(
            d == target_clean or d.endswith(f".{target_clean}")
            for d in domains_in_answer
        )

        return QueryResult(
            query_id=packet.query_id, query_text=packet.query_text,
            hypothetical_prompt=packet.hypothetical_prompt,
            system_context=system_context, provider=answer_response.provider,
            model=answer_response.model, answer_text=answer_response.text,
            appears_in_answer=appears, domain_list_prompt=domain_list_prompt,
            domain_list_text=domains_response.text, domains_list=domains,
            appears_in_top5=top5, appears_in_top10=top10, rank_if_present=rank,
            answer_request_id=answer_request_id, domains_request_id=domains_request_id,
            clicks=packet.clicks, impressions=packet.impressions,
            country_code=packet.country_code, page_url=packet.page_url,
            tokens_used=answer_response.tokens_used + domains_response.tokens_used,
            domains_in_answer=domains_in_answer,
            any_domain_in_answer=len(domains_in_answer) > 0,
            target_domain_in_answer=target_domain_in_answer,
        )

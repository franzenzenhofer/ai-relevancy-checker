"""KPI aggregation for AI Relevancy Checker."""
from dataclasses import dataclass, field
from typing import List
from .relevancy_engine import QueryResult


@dataclass
class ProviderStats:
    """Statistics for a single LLM provider."""
    provider: str
    total_queries: int = 0
    total_visibility_count: int = 0  # Answer OR ranked list
    answer_visible_count: int = 0
    top5_count: int = 0
    top10_count: int = 0
    total_tokens: int = 0
    rank_sum_if_present: int = 0
    rank_count: int = 0
    # Domain mention analysis
    answers_with_any_domain: int = 0  # Answers that mention ANY domain
    answers_with_target_when_any: int = 0  # When any domain mentioned, how many include target

    @property
    def answer_visible_pct(self) -> float:
        return (self.answer_visible_count / self.total_queries * 100) if self.total_queries else 0

    @property
    def top5_pct(self) -> float:
        return (self.top5_count / self.total_queries * 100) if self.total_queries else 0

    @property
    def top10_pct(self) -> float:
        return (self.top10_count / self.total_queries * 100) if self.total_queries else 0

    @property
    def avg_rank_if_present(self) -> float:
        return (self.rank_sum_if_present / self.rank_count) if self.rank_count else 0

    @property
    def avg_tokens_per_query(self) -> float:
        return (self.total_tokens / self.total_queries) if self.total_queries else 0

    @property
    def visibility_pct(self) -> float:
        """% where provider mentions or ranks the domain."""
        return (self.total_visibility_count / self.total_queries * 100) if self.total_queries else 0

    @property
    def any_domain_pct(self) -> float:
        """% of answers that mention any domain."""
        return (self.answers_with_any_domain / self.total_queries * 100) if self.total_queries else 0

    @property
    def target_share_when_any_pct(self) -> float:
        """When domains are mentioned, % that include target domain."""
        return (self.answers_with_target_when_any / self.answers_with_any_domain * 100) if self.answers_with_any_domain else 0


@dataclass
class AggregatedKPIs:
    """Aggregated KPIs across all queries."""
    openai_stats: ProviderStats = field(default_factory=lambda: ProviderStats("openai"))
    gemini_stats: ProviderStats = field(default_factory=lambda: ProviderStats("gemini"))
    # Answer visibility comparison (only counts queries where BOTH providers returned data)
    both_answer: int = 0
    only_openai_answer: int = 0
    only_gemini_answer: int = 0
    neither_answer: int = 0
    # Domain rank comparison (only counts queries where BOTH providers returned data)
    both_ranked: int = 0
    only_openai_ranked: int = 0
    only_gemini_ranked: int = 0
    neither_ranked: int = 0
    # Combined visibility (answer OR rank)
    any_visibility: int = 0
    no_visibility: int = 0
    # Error/skip tracking
    openai_failed: int = 0
    gemini_failed: int = 0
    queries_with_both_providers: int = 0
    # Domain mention analysis comparison
    both_any_domain: int = 0  # Both AIs mention some domain
    only_openai_any_domain: int = 0
    only_gemini_any_domain: int = 0
    neither_any_domain: int = 0  # Neither AI mentions any domain


class Aggregator:
    """Aggregates query results into KPIs."""

    def aggregate(self, openai: List[QueryResult], gemini: List[QueryResult]) -> AggregatedKPIs:
        kpis = AggregatedKPIs()
        for r in openai:
            kpis.openai_stats.total_queries += 1
            kpis.openai_stats.total_tokens += r.tokens_used
            if r.appears_in_answer or (r.rank_if_present and r.rank_if_present > 0):
                kpis.openai_stats.total_visibility_count += 1
            if r.appears_in_answer: kpis.openai_stats.answer_visible_count += 1
            if r.appears_in_top5: kpis.openai_stats.top5_count += 1
            if r.appears_in_top10: kpis.openai_stats.top10_count += 1
            if r.rank_if_present:
                kpis.openai_stats.rank_sum_if_present += r.rank_if_present
                kpis.openai_stats.rank_count += 1
            # Domain mention analysis
            if r.any_domain_in_answer:
                kpis.openai_stats.answers_with_any_domain += 1
                if r.appears_in_answer:
                    kpis.openai_stats.answers_with_target_when_any += 1
        for r in gemini:
            kpis.gemini_stats.total_queries += 1
            kpis.gemini_stats.total_tokens += r.tokens_used
            if r.appears_in_answer or (r.rank_if_present and r.rank_if_present > 0):
                kpis.gemini_stats.total_visibility_count += 1
            if r.appears_in_answer: kpis.gemini_stats.answer_visible_count += 1
            if r.appears_in_top5: kpis.gemini_stats.top5_count += 1
            if r.appears_in_top10: kpis.gemini_stats.top10_count += 1
            if r.rank_if_present:
                kpis.gemini_stats.rank_sum_if_present += r.rank_if_present
                kpis.gemini_stats.rank_count += 1
            # Domain mention analysis
            if r.any_domain_in_answer:
                kpis.gemini_stats.answers_with_any_domain += 1
                if r.appears_in_answer:
                    kpis.gemini_stats.answers_with_target_when_any += 1
        g_map = {r.query_id: r for r in gemini}
        o_ids = {r.query_id for r in openai}
        g_ids = {r.query_id for r in gemini}

        # Track failed queries (missing results)
        kpis.gemini_failed = len(o_ids - g_ids)
        kpis.openai_failed = len(g_ids - o_ids)

        for o in openai:
            g = g_map.get(o.query_id)

            # Only count comparison KPIs when BOTH providers have data
            if g is None:
                # Gemini failed for this query - still count overall visibility
                o_ans = o.appears_in_answer
                o_rank = bool(o.rank_if_present and o.rank_if_present > 0)
                if o_ans or o_rank:
                    kpis.any_visibility += 1
                else:
                    kpis.no_visibility += 1
                continue

            kpis.queries_with_both_providers += 1
            o_ans = o.appears_in_answer
            g_ans = g.appears_in_answer
            o_rank = bool(o.rank_if_present and o.rank_if_present > 0)
            g_rank = bool(g.rank_if_present and g.rank_if_present > 0)

            # Answer comparison (only when both have data)
            if o_ans and g_ans: kpis.both_answer += 1
            elif o_ans: kpis.only_openai_answer += 1
            elif g_ans: kpis.only_gemini_answer += 1
            else: kpis.neither_answer += 1

            # Rank comparison (only when both have data)
            if o_rank and g_rank: kpis.both_ranked += 1
            elif o_rank: kpis.only_openai_ranked += 1
            elif g_rank: kpis.only_gemini_ranked += 1
            else: kpis.neither_ranked += 1

            # Combined visibility (answer OR rank in either AI)
            o_any = o_ans or o_rank
            g_any = g_ans or g_rank
            if o_any or g_any:
                kpis.any_visibility += 1
            else:
                kpis.no_visibility += 1

            # Domain mention comparison (any domain in answer text)
            o_any_dom = o.any_domain_in_answer
            g_any_dom = g.any_domain_in_answer
            if o_any_dom and g_any_dom: kpis.both_any_domain += 1
            elif o_any_dom: kpis.only_openai_any_domain += 1
            elif g_any_dom: kpis.only_gemini_any_domain += 1
            else: kpis.neither_any_domain += 1
        return kpis

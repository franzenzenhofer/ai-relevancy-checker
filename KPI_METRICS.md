# KPI Metrics Captured

## A. Overall Presence (Any AI)
- `any_visibility`: queries where the domain is visible anywhere (answer text OR ranked list, any provider).
- `no_visibility`: queries with zero visibility across answers and ranked lists.

## B1. Provider Presence (OpenAI)
- `openai.total_queries`: queries with OpenAI results.
- `openai.total_visibility_count` / `openai.visibility_pct`: domain visible in answer OR ranked list for OpenAI.

## B2. Provider Presence (Gemini)
- `gemini.total_queries`: queries with Gemini results.
- `gemini.total_visibility_count` / `gemini.visibility_pct`: domain visible in answer OR ranked list for Gemini.

## C. Narrative Visibility (Answer Text)
- `openai.answer_visible_count` / `openai.answer_visible_pct`: domain mentioned in OpenAI answer text.
- `gemini.answer_visible_count` / `gemini.answer_visible_pct`: domain mentioned in Gemini answer text.
- Overlap (both-have-data): `both_answer`, `only_openai_answer`, `only_gemini_answer`, `neither_answer`.

## D. Structured Visibility (Top-10 Lists)
- `openai.top5_count` / `openai.top5_pct`: domain ranked #1-5 by OpenAI.
- `gemini.top5_count` / `gemini.top5_pct`: domain ranked #1-5 by Gemini.
- `openai.top10_count` / `openai.top10_pct`: domain ranked #1-10 by OpenAI.
- `gemini.top10_count` / `gemini.top10_pct`: domain ranked #1-10 by Gemini.
- Overlap (both-have-data): `both_ranked`, `only_openai_ranked`, `only_gemini_ranked`, `neither_ranked`.

## E. Ranking Position
- `openai.rank_sum_if_present`, `openai.rank_count`, `openai.avg_rank_if_present`: cumulative and average rank when present for OpenAI.
- `gemini.rank_sum_if_present`, `gemini.rank_count`, `gemini.avg_rank_if_present`: cumulative and average rank when present for Gemini.

## F. Domain Mentions in Answers
- `openai.answers_with_any_domain` / `openai.any_domain_pct`: OpenAI answers that mention any domain.
- `gemini.answers_with_any_domain` / `gemini.any_domain_pct`: Gemini answers that mention any domain.
- `openai.answers_with_target_when_any` / `openai.target_share_when_any_pct`: when OpenAI mentions domains, how often the target is included.
- `gemini.answers_with_target_when_any` / `gemini.target_share_when_any_pct`: when Gemini mentions domains, how often the target is included.
- Overlap (both-have-data): `both_any_domain`, `only_openai_any_domain`, `only_gemini_any_domain`, `neither_any_domain`.

## G. Data Completeness & Failures
- `queries_with_both_providers`: queries where both providers returned data.
- `openai_failed`: queries missing OpenAI results (Gemini present).
- `gemini_failed`: queries missing Gemini results (OpenAI present).

## H. API Usage / Cost Signals
- `openai.total_tokens`, `openai.avg_tokens_per_query`: token usage totals and per-query average for OpenAI.
- `gemini.total_tokens`, `gemini.avg_tokens_per_query`: token usage totals and per-query average for Gemini.
- Successful call counts per provider: `total_queries * 2` (answer + domains).
- Failed call estimate per provider: `failed_queries * 2` (informational).

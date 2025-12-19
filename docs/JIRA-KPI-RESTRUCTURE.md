# JIRA Ticket: KPI Dashboard Restructure

**Ticket ID**: AIR-2024-KPI-RESTRUCTURE
**Priority**: High
**Type**: Enhancement
**Reporter**: Franz Enzenhofer
**Created**: 2025-12-15

---

## Summary

Restructure the KPI dashboard to follow a logical flow from data quality → overall results → detailed breakdowns. Remove confusing "only X provider" comparison boxes and simplify the presentation while retaining critical insights.

---

## Current State (IS)

### Current Section Order:
| # | Section | KPI Boxes |
|---|---------|-----------|
| 0 | Run Completion Status | 3 boxes |
| 1 | Overall Visibility | 2 boxes |
| 2 | Answer Text | 2 individual + 4 comparison = 6 boxes |
| 3 | Domain Ranking | 2 individual + 4 comparison = 6 boxes |
| 4 | Ranking Position | 2 boxes |
| 5 | Data Quality & Failures | 3 boxes |
| 6 | API Usage | 4 boxes |
| 7 | Domain Mentions | 2+4+2 = 8 boxes |

**Total: ~34 KPI boxes** (overwhelming, redundant)

### Current Problems:
1. **Redundancy**: Section 0 and Section 5 both show data completeness
2. **Confusing comparisons**: "ONLY OPENAI" and "ONLY GEMINI" boxes don't provide clear action items
3. **Information overload**: 34 boxes is too many to digest
4. **Illogical order**: Data quality check is buried at Section 5
5. **Top-5 vs Top-10 split**: Adds complexity without clear value

---

## Target State (SHOULD)

### New Section Order:

| # | Section | KPI Boxes | Purpose |
|---|---------|-----------|---------|
| 0 | Data Completeness | 3 | Trust check: Can we use this data? |
| A | Overall Presence | 2 | Headline: Are we visible anywhere? |
| B | Provider Presence | 4 | Breakdown by provider (OpenAI vs Gemini) |
| C | Answer Text Visibility | 4 | Narrative: AI mentions us in answers? |
| D | Domain Ranking | 4 | Structured: AI ranks us in lists? |
| E | Ranking Position | 2 | Depth: Where do we rank when present? |
| F | Domain Citation Behavior | 4 | Context: Does AI cite sources at all? |
| G | API Usage | 2-3 | Cost: Token usage summary |

**Total: ~24-26 KPI boxes** (30% reduction)

---

## Detailed Specification

### Section 0: Data Completeness & Failures (WAS Section 0 + 5)

**KEEP:**
```
┌─────────────────┬─────────────────┬─────────────────┐
│ OpenAI SUCCESS  │ Gemini SUCCESS  │ TOTAL MISSING   │
│ 300/300 · 100%  │ 300/300 · 100%  │ 0/600           │
│ ↑ HIGH is good  │ ↑ HIGH is good  │ ↓ LOW is good   │
└─────────────────┴─────────────────┴─────────────────┘
```

**REMOVE:**
- Section 5 "Data Quality & Failures" (merged here)
- Separate "COMPLETE DATA" box (redundant with success counts)

**Rationale**: Data quality MUST come first. If data is incomplete, all other metrics are questionable.

---

### Section A: Overall Presence (WAS Section 1)

**KEEP:**
```
┌─────────────────────────┬─────────────────────────┐
│ VISIBLE (any AI)        │ NOT VISIBLE             │
│ 293/300 · 98%           │ 7/300 · 2%              │
│ ↑ HIGH is good          │ ↓ LOW is good           │
└─────────────────────────┴─────────────────────────┘
```

**Rationale**: This is THE headline number. "98% of queries have visibility" is the executive summary.

---

### Section B: Provider Presence (NEW - combines individual metrics)

**SHOULD:**
```
┌─────────────────────────┬─────────────────────────┐
│ OpenAI VISIBILITY       │ Gemini VISIBILITY       │
│ 283/300 · 94%           │ 264/300 · 88%           │
│ (answer OR ranked)      │ (answer OR ranked)      │
│ ↑ HIGH is good          │ ↑ HIGH is good          │
└─────────────────────────┴─────────────────────────┘
┌─────────────────────────┬─────────────────────────┐
│ BOTH VISIBLE            │ NEITHER VISIBLE         │
│ 254/300 · 85%           │ 7/300 · 2%              │
│ ↑ HIGH is good          │ ↓ LOW is good           │
└─────────────────────────┴─────────────────────────┘
```

**REMOVE:**
- No "ONLY OPENAI VISIBLE" box
- No "ONLY GEMINI VISIBLE" box

**Rationale**:
- Individual totals (94%, 88%) already show the gap
- "ONLY X" boxes are confusing - what action do you take?
- BOTH + NEITHER give the important story

---

### Section C: Answer Text Visibility (WAS Section 2)

**SHOULD:**
```
Individual:
┌─────────────────────────┬─────────────────────────┐
│ OpenAI MENTIONS         │ Gemini MENTIONS         │
│ 162/300 · 54%           │ 114/300 · 38%           │
│ in answer text          │ in answer text          │
│ ↑ HIGH is good          │ ↑ HIGH is good          │
└─────────────────────────┴─────────────────────────┘

Comparison (collapsed/small):
┌─────────────────────────┬─────────────────────────┐
│ BOTH mention            │ NEITHER mentions        │
│ 78/300 · 26%            │ 102/300 · 34%           │
│ ↑ HIGH is good          │ ↓ LOW is good           │
└─────────────────────────┴─────────────────────────┘
```

**REMOVE:**
- ~~ONLY OPENAI ANSWER~~ (confusing)
- ~~ONLY GEMINI ANSWER~~ (confusing)

---

### Section D: Domain Ranking in Top-10 Lists (WAS Section 3)

**SHOULD:**
```
Individual:
┌─────────────────────────┬─────────────────────────┐
│ OpenAI RANKS            │ Gemini RANKS            │
│ 281/300 · 94%           │ 264/300 · 88%           │
│ in top-10 list          │ in top-10 list          │
│ ↑ HIGH is good          │ ↑ HIGH is good          │
└─────────────────────────┴─────────────────────────┘

Comparison (collapsed/small):
┌─────────────────────────┬─────────────────────────┐
│ BOTH rank               │ NEITHER ranks           │
│ 254/300 · 85%           │ 12/300 · 4%             │
│ ↑ HIGH is good          │ ↓ LOW is good           │
└─────────────────────────┴─────────────────────────┘
```

**REMOVE:**
- ~~top5_count / top5_pct~~ (keep only top-10)
- ~~ONLY OPENAI RANKED~~
- ~~ONLY GEMINI RANKED~~

---

### Section E: Ranking Position (WAS Section 4)

**KEEP AS-IS:**
```
┌─────────────────────────┬─────────────────────────┐
│ OpenAI Avg Position     │ Gemini Avg Position     │
│ #1.8                    │ #2.1                    │
│ Based on 281/300        │ Based on 264/300        │
│ ↓ LOW is good           │ ↓ LOW is good           │
└─────────────────────────┴─────────────────────────┘
```

**Rationale**: Average position is crucial - being #1 vs #10 matters enormously.

---

### Section F: Domain Citation Behavior (WAS Section 7)

**SHOULD:**
```
Part A - Does AI cite ANY sources?
┌─────────────────────────┬─────────────────────────┐
│ OpenAI cites domains    │ Gemini cites domains    │
│ 89/300 · 30%            │ 67/300 · 22%            │
│ (any domain in answer)  │ (any domain in answer)  │
└─────────────────────────┴─────────────────────────┘

Part B - When citing, do they cite US?
┌─────────────────────────┬─────────────────────────┐
│ OpenAI: Our share       │ Gemini: Our share       │
│ 72/89 · 81%             │ 45/67 · 67%             │
│ ↑ HIGH is good          │ ↑ HIGH is good          │
└─────────────────────────┴─────────────────────────┘
```

**REMOVE:**
- ~~BOTH cite domains~~ (not actionable)
- ~~ONLY OPENAI cites~~
- ~~ONLY GEMINI cites~~
- ~~NEITHER cites~~ (maybe keep as context?)

---

### Section G: API Usage (WAS Section 6)

**SHOULD (simplified):**
```
┌─────────────────────────┬─────────────────────────┐
│ OpenAI Tokens           │ Gemini Tokens           │
│ 450,000 total           │ 380,000 total           │
│ 1,500 avg/query         │ 1,267 avg/query         │
└─────────────────────────┴─────────────────────────┘
```

**REMOVE:**
- Separate "Successful calls" boxes (redundant with Section 0)
- "Failed calls" box (already in Section 0)
- "Total Successful" combined box (just math)

---

## What We're Removing (RISK ASSESSMENT)

| Metric | Current Use | Risk of Removal | Decision |
|--------|-------------|-----------------|----------|
| `only_openai_answer` | Shows OpenAI-only wins | LOW - individual totals show gap | REMOVE |
| `only_gemini_answer` | Shows Gemini-only wins | LOW - individual totals show gap | REMOVE |
| `only_openai_ranked` | Shows OpenAI-only rankings | LOW - individual totals show gap | REMOVE |
| `only_gemini_ranked` | Shows Gemini-only rankings | LOW - individual totals show gap | REMOVE |
| `top5_count/pct` | Premium position signal | MEDIUM - top-5 is stronger signal | KEEP IN AVG RANK |
| `only_openai_any_domain` | Citation behavior diff | LOW - not actionable | REMOVE |
| `only_gemini_any_domain` | Citation behavior diff | LOW - not actionable | REMOVE |
| Duplicate data quality boxes | Redundancy | NONE - pure cleanup | REMOVE |

---

## Challenge: Are We Missing Critical Information?

### Challenge 1: Removing "ONLY X" boxes loses opportunity signals

**Argument**: "ONLY OPENAI" queries show where Gemini can be improved.

**Counter**:
- The GAP between individual provider numbers (94% vs 88%) already shows this
- Action is the same: "improve Gemini presence"
- Adding 4 extra boxes for "only X" creates visual noise

**Verdict**: ✅ SAFE TO REMOVE - information preserved in gap between totals

---

### Challenge 2: Removing Top-5 loses premium position signal

**Argument**: Being #1-5 is much more valuable than #6-10.

**Counter**:
- Average rank already captures this (#1.8 vs #5.2 tells the story)
- Adding top-5 breakdown doubles the ranking boxes

**Alternative**: Add top-5 count as sub-text in avg rank box:
```
OpenAI Avg Position: #1.8
"Based on 281 ranked (267 in top-5)"
```

**Verdict**: ⚠️ PARTIAL KEEP - embed in avg rank detail text

---

### Challenge 3: Removing "NEITHER cites" loses context

**Argument**: Knowing "neither AI cited any domain" shows generic answer patterns.

**Counter**: This is interesting context but not actionable.

**Alternative**: Keep as small text under citation section:
```
"Note: In 134 queries (45%), neither AI cited any sources."
```

**Verdict**: ⚠️ PARTIAL KEEP - as explanatory text, not KPI box

---

### Challenge 4: What about trend tracking over time?

**Current**: No trend data shown.

**Risk**: Simplified dashboard loses nothing here - we never had it.

**Future**: Consider adding trend arrows when comparing runs.

**Verdict**: ✅ NOT A REMOVAL RISK - future enhancement

---

## Implementation Plan

### Phase 1: Backend (aggregator.py)
- [ ] Keep all current calculations (don't break data)
- [ ] Add `total_visibility_count` to ProviderStats if not present
- [ ] Ensure `top5_count` still calculated for detail text

### Phase 2: Frontend (report_kpi.py)
- [ ] Reorder sections: 0 → A → B → C → D → E → F → G
- [ ] Remove "ONLY X" KPI boxes (keep calculations)
- [ ] Merge Section 5 into Section 0
- [ ] Simplify API Usage section
- [ ] Add top-5 count as sub-text in ranking position

### Phase 3: Testing
- [ ] Regenerate existing report, verify no data loss
- [ ] Compare old vs new report side-by-side
- [ ] Verify all numbers still add up

---

## Acceptance Criteria

1. ✅ KPI box count reduced from ~34 to ~24
2. ✅ Data completeness shown FIRST (Section 0)
3. ✅ No "ONLY X" comparison boxes
4. ✅ Top-5 info preserved in avg rank detail
5. ✅ All underlying calculations unchanged
6. ✅ Report still accurate (spot-check 5 queries)

---

## Final Structure Summary

```
┌─────────────────────────────────────────────────────────┐
│  0. DATA COMPLETENESS (3 boxes)                         │
│     OpenAI Success | Gemini Success | Total Missing     │
├─────────────────────────────────────────────────────────┤
│  A. OVERALL PRESENCE (2 boxes)                          │
│     Visible (any AI) | Not Visible                      │
├─────────────────────────────────────────────────────────┤
│  B. PROVIDER PRESENCE (4 boxes)                         │
│     OpenAI Visibility | Gemini Visibility               │
│     Both Visible | Neither Visible                      │
├─────────────────────────────────────────────────────────┤
│  C. ANSWER TEXT (4 boxes)                               │
│     OpenAI Mentions | Gemini Mentions                   │
│     Both Mention | Neither Mentions                     │
├─────────────────────────────────────────────────────────┤
│  D. DOMAIN RANKING (4 boxes)                            │
│     OpenAI Ranks | Gemini Ranks                         │
│     Both Rank | Neither Ranks                           │
├─────────────────────────────────────────────────────────┤
│  E. RANKING POSITION (2 boxes)                          │
│     OpenAI Avg #X (Y in top-5) | Gemini Avg #X          │
├─────────────────────────────────────────────────────────┤
│  F. CITATION BEHAVIOR (4 boxes)                         │
│     OpenAI Cites | Gemini Cites                         │
│     Our Share (OpenAI) | Our Share (Gemini)             │
├─────────────────────────────────────────────────────────┤
│  G. API USAGE (2 boxes)                                 │
│     OpenAI Tokens | Gemini Tokens                       │
└─────────────────────────────────────────────────────────┘

TOTAL: 25 boxes (down from 34)
```

---

## Appendix: Metrics Reference

### KEEP (in new structure)
- `queries_with_both_providers`
- `openai_failed`, `gemini_failed`
- `any_visibility`, `no_visibility`
- `openai.total_visibility_count`, `gemini.total_visibility_count`
- `openai.answer_visible_count`, `gemini.answer_visible_count`
- `both_answer`, `neither_answer`
- `openai.top10_count`, `gemini.top10_count`
- `both_ranked`, `neither_ranked`
- `openai.avg_rank_if_present`, `gemini.avg_rank_if_present`
- `openai.answers_with_any_domain`, `gemini.answers_with_any_domain`
- `openai.target_share_when_any_pct`, `gemini.target_share_when_any_pct`
- `openai.total_tokens`, `gemini.total_tokens`

### REMOVE (from display, keep in backend)
- `only_openai_answer`, `only_gemini_answer`
- `only_openai_ranked`, `only_gemini_ranked`
- `only_openai_any_domain`, `only_gemini_any_domain`
- `both_any_domain`, `neither_any_domain` (as full boxes)

### DEMOTE (to sub-text)
- `openai.top5_count`, `gemini.top5_count`

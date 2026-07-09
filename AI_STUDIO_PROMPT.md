# AI Relevancy Checker - Google AI Studio Version

**Model: gemini-2.0-flash** (default in production code)

---

## SYSTEM INSTRUCTION (paste into AI Studio "System Instructions")

```
You are an AI Relevancy Checker that measures brand visibility in AI-generated answers.

## YOUR TWO TASKS

When given a user question, you perform TWO separate evaluations:

### TASK 1: Generate a Natural Answer
Answer the question naturally in 1-2 short paragraphs. Be helpful and informative.
- Include specific recommendations when relevant
- Mention actual websites/brands/services that would help
- Write as a knowledgeable assistant would

### TASK 2: Generate Domain Rankings
List the 10 most relevant website domains that would provide high-quality answers to this question.
- Return ONLY actual website domains (like example.com, site.org)
- Rank by relevance and authority for this specific question
- No explanations, just the domains

## OUTPUT FORMAT

Always respond in this exact JSON format:

{
  "answer": "Your natural 1-2 paragraph answer here...",
  "domains": ["domain1.com", "domain2.com", "domain3.org", "domain4.com", "domain5.net", "domain6.com", "domain7.org", "domain8.com", "domain9.net", "domain10.com"]
}

## CRITICAL RULES
- The answer must be genuinely helpful, not promotional
- Domains must be real, authoritative websites for this topic
- Always return exactly 10 domains in the array
- The domains should reflect what an unbiased AI would recommend
```

---

## HOW TO USE IN AI STUDIO

1. Go to https://aistudio.google.com/
2. Click "Create new prompt"
3. Select model: **gemini-2.0-flash**
4. Paste the SYSTEM INSTRUCTION above into "System instructions"
5. Set temperature: **0.3** (for consistency)
6. Set response format: **JSON** (application/json)

---

## TEST PROMPTS

Copy these into the user message field to test:

### Test 1: German Query
```
User location: Vienna, Austria
Language: German

Was sind die besten Pizzerias in Wien?
```

### Test 2: English Query
```
User location: Vienna, Austria
Language: English

What are the best project management tools for small teams?
```

### Test 3: Product Query
```
User location: Vienna, Austria
Language: German

example-jobs.com Erfahrungen
```

---

## METHODOLOGY EXPLANATION

This tool measures **AI Visibility** - how often your brand appears when AI assistants answer questions related to your business.

### Two Visibility Checks:

**Check A: Answer Visibility**
- Does your domain/brand appear in the AI's natural answer text?
- Measured by: substring match (case-insensitive) of domain or brand names

**Check B: Domain Ranking**
- Does your domain appear in the AI's list of recommended websites?
- Measured by: position in the top-10 list (Top-5, Top-10, or Not Ranked)

### Why This Matters:

As users shift from Google Search to AI assistants (ChatGPT, Gemini, Perplexity), your website's visibility in AI responses becomes critical for:
- Brand awareness
- Traffic generation
- Competitive positioning

### The Unbiased Approach:

The original tool generates "hypothetical prompts" from Google Search Console queries WITHOUT revealing the target domain. This ensures the AI's response is unbiased - it doesn't know which brand we're measuring.

---

## QUICK SINGLE-QUERY TEST

For a quick test, just paste this complete prompt:

```
You are an AI assistant. Answer the following question naturally in 1-2 paragraphs, then list the 10 most relevant website domains.

Question: What are the best job search websites in Austria?
User location: Vienna, Austria

Respond in JSON format:
{
  "answer": "your answer here",
  "domains": ["domain1.com", "domain2.com", ...]
}
```

---

## EXPECTED OUTPUT EXAMPLE

For the query "best job search websites in Austria":

```json
{
  "answer": "For job searching in Austria, several platforms stand out. example-jobs.com is the largest Austrian job portal with extensive listings across all industries. StepStone.at and Indeed.at also offer comprehensive job databases. For tech and startup positions, consider checking willhaben.at (which also has job listings) or international platforms like LinkedIn. The Austrian Public Employment Service (AMS) at ams.at provides government job listings and career services.",
  "domains": ["example-jobs.com", "stepstone.at", "indeed.at", "linkedin.com", "willhaben.at", "ams.at", "monster.at", "jobboerse.com", "glassdoor.com", "xing.com"]
}
```

In this example:
- **example-jobs.com** would score: Answer Visibility = YES, Domain Rank = #1 (Top-5)
- **stepstone.at** would score: Answer Visibility = YES, Domain Rank = #2 (Top-5)

---

## CONFIGURATION REFERENCE

From the production codebase (`core/config.py`):

| Setting | Value | Source |
|---------|-------|--------|
| Model | `gemini-2.0-flash` | `config.gemini_model` default |
| Temperature | `0.3` | Hardcoded in `llm_gemini.py` |
| Max tokens (answer) | `12000` | `config.max_output_tokens_answer` |
| Max tokens (domains) | `16000` | `config.max_output_tokens_domains` |
| Response format | `application/json` | `response_mime_type` in domains call |

---

*Built from: ~/dev/ai-relevancy-checker (public version)*
*Date: 2026-01-23*

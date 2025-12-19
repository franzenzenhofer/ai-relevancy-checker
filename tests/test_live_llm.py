"""Live integration test for OpenAI + Gemini (requires real API keys).

This test hits the live LLM endpoints. It is skipped unless both
OPENAI_API_KEY and GEMINI_API_KEY are set in the environment.
"""
import os
import unittest
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
import sys
sys.path.append(str(repo_root))

from core.config import config  # noqa: E402
from core.prompt_generator import PromptGenerator  # noqa: E402
from core.gsc_query import QueryRecord  # noqa: E402
from core.llm_openai import OpenAIClient  # noqa: E402
from core.llm_gemini import GeminiClient  # noqa: E402
from core.relevancy_engine import RelevancyEngine  # noqa: E402


def _has_live_keys() -> bool:
    return bool(config.openai_api_key and config.gemini_api_key)


@unittest.skipUnless(_has_live_keys(), "Live LLM keys required")
class LiveLLMTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep token usage low for the test
        config.max_output_tokens_answer = 400
        config.max_output_tokens_domains = 200
        cls.openai = OpenAIClient()
        cls.gemini = GeminiClient()
        cls.gen = PromptGenerator()
        cls.engine = RelevancyEngine(config.domain, config.brand_names)

    def test_openai_and_gemini_visibility(self):
        query = "Reisepass verlängern"
        lang = self.gen.detect_language(query)
        # Avoid extra prompt-model call; use the deterministic template prompt
        record = QueryRecord(query_text=query, page_url="", country_code="AT",
                             clicks=0, impressions=0, ctr=0.0, position=0.0)
        packet = self.gen.create_packets([record], prompt_client=None)[0]
        ctx = self.gen.get_system_context(lang)

        o_ans = self.openai.generate_answer(packet.hypothetical_prompt, ctx)
        self.assertTrue(len(o_ans.text) > 10)
        o_dom = self.openai.generate_relevant_domains(packet.hypothetical_prompt, ctx)
        self.assertTrue(len(o_dom.text) > 0)
        o_res = self.engine.check_visibility(packet, o_ans, o_dom, ctx, packet.hypothetical_prompt)
        self.assertEqual(o_res.provider, "openai")
        self.assertIsNotNone(o_res.domains_list)

        g_ans = self.gemini.generate_answer(packet.hypothetical_prompt, ctx)
        self.assertTrue(len(g_ans.text) > 10)
        g_dom = self.gemini.generate_relevant_domains(packet.hypothetical_prompt, ctx)
        self.assertTrue(len(g_dom.text) > 0)
        g_res = self.engine.check_visibility(packet, g_ans, g_dom, ctx, packet.hypothetical_prompt)
        self.assertEqual(g_res.provider, "gemini")
        self.assertIsNotNone(g_res.domains_list)


if __name__ == "__main__":
    unittest.main()

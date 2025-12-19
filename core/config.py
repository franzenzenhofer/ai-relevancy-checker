"""Configuration for AI Relevancy Checker - single source of truth (no hidden defaults)."""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config_loader import get_env_key, load_dotenv

load_dotenv()


@dataclass
class Config:
    """Central configuration for AI Relevancy Checker."""

    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    exports_dir: Path = field(init=False)
    reports_dir: Path = field(init=False)
    parent_dir: Path = field(init=False)
    client_secret_path: Path = field(init=False)
    token_path: Path = field(init=False)

    # Target domain configuration - MUST be set via config file
    site_url: str = ""
    domain: str = ""
    brand_names: List[str] = field(default_factory=list)

    # Location configuration - MUST be set via config file
    user_city: str = ""
    user_city_en: str = ""
    user_country: str = ""
    user_country_en: str = ""

    # Language detection indicators - configurable per locale
    language_indicators: Dict[str, List[str]] = field(default_factory=dict)
    default_language: Optional[str] = None
    force_language: Optional[str] = field(default_factory=lambda: os.getenv("FORCE_LANGUAGE"))

    # GSC configuration
    gsc_scopes: List[str] = field(
        default_factory=lambda: ["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    gsc_row_limit: int = 25000
    gsc_dimensions: List[str] = field(default_factory=lambda: ["query", "page", "country"])
    client_secret_path_override: Optional[str] = None
    token_path_override: Optional[str] = None

    # API keys (from environment)
    openai_api_key: Optional[str] = field(default=None)
    gemini_api_key: Optional[str] = field(default=None)

    # Models - sensible defaults, overridable via config
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_prompt_model: str = field(default_factory=lambda: os.getenv("OPENAI_PROMPT_MODEL", "gpt-4o-mini"))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

    # Token limits
    max_output_tokens_answer: int = 12000
    max_output_tokens_domains: int = 16000

    # Runtime settings
    max_queries: int = 100
    max_query_workers: int = 50  # Concurrent queries
    max_provider_workers: int = 2  # Per-query concurrency (answer + domains)
    prompt_concurrency: int = 8  # Concurrency for prompt generation
    request_delay: float = 0.0
    gsc_days: int = 90
    prompt_mode: str = field(default_factory=lambda: os.getenv("PROMPT_MODE", "ai"))
    default_providers: List[str] = field(default_factory=lambda: ["openai", "gemini"])

    # Rate limits / resilience
    llm_timeout_seconds: int = 120
    llm_retries: int = 2
    llm_retry_delay_seconds: int = 5
    stuck_timeout_seconds: int = 300
    debug_default_clicks: int = 0
    debug_default_impressions: int = 0
    debug_default_page_url: Optional[str] = None

    # Prompt / text configuration (single source of truth)
    domain_list_suffix: str = (
        "Based on this question, list the 10 most relevant website domains "
        "that are likely to have high-quality answers. "
        "Return ONLY the domains in a comma-separated list, no explanations. "
        "Example format: example.com, another.org, third.net"
    )
    openai_domain_json_prompt: str = (
        "List exactly 10 relevant WEBSITE DOMAINS that would provide high-quality answers. "
        "Return ONLY a JSON object with actual website domain names (like example.com, site.org). "
        "Format: {\"domains\": [\"domain1.tld\", \"domain2.tld\", ...]}"
    )
    gemini_domain_json_prompt: str = (
        "List 10 relevant website domains for this question. "
        "Return JSON only: {\"domains\": [\"domain1.com\", \"domain2.org\", ...]}"
    )
    prompt_system_template: str = (
        "You convert a Google search query into a natural AI assistant prompt. "
        "The user is in {location_clause}. "
        "CRITICAL: The prompt MUST be ABOUT the exact search term! "
        "If they searched for a product name like 'ProductX', ask about ProductX. "
        "If they searched for a symptom like 'headache', ask about headaches. "
        "Keep the SAME topic/product/brand from the search query. "
        "Write naturally - casual, direct. Include location context where natural. "
        "Max 25 words. ALWAYS include the search term's topic/product in your output."
    )
    prompt_user_template: str = (
        "Google search query: \"{query}\"\n"
        "User location: {location_clause}\n"
        "Language: {language_hint}\n\n"
        "Convert this search query into a natural AI assistant prompt. "
        "The prompt MUST be about '{query}' - keep the same topic/product/brand! "
        "Write as a real person would ask."
    )
    answer_system_contexts: Dict[str, str] = field(
        default_factory=lambda: {
            "de": "Du bist ein hilfreicher Assistent. Antworte in 1-2 kurzen Absätzen.",
            "en": "You are a helpful assistant. Answer in 1-2 short paragraphs.",
        }
    )

    # Report text configuration (overridable)
    report_text: Dict[str, Any] = field(
        default_factory=lambda: {
            "title_prefix": "AI Relevancy Report",
            "summary_heading": "Summary KPIs",
            "methodology_heading": "Methodology - Full Transparency",
            "detail_heading": "Detailed Results (Ordered by Clicks)",
            "quick_filters_label": "Quick Filters:",
            "sort_label": "Sort by:",
            "display_label": "Display:",
            "any_vis_label": "Any Visibility:",
            "openai_answer_label": "OpenAI Answer:",
            "openai_domain_label": "OpenAI Domain:",
            "gemini_answer_label": "Gemini Answer:",
            "gemini_domain_label": "Gemini Domain:",
            "filter_options": {
                "all": "All",
                "yes": "✓ Visible (any AI)",
                "no": "✗ NOT Visible (nowhere)",
                "in_answer_yes": "✓ In Answer",
                "in_answer_no": "✗ NOT in Answer",
                "domain_top5": "Top 5",
                "domain_top10": "Top 6-10",
                "domain_ranked": "Any Rank",
                "domain_none": "Not Ranked",
            },
            "quick_filter_groups": {
                "successes": "🎯 Successes",
                "problems": "⚠️ Problems",
                "opportunities": "🔍 Opportunities",
            },
            "quick_filter_labels": {
                "both_answer": "Both AI mention in answer",
                "both_top5": "Both AI rank Top-5",
                "full_success": "Full success (answer + top5 both)",
                "neither_answer": "Neither AI mentions in answer",
                "neither_ranked": "Neither AI ranks domain",
                "full_fail": "Full fail (no answer, no rank)",
                "openai_only_answer": "Only OpenAI in answer",
                "gemini_only_answer": "Only Gemini in answer",
                "openai_only_ranked": "Only OpenAI ranks",
                "gemini_only_ranked": "Only Gemini ranks",
            },
            "buttons": {
                "expand_all": "Expand all",
                "collapse_all": "Collapse all",
                "reset_filters": "Reset filters",
            },
            "table_headers": {
                "query": "Query",
                "gsc_clicks": "GSC Clicks",
                "any_visibility": "Any Visibility?",
                "prompt": "Prompt",
                "answer": "Answer",
                "in_answer": "In Answer?",
                "domains": "Domains",
                "rank": "Rank",
                "checked": "Checked",
                "no_data": "No data",
            },
        }
    )
    report_truncate_length: int = 250
    domain_match_strategy: str = "exact"  # exact | subdomain

    # State tracking
    _config_loaded: bool = field(default=False, repr=False)
    _config_path: Optional[Path] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.exports_dir = self.base_dir / "exports"
        self.reports_dir = self.base_dir / "reports"
        self._refresh_paths()
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "state").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "state" / "prompts").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "results").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "logs").mkdir(parents=True, exist_ok=True)

        if self.openai_api_key is None:
            self.openai_api_key = get_env_key("OPENAI_API_KEY")
        if self.gemini_api_key is None:
            self.gemini_api_key = get_env_key("GEMINI_API_KEY")
        if self.max_query_workers < 1:
            self.max_query_workers = 1
        if self.max_provider_workers < 1:
            self.max_provider_workers = 1
        if self.prompt_concurrency < 1:
            self.prompt_concurrency = 1

    def get_export_path(self, filename: str) -> Path:
        return self.exports_dir / filename

    def get_report_path(self, filename: str) -> Path:
        return self.reports_dir / filename

    def validate(self) -> None:
        """Validate that required config values are set."""
        errors = []
        if not self.site_url:
            errors.append("site_url is required")
        if not self.domain:
            errors.append("domain is required")
        if not self.brand_names:
            errors.append("brand_names is required (at least one)")
        if not self.user_country and not self.user_country_en:
            errors.append("user_country or user_country_en is required")
        if not self.default_providers:
            errors.append("default_providers is required (at least one provider)")
        # MANDATORY: prompt_mode MUST be "ai" - NO FALLBACKS!
        if self.prompt_mode != "ai":
            errors.append(f"FATAL: prompt_mode must be 'ai', got '{self.prompt_mode}'. NO TEMPLATE FALLBACKS!")
        if self.max_queries <= 0:
            errors.append("max_queries must be > 0")
        if self.max_query_workers <= 0:
            errors.append("max_query_workers must be > 0")
        if self.max_provider_workers <= 0:
            errors.append("max_provider_workers must be > 0")
        if self.prompt_concurrency <= 0:
            errors.append("prompt_concurrency must be > 0")
        if self.gsc_days <= 0:
            errors.append("gsc_days must be > 0")
        if self.gsc_row_limit <= 0:
            errors.append("gsc_row_limit must be > 0")
        if not self.gsc_dimensions:
            errors.append("gsc_dimensions must contain at least one dimension")
        elif self.gsc_dimensions[:3] != ["query", "page", "country"]:
            errors.append("gsc_dimensions must start with ['query', 'page', 'country'] for parser compatibility")
        if self.llm_timeout_seconds <= 0:
            errors.append("llm_timeout_seconds must be > 0")
        if self.llm_retries < 0:
            errors.append("llm_retries must be >= 0")
        if self.llm_retry_delay_seconds < 0:
            errors.append("llm_retry_delay_seconds must be >= 0")
        if self.stuck_timeout_seconds <= 0:
            errors.append("stuck_timeout_seconds must be > 0")
        if not self.language_indicators and not self.force_language and not self.default_language:
            errors.append("language_indicators required unless force_language or default_language is set")
        if self.domain_match_strategy not in ("exact", "subdomain"):
            errors.append("domain_match_strategy must be 'exact' or 'subdomain'")
        if self.report_truncate_length <= 0:
            errors.append("report_truncate_length must be > 0")
        if not self.report_text.get("title_prefix"):
            errors.append("report_text.title_prefix must be set")
        if not self.answer_system_contexts:
            errors.append("answer_system_contexts must be provided for at least one language")
        if self.debug_default_clicks < 0 or self.debug_default_impressions < 0:
            errors.append("debug defaults (clicks/impressions) must be >= 0")
        if errors:
            raise ValueError(f"Config validation failed: {'; '.join(errors)}")

    def apply_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply overrides from CLI or config file."""
        allowed = {
            "site_url", "domain", "brand_names", "user_city", "user_city_en",
            "user_country", "user_country_en", "openai_model", "openai_prompt_model",
            "gemini_model", "request_delay", "prompt_mode",
            "default_providers", "gsc_days", "max_output_tokens_answer", "max_output_tokens_domains",
            "force_language", "language_indicators", "max_queries", "gsc_row_limit",
            "gsc_dimensions", "client_secret_path_override", "token_path_override",
            "llm_timeout_seconds", "llm_retries", "llm_retry_delay_seconds", "stuck_timeout_seconds",
            "domain_list_suffix", "openai_domain_json_prompt", "gemini_domain_json_prompt",
            "prompt_system_template", "prompt_user_template", "answer_system_contexts", "report_text", "report_truncate_length",
            "domain_match_strategy", "default_language",
            "debug_default_clicks", "debug_default_impressions", "debug_default_page_url",
            "max_query_workers", "max_provider_workers", "prompt_concurrency",
        }
        for key, value in overrides.items():
            if key.startswith("_"):
                # Allow metadata keys like _comment without failing
                continue
            if key not in allowed:
                raise ValueError(f"Unknown config key: {key}")
            if key in {"brand_names", "default_providers"} and isinstance(value, str):
                value = [v.strip() for v in value.split(",") if v.strip()]
            setattr(self, key, value)
        self._refresh_paths()

    def load_from_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from JSON config file."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("Config file must contain a JSON object")
        self.apply_overrides(data)
        self._config_loaded = True
        self._config_path = path
        return data

    def _refresh_paths(self) -> None:
        """Refresh dependent paths when overrides change."""
        self.parent_dir = self.base_dir.parent
        self.client_secret_path = (
            Path(self.client_secret_path_override).expanduser().resolve()
            if self.client_secret_path_override
            else self.parent_dir / "client_secret.json"
        )
        self.token_path = (
            Path(self.token_path_override).expanduser().resolve()
            if self.token_path_override
            else self.parent_dir / "token.json"
        )


# Global config instance - must be loaded via load_from_file() before use
config = Config()


def load_config(config_path: str) -> Config:
    """Load config from file path. Call this before using config."""
    path = Path(config_path).resolve()
    config.load_from_file(path)
    config.validate()
    return config


def get_config() -> Config:
    """Get the loaded config. Raises if not loaded."""
    if not config._config_loaded:
        raise RuntimeError(
            "Config not loaded. Use --config to specify a config file, "
            "e.g.: python run.py --config configs/mysite.config.json"
        )
    return config

"""Web run manager - orchestrates AI relevancy checks from uploaded data.

Bridges web uploads to the existing core engine.
Handles per-session API keys (never persisted to disk).
Thread-safe: uses a lock to serialize config access.
"""
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.gsc_query import QueryRecord

# Serialize access to the global config singleton
_config_lock = threading.Lock()


@dataclass
class WebRunConfig:
    """Configuration for a web-initiated run."""
    domain: str
    brand_names: List[str]
    openai_api_key: str = ""
    gemini_api_key: str = ""
    providers: List[str] = field(default_factory=lambda: ["openai", "gemini"])
    max_queries: int = 100
    user_city: str = ""
    user_city_en: str = ""
    user_country: str = ""
    user_country_en: str = ""
    default_language: str = "en"


@dataclass
class RunProgress:
    """Live progress for a running evaluation."""
    run_id: str
    status: str = "pending"
    total_queries: int = 0
    completed_queries: int = 0
    current_query: str = ""
    message: str = ""
    errors: List[str] = field(default_factory=list)
    report_html: str = ""
    csv_data: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    detected_columns: Optional[Dict] = None
    warnings: List[str] = field(default_factory=list)


# In-memory run storage
_runs: Dict[str, RunProgress] = {}
_run_lock = threading.Lock()

# Cleanup threshold: remove completed runs older than this (seconds)
_CLEANUP_AGE = 3600


def create_run() -> str:
    """Create a new run and return its ID."""
    run_id = str(uuid.uuid4())[:8]
    _cleanup_old_runs()
    with _run_lock:
        _runs[run_id] = RunProgress(
            run_id=run_id,
            started_at=datetime.now().isoformat(),
        )
    return run_id


def get_run(run_id: str) -> Optional[RunProgress]:
    with _run_lock:
        return _runs.get(run_id)


def update_run(run_id: str, **kwargs) -> None:
    with _run_lock:
        run = _runs.get(run_id)
        if run:
            for k, v in kwargs.items():
                setattr(run, k, v)


def is_run_active() -> bool:
    """Check if any run is currently executing (holding the config lock)."""
    acquired = _config_lock.acquire(blocking=False)
    if acquired:
        _config_lock.release()
        return False
    return True


def _cleanup_old_runs() -> None:
    """Remove completed/failed runs older than threshold."""
    now = datetime.now()
    to_remove = []
    with _run_lock:
        for rid, run in _runs.items():
            if run.status in ("completed", "failed") and run.completed_at:
                try:
                    completed = datetime.fromisoformat(run.completed_at)
                    if (now - completed).total_seconds() > _CLEANUP_AGE:
                        to_remove.append(rid)
                except (ValueError, TypeError):
                    pass
        for rid in to_remove:
            del _runs[rid]


def execute_run(
    run_id: str,
    records: List[QueryRecord],
    web_config: WebRunConfig,
) -> None:
    """Execute the full evaluation pipeline in the current thread.

    Called from a background thread by the server.
    Uses _config_lock to serialize global config access.
    """
    try:
        update_run(run_id, status="initializing", message="Configuring...")

        # Acquire config lock for the entire run to prevent concurrent config mutation
        with _config_lock:
            _run_with_config(run_id, records, web_config)

    except Exception as e:
        update_run(
            run_id, status="failed",
            message=f"Run failed: {str(e)}",
            errors=[str(e)],
            completed_at=datetime.now().isoformat(),
        )


def _run_with_config(
    run_id: str,
    records: List[QueryRecord],
    web_config: WebRunConfig,
) -> None:
    """Inner run logic executed while holding the config lock."""
    from core.config import config
    from core.llm_openai import OpenAIClient
    from core.llm_gemini import GeminiClient
    from core.prompt_generator import PromptGenerator
    from core.relevancy_engine import RelevancyEngine
    from core.aggregator import Aggregator
    from core.report_generator import ReportGenerator
    from core.csv_exporter import CSVExporter
    from core.run_state import RunState, RunStateManager
    from core.result_store import ResultStore
    from core.runner_checks import run_all_checks
    from core.healthcheck import check_llms
    from core.prompt_cache import PromptCache
    from core.logger import init_logger

    # Configure global config for this run
    _configure_for_run(web_config)

    base_dir = config.base_dir
    state_mgr = RunStateManager(base_dir / "state")
    store = ResultStore(base_dir / "results")

    # Determine providers
    providers = []
    if web_config.openai_api_key and "openai" in web_config.providers:
        providers.append("openai")
    if web_config.gemini_api_key and "gemini" in web_config.providers:
        providers.append("gemini")

    if not providers:
        update_run(run_id, status="failed", message="No valid API keys provided")
        return

    # Init LLM clients with user-provided keys
    update_run(run_id, status="initializing", message="Initializing AI providers...")
    openai_client = None
    gemini_client = None
    prompt_client = None

    try:
        if "openai" in providers:
            openai_client = OpenAIClient(api_key=web_config.openai_api_key)
            prompt_client = openai_client
        if "gemini" in providers:
            gemini_client = GeminiClient(api_key=web_config.gemini_api_key)
        if not prompt_client and web_config.openai_api_key:
            prompt_client = OpenAIClient(api_key=web_config.openai_api_key)
    except Exception as e:
        update_run(run_id, status="failed", message=f"Failed to initialize AI client: {e}")
        return

    if not prompt_client:
        update_run(
            run_id, status="failed",
            message="OpenAI API key required for prompt generation (even when using Gemini only)",
        )
        return

    # Healthcheck
    update_run(run_id, status="initializing", message="Checking API connectivity...")
    try:
        ok, msg = check_llms(providers, openai_client, gemini_client)
    except Exception as e:
        update_run(run_id, status="failed", message=f"API key validation error: {e}")
        return

    if not ok:
        update_run(run_id, status="failed", message=f"API healthcheck failed: {msg}")
        return

    update_run(run_id, message="API keys verified")

    # Limit and process records
    records = records[:web_config.max_queries]
    total = len(records)
    update_run(run_id, total_queries=total)

    # Generate prompts
    update_run(run_id, status="generating_prompts", message=f"Generating AI prompts for {total} queries...")
    gen = PromptGenerator()
    engine = RelevancyEngine(config.domain, config.brand_names)
    cache = PromptCache(base_dir / "state" / "prompts")

    state = RunState.create_new(
        config.domain, total, total, providers=providers,
        cli_command=f"web-run:{run_id}",
    )
    state_mgr.save(state)

    def on_prompt_progress(pkts):
        update_run(run_id, message=f"Generated {len(pkts)}/{total} prompts...")

    packets = gen.create_packets(
        records, prompt_client,
        start_query_id=0,
        on_progress=on_prompt_progress,
        progress_interval=5,
    )
    cache.save(state.run_id, packets)
    state.total_queries = len(packets)
    state_mgr.save(state)

    # Initialize logger
    init_logger(base_dir / "logs", state.run_id)

    # Run evaluations with progress callback
    update_run(
        run_id, status="evaluating",
        message=f"Evaluating {len(packets)} queries with {', '.join(providers)}...",
        total_queries=len(packets), completed_queries=0,
    )

    def on_eval_progress(completed, total_q, query_text):
        update_run(
            run_id,
            completed_queries=completed,
            message=f"[{completed}/{total_q}] {query_text[:50]}",
        )

    openai_res, gemini_res = run_all_checks(
        packets, openai_client, gemini_client, engine, gen,
        state, state_mgr, store, providers, debug=False,
        on_progress=on_eval_progress,
    )

    state_mgr.mark_completed(state)
    openai_res, gemini_res = store.load_all_results(state.run_id)

    # Generate report
    update_run(run_id, status="reporting", message="Generating report...")
    kpis = Aggregator().aggregate(openai_res, gemini_res)
    lang = config.force_language or config.default_language or "en"
    ctx = gen.get_system_context(lang)
    report_gen = ReportGenerator(
        config.domain, run_id=state.run_id, offset=0,
        max_queries=len(packets), cli_command=f"web-run:{run_id}",
    )
    html = report_gen.generate(openai_res, gemini_res, kpis, ctx)

    # Save report to disk
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_{config.domain}_{state.run_id}_{ts}.html"
    report_path = config.get_report_path(report_filename)
    report_path.write_text(html, encoding="utf-8")

    # Generate CSV
    csv_exporter = CSVExporter()
    csv_path = csv_exporter.export(openai_res, gemini_res, run_id=state.run_id)
    csv_data = csv_path.read_text(encoding="utf-8") if csv_path and csv_path.exists() else ""

    # Build summary
    o, g = kpis.openai_stats, kpis.gemini_stats
    summary = (
        f"OpenAI: {o.answer_visible_pct:.0f}% answer, {o.top5_pct:.0f}% top-5 | "
        f"Gemini: {g.answer_visible_pct:.0f}% answer, {g.top5_pct:.0f}% top-5"
    )

    update_run(
        run_id, status="completed",
        message=summary,
        completed_queries=len(packets),
        report_html=html,
        csv_data=csv_data,
        completed_at=datetime.now().isoformat(),
    )


def _configure_for_run(web_config: WebRunConfig) -> None:
    """Configure the global config singleton for this run.

    MUST be called while holding _config_lock.
    """
    from core.config import config

    clean_domain = web_config.domain.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    site_url = f"https://www.{clean_domain}/" if "://" not in web_config.domain else web_config.domain

    overrides = {
        "site_url": site_url,
        "domain": clean_domain,
        "brand_names": web_config.brand_names,
        "prompt_mode": "ai",
        "default_providers": web_config.providers,
        "default_language": web_config.default_language or "en",
        "user_city": web_config.user_city or "",
        "user_city_en": web_config.user_city_en or web_config.user_city or "",
        "user_country": web_config.user_country or "",
        "user_country_en": web_config.user_country_en or web_config.user_country or "Global",
        "force_language": web_config.default_language or "en",
        "answer_system_contexts": {
            "en": "You are a helpful assistant. Answer in 1-2 short paragraphs.",
            "de": "Du bist ein hilfreicher Assistent. Antworte in 1-2 kurzen Absätzen.",
            "fr": "Tu es un assistant utile. Réponds en 1-2 courts paragraphes.",
            "es": "Eres un asistente útil. Responde en 1-2 párrafos cortos.",
            "it": "Sei un assistente utile. Rispondi in 1-2 brevi paragrafi.",
            "pt": "Você é um assistente útil. Responda em 1-2 parágrafos curtos.",
            "nl": "Je bent een behulpzame assistent. Antwoord in 1-2 korte alinea's.",
            "ja": "あなたは役に立つアシスタントです。1-2段落で簡潔に答えてください。",
        },
    }

    config.openai_api_key = web_config.openai_api_key or config.openai_api_key
    config.gemini_api_key = web_config.gemini_api_key or config.gemini_api_key

    config.apply_overrides(overrides)
    config._config_loaded = True

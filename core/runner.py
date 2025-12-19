"""Core runner logic for AI Relevancy Checker."""
from datetime import datetime, timedelta
from typing import List, Tuple

from .config import config
from .gsc_client import GSCClient
from .gsc_query import QueryRecord
from .llm_client import OpenAIClient, GeminiClient
from .prompt_generator import PromptGenerator, PromptPacket
from .prompt_cache import PromptCache
from .relevancy_engine import RelevancyEngine
from .aggregator import Aggregator
from .report_generator import ReportGenerator
from .csv_exporter import CSVExporter
from .run_state import RunState, RunStateManager
from .result_store import ResultStore
from .runner_checks import run_all_checks
from .logger import init_logger
from .healthcheck import check_llms


def _init_clients(providers: List[str], use_prompt_client: bool = True) -> Tuple[OpenAIClient | None, GeminiClient | None, OpenAIClient | None]:
    """Initialize only the requested LLM clients."""
    prompt_client = OpenAIClient() if use_prompt_client and config.prompt_mode == "ai" else None
    openai_client = prompt_client if ("openai" in providers and prompt_client) else None
    if "openai" in providers and openai_client is None:
        openai_client = OpenAIClient()
    gemini_client = GeminiClient() if "gemini" in providers else None
    return openai_client, gemini_client, prompt_client


def run_new(max_queries: int, days: int, state_mgr: RunStateManager, store: ResultStore,
            providers: List[str], debug: bool = False, offset: int = 0, desktop: bool = False,
            output_name: str = None, cli_command: str = "", generate_presentation: bool = False) -> int:
    """Run a new evaluation with optional offset for continuation."""
    print("\n[1/5] Initializing...")
    gsc = GSCClient()
    openai, gemini, prompt_client = _init_clients(providers)
    print(f"Pinging API keys for: {', '.join(providers)}...")
    ok, msg = check_llms(providers, openai, gemini)
    if not ok:
        print(f"❌ HEALTHCHECK FAILED: {msg}")
        print("ABORTING - fix API keys before running!")
        return 1
    print(f"✓ API healthcheck PASSED - all providers reachable")
    gen = PromptGenerator()
    engine = RelevancyEngine(config.domain, config.brand_names)
    cache = PromptCache(config.base_dir / "state" / "prompts")

    print("\n[2/5] Fetching GSC data...")
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    # Fetch enough records to cover offset + max_queries
    fetch_count = offset + max_queries
    records = gsc.get_top_queries(config.site_url, start, end, fetch_count)
    if not records:
        print("ERROR: No queries found")
        return 1

    # Apply offset - skip first N records
    if offset > 0:
        if offset >= len(records):
            print(f"ERROR: Offset {offset} exceeds available queries ({len(records)})")
            return 1
        records = records[offset:]
        print(f"Skipped first {offset} queries, processing from #{offset + 1}")

    # Limit to max_queries after offset
    records = records[:max_queries]

    print("\n[3/5] Generating AI prompts...")
    state = RunState.create_new(config.domain, max_queries, len(records), providers=providers, cli_command=cli_command)
    state_mgr.save(state)
    prompt_source = prompt_client if config.prompt_mode == "ai" else None
    packets = gen.create_packets(
        records,
        prompt_source,
        start_query_id=0,
        on_progress=lambda pkts: cache.save(state.run_id, pkts),
    )
    cache.save(state.run_id, packets)
    state.total_queries = len(packets)
    state_mgr.save(state)
    print(f"Run ID: {state.run_id} | Providers: {', '.join(providers)}")

    # Initialize logger for this run
    init_logger(config.base_dir / "logs", state.run_id)

    print("\n[4/5] Running evaluations...")
    openai_res, gemini_res = run_all_checks(
        packets, openai, gemini, engine, gen, state, state_mgr, store, providers, debug=debug
    )
    state_mgr.mark_completed(state)
    openai_res, gemini_res = store.load_all_results(state.run_id)
    return generate_report(openai_res, gemini_res, state.run_id, offset=offset, max_queries=len(packets), desktop=desktop, output_name=output_name, cli_command=cli_command, generate_presentation=generate_presentation)


def run_add_to_existing(run_id: str, max_queries: int, days: int, state_mgr: RunStateManager,
                        store: ResultStore, providers: List[str], debug: bool = False, offset: int = 0, desktop: bool = False,
                        output_name: str = None, cli_command: str = "", generate_presentation: bool = False) -> int:
    """Add more queries to an existing run, accumulating results."""
    print("\n[1/5] Initializing...")
    gsc = GSCClient()
    openai, gemini, prompt_client = _init_clients(providers)
    print(f"Pinging API keys for: {', '.join(providers)}...")
    ok, msg = check_llms(providers, openai, gemini)
    if not ok:
        print(f"❌ HEALTHCHECK FAILED: {msg}")
        print("ABORTING - fix API keys before running!")
        return 1
    print(f"✓ API healthcheck PASSED - all providers reachable")
    gen = PromptGenerator()
    engine = RelevancyEngine(config.domain, config.brand_names)
    cache = PromptCache(config.base_dir / "state" / "prompts")

    existing_packets = cache.load(run_id)
    existing_openai, existing_gemini = store.load_all_results(run_id)
    existing_ids = {r.query_id for r in (existing_openai + existing_gemini)}
    max_packet_id = max((p.query_id for p in existing_packets), default=-1)
    max_result_id = max(existing_ids) if existing_ids else -1
    next_query_id = max(max_packet_id, max_result_id) + 1
    base_count = max(len(existing_packets), len(existing_ids))
    print(f"Loaded {base_count} existing queries from run {run_id}")

    print("\n[2/5] Fetching GSC data...")
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    fetch_count = offset + max_queries
    records = gsc.get_top_queries(config.site_url, start, end, fetch_count)
    if not records:
        print("ERROR: No queries found")
        return 1

    # Apply offset
    if offset > 0:
        if offset >= len(records):
            print(f"ERROR: Offset {offset} exceeds available queries ({len(records)})")
            return 1
        records = records[offset:]
        print(f"Skipped first {offset} queries, processing from #{offset + 1}")

    records = records[:max_queries]

    print("\n[3/5] Generating AI prompts...")
    prompt_source = prompt_client if config.prompt_mode == "ai" else None
    new_packets = gen.create_packets(
        records,
        prompt_source,
        start_query_id=next_query_id,
        on_progress=lambda pkts: cache.save(run_id, existing_packets + pkts),
    )
    packets = existing_packets + new_packets
    cache.save(run_id, packets)

    # Load or create state
    state = state_mgr.load(run_id)
    if not state:
        state = RunState.create_new(config.domain, max_queries, len(packets), providers=providers, cli_command=cli_command)
        state.run_id = run_id
    else:
        state.cli_command = cli_command  # Update CLI command for existing runs
    state.total_queries = len(packets)
    state.providers = providers
    state_mgr.save(state)
    print(f"Run ID: {run_id} (adding {len(new_packets)} queries, total: {state.total_queries})")

    # Initialize logger
    init_logger(config.base_dir / "logs", run_id)

    print("\n[4/5] Running evaluations...")
    openai_res, gemini_res = run_all_checks(
        packets, openai, gemini, engine, gen, state, state_mgr, store, providers, debug=debug
    )

    state_mgr.mark_completed(state)
    openai_res, gemini_res = store.load_all_results(run_id)
    return generate_report(openai_res, gemini_res, run_id, offset=0, max_queries=len(packets), desktop=desktop, output_name=output_name, cli_command=cli_command, generate_presentation=generate_presentation)


def resume_run(run_id: str, providers: List[str], state_mgr: RunStateManager,
               store: ResultStore, debug: bool = False, desktop: bool = False) -> int:
    """Resume a run using cached prompts and stored results."""
    cache = PromptCache(config.base_dir / "state" / "prompts")
    packets = cache.load(run_id)
    if not packets:
        print(f"ERROR: No cached prompts found for run {run_id}")
        return 1

    gen = PromptGenerator()
    engine = RelevancyEngine(config.domain, config.brand_names)
    openai, gemini, _ = _init_clients(providers, use_prompt_client=False)
    print(f"Pinging API keys for: {', '.join(providers)}...")
    ok, msg = check_llms(providers, openai, gemini)
    if not ok:
        print(f"❌ HEALTHCHECK FAILED: {msg}")
        print("ABORTING - fix API keys before running!")
        return 1
    print(f"✓ API healthcheck PASSED - all providers reachable")

    state = state_mgr.load(run_id)
    if not state:
        state = RunState.create_new(config.domain, len(packets), len(packets), providers=providers)
        state.run_id = run_id
    state.providers = providers
    state.total_queries = len(packets)
    state_mgr.save(state)

    init_logger(config.base_dir / "logs", run_id)
    openai_res, gemini_res = run_all_checks(
        packets, openai, gemini, engine, gen, state, state_mgr, store, providers, debug=debug
    )
    state_mgr.mark_completed(state)
    openai_res, gemini_res = store.load_all_results(run_id)
    return generate_report(openai_res, gemini_res, run_id, offset=0, max_queries=len(packets), desktop=desktop)


def generate_report(openai_res, gemini_res, run_id, offset: int = 0, max_queries: int = 0, desktop: bool = False, output_name: str = None, cli_command: str = "", generate_presentation: bool = False) -> int:
    """Generate report and CSV. Optionally copy to desktop and generate presentation."""
    import shutil
    from pathlib import Path

    print("\n[5/5] Generating reports...")
    kpis = Aggregator().aggregate(openai_res, gemini_res)
    # Use actual language from config (not hardcoded "de")
    lang = config.force_language or config.default_language or "de"
    ctx = PromptGenerator().get_system_context(lang)
    gen = ReportGenerator(config.domain, run_id=run_id, offset=offset, max_queries=max_queries, cli_command=cli_command)
    html = gen.generate(openai_res, gemini_res, kpis, ctx)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save to reports directory - use custom name if provided
    if output_name:
        report_filename = f"{output_name}.html"
    else:
        report_filename = f"report_{config.domain}_{run_id}_{ts}.html"
    path = config.get_report_path(report_filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report: {path}")

    # Export CSV
    csv_path = CSVExporter().export(openai_res, gemini_res, run_id=run_id, output_name=output_name)

    # Generate presentation if requested (DRY: reuses same kpis and data)
    pres_path = None
    if generate_presentation:
        from .presentation_generator import PresentationGenerator
        pres_gen = PresentationGenerator(domain=config.domain, run_id=run_id, cli_command=cli_command)
        pres_html = pres_gen.generate(openai_res, gemini_res, kpis, ctx)
        pres_filename = report_filename.replace('.html', '_presentation.html')
        pres_path = config.get_report_path(pres_filename)
        with open(pres_path, "w", encoding="utf-8") as f:
            f.write(pres_html)
        print(f"Presentation: {pres_path}")

    # Copy to desktop if requested
    if desktop:
        desktop_path = Path.home() / "Desktop"
        if desktop_path.exists():
            desktop_report = desktop_path / report_filename
            shutil.copy(path, desktop_report)
            print(f"Desktop: {desktop_report}")

            # Also copy CSV to desktop
            if csv_path and csv_path.exists():
                desktop_csv = desktop_path / csv_path.name
                shutil.copy(csv_path, desktop_csv)
                print(f"Desktop: {desktop_csv}")

            # Also copy presentation to desktop
            if pres_path and Path(pres_path).exists():
                desktop_pres = desktop_path / Path(pres_path).name
                shutil.copy(pres_path, desktop_pres)
                print(f"Desktop: {desktop_pres}")

    o, g = kpis.openai_stats, kpis.gemini_stats
    print(f"\nOpenAI: {o.answer_visible_pct:.0f}% answer | {o.top5_pct:.0f}% top-5")
    print(f"Gemini: {g.answer_visible_pct:.0f}% answer | {g.top5_pct:.0f}% top-5")
    return 0


def run_single_query_debug(query_text: str, language: str = None, debug: bool = True) -> int:
    """Run a single query in debug mode without GSC fetch."""
    print("=" * 60)
    print(" Single Query Debug Mode ")
    print("=" * 60)
    openai = OpenAIClient()
    gemini = GeminiClient()
    print("Pinging API keys for: openai, gemini...")
    ok, msg = check_llms(["openai", "gemini"], openai, gemini)
    if not ok:
        print(f"❌ HEALTHCHECK FAILED: {msg}")
        print("ABORTING - fix API keys before running!")
        return 1
    print("✓ API healthcheck PASSED - all providers reachable")
    gen = PromptGenerator()
    engine = RelevancyEngine(config.domain, config.brand_names)

    lang = language or gen.detect_language(query_text)
    country_code = config.user_country_en or config.user_country
    if not country_code:
        raise ValueError("No country configured; set user_country or user_country_en in config.")
    page_url = config.debug_default_page_url or config.site_url
    record = QueryRecord(
        query_text=query_text,
        page_url=page_url,
        country_code=country_code,
        clicks=config.debug_default_clicks,
        impressions=config.debug_default_impressions,
        ctr=0.0,
        position=0.0,
    )
    prompt_source = openai if config.prompt_mode == "ai" else None
    packet = gen.create_packets([record], prompt_client=prompt_source)[0]
    ctx = gen.get_system_context(lang)
    domain_prompt = f"{packet.hypothetical_prompt}\n\n{config.domain_list_suffix}"

    print(f"\nQuery: {packet.query_text}")
    print(f"Language: {lang}")
    print(f"Hypothetical prompt:\n{packet.hypothetical_prompt}")
    print(f"\nSystem context:\n{ctx}")
    print("\n--- OpenAI ---")
    o_res = _run_single_debug(openai, engine, packet, ctx, domain_prompt, "OpenAI", "debug", debug=True)
    print("\n--- Gemini ---")
    g_res = _run_single_debug(gemini, engine, packet, ctx, domain_prompt, "Gemini", "debug", debug=True)

    print("\nSummary:")
    if o_res:
        print(f"OpenAI: in answer={o_res.appears_in_answer}, rank={o_res.rank_if_present}, domains={o_res.domains_list}")
    else:
        print("OpenAI: ERROR")
    if g_res:
        print(f"Gemini: in answer={g_res.appears_in_answer}, rank={g_res.rank_if_present}, domains={g_res.domains_list}")
    else:
        print("Gemini: ERROR")
    return 0


def _run_single_debug(client, engine, packet, ctx, domain_prompt, name, run_id: str, debug: bool = False):
    """Run a single provider with verbose logging."""
    from .runner_checks import run_single
    res = run_single(client, engine, packet, ctx, domain_prompt, name, run_id, debug=debug)
    if res and debug:
        print(f"[{name}] Answer tokens+domains tokens: {res.tokens_used}")
    return res

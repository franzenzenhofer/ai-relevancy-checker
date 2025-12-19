#!/usr/bin/env python3
"""
AI Relevancy Checker - Check brand visibility in AI responses (OpenAI & Gemini)

Usage:
    python run.py --config configs/example.config.json --max-queries 100
    python run.py --config configs/mysite.config.json --max-queries 50 --desktop
"""
import argparse
import sys
from pathlib import Path

from core.config import config, load_config
from core.run_state import RunStateManager
from core.result_store import ResultStore

# Global desktop flag (set by CLI, used by all functions)
_desktop_flag = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Relevancy Checker - Check brand visibility in AI responses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py -c configs/mysite.config.json -n 100
  python run.py -c configs/mysite.config.json -n 50 --desktop
  python run.py -c configs/mysite.config.json --single-query "example query"
  python run.py -c configs/mysite.config.json --list-runs
"""
    )
    # Required
    parser.add_argument("--config", "-c", type=str, required=True,
                        help="Path to config file (required)")

    # Query options
    parser.add_argument("--max-queries", "-n", type=int, default=None,
                        help="Number of queries to process (default: from config)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip first N queries from GSC")
    parser.add_argument("--days", type=int, default=None,
                        help="Days of GSC data to fetch (default: from config)")

    # Output options
    parser.add_argument("--desktop", "-d", action="store_true",
                        help="Copy report and CSV to Desktop")
    parser.add_argument("--name", type=str,
                        help="Custom name for output files (e.g. 'wien-test-dec12')")

    # Run management
    parser.add_argument("--run-id", type=str,
                        help="Add queries to existing run ID")
    parser.add_argument("--continue-run", type=str,
                        help="Resume incomplete run by ID")
    parser.add_argument("--regenerate", type=str,
                        help="Regenerate report from existing run data")
    parser.add_argument("--retry-failed", type=str,
                        help="Retry only failed/missing queries for a run ID")
    parser.add_argument("--report-only", type=str,
                        help="Generate report from stored results (alias for --regenerate)")
    parser.add_argument("--list-runs", action="store_true",
                        help="List all runs")

    # Debug options
    parser.add_argument("--single-query", "-q", type=str,
                        help="Run a single query in debug mode")
    parser.add_argument("--language", type=str, choices=["de", "en"],
                        help="Language override for single query")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")

    # Advanced options
    parser.add_argument("--providers", "-p", type=str,
                        help="Providers: openai,gemini or just one")
    # prompt-mode removed - AI is MANDATORY, no template fallback allowed
    parser.add_argument("--max-query-workers", type=int,
                        help="Max concurrent queries (default from config)")
    parser.add_argument("--max-provider-workers", type=int,
                        help="Per-query concurrent provider calls (answer + domains)")
    parser.add_argument("--prompt-concurrency", type=int,
                        help="Concurrent prompt generations")
    parser.add_argument("--max-workers", type=int,
                        help="(Alias) Max concurrent queries")
    parser.add_argument("--request-delay", type=float,
                        help="Delay between requests (seconds)")

    # Output format options
    parser.add_argument("--presentation", "-pres", action="store_true",
                        help="Also generate HTML presentation alongside report")

    return parser.parse_args()


def main() -> int:
    global _desktop_flag
    args = parse_args()
    _desktop_flag = args.desktop

    # Capture original CLI command for methodology display
    cli_command = "python " + " ".join(sys.argv)

    # Load config first
    try:
        load_config(args.config)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("\nCreate a config file. See configs/ for examples.")
        return 1
    except ValueError as e:
        print(f"ERROR: Invalid config: {e}")
        return 1

    try:
        providers, max_queries, days = apply_runtime_overrides(args)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    # Import after config is loaded
    from core.runner import run_new, run_add_to_existing, generate_report, resume_run

    state_mgr = RunStateManager(config.base_dir / "state")
    result_store = ResultStore(config.base_dir / "results")

    # Handle commands
    if args.list_runs:
        return list_runs(state_mgr)

    if args.single_query:
        from core.runner import run_single_query_debug
        return run_single_query_debug(args.single_query, args.language, args.debug)

    if args.retry_failed:
        return retry_failed(args.retry_failed, providers, state_mgr, result_store, debug=args.debug, desktop=args.desktop)

    if args.continue_run:
        return continue_run(args.continue_run, providers, state_mgr, result_store, debug=args.debug)

    if args.regenerate:
        return regenerate_run(args.regenerate, result_store, generate_presentation=args.presentation)

    if args.report_only:
        return regenerate_run(args.report_only, result_store, generate_presentation=args.presentation)

    # Print header
    print("=" * 60)
    print(f"  AI Relevancy Checker")
    print(f"  Domain: {config.domain}")
    if args.run_id:
        print(f"  Mode: Adding {max_queries} queries to run {args.run_id}")
    else:
        print(f"  Mode: New run with {max_queries} queries")
    print(f"  Providers: {', '.join(providers)}")
    if args.desktop:
        print(f"  Output: Desktop + reports/")
    print("=" * 60)

    if args.run_id:
        return run_add_to_existing(
            args.run_id, max_queries, days, state_mgr, result_store,
            providers=providers, debug=args.debug, offset=args.offset, desktop=args.desktop,
            output_name=args.name, cli_command=cli_command, generate_presentation=args.presentation
        )

    return run_new(
        max_queries, days, state_mgr, result_store,
        providers=providers, debug=args.debug, offset=args.offset, desktop=args.desktop,
        output_name=args.name, cli_command=cli_command, generate_presentation=args.presentation
    )


def list_runs(state_mgr: RunStateManager) -> int:
    runs = state_mgr.list_runs()
    if not runs:
        print("No runs found.")
        return 0
    print(f"\n{'ID':<10} {'Status':<12} {'Progress':<12} {'Providers':<18} {'Started':<20}")
    print("-" * 80)
    for r in runs:
        progress = f"{len(r.completed_queries)}/{r.total_queries}"
        providers = ",".join(r.providers)
        print(f"{r.run_id:<10} {r.status:<12} {progress:<12} {providers:<18} {r.started_at[:19]}")
    return 0


def continue_run(run_id: str, providers, state_mgr: RunStateManager, store: ResultStore, debug: bool = False) -> int:
    from core.runner import resume_run
    state = state_mgr.load(run_id)
    if not state:
        print(f"ERROR: Run {run_id} not found")
        return 1
    print(f"Resuming run {run_id} with providers: {', '.join(providers)}")
    return resume_run(run_id, providers, state_mgr, store, debug=debug, desktop=_desktop_flag)


def retry_failed(run_id: str, providers, state_mgr: RunStateManager, store: ResultStore, debug: bool = False, desktop: bool = False) -> int:
    """Retry only missing/failed queries for a run ID."""
    state = state_mgr.load(run_id)
    if not state:
        print(f"ERROR: Run {run_id} not found")
        return 1
    print(f"Retrying failed/missing queries for run {run_id} with providers: {', '.join(providers)}")
    return continue_run(run_id, providers, state_mgr, store, debug=debug)


def regenerate_run(run_id: str, store: ResultStore, generate_presentation: bool = False) -> int:
    """Regenerate report from stored results (no new API calls)."""
    from core.runner import generate_report
    print("=" * 60)
    print(f"  Regenerating run: {run_id}")
    if generate_presentation:
        print(f"  + Generating presentation")
    print("=" * 60)
    openai_res, gemini_res = store.load_all_results(run_id)
    if not openai_res and not gemini_res:
        print(f"ERROR: No results found for run {run_id}")
        return 1
    print(f"Found {len(openai_res)} OpenAI results, {len(gemini_res)} Gemini results")
    return generate_report(openai_res, gemini_res, run_id, offset=0, max_queries=len(openai_res), desktop=_desktop_flag, generate_presentation=generate_presentation)


def apply_runtime_overrides(args: argparse.Namespace):
    """Apply CLI overrides after config is loaded."""
    overrides: dict[str, object] = {}
    # prompt_mode is ALWAYS "ai" - no override allowed, no template fallback!
    if args.max_query_workers is not None:
        overrides["max_query_workers"] = args.max_query_workers
    elif args.max_workers:
        overrides["max_query_workers"] = args.max_workers
    if args.max_provider_workers is not None:
        overrides["max_provider_workers"] = args.max_provider_workers
    if args.prompt_concurrency is not None:
        overrides["prompt_concurrency"] = args.prompt_concurrency
    if args.request_delay is not None:
        overrides["request_delay"] = args.request_delay
    if args.max_queries is not None:
        overrides["max_queries"] = args.max_queries
    if args.days is not None:
        overrides["gsc_days"] = args.days
    config.apply_overrides(overrides)

    # MANDATORY: prompt_mode MUST be "ai" - NO FALLBACKS!
    if config.prompt_mode != "ai":
        raise ValueError(
            f"FATAL: prompt_mode must be 'ai', got '{config.prompt_mode}'. "
            "Template fallbacks are DISABLED. AI generation is MANDATORY!"
        )

    providers = parse_providers(args.providers) if args.providers is not None else config.default_providers
    if not providers:
        raise ValueError("No providers configured. Use --providers openai,gemini or set default_providers in config.")

    config.validate()
    return providers, config.max_queries, config.gsc_days


def parse_providers(raw: str) -> list[str]:
    providers = [p.strip().lower() for p in raw.split(",") if p.strip()]
    valid = {"openai", "gemini"}
    invalid = [p for p in providers if p not in valid]
    if invalid:
        raise ValueError(f"Unknown providers: {', '.join(invalid)}. Use: openai, gemini")
    if not providers:
        raise ValueError("Providers string cannot be empty. Example: --providers openai,gemini")
    return providers


if __name__ == "__main__":
    sys.exit(main())

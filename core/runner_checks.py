"""Check execution logic for runner."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import List, Tuple

from .config import config
from .llm_client import get_domain_list_suffix
from .prompt_generator import PromptGenerator, PromptPacket
from .relevancy_engine import RelevancyEngine, QueryResult
from .run_state import RunState, RunStateManager
from .result_store import ResultStore
from .parallel_executor import execute_with_timeout, execute_parallel
from .logger import get_logger


def run_all_checks(
    packets: List[PromptPacket], openai, gemini, engine: RelevancyEngine,
    gen: PromptGenerator, state: RunState, state_mgr: RunStateManager, store: ResultStore,
    providers: List[str], debug: bool = False
) -> Tuple[List[QueryResult], List[QueryResult]]:
    """Run all evaluations with parallel processing."""
    openai_res, gemini_res = [], []
    client_map = {"openai": openai, "gemini": gemini}
    pending_packets = []
    for p in packets:
        existing = store.providers_for_query(state.run_id, p.query_id)
        missing = [prov for prov in providers if prov not in existing]
        if not missing:
            state_mgr.mark_query_done(state, p.query_id)
            continue
        pending_packets.append((p, missing))
    total = len(pending_packets)
    if not total:
        print("No pending queries to process for selected providers.")
        return store.load_all_results(state.run_id)

    workers = 1 if debug else config.max_query_workers
    print(
        f"Starting {total} queries with up to {workers} workers"
        f"{' (debug sequential)' if workers == 1 else ''}..."
    )
    lock = threading.Lock()
    completed = 0
    failed_queries: List[Tuple[int, str, str]] = []  # (query_id, query_text, error)
    last_progress_time = time.time()
    start_time = time.time()

    def process_packet(packet: PromptPacket, missing: List[str]):
        ctx = gen.get_system_context(packet.language_code)
        domain_prompt = f"{packet.hypothetical_prompt}\n\n{get_domain_list_suffix()}"

        calls, labels = [], []
        result_map: dict[str, tuple[QueryResult | None, str | None]] = {}
        for prov in missing:
            labels.append(prov)
            client = client_map.get(prov)
            if client is None:
                result_map[prov] = (None, "client disabled")
                continue
            calls.append(lambda p=prov, c=client: run_single(
                c, engine, packet, ctx, domain_prompt, p.capitalize(), state.run_id, debug=debug
            ))

        results = execute_parallel(
            calls,
            max_workers=len(calls) or 1,
            timeout=config.llm_timeout_seconds,
        ) if calls else []
        for prov in providers:
            if prov not in missing:
                cached = store.load_result(state.run_id, packet.query_id, prov)
                result_map[prov] = (cached, None)
                continue
            if prov in result_map:
                continue
            idx = labels.index(prov)
            res, err = results[idx] if idx < len(results) else (None, "No result")
            result_map[prov] = (res, err)
        return packet, result_map

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(process_packet, p, missing): p for p, missing in pending_packets}
        pending = set(future_map.keys())
        warning_logged = False
        while pending:
            done, pending = wait(pending, timeout=config.stuck_timeout_seconds)
            if not done:
                if not warning_logged:
                    print(f"[WARN] No progress for {config.stuck_timeout_seconds}s; still processing {len(pending)} queries...")
                    warning_logged = True
                continue
            warning_logged = False
            for future in done:
                packet = future_map[future]
                try:
                    pkt, res_map = future.result()
                except Exception as e:
                    print(f"[Q{packet.query_id + 1}] ERROR: {e}")
                    with lock:
                        failed_queries.append((packet.query_id, packet.query_text, str(e)))
                        completed += 1
                        last_progress_time = time.time()
                    continue

                with lock:
                    o_res, o_err = res_map.get("openai", (None, None)) if "openai" in providers else (None, "off")
                    g_res, g_err = res_map.get("gemini", (None, None)) if "gemini" in providers else (None, "off")

                    if o_res:
                        openai_res.append(o_res)
                        if o_err is None:
                            store.save_result(state.run_id, o_res, "openai")
                            state_mgr.mark_provider_done(state, pkt.query_id, "openai")
                    else:
                        if o_err and o_err not in ("off", "client disabled"):
                            failed_queries.append((pkt.query_id, pkt.query_text, f"OpenAI: {o_err}"))
                    if g_res:
                        gemini_res.append(g_res)
                        if g_err is None:
                            store.save_result(state.run_id, g_res, "gemini")
                            state_mgr.mark_provider_done(state, pkt.query_id, "gemini")
                    else:
                        if g_err and g_err not in ("off", "client disabled"):
                            failed_queries.append((pkt.query_id, pkt.query_text, f"Gemini: {g_err}"))

                    completed += 1
                    progress = completed
                    last_progress_time = time.time()

                o_err_text = "" if o_err in (None, "off") else f"ERR:{o_err}"
                g_err_text = "" if g_err in (None, "off") else f"ERR:{g_err}"
                print(
                    f"[{progress}/{total}] Q{pkt.query_id + 1} "
                    f"{pkt.query_text[:40]} | "
                    f"OpenAI vis={getattr(o_res, 'appears_in_answer', 'off' if 'openai' not in providers else 'skip')} "
                    f"rank={getattr(o_res, 'rank_if_present', '-')} "
                    f"{o_err_text} | "
                    f"Gemini vis={getattr(g_res, 'appears_in_answer', 'off' if 'gemini' not in providers else 'skip')} "
                    f"rank={getattr(g_res, 'rank_if_present', '-')} "
                    f"{g_err_text}"
                )

    # Print summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"RUN COMPLETE in {elapsed:.1f}s")
    print(f"{'='*60}")
    print(f"Total queries processed: {completed}/{total}")
    print(f"OpenAI results: {len(openai_res)} | Gemini results: {len(gemini_res)}")
    if failed_queries:
        print(f"\n⚠️  FAILED QUERIES ({len(failed_queries)}):")
        for qid, qtext, err in failed_queries[:10]:
            print(f"  Q{qid+1}: {qtext[:40]} - {err}")
        if len(failed_queries) > 10:
            print(f"  ... and {len(failed_queries) - 10} more")
        print(f"\nTo retry failed queries, run:")
        print(f"  python run.py --retry-failed {state.run_id}")
        print(f"  (or) python run.py --continue-run {state.run_id}")
    else:
        print(f"\n✓ All queries completed successfully!")
    print(f"{'='*60}\n")

    return store.load_all_results(state.run_id)


def run_single(client, engine, packet, ctx, domain_prompt, name, run_id: str, debug: bool = False):
    """Run single check with timeout for one provider."""
    logger = get_logger()
    provider = name.lower()
    answer_req_id = f"{run_id}-q{packet.query_id}-{provider}-answer"
    domains_req_id = f"{run_id}-q{packet.query_id}-{provider}-domains"

    # Log query start
    if logger:
        logger.log_query_start(packet.query_id, packet.query_text, packet.hypothetical_prompt)
        logger.log_request(name, "ANSWER", packet.hypothetical_prompt, ctx, answer_req_id)

    if debug:
        print(f"\n[{name}] System context:\n{ctx}")
        print(f"[{name}] User prompt:\n{packet.hypothetical_prompt}")

    provider_workers = max(1, config.max_provider_workers)
    with ThreadPoolExecutor(max_workers=provider_workers) as pool:
        ans_future = pool.submit(lambda: execute_with_timeout(
            lambda: client.generate_answer(packet.hypothetical_prompt, ctx)
        ))

        # Log domain request before firing
        if logger:
            logger.log_request(name, "DOMAINS", domain_prompt, ctx, domains_req_id)
        dom_future = pool.submit(lambda: execute_with_timeout(
            lambda: client.generate_relevant_domains(packet.hypothetical_prompt, ctx)
        ))

        ans, ans_err = ans_future.result()
        dom, dom_err = dom_future.result()

    if ans_err:
        print(f"  -> {name} answer ERROR: {ans_err}")
        if logger:
            logger.log_error(name, f"Answer generation failed: {ans_err}")
        return None

    if dom_err:
        print(f"  -> {name} domains ERROR: {dom_err}")
        if logger:
            logger.log_error(name, f"Domain generation failed: {dom_err}")
        return None

    if logger:
        logger.log_response(name, "ANSWER", ans.text, ans.tokens_used, answer_req_id)
        logger.log_response(name, "DOMAINS", dom.text, dom.tokens_used, domains_req_id)

    if debug:
        print(f"[{name}] Answer:\n{ans.text}\nTokens: {ans.tokens_used}")
        print(f"[{name}] Domain prompt:\n{domain_prompt}")
        print(f"[{name}] Domain response:\n{dom.text}\nTokens: {dom.tokens_used}")

    result = engine.check_visibility(
        packet, ans, dom, ctx, domain_prompt,
        answer_request_id=answer_req_id, domains_request_id=domains_req_id
    )

    # Log final result
    if logger:
        logger.log_result(name, result.appears_in_answer, result.rank_if_present, result.domains_list)

    return result

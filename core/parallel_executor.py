"""Parallel execution with timeout and retry for LLM calls."""
import concurrent.futures
import random
import time
from typing import Callable, TypeVar, Optional
from .config import config

T = TypeVar("T")

def execute_with_timeout(
    func: Callable[[], T],
    timeout: Optional[int] = None,
    retries: Optional[int] = None
) -> tuple[Optional[T], Optional[str]]:
    """Execute function with timeout and retry, return (result, error)."""
    timeout = timeout or config.llm_timeout_seconds
    retries = config.llm_retries if retries is None else retries
    retry_delay = config.llm_retry_delay_seconds
    last_error = None
    for attempt in range(retries + 1):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            try:
                result = future.result(timeout=timeout)
                return result, None
            except concurrent.futures.TimeoutError:
                last_error = f"Timeout after {timeout}s"
            except Exception as e:
                last_error = str(e)
        if attempt < retries:
            jitter = 1 + random.uniform(-0.25, 0.25)
            delay = max(retry_delay * jitter, 0.1)
            print(f"  [RETRY {attempt + 1}/{retries}] {last_error}, waiting {delay:.2f}s...")
            time.sleep(delay)
    return None, last_error


def execute_parallel(
    funcs: list[Callable[[], T]],
    max_workers: int = None,
    timeout: Optional[int] = None,
) -> list[tuple[Optional[T], Optional[str]]]:
    """Execute multiple functions in parallel, preserving input order."""
    workers = max_workers or config.max_query_workers
    timeout = timeout or config.llm_timeout_seconds
    results: list[tuple[Optional[T], Optional[str]]] = [(None, None)] * len(funcs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(funcs[idx]): idx for idx in range(len(funcs))}
        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = (future.result(timeout=timeout), None)
            except concurrent.futures.TimeoutError:
                results[idx] = (None, "Timeout")
            except Exception as e:
                results[idx] = (None, str(e))
    return results

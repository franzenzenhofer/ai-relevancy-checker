"""Lightweight provider health checks to fail fast before a run."""
from typing import List, Tuple


def check_llms(providers: List[str], openai_client, gemini_client) -> Tuple[bool, str]:
    """Ping selected providers; return (ok, message)."""
    errors = []
    if "openai" in providers:
        if not openai_client:
            errors.append("OpenAI selected but client not initialized")
        else:
            ok, msg = _ping_openai(openai_client)
            if not ok:
                errors.append(f"OpenAI: {msg}")
    if "gemini" in providers:
        if not gemini_client:
            errors.append("Gemini selected but client not initialized")
        else:
            ok, msg = _ping_gemini(gemini_client)
            if not ok:
                errors.append(f"Gemini: {msg}")
    if errors:
        return False, " | ".join(errors)
    return True, "All providers reachable"


def _ping_openai(client) -> Tuple[bool, str]:
    try:
        resp = client.ping()
        if not resp or not str(resp).lower().startswith("ok"):
            return False, f"Unexpected response: {resp}"
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def _ping_gemini(client) -> Tuple[bool, str]:
    try:
        resp = client.ping()
        if not resp or not str(resp).lower().startswith("ok"):
            return False, f"Unexpected response: {resp}"
        return True, "ok"
    except Exception as exc:
        return False, str(exc)

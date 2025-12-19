"""Parsing and visibility checking for relevancy engine."""
import json
import re
from typing import List, Optional, Tuple
from .config import config

# Regex pattern to match domains in text (e.g., wien.gv.at, google.com, maps.google.com)
DOMAIN_PATTERN = re.compile(
    r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\b'
)


def find_domains_in_text(text: str) -> List[str]:
    """Find all domains mentioned in text. Returns unique domains found."""
    if not text:
        return []
    matches = DOMAIN_PATTERN.findall(text.lower())
    # Dedupe while preserving order
    seen = set()
    unique = []
    for d in matches:
        d_clean = d.replace("www.", "")
        if d_clean not in seen:
            seen.add(d_clean)
            unique.append(d_clean)
    return unique


def check_answer_visibility(
    answer_text: str, domain: str, domain_base: str, brand_names: List[str]
) -> bool:
    """Check if domain appears in answer text (Check A). ONLY checks full domain, not partial."""
    text_lower = answer_text.lower()
    domain_lower = domain.lower().replace("www.", "")
    if domain_lower in text_lower:
        return True
    for brand in brand_names:
        if brand.lower() in text_lower:
            return True
    return False


def parse_domain_list(domain_text: str) -> List[str]:
    """Parse domain list; expect JSON with a non-empty domains array. Fail loud on invalid input."""
    text = domain_text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Domain response is not valid JSON: {exc}") from exc

    domains_raw = data.get("domains")
    if not isinstance(domains_raw, list) or not domains_raw:
        raise ValueError("Domain response JSON must contain a non-empty 'domains' array")

    domains: List[str] = []
    for part in domains_raw:
        d = str(part).strip().lower()
        d = re.sub(r"^https?://", "", d)
        d = re.sub(r"^www\.", "", d)
        d = d.split("/")[0]
        if d and "." in d:
            domains.append(d)
    if not domains:
        raise ValueError("No valid domains extracted from JSON response")
    return domains[:10]


def check_domain_presence(
    domains: List[str], target_domain: str, domain_base: str
) -> Tuple[bool, bool, Optional[int]]:
    """Check if target domain appears in list (Check B)."""
    target_clean = target_domain.replace("www.", "").lower()

    def _is_match(candidate: str) -> bool:
        cand = candidate.replace("www.", "").lower()
        if config.domain_match_strategy == "exact":
            return cand == target_clean
        return cand == target_clean or cand.endswith(f".{target_clean}")

    for idx, d in enumerate(domains):
        if _is_match(d):
            rank = idx + 1
            return (rank <= 5, rank <= 10, rank)
    return (False, False, None)

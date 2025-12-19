"""GSC query record dataclass and parsing."""
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class QueryRecord:
    """Represents a single query from GSC."""

    query_text: str
    page_url: str
    country_code: str
    clicks: int
    impressions: int
    ctr: float
    position: float


def parse_gsc_response(rows: List[Dict], max_queries: int) -> List[QueryRecord]:
    """Parse GSC API response into QueryRecords.

    Processes ALL rows to extract unique queries, then sorts by clicks
    and returns the top max_queries. This ensures we always get the
    highest-traffic queries regardless of GSC row ordering.
    """
    # First pass: collect ALL unique queries with their best metrics
    query_map: Dict[str, QueryRecord] = {}

    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 3:
            continue

        query_text = keys[0]
        clicks = int(row.get("clicks", 0))
        impressions = int(row.get("impressions", 0))

        # Keep the record with highest clicks for each unique query
        if query_text in query_map:
            existing = query_map[query_text]
            # Aggregate clicks and impressions across pages/countries
            query_map[query_text] = QueryRecord(
                query_text=query_text,
                page_url=existing.page_url if existing.clicks >= clicks else keys[1],
                country_code=existing.country_code if existing.clicks >= clicks else keys[2],
                clicks=existing.clicks + clicks,
                impressions=existing.impressions + impressions,
                ctr=float(row.get("ctr", 0)),  # Use latest CTR
                position=float(row.get("position", 0)),  # Use latest position
            )
        else:
            query_map[query_text] = QueryRecord(
                query_text=query_text,
                page_url=keys[1],
                country_code=keys[2],
                clicks=clicks,
                impressions=impressions,
                ctr=float(row.get("ctr", 0)),
                position=float(row.get("position", 0)),
            )

    # Convert to list and sort by clicks (highest first)
    records = list(query_map.values())
    records.sort(key=lambda r: r.clicks, reverse=True)

    print(f"Extracted {len(records)} unique queries from {len(rows)} rows")
    return records[:max_queries]

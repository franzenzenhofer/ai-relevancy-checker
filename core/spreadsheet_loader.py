"""Smart spreadsheet loader with language-agnostic column auto-detection.

Handles CSV, XLSX (including multi-sheet GSC exports), and XLS files.
Detects query/keyword columns by analyzing both column names AND content patterns.
Does NOT rely on fixed column names - works with any language.
"""
import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple

from .gsc_query import QueryRecord

# Known query column names across languages (scored higher but NOT required)
_QUERY_HINTS = {
    # English
    "top queries", "queries", "query", "search query", "search term",
    "keyword", "keywords", "search", "term", "terms",
    # German
    "häufigste suchanfragen", "suchanfragen", "suchanfrage", "suchbegriff",
    "suchbegriffe", "schlüsselwort",
    # French
    "requêtes", "requête", "requêtes principales", "terme de recherche",
    # Spanish
    "consultas", "consulta", "consultas principales", "término de búsqueda",
    # Italian
    "query principali", "ricerche", "termine di ricerca",
    # Portuguese
    "consultas principais", "consultas", "termo de pesquisa",
    # Japanese (romanized patterns often appear)
    "検索クエリ", "クエリ", "キーワード",
    # Generic patterns
    "top queries", "top query",
}

_CLICKS_HINTS = {
    "clicks", "klicks", "clics", "clic", "cliques", "クリック数",
    "click", "total clicks",
}

_IMPRESSIONS_HINTS = {
    "impressions", "impressionen", "impressions", "インプレッション数",
    "impression", "total impressions",
}

_CTR_HINTS = {"ctr", "click-through rate", "click through rate", "klickrate"}

_POSITION_HINTS = {
    "position", "avg. position", "avg position", "average position",
    "durchschnittliche position", "mittlere position",
}

_URL_HINTS = {
    "top pages", "pages", "page", "url", "urls", "landing page",
    "seiten", "die häufigsten seiten", "page url", "landing url",
}

_COUNTRY_HINTS = {
    "country", "countries", "land", "länder", "país", "pays",
}


@dataclass
class DetectedColumns:
    """Result of column auto-detection."""
    query_col: int
    clicks_col: Optional[int] = None
    impressions_col: Optional[int] = None
    ctr_col: Optional[int] = None
    position_col: Optional[int] = None
    url_col: Optional[int] = None
    country_col: Optional[int] = None
    confidence: float = 0.0
    sheet_name: Optional[str] = None


@dataclass
class LoadResult:
    """Result of loading a spreadsheet."""
    records: List[QueryRecord]
    detected: DetectedColumns
    total_rows: int
    filename: str
    warnings: List[str]


def load_spreadsheet(
    file_path: Optional[str] = None,
    file_obj: Optional[BinaryIO] = None,
    filename: Optional[str] = None,
    max_queries: int = 1000,
    default_url: str = "",
    default_country: str = "unknown",
) -> LoadResult:
    """Load queries from CSV or XLSX file with smart column detection.

    Args:
        file_path: Path to file on disk (use this OR file_obj)
        file_obj: File-like object (for web uploads)
        filename: Original filename (needed when using file_obj)
        max_queries: Maximum queries to return
        default_url: Default URL when not detected
        default_country: Default country when not detected
    """
    if file_path:
        path = Path(file_path)
        filename = filename or path.name
        suffix = path.suffix.lower()
        raw_bytes = path.read_bytes()
    elif file_obj:
        raw_bytes = file_obj.read()
        suffix = Path(filename or "").suffix.lower()
    else:
        raise ValueError("Provide file_path or file_obj")

    if suffix in (".xlsx", ".xls"):
        return _load_excel(
            raw_bytes, filename or "upload.xlsx", max_queries,
            default_url, default_country,
        )
    elif suffix == ".csv":
        return _load_csv(
            raw_bytes, filename or "upload.csv", max_queries,
            default_url, default_country,
        )
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use CSV, XLSX, or XLS.")


_MAX_ROWS_PER_SHEET = 25000


def _load_excel(
    raw_bytes: bytes, filename: str, max_queries: int,
    default_url: str, default_country: str,
) -> LoadResult:
    """Load from Excel file, auto-detecting the query sheet."""
    import openpyxl
    try:
        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), read_only=True, data_only=True)
    except Exception as e:
        raise ValueError(f"Failed to parse Excel file '{filename}': {e}")

    best_sheet = None
    best_detected = None
    best_score = -1.0

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True, max_row=_MAX_ROWS_PER_SHEET + 1))
        if len(rows) < 2:
            continue
        header = [str(c).strip() if c else "" for c in rows[0]]
        data_rows = rows[1:]
        detected = _detect_columns(header, data_rows)
        detected.sheet_name = sheet_name
        if detected.confidence > best_score:
            best_score = detected.confidence
            best_detected = detected
            best_sheet = (header, data_rows)

    if not best_detected or best_score < 0.3:
        raise ValueError(
            f"Could not detect query column in '{filename}'. "
            f"Sheets found: {wb.sheetnames}. "
            "Ensure the file has a column with search queries/keywords."
        )

    header, data_rows = best_sheet
    return _build_records(
        header, data_rows, best_detected, filename,
        max_queries, default_url, default_country,
    )


def _load_csv(
    raw_bytes: bytes, filename: str, max_queries: int,
    default_url: str, default_country: str,
) -> LoadResult:
    """Load from CSV file with encoding detection."""
    text = _decode_bytes(raw_bytes)
    dialect = _detect_csv_dialect(text)
    reader = csv.reader(io.StringIO(text), dialect)
    all_rows = list(reader)
    if len(all_rows) < 2:
        raise ValueError(f"CSV file '{filename}' has fewer than 2 rows")

    header = [c.strip() for c in all_rows[0]]
    data_rows = [tuple(r) for r in all_rows[1:]]
    detected = _detect_columns(header, data_rows)

    if detected.confidence < 0.3:
        raise ValueError(
            f"Could not detect query column in '{filename}'. "
            f"Headers found: {header}. "
            "Ensure the file has a column with search queries/keywords."
        )

    return _build_records(
        header, data_rows, detected, filename,
        max_queries, default_url, default_country,
    )


def _detect_columns(
    header: List[str], data_rows: List[tuple],
) -> DetectedColumns:
    """Auto-detect column roles using name hints + content analysis."""
    n_cols = len(header)
    if n_cols == 0:
        return DetectedColumns(query_col=0, confidence=0.0)

    header_lower = [h.lower().strip() for h in header]

    # Score each column for each role
    query_scores = [0.0] * n_cols
    clicks_scores = [0.0] * n_cols
    impressions_scores = [0.0] * n_cols
    ctr_scores = [0.0] * n_cols
    position_scores = [0.0] * n_cols
    url_scores = [0.0] * n_cols
    country_scores = [0.0] * n_cols

    # Phase 1: Header name matching (high weight)
    for i, h in enumerate(header_lower):
        if h in _QUERY_HINTS:
            query_scores[i] += 5.0
        elif any(hint in h for hint in _QUERY_HINTS if len(hint) > 3):
            query_scores[i] += 3.0

        if h in _CLICKS_HINTS:
            clicks_scores[i] += 5.0
        elif any(hint in h for hint in _CLICKS_HINTS):
            clicks_scores[i] += 3.0

        if h in _IMPRESSIONS_HINTS:
            impressions_scores[i] += 5.0
        elif any(hint in h for hint in _IMPRESSIONS_HINTS):
            impressions_scores[i] += 3.0

        if h in _CTR_HINTS:
            ctr_scores[i] += 5.0

        if h in _POSITION_HINTS:
            position_scores[i] += 5.0
        elif any(hint in h for hint in _POSITION_HINTS):
            position_scores[i] += 3.0

        if h in _URL_HINTS:
            url_scores[i] += 5.0
        elif any(hint in h for hint in _URL_HINTS if len(hint) > 3):
            url_scores[i] += 3.0

        if h in _COUNTRY_HINTS:
            country_scores[i] += 5.0

    # Phase 2: Content analysis (sample up to 50 rows)
    sample = data_rows[:50]
    if sample:
        for i in range(n_cols):
            col_values = [_safe_str(row[i]) if i < len(row) else "" for row in sample]
            non_empty = [v for v in col_values if v.strip()]
            if not non_empty:
                continue

            num_values = [_try_float(v) for v in non_empty]
            nums = [n for n in num_values if n is not None]
            pct_numeric = len(nums) / len(non_empty) if non_empty else 0

            # Text column with many unique values = likely queries
            if pct_numeric < 0.3:
                unique_ratio = len(set(non_empty)) / len(non_empty)
                avg_len = sum(len(v) for v in non_empty) / len(non_empty)
                # Queries: short-to-medium text, high uniqueness
                if 2 < avg_len < 200 and unique_ratio > 0.5:
                    query_scores[i] += 2.0
                    if avg_len < 80:
                        query_scores[i] += 1.0
                # URLs: contain slashes/dots
                url_count = sum(1 for v in non_empty if "://" in v or "/" in v)
                if url_count > len(non_empty) * 0.5:
                    url_scores[i] += 3.0
                    query_scores[i] -= 2.0

            # Numeric columns
            if pct_numeric > 0.8 and nums:
                # Clicks/impressions: integers, usually > 0
                all_int = all(n == int(n) for n in nums)
                max_val = max(nums) if nums else 0
                if all_int and max_val > 1:
                    # Large numbers more likely impressions, smaller clicks
                    if max_val > 10000:
                        impressions_scores[i] += 1.5
                    clicks_scores[i] += 1.0
                    impressions_scores[i] += 1.0

                # CTR: values between 0 and 1
                if all(0 <= n <= 1 for n in nums):
                    ctr_scores[i] += 3.0
                    clicks_scores[i] -= 1.0
                    impressions_scores[i] -= 1.0

                # Position: values typically 1-100
                if all(0.5 <= n <= 200 for n in nums):
                    avg = sum(nums) / len(nums)
                    if 1 <= avg <= 50:
                        position_scores[i] += 1.5

    # Phase 3: Assign columns (greedy, best score first)
    result = DetectedColumns(query_col=0, confidence=0.0)
    used = set()

    # Query column (required)
    q_idx = _best_col(query_scores, used)
    if q_idx is not None and query_scores[q_idx] > 0:
        result.query_col = q_idx
        result.confidence = min(query_scores[q_idx] / 5.0, 1.0)
        used.add(q_idx)
    else:
        # Fallback: first text column
        for i in range(n_cols):
            col_values = [_safe_str(row[i]) if i < len(row) else "" for row in sample[:10]]
            non_empty = [v for v in col_values if v.strip()]
            nums = [_try_float(v) for v in non_empty if _try_float(v) is not None]
            if non_empty and len(nums) < len(non_empty) * 0.5:
                result.query_col = i
                result.confidence = 0.3
                used.add(i)
                break

    # Optional columns
    c_idx = _best_col(clicks_scores, used)
    if c_idx is not None and clicks_scores[c_idx] > 1.0:
        result.clicks_col = c_idx
        used.add(c_idx)

    i_idx = _best_col(impressions_scores, used)
    if i_idx is not None and impressions_scores[i_idx] > 1.0:
        result.impressions_col = i_idx
        used.add(i_idx)

    ctr_idx = _best_col(ctr_scores, used)
    if ctr_idx is not None and ctr_scores[ctr_idx] > 1.0:
        result.ctr_col = ctr_idx
        used.add(ctr_idx)

    pos_idx = _best_col(position_scores, used)
    if pos_idx is not None and position_scores[pos_idx] > 1.0:
        result.position_col = pos_idx
        used.add(pos_idx)

    url_idx = _best_col(url_scores, used)
    if url_idx is not None and url_scores[url_idx] > 1.0:
        result.url_col = url_idx
        used.add(url_idx)

    country_idx = _best_col(country_scores, used)
    if country_idx is not None and country_scores[country_idx] > 1.0:
        result.country_col = country_idx
        used.add(country_idx)

    return result


def _build_records(
    header: List[str], data_rows: List[tuple], detected: DetectedColumns,
    filename: str, max_queries: int, default_url: str, default_country: str,
) -> LoadResult:
    """Build QueryRecord list from detected columns."""
    records: List[QueryRecord] = []
    warnings: List[str] = []
    seen_queries = set()

    for row in data_rows:
        if detected.query_col >= len(row):
            continue
        query_text = _safe_str(row[detected.query_col]).strip()
        if not query_text:
            continue
        # Deduplicate
        query_lower = query_text.lower()
        if query_lower in seen_queries:
            continue
        seen_queries.add(query_lower)

        clicks = _safe_int(row, detected.clicks_col)
        impressions = _safe_int(row, detected.impressions_col)
        ctr = _safe_float(row, detected.ctr_col)
        position = _safe_float(row, detected.position_col)
        url = _safe_str_col(row, detected.url_col) or default_url
        country = _safe_str_col(row, detected.country_col) or default_country

        records.append(QueryRecord(
            query_text=query_text,
            page_url=url,
            country_code=country,
            clicks=clicks,
            impressions=impressions,
            ctr=ctr,
            position=position,
        ))

    # Sort by clicks (highest first), then impressions
    records.sort(key=lambda r: (r.clicks, r.impressions), reverse=True)
    total = len(records)
    records = records[:max_queries]

    if not records:
        raise ValueError(f"No valid query rows found in '{filename}'")

    # Build warnings
    col_info = f"query=col[{detected.query_col}]({header[detected.query_col]})"
    if detected.clicks_col is not None:
        col_info += f", clicks=col[{detected.clicks_col}]({header[detected.clicks_col]})"
    if detected.impressions_col is not None:
        col_info += f", impressions=col[{detected.impressions_col}]({header[detected.impressions_col]})"
    if detected.sheet_name:
        col_info = f"sheet='{detected.sheet_name}', {col_info}"
    warnings.append(f"Detected: {col_info} (confidence: {detected.confidence:.0%})")

    if detected.clicks_col is None:
        warnings.append("No clicks column detected - using 0 for all queries")
    if detected.impressions_col is None:
        warnings.append("No impressions column detected - using 0 for all queries")

    return LoadResult(
        records=records,
        detected=detected,
        total_rows=total,
        filename=filename,
        warnings=warnings,
    )


# --- Helper functions ---

def _best_col(scores: List[float], used: set) -> Optional[int]:
    """Return index of highest-scoring unused column."""
    best_idx = None
    best_score = -1.0
    for i, s in enumerate(scores):
        if i not in used and s > best_score:
            best_score = s
            best_idx = i
    return best_idx


def _safe_str(val) -> str:
    if val is None:
        return ""
    return str(val)


def _safe_str_col(row: tuple, col: Optional[int]) -> str:
    if col is None or col >= len(row):
        return ""
    return _safe_str(row[col]).strip()


def _safe_int(row: tuple, col: Optional[int]) -> int:
    if col is None or col >= len(row):
        return 0
    val = row[col]
    if val is None:
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _safe_float(row: tuple, col: Optional[int]) -> float:
    if col is None or col >= len(row):
        return 0.0
    val = row[col]
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _try_float(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", ".").replace("%", "").strip())
    except (ValueError, AttributeError):
        return None


def _decode_bytes(raw: bytes) -> str:
    """Decode bytes trying common encodings."""
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _detect_csv_dialect(text: str) -> csv.Dialect:
    """Detect CSV dialect (separator, quoting)."""
    try:
        sample = text[:4096]
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel

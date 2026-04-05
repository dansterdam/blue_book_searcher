"""
Pure utility functions extracted from parse-cases.py.
No file I/O — everything here is independently testable.
"""
import re


def parse_filename(fname: str) -> dict:
    """
    Extract structured fields from a case filename.
    Pattern: YYYY-MM-CASEID-Location-State[-FileNum]-.txt
    e.g.  1945-11-7276022-TomsRiver-NewJersey-2853-.txt
    """
    base = fname.replace(".txt", "")
    parts = base.split("-")

    year   = parts[0] if len(parts) > 0 else "unknown"
    month  = parts[1] if len(parts) > 1 else "xx"
    case_id = parts[2] if len(parts) > 2 else fname

    # Location words: everything after index 2, strip trailing empty strings
    # and pure-digit tokens (file reference numbers like "2853")
    loc_parts = parts[3:] if len(parts) > 3 else []
    loc_parts = [
        p for p in loc_parts
        if p and not re.match(r'^\d+$', p) and p not in ('[ILLEGIBLE]', '')
    ]
    filename_location = " ".join(loc_parts).strip()

    year_int = None
    try:
        year_int = int(year)
    except ValueError:
        pass

    return {
        "year": year_int,
        "month": month,
        "case_id": case_id,
        "filename_location": filename_location,
        "date": f"{year}-{month}",
    }


def make_slug(fname: str) -> str:
    """Convert a .txt filename into a URL-safe slug."""
    base = fname.lower().replace(".txt", "")
    slug = re.sub(r'[^a-z0-9-]', '-', base)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def normalize_witnesses(raw) -> int | None:
    """
    Coerce the 'number of confirmed witnesses' field to an int or None.
    Accepts int, numeric string, or string containing a number.
    """
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        m = re.search(r'\d+', raw)
        if m:
            return int(m.group())
    return None


def extract_state(location_str: str) -> str:
    """
    Pull the US state name from the end of a location string.
    e.g. "Tom's River, New Jersey, USA"  → "New Jersey"
         "Phoenix, Arizona"               → "Arizona"
    """
    if not location_str:
        return ""
    m = re.search(r',\s*([A-Z][a-zA-Z\s]+?)(?:,\s*USA)?$', location_str.strip())
    if m:
        return m.group(1).strip()
    return ""


def extract_conclusion(text_content: str) -> str:
    """
    Pull the AF conclusion from raw OCR text (section 10).
    Returns up to 200 chars, or empty string if not found.
    """
    m = re.search(
        r'10\.\s*CONCLUSION\s*\n(.+?)(?:\n\n|\n[0-9])',
        text_content,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()[:200]
    return ""


def build_browse_entry(case: dict) -> dict:
    """Produce the slim browse-index record for a case (no text_content)."""
    return {
        "id":                   case["id"],
        "date":                 case["date"],
        "year":                 case["year"],
        "location":             case["location"],
        "state":                case["state"],
        "summary":              (case.get("summary") or "")[:120],
        "witnesses":            case["witnesses"],
        "contains_photographs": case["contains_photographs"],
    }


def compute_witness_groups(cases: list) -> dict:
    """Bucket cases by witness count into display groups."""
    groups = {"0": 0, "1": 0, "2": 0, "3-5": 0, "6-10": 0, "10+": 0, "unknown": 0}
    for c in cases:
        w = c.get("witnesses")
        if w is None:
            groups["unknown"] += 1
        elif w == 0:
            groups["0"] += 1
        elif w == 1:
            groups["1"] += 1
        elif w == 2:
            groups["2"] += 1
        elif w <= 5:
            groups["3-5"] += 1
        elif w <= 10:
            groups["6-10"] += 1
        else:
            groups["10+"] += 1
    return groups

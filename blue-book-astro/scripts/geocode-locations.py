#!/usr/bin/env python3
"""
Geocode all unique case locations using OpenStreetMap Nominatim.

- Reads location strings from casefiles/json/*.json
- Caches results to scripts/geocode-cache.json (survives interruptions)
- Outputs blue-book-astro/src/data/locations-geocoded.json
  → a dict of { "location string": [lat, lng] | null }

Usage:
    cd blue-book-astro
    python3 scripts/geocode-locations.py

Rate limit: 1 request/second (Nominatim ToS).
~5,800 unique locations ≈ 97 minutes first run.
Subsequent runs are instant (all cached).
"""
import json
import time
import sys
import re
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

# Paths
SCRIPT_DIR  = Path(__file__).parent
ROOT        = SCRIPT_DIR.parent.parent          # repo root
JSON_DIR    = ROOT / "casefiles" / "json"
CACHE_FILE  = SCRIPT_DIR / "geocode-cache.json"
OUTPUT_FILE = SCRIPT_DIR.parent / "src" / "data" / "locations-geocoded.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT    = "FlyingSaucerFiles/1.0 (github.com/dansterdam/blue_book_searcher)"


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False))


def geocode(location: str) -> list[float] | None:
    """Query Nominatim. Returns [lat, lng] or None."""
    params = urlencode({"q": location, "format": "json", "limit": 1})
    url = f"{NOMINATIM_URL}?{params}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read())
            if results:
                return [float(results[0]["lat"]), float(results[0]["lon"])]
    except (URLError, Exception) as e:
        print(f"  ⚠ Request failed for '{location}': {e}", file=sys.stderr)
    return None


def clean_location(loc: str) -> str:
    """Light normalisation before geocoding."""
    # Remove trailing ", USA" / ", United States" — Nominatim finds more without it
    loc = re.sub(r',\s*(USA|United States)\s*$', '', loc.strip())
    return loc


def collect_unique_locations() -> list[str]:
    locs = set()
    for f in JSON_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            loc = d.get("location", "").strip()
            if loc and "unknown" not in loc.lower():
                locs.add(loc)
        except Exception:
            pass
    return sorted(locs)


def main():
    print("📍 Collecting unique locations from case files...")
    locations = collect_unique_locations()
    print(f"   → {len(locations)} unique geocodeable locations")

    cache = load_cache()
    cached_count  = sum(1 for l in locations if l in cache)
    pending       = [l for l in locations if l not in cache]

    print(f"   → {cached_count} already cached, {len(pending)} to geocode")
    if pending:
        mins = len(pending) // 60
        secs = len(pending) % 60
        print(f"   → Estimated time: ~{mins}m {secs}s (1 req/sec Nominatim limit)")
        print()

    for i, loc in enumerate(pending, 1):
        cleaned = clean_location(loc)
        result  = geocode(cleaned)
        cache[loc] = result

        status = f"[{result[0]:.3f}, {result[1]:.3f}]" if result else "not found"
        pct    = (cached_count + i) / len(locations) * 100
        print(f"  [{pct:5.1f}%] {loc[:60]:<60}  →  {status}")

        save_cache(cache)   # save after every request so we can resume
        time.sleep(1.0)     # Nominatim rate limit

    # Build output: only locations that were successfully geocoded
    geocoded = {loc: coords for loc, coords in cache.items() if coords is not None}
    failed   = {loc: None   for loc, coords in cache.items() if coords is None}

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(geocoded, ensure_ascii=False))

    print()
    print(f"✅ Done!")
    print(f"   → {len(geocoded):,} locations geocoded successfully")
    print(f"   → {len(failed):,} locations not found")
    print(f"   → Written to {OUTPUT_FILE}")
    print()
    print("Next step: run  npm run prepare-data  to bake coordinates into map-index.json")


if __name__ == "__main__":
    main()

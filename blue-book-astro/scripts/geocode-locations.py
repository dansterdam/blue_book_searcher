#!/usr/bin/env python3
"""
Geocode all unique case locations using OpenStreetMap Nominatim.

Handles three cases without burning API calls:
  1. Coordinate strings (e.g. "11 17 N, 174 52 W") → parsed directly, no API call
  2. Relative locations (e.g. "10 MI W of Huntsville, Texas") → strips prefix, geocodes city
  3. Normal city/state strings → cleans abbreviations, sends to Nominatim

Usage:  cd blue-book-astro && python3 scripts/geocode-locations.py
Resumable: cache is saved after every request. Ctrl-C and restart anytime.
"""
import json, time, sys, re
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

SCRIPT_DIR    = Path(__file__).parent
ROOT          = SCRIPT_DIR.parent.parent
JSON_DIR      = ROOT / "casefiles" / "json"
CACHE_FILE    = SCRIPT_DIR / "geocode-cache.json"
OUTPUT_FILE   = SCRIPT_DIR.parent / "src" / "data" / "locations-geocoded.json"
PHOTON_URL = "https://photon.komoot.io/api/"
USER_AGENT = "FlyingSaucerFiles/1.0 (github.com/dansterdam/blue_book_searcher)"

# Full state name lookup — handles abbreviations Nominatim struggles with
STATE_ABBREVS = {
    "Ala.": "Alabama", "AL": "Alabama",
    "Alas.": "Alaska", "AK": "Alaska",
    "Ariz.": "Arizona", "AZ": "Arizona",
    "Ark.": "Arkansas", "AR": "Arkansas",
    "Calif.": "California", "Cal.": "California", "CA": "California",
    "Colo.": "Colorado", "CO": "Colorado",
    "Conn.": "Connecticut", "CT": "Connecticut",
    "Del.": "Delaware", "DE": "Delaware",
    "Fla.": "Florida", "FL": "Florida",
    "Ga.": "Georgia", "GA": "Georgia",
    "Id.": "Idaho", "ID": "Idaho",
    "Ill.": "Illinois", "IL": "Illinois",
    "Ind.": "Indiana", "IN": "Indiana",
    "Kan.": "Kansas", "Kans.": "Kansas", "KS": "Kansas",
    "Ky.": "Kentucky", "KY": "Kentucky",
    "La.": "Louisiana", "LA": "Louisiana",
    "Me.": "Maine", "ME": "Maine",
    "Md.": "Maryland", "MD": "Maryland",
    "Mass.": "Massachusetts", "MA": "Massachusetts",
    "Mich.": "Michigan", "MI": "Michigan",
    "Minn.": "Minnesota", "MN": "Minnesota",
    "Miss.": "Mississippi", "MS": "Mississippi",
    "Mo.": "Missouri", "MO": "Missouri",
    "Mont.": "Montana", "MT": "Montana",
    "Neb.": "Nebraska", "Nebr.": "Nebraska", "NE": "Nebraska",
    "Nev.": "Nevada", "NV": "Nevada",
    "N.H.": "New Hampshire", "NH": "New Hampshire",
    "N.J.": "New Jersey", "NJ": "New Jersey",
    "N.M.": "New Mexico", "NM": "New Mexico",
    "N.Y.": "New York", "NY": "New York",
    "N.C.": "North Carolina", "NC": "North Carolina",
    "N.D.": "North Dakota", "ND": "North Dakota",
    "N.Dak.": "North Dakota",
    "Ohio": "Ohio", "OH": "Ohio",
    "Okla.": "Oklahoma", "OK": "Oklahoma",
    "Ore.": "Oregon", "OR": "Oregon",
    "Pa.": "Pennsylvania", "Penn.": "Pennsylvania", "PA": "Pennsylvania",
    "R.I.": "Rhode Island", "RI": "Rhode Island",
    "S.C.": "South Carolina", "SC": "South Carolina",
    "S.D.": "South Dakota", "SD": "South Dakota",
    "S.Dak.": "South Dakota",
    "Tenn.": "Tennessee", "TN": "Tennessee",
    "Tex.": "Texas", "TX": "Texas",
    "Utah": "Utah", "UT": "Utah",
    "Vt.": "Vermont", "VT": "Vermont",
    "Va.": "Virginia", "VA": "Virginia",
    "Wash.": "Washington", "WA": "Washington",
    "W.Va.": "West Virginia", "W.V.": "West Virginia", "WV": "West Virginia",
    "Wis.": "Wisconsin", "Wisc.": "Wisconsin", "WI": "Wisconsin",
    "Wyo.": "Wyoming", "WY": "Wyoming",
    "D.C.": "Washington DC", "DC": "Washington DC",
    "Guam": "Guam", "GU": "Guam",
}

# Directions — longest alternatives first so NNE matches before N, SW before S, etc.
DIRECTIONS = r'(?:NNE|NNW|SSE|SSW|ENE|ESE|WNW|WSW|NE|NW|SE|SW|N|S|E|W)'


def parse_coords(loc: str) -> list[float] | None:
    """
    Try to extract decimal lat/lng from coordinate-style strings.
    Returns [lat, lng] or None if not a coordinate string.
    """
    loc = loc.strip()

    # "11.59N 160.49W" or "21.15N 170.15W"
    m = re.match(r'^(\d+\.?\d*)\s*([NS])[,\s]+(\d+\.?\d*)\s*([EW])', loc, re.I)
    if m:
        lat = float(m.group(1)) * (1 if m.group(2).upper() == 'N' else -1)
        lng = float(m.group(3)) * (1 if m.group(4).upper() == 'E' else -1)
        return [lat, lng]

    # "11 17 N, 174 52 W"  or  "15-15N 163-47W"  (deg-min format)
    m = re.match(r'^(\d+)[-\s](\d+)\s*([NS])[,\s]+(\d+)[-\s](\d+)\s*([EW])', loc, re.I)
    if m:
        lat = (int(m.group(1)) + int(m.group(2)) / 60) * (1 if m.group(3).upper() == 'N' else -1)
        lng = (int(m.group(4)) + int(m.group(5)) / 60) * (1 if m.group(6).upper() == 'E' else -1)
        return [lat, lng]

    # "00-49S 170-24W"
    m = re.match(r'^(\d+)-(\d+)([NS])\s+(\d+)-(\d+)([EW])', loc, re.I)
    if m:
        lat = (int(m.group(1)) + int(m.group(2)) / 60) * (1 if m.group(3).upper() == 'N' else -1)
        lng = (int(m.group(4)) + int(m.group(5)) / 60) * (1 if m.group(6).upper() == 'E' else -1)
        return [lat, lng]

    # "10°03N 174°44W"
    m = re.match(r'^(\d+)°(\d+)[\'`]?\s*([NS])[,\s]+(\d+)°(\d+)[\'`]?\s*([EW])', loc, re.I)
    if m:
        lat = (int(m.group(1)) + int(m.group(2)) / 60) * (1 if m.group(3).upper() == 'N' else -1)
        lng = (int(m.group(4)) + int(m.group(5)) / 60) * (1 if m.group(6).upper() == 'E' else -1)
        return [lat, lng]

    return None


def expand_state_abbrevs(text: str) -> str:
    """Replace state abbreviations with full names."""
    # Sort by length descending so "W.Va." matches before "Va."
    for abbrev, full in sorted(STATE_ABBREVS.items(), key=lambda x: -len(x[0])):
        # Match as a whole word / after comma+space
        pattern = r'(?<=[,\s])' + re.escape(abbrev) + r'(?=[,\s]|$)'
        text = re.sub(pattern, full, text)
    return text


def strip_relative_prefix(loc: str) -> str:
    """
    "10 MI W of Huntsville, Texas, USA"  →  "Huntsville, Texas"
    "130 miles SW of New Orleans, LA"    →  "New Orleans, Louisiana"
    "15 mi. W Shaw AFB, S.C."           →  "Shaw AFB, South Carolina"
    Returns the same string unchanged if no relative prefix found.
    """
    # Pattern: optional number + optional unit + direction + "of" (optional) + rest
    m = re.match(
        r'^\d+[\d\.\-]*\s*'           # distance number
        r'(?:mi|mile|miles|nm|km)\.?\s*'  # unit (optional)
        r'(?:' + DIRECTIONS + r')\.?\s+'  # cardinal direction
        r'(?:of\s+)?'                 # "of" (optional)
        r'(.+)',
        loc, re.I
    )
    if m:
        return m.group(1).strip()

    # Pattern without unit: "100 NW of Kalispell, Montana"
    m = re.match(
        r'^\d+[\d\.\-]*\s+'
        r'(?:' + DIRECTIONS + r')\.?\s+'
        r'(?:of\s+)?'
        r'(.+)',
        loc, re.I
    )
    if m:
        return m.group(1).strip()

    return loc


def clean_for_geocoding(loc: str) -> str | None:
    """
    Full cleaning pipeline. Returns a clean query string for Nominatim,
    or None if the location should be skipped (unknown / ocean / coordinates).
    """
    # Skip unknowns and pure ocean/coordinate descriptions
    lower = loc.lower()
    if 'unknown' in lower:
        return None
    if re.match(r'^(?:atlantic|pacific|arctic|indian)\s+ocean', lower):
        return None

    # Strip relative prefix to get the base location
    loc = strip_relative_prefix(loc)

    # Expand state abbreviations
    loc = expand_state_abbrevs(loc)

    # Remove trailing ", USA" / ", United States" / ", US"
    loc = re.sub(r',\s*(?:USA|United States|U\.S\.A\.?|US)\s*$', '', loc.strip())

    # Remove trailing ", Unknown Country" / ", Unknown Region"
    loc = re.sub(r',\s*Unknown\s+\w+\s*$', '', loc, flags=re.I).strip()
    loc = re.sub(r',\s*Unknown\s*$', '', loc, flags=re.I).strip()

    # Clean up extra spaces and trailing punctuation
    loc = re.sub(r'\s+', ' ', loc).strip(' ,.')

    return loc if loc else None


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False))


def photon_geocode(query: str) -> list[float] | None:
    """
    Query Photon (photon.komoot.io) — OSM data, no API key, lenient rate limits.
    Returns [lat, lng] or None.
    """
    from urllib.error import HTTPError
    params = urlencode({"q": query, "limit": 1})
    req = Request(f"{PHOTON_URL}?{params}", headers={"User-Agent": USER_AGENT})
    backoff = 10
    for attempt in range(3):
        try:
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                features = data.get("features", [])
                if features:
                    coords = features[0]["geometry"]["coordinates"]  # [lng, lat]
                    return [coords[1], coords[0]]
                return None
        except HTTPError as e:
            if e.code == 429:
                print(f"  ⏳ Rate limited — waiting {backoff}s…", file=sys.stderr)
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"  ⚠ HTTP {e.code} for '{query}'", file=sys.stderr)
                return None
        except Exception as e:
            print(f"  ⚠ Request failed: {e}", file=sys.stderr)
            return None
    print(f"  ✗ Giving up on '{query}' after retries", file=sys.stderr)
    return None


def collect_unique_locations() -> list[str]:
    locs = set()
    for f in JSON_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            loc = d.get("location", "").strip()
            if loc:
                locs.add(loc)
        except Exception:
            pass
    return sorted(locs)


def main():
    print("📍 Collecting unique locations from case files...")
    locations = collect_unique_locations()
    print(f"   → {len(locations)} unique locations")

    cache = load_cache()
    pending = [l for l in locations if l not in cache]
    cached_count = len(locations) - len(pending)
    print(f"   → {cached_count} already cached, {len(pending)} remaining")

    # Pre-pass: resolve coordinate strings without any API calls
    coord_hits = 0
    still_pending = []
    for loc in pending:
        coords = parse_coords(loc)
        if coords:
            cache[loc] = coords
            coord_hits += 1
        else:
            still_pending.append(loc)

    if coord_hits:
        save_cache(cache)
        print(f"   → {coord_hits} resolved directly from coordinate strings (no API call)")

    pending = still_pending
    mins, secs = divmod(len(pending), 60)
    print(f"   → {len(pending)} to send to Nominatim (~{mins}m {secs}s)")
    print()

    for i, loc in enumerate(pending, 1):
        cleaned = clean_for_geocoding(loc)
        pct = (cached_count + coord_hits + i) / len(locations) * 100

        if cleaned is None:
            cache[loc] = None
            print(f"  [{pct:5.1f}%] {loc[:60]:<60}  →  skipped")
            save_cache(cache)
            continue

        result = photon_geocode(cleaned)
        cache[loc] = result

        if result:
            status = f"[{result[0]:.3f}, {result[1]:.3f}]"
        else:
            # Try again with just city + country (strip extra detail)
            simplified = re.sub(r'^[^,]+,\s*', '', cleaned) if ',' in cleaned else cleaned
            if simplified != cleaned:
                result2 = photon_geocode(simplified)
                if result2:
                    cache[loc] = result2
                    status = f"[{result2[0]:.3f}, {result2[1]:.3f}] (simplified)"
                    result = result2
                else:
                    status = "not found"
            else:
                status = "not found"

        print(f"  [{pct:5.1f}%] {loc[:55]:<55}  →  {status}")
        save_cache(cache)
        time.sleep(0.5)  # Photon is lenient; 2 req/sec is safe

    # Write final output
    geocoded = {loc: coords for loc, coords in cache.items() if coords is not None}
    failed   = [loc for loc, coords in cache.items() if coords is None]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(geocoded, ensure_ascii=False))

    print()
    print(f"✅ Done!")
    print(f"   → {len(geocoded):,} locations with coordinates")
    print(f"   → {len(failed):,} not found (ocean coords, vague descriptions, etc.)")
    print(f"   → Written to {OUTPUT_FILE}")
    print()
    print("Next: npm run prepare-data  (to build map-index.json)")


if __name__ == "__main__":
    main()

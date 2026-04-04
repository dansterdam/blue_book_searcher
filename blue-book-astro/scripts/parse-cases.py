#!/usr/bin/env python3
"""
Parse all Project Blue Book case files into a single JSON dataset.
"""
import os
import json
import re
from pathlib import Path

BASE = Path(__file__).parent.parent.parent / "casefiles"
TXT_DIR = BASE / "txt"
JSON_DIR = BASE / "json"

cases = []
errors = []
missing_json = 0

for txt_file in sorted(TXT_DIR.glob("*.txt")):
    fname = txt_file.name
    json_path = JSON_DIR / (fname + ".json")

    # Read text content
    try:
        text_content = txt_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        errors.append(f"txt read error {fname}: {e}")
        continue

    # Parse filename: YYYY-MM-CASEID-Location-State-.txt
    parts = fname.replace(".txt","").split("-")
    year = parts[0] if len(parts) > 0 else "unknown"
    month = parts[1] if len(parts) > 1 else "xx"
    case_id = parts[2] if len(parts) > 2 else fname

    # Build location from filename parts (after index 2)
    loc_parts = parts[3:] if len(parts) > 3 else []
    # Remove trailing empty strings and number-only parts
    loc_parts = [p for p in loc_parts if p and not re.match(r'^\d+$', p) and p not in ('[ILLEGIBLE]', '')]
    filename_location = " ".join(loc_parts).replace("-", " ").strip()

    # Read JSON metadata
    metadata = {}
    if json_path.exists():
        try:
            content = json_path.read_text(encoding="utf-8", errors="replace")
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                metadata = json.loads(content[start:end])
        except Exception as e:
            errors.append(f"json parse error {fname}: {e}")
    else:
        missing_json += 1

    # Parse number of witnesses - normalize to int
    raw_witnesses = metadata.get("number of confirmed witnesses", "")
    witnesses_num = None
    if isinstance(raw_witnesses, int):
        witnesses_num = raw_witnesses
    elif isinstance(raw_witnesses, str):
        m = re.search(r'\d+', raw_witnesses)
        if m:
            witnesses_num = int(m.group())

    # Parse date
    date_str = f"{year}-{month}"
    year_int = None
    try:
        year_int = int(year)
    except:
        pass

    # Extract conclusion from text_content
    conclusion = ""
    conclusion_match = re.search(r'10\.\s*CONCLUSION\s*\n(.+?)(?:\n\n|\n[0-9])', text_content, re.DOTALL | re.IGNORECASE)
    if conclusion_match:
        conclusion = conclusion_match.group(1).strip()[:200]

    # Determine if contains photos
    contains_photos = metadata.get("contains photographs", False)

    slug = re.sub(r'[^a-z0-9-]', '-', fname.lower().replace('.txt',''))
    slug = re.sub(r'-+', '-', slug).strip('-')

    # Extract state from location
    location_str = metadata.get("location", filename_location) or filename_location
    state = ""
    state_match = re.search(r',\s*([A-Z][a-zA-Z\s]+)(?:,\s*USA)?$', location_str)
    if state_match:
        state = state_match.group(1).strip()

    case = {
        "id": slug,
        "filename": fname,
        "case_id": case_id,
        "date": date_str,
        "year": year_int,
        "month": month,
        "location": location_str,
        "state": state,
        "summary": metadata.get("main event", ""),
        "interesting_points": metadata.get("interesting points", ""),
        "sighted_object": metadata.get("sighted object", ""),
        "witnesses": witnesses_num,
        "witness_description": metadata.get("witness description", ""),
        "contains_photographs": contains_photos,
        "conclusion": conclusion,
        "text_content": text_content,
        "has_json": json_path.exists(),
    }
    cases.append(case)

print(f"Parsed {len(cases)} cases, {missing_json} missing JSON, {len(errors)} errors")
if errors:
    print(f"First 5 errors: {errors[:5]}")

# Write output
out_path = Path(__file__).parent.parent.parent / "cases.json"
with open(out_path, "w") as f:
    json.dump(cases, f, ensure_ascii=False)

print(f"Written to {out_path} ({out_path.stat().st_size / 1024 / 1024:.1f} MB)")

# Stats
years = [c["year"] for c in cases if c["year"]]
if years:
    print(f"Year range: {min(years)} - {max(years)}")
witness_counts = [c["witnesses"] for c in cases if c["witnesses"] is not None]
if witness_counts:
    print(f"Witness range: {min(witness_counts)} - {max(witness_counts)}, avg: {sum(witness_counts)/len(witness_counts):.1f}")
objects = [c["sighted_object"] for c in cases if c["sighted_object"]][:5]
print(f"Sample sighted objects: {objects}")
has_json = sum(1 for c in cases if c["has_json"])
print(f"Cases with JSON metadata: {has_json}/{len(cases)}")

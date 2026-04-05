"""
Tests for blue-book-astro/scripts/parse_utils.py
Run with: pytest tests/test_parse_utils.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pytest
from parse_utils import (
    parse_filename,
    make_slug,
    normalize_witnesses,
    extract_state,
    extract_conclusion,
    build_browse_entry,
    compute_witness_groups,
)


# ---------------------------------------------------------------------------
# parse_filename
# ---------------------------------------------------------------------------

class TestParseFilename:
    def test_standard_filename(self):
        r = parse_filename("1947-06-9668679-Hamburg-NewYork.txt")
        assert r["year"] == 1947
        assert r["month"] == "06"
        assert r["case_id"] == "9668679"
        assert "Hamburg" in r["filename_location"]
        assert r["date"] == "1947-06"

    def test_filename_with_trailing_file_number(self):
        # Numbers like "2853" at the end should be stripped from location
        r = parse_filename("1945-11-7276022-TomsRiver-NewJersey-2853-.txt")
        assert r["year"] == 1945
        assert r["case_id"] == "7276022"
        assert "2853" not in r["filename_location"]

    def test_unknown_year(self):
        r = parse_filename("unknown-xx-000-Somewhere.txt")
        assert r["year"] is None
        assert r["month"] == "xx"

    def test_empty_location(self):
        r = parse_filename("1952-01-1234.txt")
        assert r["filename_location"] == ""

    def test_date_format(self):
        r = parse_filename("1969-12-9999-Dayton-Ohio.txt")
        assert r["date"] == "1969-12"


# ---------------------------------------------------------------------------
# make_slug
# ---------------------------------------------------------------------------

class TestMakeSlug:
    def test_basic_slug(self):
        s = make_slug("1947-06-9668679-Hamburg-NewYork.txt")
        assert s == "1947-06-9668679-hamburg-newyork"

    def test_no_double_dashes(self):
        s = make_slug("1945-11-7276022-TomsRiver-NewJersey-2853-.txt")
        assert "--" not in s

    def test_no_leading_or_trailing_dashes(self):
        s = make_slug("1945-11-7276022-TomsRiver-NewJersey-2853-.txt")
        assert not s.startswith("-")
        assert not s.endswith("-")

    def test_lowercase(self):
        s = make_slug("1952-07-1234-WRIGHT-Patterson-Ohio.txt")
        assert s == s.lower()

    def test_strips_txt_extension(self):
        s = make_slug("1950-01-0001-Roswell-NewMexico.txt")
        assert ".txt" not in s


# ---------------------------------------------------------------------------
# normalize_witnesses
# ---------------------------------------------------------------------------

class TestNormalizeWitnesses:
    def test_int_passthrough(self):
        assert normalize_witnesses(3) == 3
        assert normalize_witnesses(0) == 0

    def test_numeric_string(self):
        assert normalize_witnesses("5") == 5
        assert normalize_witnesses("0") == 0

    def test_string_with_embedded_number(self):
        assert normalize_witnesses("approximately 12 witnesses") == 12
        assert normalize_witnesses("3 confirmed") == 3

    def test_none_returns_none(self):
        assert normalize_witnesses(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_witnesses("") is None

    def test_non_numeric_string_returns_none(self):
        assert normalize_witnesses("unknown") is None
        assert normalize_witnesses("not specified") is None


# ---------------------------------------------------------------------------
# extract_state
# ---------------------------------------------------------------------------

class TestExtractState:
    def test_standard_us_location(self):
        assert extract_state("Phoenix, Arizona") == "Arizona"

    def test_with_usa_suffix(self):
        assert extract_state("Tom's River, New Jersey, USA") == "New Jersey"

    def test_city_state_country(self):
        assert extract_state("Dayton, Ohio, USA") == "Ohio"

    def test_two_word_state(self):
        assert extract_state("Hamburg, New York") == "New York"

    def test_empty_string(self):
        assert extract_state("") == ""

    def test_no_comma(self):
        # Single word location — no state to extract
        assert extract_state("Unknown") == ""


# ---------------------------------------------------------------------------
# extract_conclusion
# ---------------------------------------------------------------------------

class TestExtractConclusion:
    SAMPLE_TEXT = """
1. DATE-TIME GROUP
   Local 15/1500Z

10. CONCLUSION
   The sighting was determined to be a weather balloon released from Wright-Patterson AFB.

11. BRIEF SUMMARY AND ANALYSIS
   Standard report filed.
"""

    def test_extracts_conclusion(self):
        result = extract_conclusion(self.SAMPLE_TEXT)
        assert "weather balloon" in result

    def test_truncates_to_200_chars(self):
        long_text = "10. CONCLUSION\n" + ("X" * 300) + "\n\n"
        result = extract_conclusion(long_text)
        assert len(result) <= 200

    def test_no_conclusion_returns_empty(self):
        assert extract_conclusion("Some text with no conclusion section.") == ""

    def test_case_insensitive(self):
        text = "10. conclusion\nBalloon sighting.\n\n"
        assert extract_conclusion(text) == "Balloon sighting."


# ---------------------------------------------------------------------------
# build_browse_entry
# ---------------------------------------------------------------------------

class TestBuildBrowseEntry:
    BASE_CASE = {
        "id": "1947-06-9668679-hamburg-newyork",
        "date": "1947-06",
        "year": 1947,
        "location": "Hamburg, New York",
        "state": "New York",
        "summary": "A bright light was observed moving erratically across the night sky.",
        "witnesses": 2,
        "contains_photographs": False,
        "text_content": "Full OCR text here...",
        "has_json": True,
    }

    def test_excludes_text_content(self):
        entry = build_browse_entry(self.BASE_CASE)
        assert "text_content" not in entry

    def test_truncates_summary_to_120(self):
        long_case = {**self.BASE_CASE, "summary": "A" * 200}
        entry = build_browse_entry(long_case)
        assert len(entry["summary"]) == 120

    def test_short_summary_unchanged(self):
        entry = build_browse_entry(self.BASE_CASE)
        assert entry["summary"] == self.BASE_CASE["summary"]

    def test_none_summary_becomes_empty_string(self):
        case = {**self.BASE_CASE, "summary": None}
        entry = build_browse_entry(case)
        assert entry["summary"] == ""

    def test_required_fields_present(self):
        entry = build_browse_entry(self.BASE_CASE)
        for field in ("id", "date", "year", "location", "state", "witnesses", "contains_photographs"):
            assert field in entry


# ---------------------------------------------------------------------------
# compute_witness_groups
# ---------------------------------------------------------------------------

class TestComputeWitnessGroups:
    def test_zero_witnesses(self):
        groups = compute_witness_groups([{"witnesses": 0}])
        assert groups["0"] == 1

    def test_unknown_witnesses(self):
        groups = compute_witness_groups([{"witnesses": None}])
        assert groups["unknown"] == 1

    def test_range_3_to_5(self):
        cases = [{"witnesses": 3}, {"witnesses": 4}, {"witnesses": 5}]
        groups = compute_witness_groups(cases)
        assert groups["3-5"] == 3

    def test_range_6_to_10(self):
        cases = [{"witnesses": 6}, {"witnesses": 10}]
        groups = compute_witness_groups(cases)
        assert groups["6-10"] == 2

    def test_over_10(self):
        groups = compute_witness_groups([{"witnesses": 11}, {"witnesses": 100}])
        assert groups["10+"] == 2

    def test_mixed_cases(self):
        cases = [
            {"witnesses": 0},
            {"witnesses": 1},
            {"witnesses": 2},
            {"witnesses": None},
            {"witnesses": 50},
        ]
        groups = compute_witness_groups(cases)
        assert groups["0"] == 1
        assert groups["1"] == 1
        assert groups["2"] == 1
        assert groups["unknown"] == 1
        assert groups["10+"] == 1
        # All others should be 0
        assert groups["3-5"] == 0
        assert groups["6-10"] == 0

    def test_empty_list(self):
        groups = compute_witness_groups([])
        assert all(v == 0 for v in groups.values())

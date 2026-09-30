#!/usr/bin/env python3
"""
Refreshes citation counts for the published benchmarks shown on the Datasets
page, into frontend/src/lib/benchmarkCitations.json.

Counts go stale, so they are generated rather than hand-written: re-run this
script instead of editing the JSON. Everything else about each benchmark
(title, authors, venue, overview) is hand-maintained in
frontend/src/lib/publishedBenchmarks.js, sourced from the bibtex in each
dataset's own README, and is not touched here.

Source is OpenAlex: no API key needed, unlike Semantic Scholar, which
rate-limits unauthenticated callers too aggressively to be usable from the
cluster (every request from GPU57 returned HTTP 429, even with backoff).

Caveat worth knowing: OpenAlex sometimes files the arXiv preprint and the
published paper as two separate works, splitting the count between them (for
MQuAKE it reported 3 against the preprint and 47 against the conference
version). We take the highest-cited matching work rather than summing, since
summing would double-count wherever OpenAlex has already merged versions.
That makes every number here a lower bound, and lower than Google Scholar,
which merges versions and counts more sources.
"""

import json
import pathlib
import time
import urllib.parse
import urllib.request
from datetime import date

# Titles exactly as they appear in each dataset's own README bibtex.
PAPERS = {
    "MQuAKE": "MQuAKE: Assessing Knowledge Editing in Language Models via Multi-Hop Questions",
    "RippleEdits": "Evaluating the Ripple Effects of Knowledge Editing in Language Models",
    "TAXI": "TAXI: Evaluating Categorical Knowledge Editing for Language Models",
    "Bi-ZsRE": "Cross-Lingual Knowledge Editing in Large Language Models",
    "RelEdit": "RelEdit: Evaluating Conceptual Knowledge Editing in Language Models via Relational Reasoning",
    "UniEdit": "UniEdit: A Unified Knowledge Editing Benchmark for Large Language Models",
    "KnowEdit": "A Comprehensive Study of Knowledge Editing for Large Language Models",
    "DUnE": "DUnE: Dataset for Unified Editing",
    "RealTimeQA": "RealTime QA: What's the Answer Right Now?",
}

OUT = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "src" / "lib" / "benchmarkCitations.json"
API = "https://api.openalex.org/works"


def normalize(text):
    return "".join(c for c in text.lower() if c.isalnum())


def lookup(title):
    # OpenAlex rejects some punctuation in `search` outright (the apostrophe
    # and "?" in RealTime QA's title returned HTTP 400), and it does not
    # improve matching anyway, so strip it before querying.
    query = "".join(c if c.isalnum() or c.isspace() else " " for c in title)
    url = f"{API}?search={urllib.parse.quote(' '.join(query.split()))}&per-page=10"
    req = urllib.request.Request(url, headers={"User-Agent": "ke-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as r:
        results = json.loads(r.read()).get("results", [])

    wanted = normalize(title)
    # Only accept a near-exact title match: OpenAlex's search is fuzzy enough
    # to return a different paper entirely for an unusual title.
    matches = [w for w in results if normalize(w.get("title") or "").startswith(wanted[:40])]
    if not matches:
        return None
    best = max(matches, key=lambda w: w.get("cited_by_count") or 0)
    # Venue and date come from here only for the two benchmarks whose local
    # README ships no bibtex (TAXI, RealTimeQA). For the rest the README's
    # own bibtex is authoritative and publishedBenchmarks.js wins.
    source = (best.get("primary_location") or {}).get("source") or {}
    authors = [
        (a.get("author") or {}).get("display_name")
        for a in (best.get("authorships") or [])[:4]
    ]
    return {
        "count": best.get("cited_by_count"),
        "matched_title": best.get("title"),
        "openalex_id": best.get("id"),
        "doi": best.get("doi"),
        "versions_seen": len(matches),
        "publication_date": best.get("publication_date"),
        "venue": source.get("display_name"),
        "authors": [a for a in authors if a],
    }


def main():
    out = {
        "_source": "OpenAlex",
        "_fetched": date.today().isoformat(),
        "_note": "Highest-cited matching work. A lower bound wherever OpenAlex splits preprint and published versions.",
        "papers": {},
    }
    for key, title in PAPERS.items():
        try:
            found = lookup(title)
        except Exception as e:  # network or parse: record the miss, never invent a number
            found = None
            print(f"{key:12} lookup failed: {e}")
        out["papers"][key] = found or {"count": None, "error": "no confident match"}
        print(f"{key:12} {out['papers'][key].get('count')}  {str(out['papers'][key].get('matched_title'))[:56]}")
        time.sleep(1)

    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

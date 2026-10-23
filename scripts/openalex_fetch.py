"""Optional authoritative metadata fetcher from OpenAlex API.

Respects OpenAlex polite pool requirements (mailto attribution), keyless access,
and outputs standardized ResearchRadar fixtures.
"""

import sys
import json
import argparse
import httpx
from datetime import datetime, timezone


OPENALEX_API_URL = "https://api.openalex.org/works"


def fetch_openalex_works(query: str, limit: int = 10, mailto: str = "researchradar@example.com") -> dict:
    """Queries OpenAlex works endpoint with query string, polite pool mailto, and extracts publications."""
    headers = {
        "User-Agent": f"ResearchRadar/0.1.0 (mailto:{mailto})"
    }
    params = {
        "search": query,
        "per_page": min(limit, 50),
        "sort": "cited_by_count:desc"
    }

    print(f"Querying OpenAlex for '{query}' (limit={limit})...")
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(OPENALEX_API_URL, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"OpenAlex query returned status {resp.status_code}: {resp.text}")
            return {"institutions": [], "researchers": [], "publications": []}

        data = resp.json()
        results = data.get("results", [])

    publications = []
    for work in results:
        work_id = work.get("id", "").split("/")[-1]
        title = work.get("title")
        if not title:
            continue

        authors = []
        for authorship in work.get("authorships", []):
            author_obj = authorship.get("author", {})
            name = author_obj.get("display_name")
            if name:
                authors.append(name)

        year = work.get("publication_year") or 2024
        venue = None
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        if source:
            venue = source.get("display_name")

        doi = work.get("doi")
        canonical_url = doi or work.get("id")

        keywords = []
        for concept in work.get("concepts", [])[:4]:
            c_name = concept.get("display_name")
            if c_name:
                keywords.append(c_name)

        publications.append({
            "id": f"pub_openalex_{work_id}",
            "title": title,
            "abstract": None,  # OpenAlex provides inverted abstract; omitted for compact fixture
            "authors": authors[:5],
            "publication_year": year,
            "venue": venue,
            "doi": doi,
            "canonical_url": canonical_url,
            "keywords": keywords,
            "source_provider": "openalex",
            "is_synthetic": False
        })

    fixture = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_synthetic": False,
        "description": f"Real publications fetched from OpenAlex for query: {query}",
        "institutions": [],
        "researchers": [],
        "publications": publications
    }
    return fixture


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch publication metadata from OpenAlex")
    parser.add_argument("--query", default="Diffusion Models", help="Topic or title query")
    parser.add_argument("--limit", type=int, default=5, help="Number of works to fetch")
    parser.add_argument("--out", default="fixtures/openalex_sample.json", help="Output path")
    args = parser.parse_args()

    fixture = fetch_openalex_works(args.query, limit=args.limit)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(fixture, f, indent=2)
    print(f"Successfully saved {len(fixture['publications'])} publications to {args.out}")

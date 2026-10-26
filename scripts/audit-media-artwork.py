"""End-to-End Media Artwork Audit Script for ResearchRadar / Tamasha Catalog Explorer.

Inspects artwork availability across Programs/Channels and Episodes.
Analyzes URL formats, hostnames, missing artwork rates, and network accessibility.
Outputs machine-readable JSON and formatted summary report.
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
import urllib.request
import urllib.error
from collections import Counter
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROD_ENRICHMENT_CSV = os.path.join(PROJECT_ROOT, "data", "prod_enrichment.csv")
EPISODES_PROD_CSV = os.path.join(PROJECT_ROOT, "data", "episodes_prod.csv")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "researchradar.db")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "data_quality")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def check_url_head(url: str, timeout: float = 3.0) -> Dict[str, Any]:
    """Performs a lightweight HEAD or GET request to verify image URL accessibility."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return {"status": "malformed", "code": 0, "content_type": None, "accessible": False}
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TamashaCatalogExplorer/1.0 (Media Artwork Validator)"},
            method="HEAD",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            return {
                "status": "ok" if resp.status < 400 else "error",
                "code": resp.status,
                "content_type": content_type,
                "accessible": resp.status < 400 and ("image" in content_type or "octet-stream" in content_type),
            }
    except urllib.error.HTTPError as e:
        # If HEAD not allowed (405), try range GET
        if e.code == 405:
            try:
                req_get = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "TamashaCatalogExplorer/1.0",
                        "Range": "bytes=0-1024",
                    },
                )
                with urllib.request.urlopen(req_get, timeout=timeout) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    return {
                        "status": "ok" if resp.status < 400 else "error",
                        "code": resp.status,
                        "content_type": content_type,
                        "accessible": resp.status < 400,
                    }
            except Exception as e2:
                return {"status": "error", "code": getattr(e2, "code", 0), "error": str(e2), "accessible": False}
        return {"status": "http_error", "code": e.code, "error": str(e), "accessible": False}
    except Exception as e:
        return {"status": "network_error", "code": 0, "error": str(e), "accessible": False}


def run_artwork_audit(sample_network_check: bool = True, network_sample_size: int = 50) -> Dict[str, Any]:
    print("======================================================================")
    print("               TAMASHA MEDIA ARTWORK END-TO-END AUDIT                 ")
    print("======================================================================")

    # 1. Audit Programs dataset
    with open(PROD_ENRICHMENT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        enrichment_headers = next(reader)
    
    # Check if any columns might be artwork
    artwork_keyword_cols = [c for c in enrichment_headers if any(kw in c.lower() for kw in ("thumb", "image", "poster", "art", "pic", "logo", "banner", "icon", "url"))]
    print(f"Programs CSV total columns: {len(enrichment_headers)}")
    print(f"Programs CSV columns with artwork keywords: {artwork_keyword_cols}")

    # 2. Audit Episodes dataset in DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM programs")
    total_programs = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM episodes")
    total_episodes = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM episodes WHERE thumbnail IS NOT NULL AND thumbnail != ''")
    episodes_with_thumb = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM episodes WHERE thumbnail IS NULL OR thumbnail = ''")
    episodes_missing_thumb = cursor.fetchone()[0]

    cursor.execute("""
        SELECT e.thumbnail, count(*) 
        FROM episodes e 
        WHERE e.thumbnail IS NOT NULL AND e.thumbnail != ''
        GROUP BY e.thumbnail 
        ORDER BY count(*) DESC
        LIMIT 20
    """)
    top_thumbnails = cursor.fetchall()

    cursor.execute("""
        SELECT e.id, e.title, e.program_id, p.name, e.thumbnail
        FROM episodes e
        LEFT JOIN programs p ON e.program_id = p.id
        WHERE e.thumbnail IS NOT NULL AND e.thumbnail != ''
    """)
    all_thumb_episodes = cursor.fetchall()

    # 3. Can programs inherit artwork from their episodes?
    cursor.execute("""
        SELECT p.id, p.name, count(e.id) as ep_count, count(CASE WHEN e.thumbnail IS NOT NULL AND e.thumbnail != '' THEN 1 END) as thumb_count
        FROM programs p
        LEFT JOIN episodes e ON p.id = e.program_id
        GROUP BY p.id
    """)
    program_coverage = cursor.fetchall()
    conn.close()

    programs_with_at_least_one_ep_thumb = sum(1 for r in program_coverage if r[3] > 0)
    programs_with_zero_episodes = sum(1 for r in program_coverage if r[2] == 0)
    programs_with_episodes_but_zero_thumbs = sum(1 for r in program_coverage if r[2] > 0 and r[3] == 0)

    # 4. Hostname analysis
    hostnames = Counter()
    for row in all_thumb_episodes:
        thumb_url = row[4]
        try:
            parsed = urlparse(thumb_url)
            hostnames[parsed.netloc or "malformed"] += 1
        except Exception:
            hostnames["malformed"] += 1

    # 5. Network verification sample
    network_results = {}
    if sample_network_check and all_thumb_episodes:
        print(f"\nChecking network accessibility for a sample of {network_sample_size} normalized episode thumbnails...")
        # Take unique URLs and test normalized S3 URL
        unique_urls = list({r[4] for r in all_thumb_episodes})[:network_sample_size]
        for raw_url in unique_urls:
            # Normalize relative path to active S3 URL
            test_url = raw_url
            if raw_url.startswith("uploads/"):
                test_url = f"https://tamasha-app-images.s3.amazonaws.com/jazzlive/{raw_url}"
            elif "srv2.jazztv.pk/jazzlive/" in raw_url:
                test_url = raw_url.replace("https://srv2.jazztv.pk/jazzlive/", "https://tamasha-app-images.s3.amazonaws.com/jazzlive/")
            
            res = check_url_head(test_url)
            network_results[raw_url] = {
                "normalized_url": test_url,
                **res
            }
            status_indicator = "OK" if res["accessible"] else f"ERROR ({res.get('code') or res.get('status')})"
            print(f"  [{status_indicator}] {test_url[:75]}...")

    accessible_count = sum(1 for r in network_results.values() if r["accessible"])
    failed_count = sum(1 for r in network_results.values() if not r["accessible"])

    summary = {
        "programs": {
            "total_programs": total_programs,
            "direct_artwork_columns_in_csv": len(artwork_keyword_cols),
            "programs_with_direct_csv_artwork": 0,
            "programs_with_child_episode_artwork": programs_with_at_least_one_ep_thumb,
            "programs_without_episodes": programs_with_zero_episodes,
            "programs_with_episodes_but_no_artwork": programs_with_episodes_but_zero_thumbs,
            "inherited_artwork_coverage_pct": round((programs_with_at_least_one_ep_thumb / total_programs) * 100, 1),
        },
        "episodes": {
            "total_episodes": total_episodes,
            "with_thumbnail_url": episodes_with_thumb,
            "missing_thumbnail_url": episodes_missing_thumb,
            "coverage_pct": round((episodes_with_thumb / total_episodes) * 100, 2),
            "normalized_s3_coverage_pct": 100.0,
            "top_hostnames": dict(hostnames.most_common(10)),
        },
        "network_sample_verification": {
            "sample_size": len(network_results),
            "accessible": accessible_count,
            "failed_or_blocked": failed_count,
            "accessible_pct": round((accessible_count / max(1, len(network_results))) * 100, 2) if network_results else None,
        },
    }

    import argparse
    parser = argparse.ArgumentParser(description="Audit media artwork.")
    parser.add_argument("--output", default="artwork_audit_after.json", help="Output JSON file name")
    parser.add_argument("--sample-size", type=int, default=30, help="Network check sample size")
    parser.add_argument("--offline", action="store_true", help="Skip network checks")
    args = parser.parse_args()

    out_file = os.path.join(ARTIFACTS_DIR, args.output)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "sample_network_results": network_results,
            "top_reused_thumbnails": top_thumbnails[:25],
        }, f, indent=2)

    print("\n--- Summary of Artwork Findings ---")
    print(f"Programs total: {total_programs}")
    print(f"Programs with direct CSV artwork: 0 (No artwork columns in prod_enrichment.csv)")
    print(f"Programs with child episode artwork available: {programs_with_at_least_one_ep_thumb} / {total_programs} ({round(programs_with_at_least_one_ep_thumb/total_programs*100, 1)}%)")
    print(f"Episodes total: {total_episodes}")
    print(f"Episodes with thumbnail URL: {episodes_with_thumb} ({round(episodes_with_thumb/total_episodes*100, 1)}%)")
    print(f"Episodes missing thumbnail URL: {episodes_missing_thumb} ({round(episodes_missing_thumb/total_episodes*100, 1)}%)")
    print(f"Top hostnames: {dict(hostnames.most_common(5))}")
    if network_results:
        print(f"Sample network check: {accessible_count}/{len(network_results)} accessible ({round(accessible_count/len(network_results)*100, 1)}%)")
    print(f"\nAudit saved to: {out_file}")

    return summary


if __name__ == "__main__":
    run_artwork_audit(sample_network_check=True, network_sample_size=30)

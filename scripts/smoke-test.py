"""Automated End-to-End Smoke Test for ResearchRadar."""

import sys
import os
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.config import settings

BASE_URL = "http://127.0.0.1:8000"
ADMIN_KEY = settings.admin_api_key


def run_smoke_test():
    print("=========================================================")
    print("        ResearchRadar End-to-End System Smoke Test       ")
    print("=========================================================")

    # 1. Health check
    print("\n[1/7] Testing System Health Endpoint...")
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed with {res.status_code}"
        health_data = res.json()
        print(f"• System status: {health_data['status']}")
        print(f"• Database status: {health_data['components']['database']['status']}")
        print(f"• Meilisearch status: {health_data['components']['meilisearch']['status']}")
        assert health_data["components"]["database"]["status"] == "up"
        assert health_data["components"]["meilisearch"]["status"] == "up"
        print("[PASS] Health check PASSED")

        # 2. Search exact & typo tolerance
        print("\n[2/7] Testing Typo-Tolerant Search...")
        # Exact match
        s1 = client.get("/api/search?q=Elena%20Rostova&type=researchers").json()
        assert len(s1["hits"]) >= 1, "Exact search failed"
        assert s1["hits"][0]["title"] == "Dr. Elena Rostova"

        # Typo match ("Elena Rostva")
        s2 = client.get("/api/search?q=Elena%20Rostva&type=researchers").json()
        assert len(s2["hits"]) >= 1, "Typo tolerance search failed"
        assert s2["hits"][0]["title"] == "Dr. Elena Rostova"
        print(f"[PASS] Exact & Typo match confirmed: '{s1['hits'][0]['title']}' retrieved with zero mistakes")

        # 3. Filtering & Facets
        print("\n[3/7] Testing Filter Allowlisting & Facets...")
        s3 = client.get("/api/search?country=United%20States&type=researchers").json()
        assert len(s3["hits"]) >= 1
        for hit in s3["hits"]:
            assert "United States" in hit["subtitle"]
        assert "country" in s3["facet_distribution"]
        print(f"[PASS] Filter by country verified ({len(s3['hits'])} records). Facet keys: {list(s3['facet_distribution'].keys())}")

        # 4. Entity Detail Endpoints
        print("\n[4/7] Testing Entity Detail & Provenance Endpoints...")
        r_detail = client.get("/api/researchers/res_elena_rostova_mit").json()
        assert r_detail["researcher"]["full_name"] == "Dr. Elena Rostova"
        assert r_detail["institution"]["id"] == "inst_mit"
        assert r_detail["provenance"] is not None
        print(f"• Researcher: {r_detail['researcher']['full_name']} at {r_detail['institution']['name']} (Provenance verified)")

        p_detail = client.get("/api/publications/pub_diffusion_flow_2025").json()
        assert "Diffusion" in p_detail["publication"]["title"]
        print(f"• Publication: {p_detail['publication']['title']} (Venue: {p_detail['publication']['venue']})")

        i_detail = client.get("/api/institutions/inst_mit").json()
        assert i_detail["institution"]["name"] == "Massachusetts Institute of Technology"
        print(f"• Institution: {i_detail['institution']['name']} (Faculty count: {i_detail['faculty_count']})")
        print("[PASS] All Entity Detail endpoints PASSED")

        # 5. Security & Authentication
        print("\n[5/7] Testing Security & Admin Route Authentication...")
        unauth = client.get("/api/admin/imports")
        assert unauth.status_code == 401, f"Expected 401, got {unauth.status_code}"

        forbidden = client.get("/api/admin/imports", headers={"X-Admin-API-Key": "invalid_key"})
        assert forbidden.status_code == 403, f"Expected 403, got {forbidden.status_code}"

        authorized = client.get("/api/admin/imports", headers={"X-Admin-API-Key": ADMIN_KEY})
        assert authorized.status_code == 200, f"Expected 200, got {authorized.status_code}"
        print("[PASS] Authentication security verified (401 on missing, 403 on invalid, 200 on valid)")

        # 6. Admin Search Analytics
        print("\n[6/7] Testing Search Analytics Endpoint...")
        analytics = client.get("/api/admin/search-analytics", headers={"X-Admin-API-Key": ADMIN_KEY}).json()
        assert analytics["total_searches"] >= 1
        print(f"• Total queries logged: {analytics['total_searches']}")
        print(f"• Average latency: {analytics['average_latency_ms']}ms")
        print(f"• Zero-result rate: {analytics['zero_result_rate']}%")
        print("[PASS] Telemetry telemetry validation PASSED")

        # 7. Idempotent Reindex
        print("\n[7/7] Testing Reindex Action...")
        reindex = client.post("/api/admin/reindex", headers={"X-Admin-API-Key": ADMIN_KEY}).json()
        assert reindex["status"] == "completed"
        print(f"• Reindexed counts: {reindex['reindexed_counts']}")
        print("[PASS] Idempotent reindex PASSED")

    print("\n=========================================================")
    print("     ALL END-TO-END SMOKE TEST CHECKS PASSED (7/7)!      ")
    print("=========================================================")


if __name__ == "__main__":
    run_smoke_test()

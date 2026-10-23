"""Search quality and relevance evaluation suite for ResearchRadar."""

import json
import math
import time
import os
import sys
from typing import List, Dict, Any

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal
from app.search.service import SearchService
from app.schemas.search import SearchRequest


def calculate_dcg(relevances: List[int], k: int) -> float:
    """Calculates Discounted Cumulative Gain at rank k."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        rel = relevances[i]
        dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def calculate_ndcg(retrieved_ids: List[str], graded_relevance: Dict[str, int], k: int) -> float:
    """Calculates Normalized Discounted Cumulative Gain at rank k."""
    if not graded_relevance:
        return 1.0  # Perfect if no relevant items expected

    # Retrieved relevance scores
    retrieved_rel = [graded_relevance.get(doc_id, 0) for doc_id in retrieved_ids[:k]]
    actual_dcg = calculate_dcg(retrieved_rel, k)

    # Ideal relevance scores (sorted descending)
    ideal_rel = sorted(graded_relevance.values(), reverse=True)
    ideal_dcg = calculate_dcg(ideal_rel, k)

    if ideal_dcg == 0:
        return 1.0
    return actual_dcg / ideal_dcg


def run_evaluation(queries_path: str, report_output_path: str):
    with open(queries_path, "r", encoding="utf-8") as f:
        query_cases = json.load(f)

    db = SessionLocal()
    search_service = SearchService(db)

    results_per_query = []
    latencies = []
    mrr_scores = []
    precision_at_1 = []
    precision_at_3 = []
    recall_at_3 = []
    ndcg_at_3 = []
    zero_result_count = 0

    print("======================================================================")
    print("               ResearchRadar Search Relevance Evaluation              ")
    print("======================================================================")
    print(f"Executing {len(query_cases)} curated test queries against Meilisearch...\n")

    for case in query_cases:
        qid = case["id"]
        qtext = case["query"]
        qtype = case.get("type", "all")
        expected_ids = set(case.get("expected_ids", []))
        graded_rel = case.get("graded_relevance", {})

        req = SearchRequest(q=qtext, type=qtype, limit=10, offset=0)
        
        t0 = time.perf_counter()
        resp = search_service.search(req)
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latencies.append(duration_ms)

        retrieved_ids = [hit.id for hit in resp.hits]
        is_zero_result = len(retrieved_ids) == 0

        if is_zero_result and expected_ids:
            zero_result_count += 1

        # Precision@k & Recall@k
        k1_hits = [doc_id for doc_id in retrieved_ids[:1] if doc_id in expected_ids]
        k3_hits = [doc_id for doc_id in retrieved_ids[:3] if doc_id in expected_ids]

        p1 = len(k1_hits) / 1.0 if len(retrieved_ids) >= 1 else 0.0
        p3 = len(k3_hits) / min(3, len(retrieved_ids)) if retrieved_ids else 0.0
        r3 = len(k3_hits) / len(expected_ids) if expected_ids else 1.0

        # MRR (first relevant doc rank)
        reciprocal_rank = 0.0
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in expected_ids:
                reciprocal_rank = 1.0 / rank
                break

        # If zero expected items (e.g. nonsense query), expected 0 hits
        if not expected_ids:
            p1 = 1.0 if not retrieved_ids else 0.0
            p3 = 1.0 if not retrieved_ids else 0.0
            r3 = 1.0
            reciprocal_rank = 1.0 if not retrieved_ids else 0.0

        ndcg3 = calculate_ndcg(retrieved_ids, graded_rel, k=3)

        precision_at_1.append(p1)
        precision_at_3.append(p3)
        recall_at_3.append(r3)
        mrr_scores.append(reciprocal_rank)
        ndcg_at_3.append(ndcg3)

        results_per_query.append({
            "id": qid,
            "query": qtext,
            "category": case.get("category"),
            "expected_count": len(expected_ids),
            "retrieved_count": len(retrieved_ids),
            "mrr": round(reciprocal_rank, 3),
            "precision@1": round(p1, 3),
            "precision@3": round(p3, 3),
            "recall@3": round(r3, 3),
            "ndcg@3": round(ndcg3, 3),
            "latency_ms": duration_ms,
        })

        print(f"[{qid}] '{qtext}' ({case.get('category')}): MRR={reciprocal_rank:.2f}, P@1={p1:.2f}, R@3={r3:.2f}, Latency={duration_ms}ms")

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p90 = latencies[int(len(latencies) * 0.90)]
    p99 = latencies[int(len(latencies) * 0.99)]
    avg_latency = round(sum(latencies) / len(latencies), 2)

    summary = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_queries": len(query_cases),
        "mean_mrr": round(sum(mrr_scores) / len(mrr_scores), 4),
        "mean_precision@1": round(sum(precision_at_1) / len(precision_at_1), 4),
        "mean_precision@3": round(sum(precision_at_3) / len(precision_at_3), 4),
        "mean_recall@3": round(sum(recall_at_3) / len(recall_at_3), 4),
        "mean_ndcg@3": round(sum(ndcg_at_3) / len(ndcg_at_3), 4),
        "zero_result_rate_pct": round((zero_result_count / len(query_cases)) * 100, 2),
        "latency_percentiles_ms": {
            "p50": p50,
            "p90": p90,
            "p99": p99,
            "mean": avg_latency,
        },
        "query_details": results_per_query,
    }

    with open(report_output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n======================================================================")
    print("                      Relevance Evaluation Summary                    ")
    print("======================================================================")
    print(f"• Mean Reciprocal Rank (MRR):  {summary['mean_mrr']:.4f}")
    print(f"• Mean Precision@1:            {summary['mean_precision@1']:.4f}")
    print(f"• Mean Precision@3:            {summary['mean_precision@3']:.4f}")
    print(f"• Mean Recall@3:               {summary['mean_recall@3']:.4f}")
    print(f"• Mean nDCG@3:                 {summary['mean_ndcg@3']:.4f}")
    print(f"• Zero Result Rate:            {summary['zero_result_rate_pct']}%")
    print(f"• Latency (p50 / p90 / p99):   {p50}ms / {p90}ms / {p99}ms (Mean: {avg_latency}ms)")
    print(f"\nFull report written to: {report_output_path}")

    db.close()
    return summary


if __name__ == "__main__":
    queries_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "evaluation_queries.json"))
    report_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "evaluation_report.json"))
    run_evaluation(queries_file, report_file)

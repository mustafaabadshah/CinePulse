"""Unit tests for normalization and stable identifier generation."""

from app.ingestion.normalizer import (
    compute_payload_hash,
    generate_institution_id,
    generate_publication_id,
    generate_researcher_id,
    normalize_text,
    slugify,
)


def test_normalize_text():
    raw = "   Machine   \n\tLearning \u00a0and AI   "
    clean = normalize_text(raw)
    assert clean == "Machine Learning and AI"


def test_slugify():
    raw = "Carnegie Mellon University & Robotics!"
    assert slugify(raw) == "carnegie_mellon_university_robotics"


def test_generate_ids():
    inst_id = generate_institution_id("Stanford University")
    assert inst_id == "inst_stanford_university"

    res_id = generate_researcher_id("Dr. Yann LeCun", inst_id)
    assert res_id.startswith("res_dr_yann_lecun_")

    pub_id = generate_publication_id(
        "Attention Is All You Need", 2017, doi="10.48550/arXiv.1706.03762"
    )
    assert "10_48550_arxiv_1706_03762" in pub_id


def test_compute_payload_hash_deterministic():
    payload1 = {"name": "Test Lab", "country": "US", "year": 2026}
    payload2 = {"year": 2026, "name": "Test Lab", "country": "US"}  # Different key order
    assert compute_payload_hash(payload1) == compute_payload_hash(payload2)

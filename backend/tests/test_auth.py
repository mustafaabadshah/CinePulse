"""Tests for API authentication and security enforcement."""


def test_admin_route_requires_auth(client):
    response = client.get("/api/admin/imports")
    assert response.status_code == 401
    assert "Admin authentication required" in response.json()["detail"]


def test_admin_route_invalid_key(client):
    response = client.get("/api/admin/imports", headers={"X-Admin-API-Key": "wrong-secret"})
    assert response.status_code == 403
    assert "Invalid or expired" in response.json()["detail"]


def test_admin_route_valid_key(client, admin_headers):
    response = client.get("/api/admin/imports", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

"""Integration tests for the users API."""

from __future__ import annotations

from httpx import AsyncClient

from accountsvc.models.user import User


async def test_get_user_returns_name(client: AsyncClient, seeded_user: User) -> None:
    response = await client.get(f"/users/{seeded_user.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == seeded_user.id
    assert body["name"] == "Ada Lovelace"
    assert response.headers["x-request-id"]


async def test_get_unknown_user_returns_problem_json(client: AsyncClient) -> None:
    response = await client.get("/users/999999999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "User not found"


async def test_get_user_invalid_id_returns_422(client: AsyncClient) -> None:
    response = await client.get("/users/not-a-valid-id")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 422
    assert "errors" in body


async def test_put_user_replaces_all_fields(client: AsyncClient, seeded_user: User) -> None:
    payload = {
        "email": "ada+new@yag.dc",
        "name": "Augusta Ada King",
        "tz": "Europe/London",
        "apps_lib": {"editor": "vscode"},
        "dob": "1815-12-10",
        "is_active": False,
    }
    response = await client.put(f"/users/{seeded_user.id}", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == seeded_user.id
    assert body["email"] == "ada+new@yag.dc"
    assert body["name"] == "Augusta Ada King"
    assert body["tz"] == "Europe/London"
    assert body["apps_lib"] == {"editor": "vscode"}
    assert body["dob"] == "1815-12-10"
    assert body["is_active"] is False

    # Follow-up read reflects the persisted state.
    read = await client.get(f"/users/{seeded_user.id}")
    assert read.status_code == 200
    assert read.json() == body


async def test_put_unknown_user_returns_404(client: AsyncClient) -> None:
    payload = {
        "email": None,
        "name": None,
        "tz": "UTC",
        "apps_lib": None,
        "dob": "2000-01-01",
        "is_active": True,
    }
    response = await client.put("/users/999999999", json=payload)

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


async def test_put_missing_required_field_returns_422(client: AsyncClient, seeded_user: User) -> None:
    # 'tz' omitted → validation error (PUT requires every mutable field).
    payload = {
        "email": None,
        "name": None,
        "apps_lib": None,
        "dob": "2000-01-01",
        "is_active": True,
    }
    response = await client.put(f"/users/{seeded_user.id}", json=payload)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


async def test_patch_user_updates_only_provided_field(client: AsyncClient, seeded_user: User) -> None:
    response = await client.patch(f"/users/{seeded_user.id}", json={"name": "Ada, Countess of Lovelace"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ada, Countess of Lovelace"
    assert body["email"] == "ada@yag.dc"  # unchanged


async def test_patch_user_can_clear_nullable_field(client: AsyncClient, seeded_user: User) -> None:
    response = await client.patch(f"/users/{seeded_user.id}", json={"email": None})

    assert response.status_code == 200
    assert response.json()["email"] is None


async def test_patch_user_rejects_unknown_field(client: AsyncClient, seeded_user: User) -> None:
    response = await client.patch(f"/users/{seeded_user.id}", json={"nickname": "Ada"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


async def test_patch_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.patch("/users/999999999", json={"name": "Ghost"})

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")

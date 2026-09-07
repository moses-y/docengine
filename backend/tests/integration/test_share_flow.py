"""End-to-end sharing flow against a real Postgres (PRD §8):

create -> edit -> share -> second user reads -> revoke -> 404

Runs the FastAPI app through `httpx.AsyncClient` over ASGI, exactly as a
real HTTP client would, so it also exercises routing, Pydantic validation,
and the `ApiError` -> JSON envelope mapping in `app.main` — not just the
service layer in isolation (that's what `tests/test_permissions.py` covers).
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio]


async def _register(client, email: str, name: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "display_name": name, "password": "correct-horse-battery"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_full_share_flow(client):
    owner_token = await _register(client, "owner@example.com", "Owner")
    other_token = await _register(client, "other@example.com", "Other")

    # create
    create_resp = await client.post(
        "/api/documents", json={"title": "Q3 Roadmap"}, headers=_auth(owner_token)
    )
    assert create_resp.status_code == 201
    doc = create_resp.json()
    assert doc["my_role"] == "owner"
    assert doc["version"] == 1

    # edit — first save
    new_content = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Draft v1"}]}],
    }
    edit_resp = await client.patch(
        f"/api/documents/{doc['id']}",
        json={"content": new_content, "base_version": 1},
        headers=_auth(owner_token),
    )
    assert edit_resp.status_code == 200
    edited = edit_resp.json()
    assert edited["version"] == 2
    assert edited["content"]["content"][0]["content"][0]["text"] == "Draft v1"

    # stale write is rejected with 409, not silently overwritten
    stale_resp = await client.patch(
        f"/api/documents/{doc['id']}",
        json={"content": new_content, "base_version": 1},
        headers=_auth(owner_token),
    )
    assert stale_resp.status_code == 409
    assert stale_resp.json()["error"]["code"] == "conflict"

    # a stranger cannot see it yet — 404, not 403 (PRD §5.3)
    stranger_resp = await client.get(f"/api/documents/{doc['id']}", headers=_auth(other_token))
    assert stranger_resp.status_code == 404

    # share as viewer
    share_resp = await client.post(
        f"/api/documents/{doc['id']}/shares",
        json={"email": "other@example.com", "role": "viewer"},
        headers=_auth(owner_token),
    )
    assert share_resp.status_code == 201
    assert share_resp.json()["role"] == "viewer"

    # second user can now read...
    read_resp = await client.get(f"/api/documents/{doc['id']}", headers=_auth(other_token))
    assert read_resp.status_code == 200
    assert read_resp.json()["my_role"] == "viewer"

    # ...but cannot write (US-11: 403, since they're known to the doc now)
    forbidden_resp = await client.patch(
        f"/api/documents/{doc['id']}",
        json={"title": "Hijacked title"},
        headers=_auth(other_token),
    )
    assert forbidden_resp.status_code == 403
    assert forbidden_resp.json()["error"]["code"] == "forbidden"

    # it shows up under "shared", not "owned", for the second user
    shared_list = await client.get(
        "/api/documents", params={"scope": "shared"}, headers=_auth(other_token)
    )
    assert any(d["id"] == doc["id"] for d in shared_list.json())
    owned_list = await client.get(
        "/api/documents", params={"scope": "owned"}, headers=_auth(other_token)
    )
    assert not any(d["id"] == doc["id"] for d in owned_list.json())

    # revoke
    revoke_resp = await client.delete(
        f"/api/documents/{doc['id']}/shares/{_user_id_from_token(share_resp.json())}",
        headers=_auth(owner_token),
    )
    assert revoke_resp.status_code == 204

    # access is gone — 404 again, exactly like a stranger
    after_revoke_resp = await client.get(f"/api/documents/{doc['id']}", headers=_auth(other_token))
    assert after_revoke_resp.status_code == 404


def _user_id_from_token(share_json: dict) -> str:
    return share_json["user_id"]

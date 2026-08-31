"""
Tests for brute-force protection (auth_routes.py) and auth regression.
NOTE: lockout tracker is in-memory per email. Uses unique throwaway emails.
"""
import os
import time
import uuid

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

ADMIN = {"email": "admin@salon.com", "password": "Admin123!"}
WORKER = {"email": "worker@salon.com", "password": "Worker123!"}


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _login(client, email, password):
    return client.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})


class TestBruteForce:
    def test_attempts_1_to_5_and_lockout(self, client):
        email = f"bruteforce-{uuid.uuid4().hex[:8]}@example.com"
        messages = []
        for i in range(1, 5):
            r = _login(client, email, "WrongPass1!")
            detail = r.json().get("detail", "")
            messages.append((i, r.status_code, detail))
            assert r.status_code == 401, f"attempt {i} expected 401, got {r.status_code}: {detail}"
            assert "Pogrešan email ili lozinka" in detail

        print("Attempts 1-4:", messages)
        # attempt 4 must expose remaining attempts count
        assert "preostalo" in messages[3][2], f"4th attempt missing remaining count: {messages[3][2]}"

        # 5th attempt -> lockout
        r5 = _login(client, email, "WrongPass1!")
        d5 = r5.json().get("detail", "")
        print("Attempt 5:", r5.status_code, d5)
        assert r5.status_code == 429, f"5th attempt expected 429, got {r5.status_code}"
        assert "privremeno zaključan na 15 minuta" in d5

        # 6th attempt (even correct password would be locked) -> countdown
        r6 = _login(client, email, "WrongPass1!")
        d6 = r6.json().get("detail", "")
        print("Attempt 6:", r6.status_code, d6)
        assert r6.status_code == 429
        assert "Pokušajte ponovo za" in d6 and "min" in d6 and "sek" in d6

    def test_generic_message_first_attempts(self, client):
        """Spec: first 3 wrong attempts should show generic message with no counter."""
        email = f"bruteforce-{uuid.uuid4().hex[:8]}@example.com"
        details = []
        for _ in range(3):
            r = _login(client, email, "WrongPass1!")
            assert r.status_code == 401
            details.append(r.json().get("detail", ""))
        print("First 3 details:", details)
        assert all("preostalo" not in d for d in details), (
            f"Counter leaked in first 3 attempts (spec says generic message): {details}"
        )

    def test_independent_counters_per_email(self, client):
        email_a = f"bf-a-{uuid.uuid4().hex[:6]}@example.com"
        email_b = f"bf-b-{uuid.uuid4().hex[:6]}@example.com"
        # lock A
        for _ in range(5):
            _login(client, email_a, "WrongPass1!")
        ra = _login(client, email_a, "WrongPass1!")
        assert ra.status_code == 429
        # B must still be at attempt 1 (401, generic)
        rb = _login(client, email_b, "WrongPass1!")
        assert rb.status_code == 401, f"email B affected by A's lockout: {rb.status_code}"
        assert "preostalo" not in rb.json().get("detail", "")

    def test_success_clears_counter(self, client):
        """3 wrong attempts on real admin, then correct login, then 1 wrong -> counter reset."""
        for _ in range(3):
            r = _login(client, ADMIN["email"], "TotallyWrong1!")
            assert r.status_code == 401
        ok = _login(client, ADMIN["email"], ADMIN["password"])
        assert ok.status_code == 200, f"correct login failed: {ok.status_code} {ok.text[:300]}"
        data = ok.json()
        assert data["email"] == ADMIN["email"]
        assert data["role"] == "admin"
        assert data["slug"] == "beauty-studio-bor"
        # next wrong attempt should be treated as attempt #1 (generic, no counter)
        r = _login(client, ADMIN["email"], "TotallyWrong1!")
        assert r.status_code == 401
        assert "preostalo" not in r.json().get("detail", ""), (
            f"counter not cleared after successful login: {r.json().get('detail')}"
        )
        # restore clean state for admin
        assert _login(client, ADMIN["email"], ADMIN["password"]).status_code == 200


class TestAuthRegression:
    def test_admin_login_cookies_and_payload(self, client):
        r = _login(client, ADMIN["email"], ADMIN["password"])
        assert r.status_code == 200
        cookies = {c.name: c for c in r.cookies}
        assert "access_token" in cookies and "refresh_token" in cookies, f"cookies: {list(cookies)}"
        set_cookie_headers = r.headers.get("set-cookie", "").lower()
        assert "httponly" in set_cookie_headers
        data = r.json()
        assert data["tenant_id"] == "tenant_bsb_001"
        assert "access_token" in data
        # /auth/me with bearer
        me = client.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
        assert me.status_code == 200
        me_data = me.json()
        assert me_data["email"] == ADMIN["email"]
        assert "_id" not in me_data
        assert me_data.get("slug") == "beauty-studio-bor"

    def test_worker_login_and_account_statuses(self, client):
        r = _login(client, WORKER["email"], WORKER["password"])
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data["role"] == "worker"
        assert data["slug"] == "beauty-studio-bor"
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # worker must be denied (admin-only bulk endpoint)
        st = client.get(f"{BASE_URL}/api/workers/account-statuses", headers=headers)
        print("worker account-statuses:", st.status_code, st.text[:200])
        assert st.status_code == 403, f"expected 403 for worker, got {st.status_code}"

        # admin can read the bulk endpoint and worker's row is present
        admin = _login(client, ADMIN["email"], ADMIN["password"]).json()
        adm = client.get(
            f"{BASE_URL}/api/workers/account-statuses",
            headers={"Authorization": f"Bearer {admin['access_token']}", "X-Tenant-ID": "tenant_bsb_001"},
        )
        assert adm.status_code == 200, f"{adm.status_code} {adm.text[:300]}"
        body = adm.json()
        assert isinstance(body, dict) and body, f"unexpected payload: {body}"
        wid = data.get("worker_id")
        assert wid and wid in body, f"worker_id {wid} missing from {list(body)}"
        assert body[wid]["email"] == WORKER["email"]
        assert "_id" not in body[wid]

    def test_logout_clears_cookies(self, client):
        r = _login(client, ADMIN["email"], ADMIN["password"])
        token = r.json()["access_token"]
        out = client.post(f"{BASE_URL}/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert out.status_code == 200
        assert "Logged out" in out.json().get("message", "")

    def test_unauthenticated_me_rejected(self, client):
        s = requests.Session()
        r = s.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code in (401, 403), r.status_code

    def test_cors_credentials_explicit_origin(self, client):
        """Preflight is answered by the edge proxy on the public URL, so assert on the app directly."""
        r = requests.options(
            "http://localhost:8001/api/auth/login",
            headers={
                "Origin": BASE_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        print("CORS headers:", dict(r.headers))
        assert r.headers.get("access-control-allow-credentials") == "true", dict(r.headers)
        assert r.headers.get("access-control-allow-origin") != "*"

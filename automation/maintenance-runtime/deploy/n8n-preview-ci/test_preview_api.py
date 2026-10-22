"""OntiCards preview-specific API checks, using the existing pytest runner."""
import json
import os
from pathlib import Path

import pytest
import requests

BASE = os.environ.get("ONTICARDS_PREVIEW_URL", "http://10.66.66.5:18110")
TIMEOUT = 20


@pytest.fixture(scope="module")
def authenticated_session():
    credentials_path = os.environ.get("ONTICARDS_PREVIEW_CREDENTIALS")
    assert credentials_path, "Private synthetic preview credentials are required"
    credentials = json.loads(Path(credentials_path).read_text(encoding="utf-8"))
    session = requests.Session()
    login = session.post(BASE + "/console/api/login", json=credentials, timeout=TIMEOUT).json()
    assert login.get("code") == 200, "Synthetic login failed; response omitted"
    session.headers["Authorization"] = login["data"]["token"]
    return session


def test_api_health():
    response = requests.get(BASE + "/console/api/healthz", timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_web_login_page():
    response = requests.get(BASE + "/login", timeout=TIMEOUT)
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert "<!DOCTYPE html>" in response.text or "<!doctype html>" in response.text


def test_user_requires_authentication():
    response = requests.get(BASE + "/console/api/user", timeout=TIMEOUT)
    assert response.status_code == 401


def test_invalid_login_is_rejected():
    response = requests.post(BASE + "/console/api/login", json={"username": "synthetic_missing_account", "password": "incorrect-synthetic-password"}, timeout=TIMEOUT)
    assert response.json()["code"] == 400
    assert "token" not in response.json().get("data", {})


def test_synthetic_admin_login_and_profile():
    credentials_path = os.environ.get("ONTICARDS_PREVIEW_CREDENTIALS")
    assert credentials_path, "Set ONTICARDS_PREVIEW_CREDENTIALS to the private synthetic credential file"
    credentials = json.loads(Path(credentials_path).read_text(encoding="utf-8"))
    response = requests.post(BASE + "/console/api/login", json=credentials, timeout=TIMEOUT)
    data = response.json()
    assert data.get("code") == 200, "Synthetic preview login failed (response intentionally omitted)"
    token = data["data"]["token"]
    # Existing OntiCards API uses a raw JWT, matching api/base.ts.
    profile = requests.get(BASE + "/console/api/user", headers={"Authorization": token}, timeout=TIMEOUT)
    assert profile.status_code == 200
    assert profile.json()["data"]["username"] == credentials["username"]
    assert profile.json()["data"]["role"] == "admin"


def test_connect_synthetic_sqlite(authenticated_session):
    response = authenticated_session.post(BASE + "/console/api/connect_test", json={
        "db_type": "sqlite", "sqlite_path": "/tmp/onticards-maintenance-fixture.sqlite",
        "connect_name": "maintenance-synthetic-baseline",
    }, timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["database_type"] == "sqlite"


def test_read_synthetic_table_metadata(authenticated_session):
    response = authenticated_session.post(BASE + "/console/api/list_tables", json={
        "db_type": "sqlite", "sqlite_path": "/tmp/onticards-maintenance-fixture.sqlite",
        "connect_name": "maintenance-synthetic-baseline",
    }, timeout=TIMEOUT)
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["result"]["total"] == 1
    assert payload["result"]["tables"] == [{"name": "maintenance_orders", "type": "TABLE"}]

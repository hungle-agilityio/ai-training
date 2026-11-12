import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings

APP_DIR = Path(__file__).resolve().parents[3]
HEALTHZ_EXEMPT = [r"^healthz/$"]
SILENCED = ["security.W005", "security.W021"]
SETTING_NAMES = [
    "SECURE_SSL_REDIRECT",
    "SECURE_REDIRECT_EXEMPT",
    "SECURE_HSTS_SECONDS",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
    "SILENCED_SYSTEM_CHECKS",
]
PRINT_SETTINGS = (
    "import json, reviewradar.settings as s; "
    f"print(json.dumps({{n: getattr(s, n) for n in {SETTING_NAMES!r}}}))"
)


def _clean_env(**env: str) -> dict[str, str]:
    """Process environment without any DJANGO_* variable, plus the given ones."""
    base = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    return {**base, **env}


def _load_settings(env: dict[str, str]) -> dict[str, object]:
    """Import the settings module in a fresh process and return the security values."""
    result = subprocess.run(
        [sys.executable, "-c", PRINT_SETTINGS],
        cwd=APP_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    loaded: dict[str, object] = json.loads(result.stdout.strip().splitlines()[-1])
    return loaded


@pytest.mark.django_db
def test_login_page_refuses_to_be_shown_in_a_frame(client: Client) -> None:
    response = client.get("/login/")

    assert response.headers["X-Frame-Options"] == "DENY"


def test_production_settings_redirect_to_https_and_send_one_year_hsts() -> None:
    env = _clean_env(DJANGO_DEBUG="0", DJANGO_SECRET_KEY=secrets.token_urlsafe(50))

    assert _load_settings(env) == {
        "SECURE_SSL_REDIRECT": True,
        "SECURE_REDIRECT_EXEMPT": HEALTHZ_EXEMPT,
        "SECURE_HSTS_SECONDS": 31536000,
        "SECURE_HSTS_INCLUDE_SUBDOMAINS": False,
        "SECURE_HSTS_PRELOAD": False,
        "SILENCED_SYSTEM_CHECKS": SILENCED,
    }


def test_development_settings_keep_http_and_turn_hsts_off() -> None:
    loaded = _load_settings(_clean_env(DJANGO_DEBUG="1"))

    assert loaded["SECURE_SSL_REDIRECT"] is False
    assert loaded["SECURE_HSTS_SECONDS"] == 0
    assert loaded["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is False
    assert loaded["SECURE_HSTS_PRELOAD"] is False
    assert loaded["SECURE_REDIRECT_EXEMPT"] == HEALTHZ_EXEMPT
    assert loaded["SILENCED_SYSTEM_CHECKS"] == SILENCED


def test_default_settings_without_debug_variable_keep_http() -> None:
    loaded = _load_settings(_clean_env())

    assert loaded["SECURE_SSL_REDIRECT"] is False
    assert loaded["SECURE_HSTS_SECONDS"] == 0


def test_deploy_check_with_production_settings_reports_no_issues() -> None:
    env = _clean_env(
        DJANGO_DEBUG="0",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(50),
        DJANGO_ALLOWED_HOSTS="reviewradar.onrender.com",
    )

    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
        cwd=APP_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "System check identified no issues (2 silenced)." in output


@pytest.mark.django_db
def test_https_redirect_exempts_healthz_and_hsts_is_sent_over_https() -> None:
    user = get_user_model().objects.create_user(username="anna", password="pw-for-tests-1")
    with override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=False,
        SECURE_HSTS_PRELOAD=False,
    ):
        client = Client()
        client.force_login(user)

        redirected = client.get("/dashboard/")
        health = Client().get("/healthz/")
        secure = client.get("/dashboard/", headers={"X-Forwarded-Proto": "https"})

    assert redirected.status_code == 301
    assert redirected["Location"] == "https://testserver/dashboard/"
    assert health.status_code == 200
    assert health.content == b"ok"
    assert secure.headers["Strict-Transport-Security"] == "max-age=31536000"

import importlib
from pathlib import Path

import pytest
from django.conf import settings as django_settings

import reviewradar.settings as project_settings


def reload_settings() -> object:
    return importlib.reload(project_settings)


def test_database_defaults_to_the_local_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_DB_NAME", raising=False)

    module = reload_settings()

    assert Path(module.DATABASES["default"]["NAME"]) == module.BASE_DIR / "db.sqlite3"  # type: ignore[attr-defined]


def test_database_file_can_be_set_with_an_environment_variable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "demo.sqlite3"
    monkeypatch.setenv("DJANGO_DB_NAME", str(target))

    module = reload_settings()

    assert Path(module.DATABASES["default"]["NAME"]) == target  # type: ignore[attr-defined]


def test_the_running_test_settings_are_untouched_by_the_reloads() -> None:
    assert django_settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"

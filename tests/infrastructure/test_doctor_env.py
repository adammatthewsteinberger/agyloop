"""DoctorEnvironment resolves GOOGLE_API_KEY vs ADC without guessing the lane."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agyloop.infrastructure.doctor_env import RealDoctorEnvironment


def _env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    home: Path,
    values: dict[str, str | None],
) -> RealDoctorEnvironment:
    for key in (
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_GENAI_USE_ENTERPRISE",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "CLOUDSDK_CONFIG",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    return RealDoctorEnvironment(environ=os.environ, home=home)


def test_google_api_key_selects_developer_api_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(monkeypatch, home=tmp_path, values={"GOOGLE_API_KEY": "test-key"})
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "developer_api"
    assert auth.source == "GOOGLE_API_KEY"


def test_adc_credentials_file_is_reported_without_guessing_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adc = tmp_path / "adc.json"
    adc.write_text("{}", encoding="utf-8")
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={"GOOGLE_APPLICATION_CREDENTIALS": str(adc)},
    )
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "unresolved"
    assert auth.source == "GOOGLE_APPLICATION_CREDENTIALS"


def test_well_known_adc_is_reported_as_adc_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    well_known = tmp_path / ".config" / "gcloud" / "application_default_credentials.json"
    well_known.parent.mkdir(parents=True)
    well_known.write_text("{}", encoding="utf-8")
    env = _env(monkeypatch, home=tmp_path, values={})
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "unresolved"
    assert auth.source == "ADC_WELL_KNOWN"


def test_vertex_env_plus_adc_selects_enterprise_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adc = tmp_path / "adc.json"
    adc.write_text("{}", encoding="utf-8")
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
            "GOOGLE_APPLICATION_CREDENTIALS": str(adc),
            "GOOGLE_CLOUD_PROJECT": "proj",
        },
    )
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "enterprise"
    assert "GOOGLE_GENAI_USE_VERTEXAI" in auth.source


def test_gemini_api_key_selects_developer_api_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(monkeypatch, home=tmp_path, values={"GEMINI_API_KEY": "gemini-key"})
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "developer_api"
    assert auth.source == "GEMINI_API_KEY"


def test_google_api_key_wins_over_gemini_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={"GOOGLE_API_KEY": "google-key", "GEMINI_API_KEY": "gemini-key"},
    )
    auth = env.resolve_auth()
    assert auth.source == "GOOGLE_API_KEY"


def test_neither_api_key_nor_adc_is_unauthenticated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(monkeypatch, home=tmp_path, values={})
    auth = env.resolve_auth()
    assert auth.authenticated is False
    assert auth.lane == "unresolved"
    assert auth.source == "none"


def test_conflicting_api_key_and_vertex_does_not_guess_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={"GOOGLE_API_KEY": "key", "GOOGLE_GENAI_USE_VERTEXAI": "true"},
    )
    auth = env.resolve_auth()
    assert auth.lane == "unresolved"
    assert auth.authenticated is False
    assert "conflict" in auth.source or "conflict" in auth.detail.lower()


def test_doctor_asserts_no_interactive_hooks() -> None:
    env = RealDoctorEnvironment()
    assert env.interactive_hooks_registered() is False

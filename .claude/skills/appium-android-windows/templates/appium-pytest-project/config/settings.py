"""Central configuration. Every machine-specific value comes from env vars / .env.

Nothing in this file is a real path, device serial or secret: only variable names
and safe, generic defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# .env is optional; real environment variables always win (override=False).
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    raw = _str(name)
    return int(raw) if raw else default


def _opt_int(name: str) -> int | None:
    raw = _str(name)
    return int(raw) if raw else None


def _bool(name: str, default: bool) -> bool:
    raw = _str(name).lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Server / general
    appium_server_url: str
    explicit_wait: int
    new_command_timeout: int
    artifacts_dir: Path
    target_platform: str

    # Android
    android_udid: str
    android_avd: str
    android_avd_launch_timeout_ms: int
    android_app: str
    android_app_package: str
    android_app_activity: str
    android_app_wait_activity: str
    android_no_reset: bool
    android_auto_grant_permissions: bool

    # Windows
    windows_app: str
    windows_top_level_window: str
    windows_app_arguments: str
    windows_app_working_dir: str
    windows_create_session_timeout_ms: int
    windows_wait_for_app_launch_s: int | None


def load_settings() -> Settings:
    artifacts = Path(_str("ARTIFACTS_DIR", "artifacts"))
    if not artifacts.is_absolute():
        artifacts = PROJECT_ROOT / artifacts
    return Settings(
        appium_server_url=_str("APPIUM_SERVER_URL", "http://127.0.0.1:4723").rstrip("/"),
        explicit_wait=_int("EXPLICIT_WAIT_SECONDS", 15),
        new_command_timeout=_int("NEW_COMMAND_TIMEOUT_SECONDS", 120),
        artifacts_dir=artifacts,
        target_platform=_str("TARGET_PLATFORM", "android").lower(),
        android_udid=_str("ANDROID_UDID"),
        android_avd=_str("ANDROID_AVD"),
        android_avd_launch_timeout_ms=_int("ANDROID_AVD_LAUNCH_TIMEOUT_MS", 180_000),
        android_app=_str("ANDROID_APP"),
        android_app_package=_str("ANDROID_APP_PACKAGE"),
        android_app_activity=_str("ANDROID_APP_ACTIVITY"),
        android_app_wait_activity=_str("ANDROID_APP_WAIT_ACTIVITY"),
        android_no_reset=_bool("ANDROID_NO_RESET", False),
        android_auto_grant_permissions=_bool("ANDROID_AUTO_GRANT_PERMISSIONS", True),
        windows_app=_str("WINDOWS_APP"),
        windows_top_level_window=_str("WINDOWS_TOP_LEVEL_WINDOW"),
        windows_app_arguments=_str("WINDOWS_APP_ARGUMENTS"),
        windows_app_working_dir=_str("WINDOWS_APP_WORKING_DIR"),
        windows_create_session_timeout_ms=_int("WINDOWS_CREATE_SESSION_TIMEOUT_MS", 30_000),
        windows_wait_for_app_launch_s=_opt_int("WINDOWS_WAIT_FOR_APP_LAUNCH_SECONDS"),
    )

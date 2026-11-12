"""Driver factory: picks Android or Windows and builds a *separate* Options object for each.

Rules enforced here:
- Appium 2.x: plain server URL (no /wd/hub), Options classes, appium:-prefixed caps.
- One builder per platform; capability objects are never shared or reused.
- Implicit wait stays at 0 so only explicit waits are used.
"""
from __future__ import annotations

import logging

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.windows import WindowsOptions

from config.settings import Settings

log = logging.getLogger(__name__)

ANDROID = "android"
WINDOWS = "windows"
SUPPORTED_PLATFORMS = (ANDROID, WINDOWS)


def build_android_options(cfg: Settings) -> UiAutomator2Options:
    """UiAutomator2 capabilities: emulator vs real device, apk vs installed package."""
    o = UiAutomator2Options()  # platformName=Android, appium:automationName=UiAutomator2

    # Device selection: udid (real device / running emulator) and/or avd (Appium boots it).
    if cfg.android_udid:
        o.udid = cfg.android_udid
    if cfg.android_avd:
        o.avd = cfg.android_avd
        o.avd_launch_timeout = cfg.android_avd_launch_timeout_ms
        o.avd_ready_timeout = cfg.android_avd_launch_timeout_ms

    # App selection: install from file, or launch an already-installed package.
    if cfg.android_app:
        o.app = cfg.android_app
        # appPackage/appActivity are auto-detected from the apk, but passing them
        # lets the driver verify the right activity came up.
        if cfg.android_app_package:
            o.app_package = cfg.android_app_package
        if cfg.android_app_activity:
            o.app_activity = cfg.android_app_activity
    elif cfg.android_app_package and cfg.android_app_activity:
        o.app_package = cfg.android_app_package
        o.app_activity = cfg.android_app_activity
    else:
        raise ValueError(
            "Android app not configured: set ANDROID_APP, or ANDROID_APP_PACKAGE "
            "and ANDROID_APP_ACTIVITY (see .env.example)."
        )
    if cfg.android_app_wait_activity:
        o.app_wait_activity = cfg.android_app_wait_activity

    o.no_reset = cfg.android_no_reset
    o.auto_grant_permissions = cfg.android_auto_grant_permissions
    o.new_command_timeout = cfg.new_command_timeout
    return o


def build_windows_options(cfg: Settings) -> WindowsOptions:
    """Windows driver capabilities: launch by AUMID/exe path, or attach to a window handle."""
    o = WindowsOptions()  # platformName=Windows, appium:automationName=Windows

    if cfg.windows_top_level_window:
        o.app_top_level_window = cfg.windows_top_level_window  # e.g. "0x1A2B3C"
    elif cfg.windows_app:
        o.app = cfg.windows_app  # AUMID (UWP), full .exe path (classic) or "Root"
    else:
        raise ValueError(
            "Windows app not configured: set WINDOWS_APP or WINDOWS_TOP_LEVEL_WINDOW "
            "(see .env.example)."
        )
    if cfg.windows_app_arguments:
        o.app_arguments = cfg.windows_app_arguments
    if cfg.windows_app_working_dir:
        o.app_working_dir = cfg.windows_app_working_dir

    o.create_session_timeout = cfg.windows_create_session_timeout_ms
    if cfg.windows_wait_for_app_launch_s:
        o.wait_for_app_launch = cfg.windows_wait_for_app_launch_s
    o.new_command_timeout = cfg.new_command_timeout
    return o


_BUILDERS = {
    ANDROID: build_android_options,
    WINDOWS: build_windows_options,
}


def create_driver(platform: str, cfg: Settings) -> webdriver.Remote:
    """Start a new Appium session for `platform` ("android" | "windows")."""
    platform = platform.lower()
    if platform not in _BUILDERS:
        raise ValueError(f"Unsupported platform {platform!r}; expected one of {SUPPORTED_PLATFORMS}")

    options = _BUILDERS[platform](cfg)  # fresh object per session, never shared
    log.info("Starting %s session at %s", platform, cfg.appium_server_url)
    log.debug("Capabilities: %s", options.to_capabilities())

    driver = webdriver.Remote(cfg.appium_server_url, options=options)
    driver.implicitly_wait(0)  # explicit waits only
    log.info("Session %s started", driver.session_id)
    return driver

"""Shared pytest fixtures: config, platform-aware driver, failure artifacts, guaranteed quit."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import pytest

from config.settings import Settings, load_settings
from core.driver_factory import SUPPORTED_PLATFORMS, create_driver

log = logging.getLogger("conftest")


@pytest.fixture(scope="session")
def settings() -> Settings:
    cfg = load_settings()
    cfg.artifacts_dir.mkdir(parents=True, exist_ok=True)
    return cfg


def _platform_for(request: pytest.FixtureRequest, cfg: Settings) -> str:
    """Platform comes from the test's marker (@pytest.mark.android / .windows), else config."""
    marked = [p for p in SUPPORTED_PLATFORMS if request.node.get_closest_marker(p)]
    if len(marked) > 1:
        raise pytest.UsageError(f"{request.node.nodeid} has more than one platform marker: {marked}")
    return marked[0] if marked else cfg.target_platform


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Expose each phase's report on the item so fixtures can see if the test failed."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def _save_failure_artifacts(driver, node, artifacts_dir: Path) -> None:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", node.nodeid)[-150:]
    base = artifacts_dir / f"{safe}-{stamp}"
    try:
        driver.get_screenshot_as_file(str(base.with_suffix(".png")))
        base.with_suffix(".xml").write_text(driver.page_source, encoding="utf-8")
        log.error("Failure artifacts saved: %s.{png,xml}", base)
    except Exception as exc:  # artifacts must never mask the real failure
        log.warning("Could not capture failure artifacts: %s", exc)


@pytest.fixture
def driver(request: pytest.FixtureRequest, settings: Settings):
    """One fresh Appium session per test; always quit, even if the test or capture fails."""
    platform = _platform_for(request, settings)
    drv = create_driver(platform, settings)
    try:
        yield drv
    finally:
        try:
            rep = getattr(request.node, "rep_call", None)
            if rep is not None and rep.failed:
                _save_failure_artifacts(drv, request.node, settings.artifacts_dir)
        finally:
            log.info("Quitting session %s", drv.session_id)
            drv.quit()

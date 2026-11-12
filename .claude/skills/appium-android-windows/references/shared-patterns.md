# Shared patterns (Android + Windows, Python + pytest)

The runnable reference implementation of everything here is
`templates/appium-pytest-project/`. When generating a new project, copy it and adapt it rather
than writing from scratch.

## 1. Project layout

```
project/
├── .env.example            # documented env vars (committed); .env holds real values (ignored)
├── pytest.ini              # markers, pythonpath, logging
├── requirements.txt        # pinned: Appium-Python-Client, pytest, python-dotenv
├── config/settings.py      # env → frozen dataclass; the ONLY place env vars are read
├── core/
│   ├── driver_factory.py   # one Options builder per platform + create_driver(platform, cfg)
│   └── waits.py            # WebDriverWait wrappers
├── pages/
│   ├── base_page.py        # platform-agnostic helpers
│   ├── android/…_page.py   # Android page objects (AppiumBy locators as class constants)
│   └── windows/…_page.py   # Windows page objects
├── tests/
│   ├── conftest.py         # settings + driver fixtures, failure artifacts, teardown
│   ├── android/test_*.py   # @pytest.mark.android
│   └── windows/test_*.py   # @pytest.mark.windows
└── artifacts/              # screenshots, page sources, logs (git-ignored)
```

Keep Android and Windows page objects in **separate packages**. A Windows page never
imports Android locators, and the reverse is also true.

## 2. Page Object Model

- Locators are **class-level tuples** `(AppiumBy.X, "value")`, listed in priority order
  (accessibility id first). Each XPath carries a `# XPath because …` comment.
- Methods describe user intent (`login(user, pw)`, `calculate(1, "+", 2)`) and return the
  next page object when navigation happens.
- Page methods wait internally (`self.wait.visible(...)`), so tests never wait or sleep.
- Assertions live in tests, not pages. Pages may expose state (`result()`, `is_displayed()`).
- Each page has `wait_until_loaded()` that waits for one stable anchor element.

```python
class LoginPage(BasePage):
    USERNAME = (AppiumBy.ACCESSIBILITY_ID, "username")
    PASSWORD = (AppiumBy.ACCESSIBILITY_ID, "password")
    SUBMIT   = (AppiumBy.ACCESSIBILITY_ID, "login")

    def wait_until_loaded(self):
        self.wait.visible(self.USERNAME)
        return self

    def login(self, user: str, password: str) -> "HomePage":
        self.type_text(self.USERNAME, user)
        self.type_text(self.PASSWORD, password)
        self.tap(self.SUBMIT)
        return HomePage(self.driver, self.timeout).wait_until_loaded()
```

Credentials come from env vars (`APP_USER`, `APP_PASSWORD`) through `Settings`, never from literals.

## 3. Driver factory: platform picked from config

```python
_BUILDERS = {"android": build_android_options, "windows": build_windows_options}

def create_driver(platform: str, cfg: Settings) -> webdriver.Remote:
    options = _BUILDERS[platform.lower()](cfg)      # new Options object per session
    driver = webdriver.Remote(cfg.appium_server_url, options=options)   # no /wd/hub
    driver.implicitly_wait(0)                       # explicit waits only
    return driver
```

Platform resolution in `conftest.py`:
1. the test's marker (`@pytest.mark.android` / `@pytest.mark.windows`), else
2. `TARGET_PLATFORM` from env/.env.

Never build one capabilities dict and tweak it per platform. The two builders share nothing
except `cfg`.

## 4. Fixtures and guaranteed teardown

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

@pytest.fixture
def driver(request, settings):
    drv = create_driver(_platform_for(request, settings), settings)
    try:
        yield drv
    finally:
        try:
            if getattr(request.node, "rep_call", None) and request.node.rep_call.failed:
                _save_failure_artifacts(drv, request.node, settings.artifacts_dir)
        finally:
            drv.quit()          # ALWAYS runs
```

- Default scope is **function**: a fresh session per test. That's the most isolated option and
  is required for Windows (WAD state leaks easily).
- For long Android suites you may use `scope="module"` with `noReset=True`, plus a per-test
  fixture that resets app state (`terminate_app` + `activate_app`, or a deep link).
- If you write a standalone script without pytest, use `try/finally: driver.quit()`.

## 5. Explicit waits

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, cfg.explicit_wait, poll_frequency=0.25)
wait.until(EC.visibility_of_element_located(LOCATOR))
wait.until(EC.element_to_be_clickable(LOCATOR)).click()
wait.until(EC.invisibility_of_element_located(SPINNER))
wait.until(lambda d: d.query_app_state(pkg) == 4)              # custom condition
wait.until(lambda d: len(d.window_handles) > 1)                # Windows: new window
```

Rules:
- **Never** `time.sleep()`. To wait for something, express it as a condition.
- Keep the implicit wait at 0. Mixing implicit and explicit waits multiplies timeouts.
- `find_elements` (plural) returns `[]` immediately. Use it for "is it there right now?" checks.
- Timeouts come from config (`EXPLICIT_WAIT_SECONDS`). Allow longer timeouts for real devices
  and first app launch.

## 6. Screenshots and page source on failure

Saved by the `driver` fixture (see §4) to `artifacts/<nodeid>-<timestamp>.png/.xml`. The capture
is wrapped in `try/except`, so a dead session can't hide the original failure. For ad-hoc
evidence inside a test, use `driver.get_screenshot_as_file(str(cfg.artifacts_dir / "step.png"))`.

Optional video: Android `driver.start_recording_screen()` / `stop_recording_screen()`. Windows
`windows: startRecordingScreen` / `windows: stopRecordingScreen` (needs ffmpeg in PATH).

## 7. Logging

`pytest.ini`:

```ini
log_cli = true
log_cli_level = INFO
log_file = artifacts/test-run.log
log_file_level = DEBUG
```

- Use `logging.getLogger(__name__)`, not `print`.
- Log capabilities at DEBUG, after confirming they contain no secrets.
- Keep the **Appium server log**: `appium --log appium.log --log-timestamp`. Most failure
  root causes are only visible there. Attach it to bug reports.
- Android device log: `driver.get_log("logcat")` (available unless `skipLogcatCapture`).

## 8. Config and environment variables

- One module (`config/settings.py`) reads env vars. Everything else receives a `Settings` object.
- `.env` (git-ignored) is loaded with `python-dotenv` using `override=False`, so real env vars
  and CI secrets win.
- `.env.example` documents every variable with safe placeholders. Update it whenever you add one.
- Required-but-missing values raise a clear `ValueError` naming the variable.

| Variable | Used for |
|---|---|
| `APPIUM_SERVER_URL` | `http://127.0.0.1:4723` (Appium 2, no base path) |
| `EXPLICIT_WAIT_SECONDS`, `NEW_COMMAND_TIMEOUT_SECONDS` | timeouts |
| `ANDROID_UDID` / `ANDROID_AVD` | device selection |
| `ANDROID_APP` or `ANDROID_APP_PACKAGE` + `ANDROID_APP_ACTIVITY` | app selection |
| `WINDOWS_APP` / `WINDOWS_TOP_LEVEL_WINDOW` | AUMID / exe path / window handle |
| `TARGET_PLATFORM` | default platform for unmarked tests |
| `APP_USER`, `APP_PASSWORD` (example) | credentials, from env or CI secrets only |

## 9. Running

```powershell
pytest -m android            # Android tests only
pytest -m windows            # Windows tests only
pytest -m "android or windows" -v
pytest -k calculator --maxfail=1
```

Markers are declared in `pytest.ini` with `--strict-markers`, so typos fail fast.

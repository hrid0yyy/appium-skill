# Core + template audit: SKILL.md, setup.md, shared-patterns.md, templates/appium-pytest-project

Scope: the router and shared files listed above, checked against the installed packages (appium 2.19.0, @appium/base-driver 9.18.0, appium-uiautomator2-driver 4.2.9, appium-windows-driver 4.4.7, Appium-Python-Client 6.1.5, selenium 4.52.0, pytest 9.2.0, python-dotenv 1.2.4), the npm and PyPI registries, a local Appium 2.19 server, and offline pytest runs of a copy of the template. Paths below are relative to `/home/user/appium-skill/.claude/skills/appium-android-windows/`. `SCRATCH` stands for `/tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad`.

Severity: **HIGH** = generated code or setup is broken; **MED** = misleading, or breaks in common situations; **LOW** = minor or polish.

## Q1. Is the `--allow-insecure` guidance correct for Appium 2.19 (prefix syntax, case, comma list)?

### Takeaway
The command in setup.md is correct in the source: `appium --allow-insecure uiautomator2:adb_shell,windows:power_shell` turns on `adb_shell` only for UiAutomator2 sessions and `power_shell` only for Windows sessions. The prefix must be the **lowercase driver extension name**: `UiAutomator2:adb_shell` is silently ignored on 2.19. There is one real risk. In PowerShell, the unquoted comma list goes through npm's `appium.ps1` shim and probably gets split, so the value should be quoted.

### Cited Findings
- `validateFeatures` adds `*:` to bare names ("backward compatibility with Appium2 … In Appium3 the separator will be mandatory"). `filterInsecureFeatures(features, driverName)` keeps a feature only when `[driverName, '*'].includes(automationName)`. This is an exact, case-sensitive string compare — [SCRATCH/appium-test/node_modules/appium/build/lib/insecure-features.js](file:///tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/appium-test/node_modules/appium/build/lib/insecure-features.js)
- In the umbrella driver, `driverName` is the extension key returned by `findMatchingDriver` (`appium.js:255,269`). That key comes from extensions.yaml: `drivers: uiautomator2: …` and `windows: …`, both lowercase. The automationNames themselves are `UiAutomator2` and `Windows` — [SCRATCH/appium-test/home/node_modules/.cache/appium/extensions.yaml]; [appium/build/lib/extension/driver-config.js:125-156]
- The driver-side check `BaseDriver.isFeatureEnabled` in base-driver 9.18.0 is case-insensitive: it compares `_.toLower(prefix)` with `_.toLower(this.opts.automationName)` — [SCRATCH/appium-test/home/node_modules/@appium/base-driver/build/lib/basedriver/core.js:183-210]
- I tested this with node by calling the real `configureGlobalFeatures`/`configureDriverFeatures` and `BaseDriver.isFeatureEnabled` (no server needed). Results:
  - `["uiautomator2:adb_shell","windows:power_shell"]` gives UiAutomator2 adb_shell=true, power_shell=false, and Windows power_shell=true, adb_shell=false.
  - `["adb_shell"]` becomes `*:adb_shell`, which is on for both drivers.
  - `["UiAutomator2:adb_shell"]` leaves `allowInsecure=[]` for both drivers, so adb_shell=false. **It fails silently.**
  - Script: [SCRATCH/audit/insec.cjs](file:///tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/audit/insec.cjs)
- The schema declares `allow-insecure` as `type: array` with `appiumCliTransformer: 'csv'`. `transformers.csv('uiautomator2:adb_shell,windows:power_shell')` returns `['uiautomator2:adb_shell','windows:power_shell']`. If the value names an existing file, the file is read as CSV instead — [SCRATCH/appium-test/node_modules/@appium/schema/lib/appium-config-schema.js:47-58]; [appium/build/lib/schema/cli-transformers.js:60-83]
- Feature names in the drivers: `adb_shell` (appium-android-driver `utils.js:14`) is checked by `mobile: shell` (`shell.js:13`) and by `mobile: changePermissions` only when `target` is `appops` (`permissions.js:66-68`). `power_shell` is checked by `prerun`/`postrun` (`driver.js:160,198`) and by `execute_script("powerShell", …)` (`commands/execute.js:19-20`). `modify_fs` is checked by `windows: deleteFile`, `windows: deleteFolder` **and `pushFile`** (`file-movement.js:32,84,102`). So setup.md's table is correct but leaves out `push_file` under `windows:modify_fs`.
- The official 2.x security guide says: "Since Appium server version `2.13` … prefixing each feature name with the `automationName` of the driver … `appium --allow-insecure=uiautomator2:adb_shell,xcuitest:get_server_logs,*:record_audio` … Feature provided without an explicit prefix are equivalent to having the wildcard prefix … Starting from Appium 3, the scope prefix is required" — [appium security.md (2.x branch)](https://raw.githubusercontent.com/appium/appium/2.x/packages/appium/docs/en/guides/security.md)
- PowerShell rule: "Commas (`,`) introduce lists passed as arrays, unless the command being called is a native application, in which case they're interpreted as part of the expandable string." `CMD /CECHO $AB` with an array gives `'A B'` — [about_Parsing](https://raw.githubusercontent.com/MicrosoftDocs/PowerShell-Docs/main/reference/7.4/Microsoft.PowerShell.Core/About/about_Parsing.md)
- npm's cmd-shim writes an `appium.ps1` next to `appium.cmd`. The shim body is `& "node$exe" "…" $args`, so in PowerShell `appium` runs a **script**, not a native application — [/opt/node24/lib/node_modules/npm/node_modules/cmd-shim/lib/index.js:175-234]

### Inferences
- **setup.md line 288 (MED, PLAUSIBLE, not run on Windows):** `appium --allow-insecure uiautomator2:adb_shell,windows:power_shell` typed in PowerShell runs `appium.ps1`, so the comma probably builds a 2-element array inside `$args`. Node would then receive either two arguments (argparse error, "Unrecognized arguments") or one value joined with a space. A joined value becomes a single feature, `uiautomator2` + `adb_shell windows:power_shell`, and nothing is enabled, with no error. **Fix:** quote it: `appium --allow-insecure "uiautomator2:adb_shell,windows:power_shell"`. The `=` form (`--allow-insecure=...`) in Appium's docs is also safer when quoted. Quoting is harmless in cmd and bash.
- **setup.md line 286-287 / 300 (LOW, add a warning):** add "The prefix is the lowercase driver name as shown by `appium driver list` (`uiautomator2`, `windows`), not the automationName spelling `UiAutomator2`/`Windows`. A wrong case is ignored without any error on 2.19." The Appium doc says "automationName", which suggests the CamelCase form works; on the 2.19 umbrella it does not.
- setup.md line 298: suggest `windows: deleteFile`, `windows: deleteFolder`, `driver.push_file(...)`.
- Bare names apply to all drivers (line 300): CONFIRMED.

### Gaps
- I could not run PowerShell (my attempt to download pwsh was blocked), so the `.ps1` comma-splitting outcome is inferred from Microsoft docs plus the shim source, not observed.

## Q2. Are the other CLI commands and flags in setup.md correct?

### Takeaway
All flags and subcommands exist with the stated meaning. One statement is wrong in practice: `appium driver update <name>` does not "move to the newest version that is safe for the installed server". It only stays within the current major version, and it does **not** check server compatibility. With the pinned versions it **errors out and tells you to re-run with `--unsafe`**, so an agent following the error text would break the install.

### Cited Findings
- Schema (Appium 2.19):
  - `address` default `'0.0.0.0'`, `port` default `4723`, `base-path` default `''` (alias `pa`)
  - `session-override` boolean "Enables session override (clobbering)"
  - `log` (alias `g`, dest `logFile`) "Also send log output to this file"
  - `log-timestamp` boolean "Show timestamps in console output"
  - `relaxed-security` (dest `relaxedSecurityEnabled`)
  - Source: [SCRATCH/appium-test/node_modules/@appium/schema/lib/appium-config-schema.js:23-277]
- The live server confirms the defaults: `GET /status` returns `{"ready":true,…"build":{"version":"2.19.0"}}`, and `GET /wd/hub/status` returns **404** — local run of `APPIUM_HOME=$PWD/home npx appium --session-override --log … --log-timestamp` (stopped afterwards), log at [SCRATCH/audit/appium.log](file:///tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/audit/appium.log)
- `--unsafe` help text: "Include any available major revision updates, which may have breaking changes" — [appium/build/lib/cli/args.js:188-193]
- In the `_update` code path: `if (!unsafe && !update.safeUpdate) throw … 'has a major revision update … re-run with --unsafe'`. `safeUpdate` comes from `npm.getLatestSafeUpgradeVersion`, which means "not crossing any major revision boundaries" (@appium/support `npm.js:146-176`). `updateExtension` → `installViaNpm` does **not** call `_checkInstallCompatibility`; only `_install` does, at line 358 — [appium/build/lib/cli/extension-command.js:541-656]
- Observed output: `appium driver update uiautomator2` printed `✖ 'uiautomator2' failed to update: Error: ✖ The driver 'uiautomator2' has a major revision update (4.2.9 => 9.0.2), which could include breaking changes. If you want to apply this update, re-run with --unsafe`. `appium driver list --installed --updates` printed `uiautomator2@4.2.9 [installed (npm)] [9.0.2 available (potentially unsafe)]` and `windows@4.4.7 [installed (npm)] [6.3.1 available (potentially unsafe)]` — local run, Nov 12 2026
- 4.2.9 is the last 4.x of appium-uiautomator2-driver (dist-tags latest 9.0.2). 4.4.7 is the last 4.x of appium-windows-driver (latest 6.3.1). 2.19.0 is the last appium 2.x (latest 3.9.0, beta 4.0.0-beta.7) — [npm registry](https://registry.npmjs.org/appium-uiautomator2-driver), [windows](https://registry.npmjs.org/appium-windows-driver), [appium](https://registry.npmjs.org/appium)
- Peer dependencies:
  - uiautomator2 4.2.9: `appium: ^2.4.1 || ^3.0.0-beta.0`
  - uiautomator2 5.0.0 and 8.0.0: `^3.0.0-rc.2`
  - uiautomator2 9.0.2: `^4.0.0-beta.6` (node `^22.22.2 || ^24.15.0 || >=26`)
  - windows 4.4.7: `^2.4.0`
  - windows 5.0.0 and 6.3.1: `^3.0.0-rc.2`
  - Sources: [npm registry per-version docs](https://registry.npmjs.org/appium-uiautomator2-driver/4.2.9). This confirms the setup.md version matrix and the pitfall message `(^4.0.0-beta.6)`. Small detail: 4.2.9's peer also allows Appium 3 betas, which does not matter here.
- The `install` compatibility error text is `'…' cannot be installed because the server version it requires (…) does not meet the currently installed one (…)` — [extension-command.js:244-255]. This matches setup.md line 178.
- `appium driver list --installed` output format, run under Node 24: `- uiautomator2@4.2.9 [installed (npm)]` and `- windows@4.4.7 [installed (npm)]`. This matches setup.md lines 201-202.
- `appium driver doctor windows` prints `The driver "windows" does not export any doctor checks` (observed; source extension-command.js:699). Doctor summary text: `util.pluralize('required fix', n, true) + ' needed'`, which gives "0 required fixes needed" — [appium/build/lib/doctor/doctor.js:195]
- `appium driver run <driver> [scriptName]` passes extra arguments through (`parse_known_args` → `extraArgs`, parser.js:94-150). `install-wad.mjs` uses `process.argv[2] ?? STABLE_VERSION`, so `install-wad 1.2.1` is valid. The script calls `Array.prototype.toSorted`, which **needs Node ≥ 20** — [SCRATCH/appium-test/home/node_modules/appium-windows-driver/scripts/install-wad.mjs:95-177]
- `appium driver uninstall <name>` exists (args.js:134-150). `APPIUM_WAD_PATH` is read (installer.js:47). The WAD port range is `[4724, 4824]` (winappdriver.js:19). The `wadUrl` capability exists (desired-caps.js:50).

### Inferences
- **setup.md lines 205-206 (MED):** Replace with: "`appium driver update <name>` only updates within the current major version, and it does not check that the new version supports your server. With the pinned versions there is no newer 4.x, so it prints *'has a major revision update (4.2.9 => 9.0.2) … re-run with --unsafe'*. **Ignore that advice.** `--unsafe` installs a driver that needs Appium 3/4, with no compatibility check, and the server will then fail to load or run it. To change versions, run `appium driver uninstall <name>` and then `appium driver install <name>@<4.x version>`." Also mention `appium driver list --installed --updates`, which shows the `(potentially unsafe)` majors.
- The `--session-override --log-timestamp --log appium.log` line and the `--relaxed-security` note: CONFIRMED.

### Gaps
- I did not check whether Windows driver ≥3.0.0 really stopped installing WAD automatically (setup.md line 172). The changelog is not in the installed package. The existence of the `install-wad` script fits the claim.

## Q3. Node.js advice and winget id

### Takeaway
The engines quote is correct. The "20 LTS or 22 LTS" advice is out of date for Nov 2026: Node 20 reached end of life on 2026-04-30. `winget install OpenJS.NodeJS.LTS` now installs **Node 26**, which became LTS on 2026-10-28 and has never been tested with Appium 2.19.

### Cited Findings
- appium 2.19.0 `engines`: `"node": "^14.17.0 || ^16.13.0 || >=18.0.0", "npm": ">=8"` — [SCRATCH/appium-test/node_modules/appium/package.json:93-96]
- Node release schedule: v20 end 2026-04-30; v22 maintenance until 2027-04-30; v24 LTS (maintenance from 2026-10-20, end 2028-04-30); **v26 LTS since 2026-10-28** — [nodejs/Release schedule.json](https://raw.githubusercontent.com/nodejs/Release/main/schedule.json)
- Appium 2.19 + the drivers ran here on Node v22.23.4 (server, sessions) and v24.22.1 (`driver list`) — local runs.

### Inferences
- **setup.md line 168 and 184 (MED):** recommend **Node 22 LTS** (tested here, supported until Apr 2027), with 24 acceptable. Say Node 20 is end of life. Replace `winget install OpenJS.NodeJS.LTS` with a version-pinned install, for example the nodejs.org 22.x MSI, or `winget install OpenJS.NodeJS.22` (unverified id, see Gaps). Add a note that the Windows `install-wad` script needs Node ≥ 20.

### Gaps
- I could not confirm that winget IDs `OpenJS.NodeJS.LTS` / `OpenJS.NodeJS.22` exist, because GitHub/winget-pkgs listing was blocked (403). I also did not test Appium 2.19 on Node 26.

## Q4. Appium-Python-Client 6.1.5 / selenium 4.52 API and server compatibility

### Takeaway
Every client API the skill uses exists and produces correct W3C payloads. The client does no server-version check and does not turn on BiDi by default. A real `webdriver.Remote` against Appium 2.19 reached the driver layer for both platforms. All PyPI pins are current.

### Cited Findings
- PyPI: Appium-Python-Client latest **6.1.5** (uploaded 2026-11-06), `Requires-Python >=3.10`, `Requires-Dist: selenium<5.0,>=4.51.0`, `typing-extensions~=4.16`. pytest latest **9.2.0** (`>=3.10`). python-dotenv latest **1.2.4** (`>=3.10`). selenium latest 4.52.0 — `pip index versions` + [PyPI JSON](https://pypi.org/pypi/Appium-Python-Client/json), [pytest](https://pypi.org/pypi/pytest/json), [python-dotenv](https://pypi.org/pypi/python-dotenv/json)
- Signature: `WebDriver.__init__(self, command_executor='http://127.0.0.1:4723', extensions=None, options: AppiumOptions | list[AppiumOptions] | None = None, client_config=None)`. `start_session` sends `capabilities.to_w3c()` — [SCRATCH/venv/lib/python3.13/site-packages/appium/webdriver/webdriver.py]
- `UiAutomator2Options().to_w3c()` gives `alwaysMatch: {"appium:automationName":"UIAutomator2","platformName":"Android","appium:udid":…,"appium:avd":…,"appium:avdLaunchTimeout":180000,"appium:avdReadyTimeout":180000,"appium:app":…,"appium:appPackage":…,"appium:appActivity":…,"appium:appWaitActivity":…,"appium:noReset":false,"appium:autoGrantPermissions":true,"appium:newCommandTimeout":120}`. `WindowsOptions` gives `automationName "Windows"`, `appium:appTopLevelWindow`, `appium:appArguments`, `appium:appWorkingDir`, `appium:createSessionTimeout`, **`ms:waitForAppLaunch`** (keeps `ms:`). `set_capability("appium:xyz",1)` is kept as given. Note: `to_capabilities()`, which the template logs, shows `automationName` without the prefix; `to_w3c()` adds it. Script: [SCRATCH/audit/opts.py](file:///tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/audit/opts.py)
- All of these caps are accepted by windows driver 4.4.7's `desiredCapConstraints`: app, appArguments, appTopLevelWindow, appWorkingDir, createSessionTimeout, `ms:waitForAppLaunch` (seconds), `ms:forcequit`, systemPort, prerun, postrun, wadUrl — [appium-windows-driver/build/lib/desired-caps.js]
- `AppiumBy` constants include `ACCESSIBILITY_ID` (= "accessibility id"), `ANDROID_UIAUTOMATOR` (= "-android uiautomator"), `ID`, `NAME`, `CLASS_NAME`, `XPATH`. `driver.current_package`, `query_app_state`, `get_log`, and `start_recording_screen` all exist in the client.
- No `webSocketUrl`/BiDi is enabled by default. `webSocketUrl` is only a known option name in `options/common/base.py:60`. No `/status` version gating in client code (grep).
- End-to-end against local Appium 2.19 at `http://127.0.0.1:4723` (no base path). The client's POST `/session` was matched ("The 'uiautomator2' driver was installed and matched caps … creating new AndroidUiautomator2Driver (v4.2.9) session") and failed only at the environment layer: `Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported` / `WinAppDriver tests only run on Windows` — [SCRATCH/audit/e2e.py], [appium.log]

### Inferences
- SKILL.md rules 1 and 5 and the minimal shapes (lines 68-137) are CONFIRMED correct for client 6.1.5 + server 2.19. The automationName sent is `UIAutomator2`; the server matches it case-insensitively, so the table's `UiAutomator2` is fine.

### Gaps
- None material.

## Q5. Template project: does it run, and is the fixture/wait/page logic correct?

### Takeaway
Collection and imports pass, and teardown always quits. There is one **real bug**: failure artifacts are written to a name built with `Path.with_suffix`, which cuts off the test name and timestamp. Every failing test in the same file overwrites the same `.png`/`.xml`. This contradicts SKILL.md, shared-patterns.md §6 and README. The other problems are lower severity.

### Cited Findings
- `pytest --collect-only` on a copy (Python 3.13, pytest 9.2.0) collects 5 tests: 2 android, 3 windows (`test_basic_operations[9---4-5]`, `[6-*-7-42]`). `pythonpath = .` works (needs pytest ≥7). pytest **creates the missing `artifacts/` dir** for `log_file` (`os.makedirs` in `_pytest/logging.py:696-700`). The path is `os.path.abspath(log_file)`, so it is resolved against the **current working directory**, not the rootdir — [SCRATCH/venv/lib/python3.13/site-packages/_pytest/logging.py:696-704]
- Fixture harness (I swapped in a fake `create_driver`): [SCRATCH/audit/tpl/tests/fake/test_fake.py](file:///tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/audit/tpl/tests/fake/test_fake.py)
  - A failing marked test: screenshot and XML were captured, then `quit` was called. Log: `Failure artifacts saved: …/artifacts/tests_fake_test_fake.py_test_a_fails-20261112-064307.{png,xml}`. But the files actually written were **`artifacts/tests_fake_test_fake.png` and `tests_fake_test_fake.xml`**.
  - `create_driver` raising: the test errors in setup, and no `drv.quit()` is attempted (correct, since there is no driver).
  - Two platform markers: the error `pytest.UsageError: … has more than one platform marker` is reported as a test ERROR.
  - An unmarked test falls back to `TARGET_PLATFORM`. `hookwrapper=True` runs with no warnings on pytest 9.2.
- Cause, in **tests/conftest.py lines 42-46**: `safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", node.nodeid)` keeps the `.` from `test_x.py`, and `base.with_suffix(".png")` replaces everything after the last dot (`.py_test_a_fails-20261112-064307`).

### Inferences
- **HIGH (template bug; also contradicts shared-patterns.md line 131 and README line 83):** replace lines 42-46 with:
  ```python
  safe = re.sub(r"[^A-Za-z0-9_-]+", "_", node.nodeid)[-150:]   # no '.' so the stem has no suffix
  base = artifacts_dir / f"{safe}-{stamp}"
  png, xml = base.parent / f"{base.name}.png", base.parent / f"{base.name}.xml"
  driver.get_screenshot_as_file(str(png))
  xml.write_text(driver.page_source, encoding="utf-8")
  ```
  (or `Path(f"{base}.png")`).
- **MED (conftest lines 61-63):** artifacts are saved only when `rep_call.failed`. A failure in a fixture that runs after the driver, such as `calculator`'s `wait_until_loaded()`/`clear()` in test_calculator.py lines 12-16, produces no screenshot, because `rep_call` never exists. Suggestion: `rep = getattr(request.node, "rep_call", None) or getattr(request.node, "rep_setup", None)` and capture when `rep.failed`.
- **LOW (core/waits.py line 22):** `timeout or self._timeout` treats `timeout=0` (a one-shot check) as the default 15 s. Use `self._timeout if timeout is None else timeout`.
- **MED/LOW (pages/windows/calculator_page.py lines 47-56):** `wait_for_result` polls `self.result()` → `text_of` → `wait.visible(...)`, which is a full 15 s wait nested inside the outer wait. `WebDriverWait` ignores only `NoSuchElementException` by default (`selenium/webdriver/support/wait.py:27`). So a `TimeoutException` from the inner wait, or a `StaleElementReferenceException` from `.text` while the display re-renders, aborts the outer wait right away with a misleading message. Fix: in the lambda use `self.driver.find_element(*self.RESULTS).text`, and build the wait with `ignored_exceptions=(NoSuchElementException, StaleElementReferenceException)`. Alternatively, extend `Waits.until` to accept `ignored_exceptions`.
- **LOW (calculator_page.py line 50):** the regex `-?[\d.,]+\s*$` gives "Display is 3" → "3", "-5" → "-5", "1,234" → "1,234" (keeps the separator), and "1 234" (a locale with a space separator) → "234". The sample tests only use results below 1000, so they pass. Document this, or normalize with `.replace(",", "")`.
- **LOW (pages/base_page.py line 36):** `is_displayed` can raise `StaleElementReferenceException` if the list re-renders between `find_elements` and `is_displayed()`. Wrap it in try/except and return False on stale.
- **pages/android/api_demos_page.py lines 35-41:** the `mobile: scroll` call is CONFIRMED valid on UiAutomator2 4.2.9. `strategy` and `selector` are required, `accessibility id` is a supported strategy, `maxSwipes` is optional, and with no `elementId` "the first currently available scrollable view is selected" — [appium-uiautomator2-driver/build/lib/commands/gestures.js:270-302], [execute-method-map.js:142-148]. The README does not explain the missing elementId; consider adding a one-line comment. The APK in `android-apidemos` 5.0.0 contains package `io.appium.android.apis`, activity `.ApiDemos` and the class `SimpleAdapterWithDesc` (strings found in classes.dex/manifest), which supports the content-desc locator note.
- **LOW (pytest.ini line 12):** `log_file = artifacts/test-run.log` is relative to the cwd, but `ARTIFACTS_DIR` is resolved against PROJECT_ROOT (settings.py lines 71-73). If pytest is run from another directory, the log goes elsewhere. Document "run pytest from the project root".
- **LOW (shared-patterns.md line 161):** it says "Required-but-missing values raise a clear ValueError naming the variable". `settings.py` only does this indirectly: `driver_factory` raises for the missing app config. `_int()` raises a bare `int()` ValueError that does not name the variable when, say, `EXPLICIT_WAIT_SECONDS=abc`. Either soften the wording or wrap `_int` to name the variable.
- No `time.sleep`, XPath, `/wd/hub` or `desired_capabilities` in template code (grep). No hardcoded paths or UDIDs in code. The AUMID and package appear only in `.env.example` and docstrings. Implicit wait is 0 (`driver_factory.py:105`). The driver quits in `finally` (`conftest.py:57-66`). All of this is CONFIRMED consistent with SKILL.md rules 2, 4, 5 and 6.

### Gaps
- I did not run against a real device or Windows desktop. Calculator AutomationIds (`clearButton`, `num{d}Button`, `CalculatorResults`, …) and the content-desc of the ApiDemos Views sub-rows were not checked live.

## Q6. Other setup.md / SKILL.md consistency items

### Takeaway
SKILL.md and the reference files agree with each other. The remaining setup problems are Windows-shell details.

### Cited Findings
- On Windows PowerShell: "If no execution policy is set in any scope, the effective execution policy is **Restricted**, which is the default for Windows clients." The same doc also says `Default` = RemoteSigned for clients. This differs by PowerShell edition and version, so the sources conflict — [about_Execution_Policies](https://raw.githubusercontent.com/MicrosoftDocs/PowerShell-Docs/main/reference/7.4/Microsoft.PowerShell.Core/About/about_Execution_Policies.md)
- setup.md line 276 and README line 30 run `.\.venv\Scripts\Activate.ps1`. As shown in Q1, `appium` in PowerShell resolves to the npm `appium.ps1` shim.

### Inferences
- **setup.md §5 / §1 (MED, conditional):** under a Restricted policy, both `Activate.ps1` and `appium.ps1` fail with "running scripts is disabled on this system". Add once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (or use `appium.cmd` / `.venv\Scripts\activate.bat`).
- **setup.md line 275 / README line 29 (LOW):** `py -3.12 -m venv .venv` fails if 3.12 is not installed, although the matrix says "3.10+". Use `py -3 -m venv .venv` or "any installed 3.10+".
- Confirmed correct:
  - SKILL.md lines 12-15, 21-23 (pins and the reason for pinning)
  - SKILL.md line 69 (no `/wd/hub`: 404 confirmed)
  - SKILL.md lines 70-73 (Options classes and prefixing)
  - SKILL.md line 84 (insecure features: `mobile: shell` → adb_shell, prerun/postrun → power_shell, `windows: deleteFile` → modify_fs)
  - setup.md lines 192-193 (defaults)
  - setup.md lines 261-263 (WAD spawned on 4724-4824; `wadUrl` exists)
  - setup.md line 316 (doctor windows message)
  - setup.md line 308 ("0 required fixes needed" wording)
  - setup.md line 331 (`value.ready`)
  - shared-patterns.md §4 hook/fixture shape, §5 EC usage, §7 `driver.get_log("logcat")`, Windows `windows: startRecordingScreen` needing ffmpeg (`record-screen.js:21,99`)

### Gaps
- Not verified (outside what local sources show): the JDK guidance (setup.md line 174, "SDK below 30 needs Java 8"), "UiAutomator2 4.x supports Android 5.0+" (line 245), and WinAppDriver's own default listen address of 127.0.0.1:4723 (line 262).

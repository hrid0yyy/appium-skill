# Troubleshooting

Method (adapted from the official appium/skills troubleshooting guidance):
1. Lock to **one driver** and capture the **exact error**, the capabilities sent, and the Appium
   server log (`appium --log appium.log --log-timestamp`).
2. Make **one** targeted, reversible change, then rerun the smallest failing test.
3. Call it fixed only after the failing test passes again.

## Setup and server

| Symptom | Cause | Fix |
|---|---|---|
| `'uiautomator2' cannot be installed because the server version it requires (^4.0.0-beta.6) does not meet the currently installed one (2.19.0)` (same for `windows`, with `^3.0.0-rc.2`) | Unpinned install pulled a driver built for Appium 3/4 | `appium driver install uiautomator2@4.2.9` / `windows@4.4.7` |
| `A driver named "uiautomator2" is already installed` | Reinstalling over an existing install | `appium driver uninstall uiautomator2`, then install the pinned version |
| `Could not find a driver for automationName 'UiAutomator2' and platformName 'Android'` | Driver not installed under the `APPIUM_HOME` the server uses | `appium driver list --installed` in the same shell/user that starts the server |
| Client gets `404` / `unknown command` on session create | URL has `/wd/hub` (Appium 1 style) | Use `http://127.0.0.1:4723`, or start the server with `--base-path /wd/hub` only if legacy clients force it |
| `Potentially insecure feature 'adb_shell' has not been enabled` (similar for `power_shell`, `modify_fs`) | Feature not allowed on the server | Restart: `appium --allow-insecure uiautomator2:adb_shell,windows:power_shell` |
| `EADDRINUSE 4723` | Another Appium **or a manually started WinAppDriver** owns 4723 | `Get-NetTCPConnection -LocalPort 4723 \| Select OwningProcess`, then stop it. Don't run WAD by hand |
| Stale sessions / "session is either terminated or not started" | Previous run crashed without `quit()` | Run the server with `--session-override` (non-parallel). Make sure fixtures quit in `finally` |

## Android / UiAutomator2

### Environment and device

| Symptom | Fix |
|---|---|
| `Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported` | Set `ANDROID_HOME` (setup.md §3), **restart the terminal that runs `appium`**, rerun `appium driver doctor uiautomator2` |
| `JAVA_HOME is not set` / wrong Java | Set `JAVA_HOME` to a JDK (17 recommended), restart the terminal |
| `Could not find a connected Android device` / `adb devices` empty | Cable/driver: install the OEM USB driver, use a data cable, `adb kill-server; adb start-server`. Emulator: is it booted? Or set `ANDROID_AVD` so Appium boots it |
| Device shows `unauthorized` | Unlock the phone, accept the RSA prompt. If it's missing: Developer options → *Revoke USB debugging authorizations*, then replug |
| Device shows `offline` | `adb kill-server`, replug, try another USB port, update platform-tools |
| Several devices, wrong one picked | Set `ANDROID_UDID`. The driver otherwise takes the first device |
| Emulator boot times out (`avdLaunchTimeout`/`avdReadyTimeout`) | Raise `ANDROID_AVD_LAUNCH_TIMEOUT_MS` (e.g. 240000). Enable hardware acceleration (WHPX / Android Emulator Hypervisor Driver). Cold boot it once by hand |
| Xiaomi/MIUI/HyperOS: `INSTALL_FAILED_USER_RESTRICTED`, or taps ignored | Developer options → enable *Install via USB* and *USB debugging (Security settings)* (needs a SIM/Mi account) |

### UiAutomator2 server startup

| Symptom | Fix |
|---|---|
| `instrumentation process is not running (probably crashed)` / `socket hang up` at startup | Check `adb logcat -d` for `io.appium.uiautomator2.server` exceptions. Clean retry: `adb uninstall io.appium.uiautomator2.server`, `adb uninstall io.appium.uiautomator2.server.test`, or run `appium driver run uiautomator2 reset` (resets all connected devices) |
| `socket hang up` mid-test | Another UiAutomator instance took over (another tool or session on the same device), the device went to sleep or disconnected, or the OS killed the server. Check logcat, keep the device awake, avoid parallel sessions on one device |
| Hidden API policy errors on some OEM ROMs | `o.ignore_hidden_api_policy_error = True` |
| `Timed out waiting for UiAutomator2 server` (slow device) | Raise `uiautomator2_server_launch_timeout` / `uiautomator2_server_install_timeout` (ms) |
| Port conflicts when running 2+ devices | Unique `appium:systemPort` (8200–8299) per session |

### App launch

| Symptom | Fix |
|---|---|
| `'<pkg>/<activity>' or '<pkg>/<waitActivity>' never started` | App opens a splash/redirect activity. Find the real one: `adb shell dumpsys window \| findstr mCurrentFocus`. Set `ANDROID_APP_WAIT_ACTIVITY` (wildcards allowed: `com.example.*`). Raise `app_wait_duration` only after that |
| `java.lang.SecurityException: Permission Denial: starting Intent` | The activity isn't exported/launchable. Use the launcher activity, and test with `adb shell am start -W -n pkg/.Activity` |
| `INSTALL_FAILED_VERSION_DOWNGRADE` | Uninstall first, or `full_reset = True`, or `mobile: installApp` with `checkVersion: true` |
| `INSTALL_FAILED_NO_MATCHING_ABIS` | APK built for ARM on an x86_64 emulator image. Use a matching image or a universal APK |
| Firebase / signature errors after install | `o.set_capability("appium:noSign", True)` (Appium re-signs by default) |
| App state leaks between tests | Default reset clears data. If you set `no_reset`, add explicit cleanup (`mobile: clearApp`, deep link to start) |

### Elements and gestures

| Symptom | Fix |
|---|---|
| `NoSuchElementException` but element is visible | Dump `driver.page_source` and search it. Different attribute (text vs content-desc)? Different window (keyboard, dialog)? Then `driver.update_settings({"enableMultiWindows": True})`. WebView? `driver.contexts` |
| Element exists only after scrolling | `mobile: scroll` (strategy + selector) or UiScrollable `scrollIntoView` (android.md §3) |
| Compose `testTag` not found by id | App must set `testTagsAsResourceId`. Then `driver.update_settings({"disableIdLocatorAutocompletion": True})` |
| Slow interactions (~10 s per action) on animated screens | `driver.update_settings({"waitForIdleTimeout": 100})`. Disable animations on the device |
| `StaleElementReferenceException` | Re-find inside the page method after navigation/re-render. Don't cache elements across actions |
| Swipe/scroll does nothing | Use `mobile: swipeGesture`/`scrollGesture` on the scrollable container's `elementId`. TouchAction is removed |
| XPath `ClassCastException` | Rewrite to a native locator. Or `driver.update_settings({"enforceXPath1": True})` |
| WebView: `No Chromedriver found that can automate Chrome 'X'` | `appium:chromedriverExecutable` pointing to a matching chromedriver, or `chromedriverExecutableDir` + `--allow-insecure uiautomator2:chromedriver_autodownload` |

Triage commands:

```powershell
adb devices -l
adb shell dumpsys window | findstr mCurrentFocus
adb shell pm list packages | findstr <part-of-pkg>
adb logcat -d > logcat.txt
Select-String -Path appium.log -Pattern "socket hang up","instrumentation","never started","Error"
```

## Windows / WinAppDriver

| Symptom | Fix |
|---|---|
| `WinAppDriver.exe has not been found in any of these locations` | `appium driver run windows install-wad` (elevated), or set `APPIUM_WAD_PATH` to the exe |
| `WinAppDriver tests only run on Windows` | The Appium server is running on a non-Windows machine. The Windows driver only works on a Windows host |
| Session fails and WAD says Developer Mode is required | Settings → For developers → Developer Mode **on** |
| `Failed to locate opened application window with appId: … and processId: …` | Slow UWP start or launcher-style app: raise `WINDOWS_CREATE_SESSION_TIMEOUT_MS` and/or `WINDOWS_WAIT_FOR_APP_LAUNCH_SECONDS` (≤50). If the launched process hands off to another process, attach via `WINDOWS_TOP_LEVEL_WINDOW` or use `app="Root"` |
| `The system cannot find the file specified` on session start | Wrong exe path or AUMID typo. `Get-StartApps` for UWP, `Test-Path` for exe |
| `Unable to connect to the remote server` / port 4723 errors when WAD was started by hand | Close the manual `WinAppDriver.exe`. The driver starts its own on 4724+. Use `appium:wadUrl` only for an externally managed WAD |
| Element found in Inspect but not by Appium | Inspect in UIA mode, not MSAA. Check whether it lives in another top-level window (§4 of windows.md). Elevated app vs non-elevated Appium: run both at the same integrity level |
| AutomationId empty | Fall back to `name` (accept the localization risk) or ask developers to set AutomationId. XPath only with a justification comment |
| `NoSuchWindowException` after closing a dialog | `windows: closeApp` and `driver.close()` don't auto-switch. `driver.switch_to.window(main_handle)` |
| Clicks land in the wrong place / do nothing | Display scaling ≠ 100% affects coordinate gestures. Prefer element-based actions (`elementId`). Keep the desktop unlocked and the RDP session visible (not minimized) |
| Typing drops characters | Use `windows: keys` with `{"text": ...}` or send shorter chunks. Make sure the target has focus first (click it) |
| Calls behave oddly or crash WAD | WAD is closed-source and unmaintained. Try another WAD release (`install-wad <version>`). If it's a WAD bug, the README suggests the NovaWindows driver as an alternative (outside this skill's pinned stack) |
| `prerun` ignored / session fails with insecure-feature error | Start Appium with `--allow-insecure windows:power_shell` |

Triage commands:

```powershell
Get-StartApps | Where-Object Name -like '*MyApp*'          # AUMID
Get-Process MyApp | Select Id, MainWindowHandle, MainWindowTitle
'0x{0:X}' -f (Get-Process MyApp).MainWindowHandle           # appTopLevelWindow value
Get-NetTCPConnection -LocalPort 4723,4724 -ErrorAction SilentlyContinue
```

## Python client

| Symptom | Fix |
|---|---|
| `TypeError: ... unexpected keyword argument 'desired_capabilities'` | Removed in modern clients. Pass `options=UiAutomator2Options()` / `WindowsOptions()` |
| `AttributeError: 'WebDriver' object has no attribute 'find_element_by_…'` | Selenium 4 API: `driver.find_element(AppiumBy.ACCESSIBILITY_ID, "x")` |
| `ImportError: TouchAction` | Removed. Use `mobile:` gestures (Android) / `windows:` gestures, or W3C `ActionChains` |
| `ModuleNotFoundError: config` when running pytest | Run from the project root. `pytest.ini` sets `pythonpath = .` |

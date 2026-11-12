---
name: appium-android-windows
description: Write, fix and run Appium 2.x automation in Python + pytest for Android apps (UiAutomator2, emulators and real devices over adb) and Windows desktop apps (Appium Windows driver / WinAppDriver), driven from a local Appium server on a Windows PC. Use whenever the request mentions Appium, an Android test, APK, emulator, adb, UiAutomator2, appPackage/appActivity, a Windows app or desktop app, WinAppDriver, WPF, WinForms, UWP, Win32, AutomationId or Inspect.exe.
---

# Appium automation: Android + Windows (Python / pytest)

This skill produces Python + pytest Appium code for two targets:

| Target | Driver (automationName) | Pinned driver version |
|---|---|---|
| Android apps on emulators or real devices (adb) | `UiAutomator2` | `uiautomator2@4.2.9` |
| Windows desktop apps (UWP, WPF, WinForms, Win32) | `Windows` (proxies WinAppDriver) | `windows@4.4.7` |

Host: a **Windows PC running a local Appium 2.x server** (`appium@2.19.0`, `http://127.0.0.1:4723`).

**Scope is strict:** only the two drivers above, against a local server on the Windows host.
Never generate, suggest or offer any other platform, automation driver, or remote/hosted
execution service. If the user asks for one, say this skill does not cover it and stop.

> Version pinning matters. The npm `latest` tags of both drivers now require Appium 3 or 4, so
> `appium driver install uiautomator2` without a version **fails** on Appium 2.x. Always use the
> pinned commands in `references/setup.md`.

## Step 1: Detect the platform

```
Read the request
│
├─ Mentions Android / APK / emulator / AVD / adb / appPackage / appActivity /
│  UiAutomator2 / resource-id / content-desc / "mobile app"?
│     └─► ANDROID ─► read references/android.md
│
├─ Mentions Windows app / desktop app / .exe / UWP / WPF / WinForms / Win32 /
│  WinAppDriver / AutomationId / Inspect.exe / AUMID / window handle?
│     └─► WINDOWS ─► read references/windows.md
│
├─ Both (e.g. "a desktop app plus its Android companion")?
│     └─► BOTH ─► read android.md AND windows.md; keep two separate
│                 Options objects, two page-object packages, two markers
│
└─ Unclear?  ─► Ask one question: "Android app, Windows desktop app, or both?"
```

Then branch on what the request is about:

| Request is about… | Read |
|---|---|
| First-time install, "appium not found", driver install, doctor | `references/setup.md` |
| Project layout, POM, driver factory, waits, screenshots, config | `references/shared-patterns.md` |
| A failure, stack trace or error message | `references/troubleshooting.md` |
| "Start a new project" / "give me a skeleton" | Copy `templates/appium-pytest-project/` and adapt it |

## Step 2: Inspect before you write locators

1. **If appium-mcp or windows2-mcp tools are available in this session, use them** to open a
   session or read the live UI tree and confirm every locator before writing it into code.
   Don't guess AutomationIds, resource-ids or content-descs.
2. Otherwise ask the user for the page source / Inspect.exe output, or tell them how to get it:
   - Android: Appium Inspector, or `driver.page_source` dumped from a debug run.
   - Windows: Inspect.exe (Windows SDK) or Accessibility Insights for Windows.
3. Mark any locator you could not confirm with `# TODO: confirm locator against live UI`.

## Step 3: Generate code. The rules below are mandatory.

Every piece of generated code must follow all of these rules. Check them again before you reply.

1. **Appium 2.x conventions only**
   - Server URL is `http://127.0.0.1:4723` with **no `/wd/hub`** suffix (the Appium 2 base path is empty).
   - Build capabilities with Options classes: `UiAutomator2Options` (`appium.options.android`)
     and `WindowsOptions` (`appium.options.windows`). Never pass raw `desired_capabilities`.
   - Vendor capabilities carry the `appium:` prefix. Options properties add it for you. For
     raw keys, use `options.set_capability("appium:xyz", value)`. The Windows `ms:` caps keep `ms:`.
2. **No hard sleeps.** Never write `time.sleep`. Use `WebDriverWait` with expected conditions.
   Set the implicit wait to 0 and don't mix implicit and explicit waits.
3. **Locator priority:** accessibility id → id → (Android) `-android uiautomator` / (Windows) name
   → class name → **XPath last**. Every XPath gets a comment explaining why nothing better works.
4. **No hardcoded paths, device IDs, AUMIDs or credentials.** Read them from env vars or config
   (see `shared-patterns.md`). Code may contain only env-var names and safe defaults.
5. **Separate capability sets per platform.** One builder function per platform, each returning
   a new Options object. Never share one caps dict/object between Android and Windows.
6. **Always quit the driver in teardown**, using `yield` plus `try/finally` in the fixture, even
   when the test or the screenshot capture fails.
7. Insecure features (`mobile: shell`, PowerShell `prerun`/`postrun`, `windows: deleteFile`)
   need the server started with `--allow-insecure` (see setup.md). Say so whenever you use one, and
   give the flag quoted with lowercase driver prefixes: `--allow-insecure "uiautomator2:adb_shell"`.

## Minimal shapes (full versions are in references/ and templates/)

```python
# Android: options builder
from appium.options.android import UiAutomator2Options

def android_options(cfg) -> UiAutomator2Options:
    o = UiAutomator2Options()          # sets platformName=Android, automationName=UiAutomator2
    if cfg.android_udid:
        o.udid = cfg.android_udid      # real device or a specific running emulator
    if cfg.android_avd:
        o.avd = cfg.android_avd        # Appium boots this emulator if it isn't running
    if cfg.android_app:
        o.app = cfg.android_app        # absolute .apk/.apks path on the Appium host
    else:
        o.app_package = cfg.android_app_package
        o.app_activity = cfg.android_app_activity
    o.new_command_timeout = cfg.new_command_timeout
    return o
```

```python
# Windows: options builder (separate function, separate object)
from appium.options.windows import WindowsOptions

def windows_options(cfg) -> WindowsOptions:
    o = WindowsOptions()               # sets platformName=Windows, automationName=Windows
    if cfg.windows_top_level_window:
        o.app_top_level_window = cfg.windows_top_level_window  # "0x1A2B3C": attach to a running window
    else:
        o.app = cfg.windows_app        # AUMID (UWP) or full .exe path (classic)
    if cfg.windows_app_arguments:
        o.app_arguments = cfg.windows_app_arguments
    return o
```

```python
# Session + explicit wait
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Remote(cfg.appium_server_url, options=android_options(cfg))
try:
    WebDriverWait(driver, cfg.explicit_wait).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Views"))
    ).click()
finally:
    driver.quit()
```

## Reply checklist

Before you finish, confirm and briefly state:
- [ ] Platform detected, and the matching reference file followed
- [ ] Locators confirmed live (MCP / Inspect / page source) or marked TODO
- [ ] No `time.sleep`, no `/wd/hub`, no `desired_capabilities`
- [ ] Every XPath has a justification comment
- [ ] No literal paths, UDIDs, AUMIDs or secrets. Each new env var is listed for the user
- [ ] Driver quit in `finally` / fixture teardown
- [ ] Any `--allow-insecure` requirement called out
- [ ] Run command given: `pytest -m android` / `pytest -m windows`

## Reference files

- `references/setup.md`: one-time Windows host setup and health check
- `references/android.md`: UiAutomator2 capabilities, locators, `mobile:` gestures, app state, permissions, keyboard
- `references/windows.md`: Windows driver capabilities, locators, Inspect.exe, multi-window, `windows:` gestures, PowerShell hooks
- `references/shared-patterns.md`: project layout, POM, driver factory, waits, screenshots, logging, config
- `references/troubleshooting.md`: failures for both drivers, with fixes
- `templates/appium-pytest-project/`: runnable skeleton (ApiDemos Android test + Windows Calculator test)

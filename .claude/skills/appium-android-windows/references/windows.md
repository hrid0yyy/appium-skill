# Windows desktop: Appium Windows driver (4.4.7 on Appium 2.x)

The driver is a thin proxy over Microsoft **WinAppDriver (WAD)**. It supports UWP, WPF, WinForms
and classic Win32 apps. Capabilities, `windows:` signatures and locator semantics below come from
the `appium-windows-driver@4.4.7` README and source. The Python properties were checked against
`Appium-Python-Client` 6.1.5.

How a session starts: Appium (port 4723) → Windows driver → spawns `WinAppDriver.exe` on a free
port in 4724–4824 (or `appium:systemPort`) → WAD launches or attaches to the app. Don't start
WAD yourself unless you also set `appium:wadUrl`.

## 1. Capabilities

`WindowsOptions()` sets `platformName=Windows`, `appium:automationName=Windows`.

| Capability | Python property | Meaning |
|---|---|---|
| `appium:app` | `app` | **UWP:** the AppUserModelId (AUMID), e.g. `Microsoft.WindowsCalculator_8wekyb3d8bbwe!App`. **Classic (WPF/WinForms/Win32):** full `.exe` path. **`Root`:** whole desktop (no specific app) |
| `appium:appTopLevelWindow` | `app_top_level_window` | Hex handle string of an already-open window to **attach** to, e.g. `"0x1A2B3C"`. Use this *or* `app` |
| `appium:appArguments` | `app_arguments` | Command-line arguments string |
| `appium:appWorkingDir` | `app_working_dir` | Working dir (classic apps only) |
| `appium:createSessionTimeout` | `create_session_timeout` | ms to keep retrying session start (default 20000). Fixes slow UWP startup |
| `ms:waitForAppLaunch` | `wait_for_app_launch` | Seconds WAD waits after launch before attaching (max 50) |
| `ms:experimental-webdriver` | `experimental_webdriver` | Enable WAD experimental features (default false) |
| `ms:forcequit` | `set_capability("ms:forcequit", True)` | Kill the app process at session end |
| `appium:systemPort` | `system_port` | Port for the spawned WAD (default: first free from 4724) |
| `appium:prerun` / `appium:postrun` | `prerun` / `postrun` | `{"script": "..."}` or `{"command": "..."}` PowerShell, run before WAD session start / after stop. Needs `--allow-insecure windows:power_shell` |
| `appium:wadUrl` | `set_capability("appium:wadUrl", url)` | Use an externally managed, already-running WAD |
| `appium:newCommandTimeout` | `new_command_timeout` | seconds, default 60 |

### Finding the `app` value

```powershell
# UWP / Store apps: AppID column is the AUMID
Get-StartApps | Where-Object Name -like '*Calculator*'
# Name        AppID
# Calculator  Microsoft.WindowsCalculator_8wekyb3d8bbwe!App

# Classic apps: the full exe path
(Get-Command notepad).Source
```

### Attaching to a running window (`appTopLevelWindow`)

Use this for apps started by a launcher, apps that open a splash first, or apps that need a manual
login before automation. Get the handle from Inspect.exe / Accessibility Insights
(`NativeWindowHandle`, decimal → convert with `hex()`), or with PowerShell:

```powershell
'0x{0:X}' -f (Get-Process MyApp | Where-Object MainWindowHandle -ne 0).MainWindowHandle
```

Pass it via an env var (`WINDOWS_TOP_LEVEL_WINDOW`). Never hardcode it, because handles change every launch.

### Builder (env-driven, Windows-only object)

```python
from appium.options.windows import WindowsOptions

def build_windows_options(cfg) -> WindowsOptions:
    o = WindowsOptions()
    if cfg.windows_top_level_window:
        o.app_top_level_window = cfg.windows_top_level_window   # attach mode
    elif cfg.windows_app:
        o.app = cfg.windows_app                                 # AUMID, exe path or "Root"
    else:
        raise ValueError("Set WINDOWS_APP or WINDOWS_TOP_LEVEL_WINDOW")
    if cfg.windows_app_arguments:
        o.app_arguments = cfg.windows_app_arguments
    if cfg.windows_app_working_dir:
        o.app_working_dir = cfg.windows_app_working_dir
    o.create_session_timeout = cfg.windows_create_session_timeout_ms
    if cfg.windows_wait_for_app_launch_s:
        o.wait_for_app_launch = cfg.windows_wait_for_app_launch_s
    o.new_command_timeout = cfg.new_command_timeout
    return o
```

## 2. Locator priority

| # | Strategy | Python | Inspect.exe property | Notes |
|---|---|---|---|---|
| 1 | accessibility id | `AppiumBy.ACCESSIBILITY_ID, "num7Button"` | **AutomationId** | Not localized, set by developers (`x:Name`/`AutomationProperties.AutomationId` in WPF/UWP, `Control.Name` in WinForms) |
| 2 | name | `AppiumBy.NAME, "Seven"` | Name | Visible label. **Localized**, so it changes with the OS language |
| 3 | class name | `AppiumBy.CLASS_NAME, "TextBlock"` | ClassName | Rarely unique alone |
| 4 | tag name | `AppiumBy.TAG_NAME, "Button"` | LocalizedControlType (UpperCamelCase) | Good for `find_elements` lists |
| 5 | id | `AppiumBy.ID, "42.333896.3.1"` | RuntimeId | **Changes every run**. Don't persist it in code |
| 6 | xpath | `AppiumBy.XPATH, "..."` | any attribute | **Last resort**, XPath 1.0 only, slow on big trees. Always add a `# XPath because …` comment |

```python
# XPath because: the grid cells expose no AutomationId and share Name values across rows;
# anchoring on the row's AutomationId is the most stable option left.
CELL = (AppiumBy.XPATH, '//*[@AutomationId="Row_3"]/DataItem[2]')
```

WinForms note: AutomationId falls back to the control's `Name` property, and auto-generated names
(`button1`) are unstable. Ask developers to name controls. WPF: elements only get an AutomationId
if `x:Name` or `AutomationProperties.AutomationId` is set.

## 3. Finding locators with Inspect.exe / Accessibility Insights

1. **If windows2-mcp (or appium-mcp) tools are available, use them first** to dump the live UIA
   tree or the session page source and confirm AutomationId/Name.
2. Inspect.exe (Windows SDK): hover over or select the control and read **AutomationId**, **Name**,
   **ClassName**, **LocalizedControlType** and **NativeWindowHandle**. Turn on *Options → Watch
   Cursor* to follow the mouse. Use the **UI Automation** mode, not MSAA.
3. Accessibility Insights for Windows → *Inspect* mode → the *Details* pane shows the same
   properties. It also flags controls missing an AutomationId.
4. From a running session: `driver.page_source` returns XML whose tags are control types and whose
   attributes are UIA properties (`AutomationId`, `Name`, `ClassName`…). Save it to a file and
   search it.

## 4. Multi-window apps

A WAD session tracks top-level windows of the launched app as WebDriver window handles.

```python
from selenium.webdriver.support.ui import WebDriverWait

main = driver.current_window_handle
open_settings_button.click()

# Wait for a new top-level window instead of sleeping
WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
new = next(h for h in driver.window_handles if h != main)
driver.switch_to.window(new)
# ... interact with the dialog ...
driver.close()                      # or windows: closeApp (closes active window, NO auto-switch)
driver.switch_to.window(main)       # always switch back explicitly
```

- Modal dialogs owned by the main window are often **children** in the UIA tree. Try finding
  them from the main window before switching handles.
- Windows spawned by a *different process* (launcher → real app, UAC, separate updater) are not
  in `window_handles`. Open a second session with `appTopLevelWindow`, or with `app="Root"` to search the
  whole desktop, then attach.
- `windows: launchApp` relaunches the app in the same session (may create a new window).

## 5. Gestures and input: `windows:` extensions

Call them as `driver.execute_script("windows: <name>", {args})`. Element ids come from `el.id`.
Coordinates are relative to the element if an element id is given, otherwise absolute
virtual-screen coordinates.

| Name | Args |
|---|---|
| `windows: click` | `elementId?`, `x?`, `y?`, `button` (`left`/`middle`/`right`/`back`/`forward`), `modifierKeys` (`Shift`,`Ctrl`,`Alt`,`Win`), `durationMs?`, `times?` (2 = double-click), `interClickDelayMs?` |
| `windows: scroll` | `elementId?`, `x?`, `y?`, `deltaX` **or** `deltaY` (wheel clicks), `modifierKeys?` |
| `windows: clickAndDrag` | `startElementId?`/`startX`,`startY`, `endElementId?`/`endX`,`endY`, `modifierKeys?`, `durationMs?` (default 5000) |
| `windows: hover` | same start/end args, `durationMs?` (default 500) |
| `windows: keys` | `actions`: list of `{text}` / `{virtualKeyCode, down?}` / `{pause}` |
| `windows: setClipboard` | `b64Content`, `contentType?` (`plaintext`/`image`) |
| `windows: getClipboard` | `contentType?` → base64 string |
| `windows: launchApp` / `windows: closeApp` | none |
| `windows: startRecordingScreen` / `stopRecordingScreen` | ffmpeg in PATH. `fps`, `timeLimit`, `captureCursor`… / returns base64 mp4 |
| `windows: deleteFile` / `deleteFolder` | `remotePath`. Needs `--allow-insecure windows:modify_fs` |

```python
# Right-click an element, double-click another
driver.execute_script("windows: click", {"elementId": row.id, "button": "right"})
driver.execute_script("windows: click", {"elementId": icon.id, "times": 2})

# Ctrl+A then type (VK_CONTROL = 0x11). Always release held keys.
driver.execute_script("windows: keys", {"actions": [
    {"virtualKeyCode": 0x11, "down": True},
    {"text": "a"},
    {"virtualKeyCode": 0x11, "down": False},
    {"text": "replacement text"},
]})

# Scroll a list 5 notches down (wheel toward the user = negative deltaY)
driver.execute_script("windows: scroll", {"elementId": lst.id, "deltaY": -5})

# Clipboard round-trip
import base64
driver.execute_script("windows: setClipboard",
                      {"b64Content": base64.b64encode(b"hello").decode()})
```

Plain `el.click()`, `el.send_keys()`, `el.clear()`, `el.text` (returns the UIA Name for most
controls) all work. For text boxes, read the value with `el.get_attribute("Value.Value")`
(UIA ValuePattern). Confirm it in Inspect for the control in question.

## 6. PowerShell hooks (prerun / postrun / ad-hoc)

All three need the server started with `--allow-insecure windows:power_shell`. Use them for
**environment prep**, not for test steps.

```python
o.prerun = {"command": "Stop-Process -Name MyApp -ErrorAction SilentlyContinue"}   # clean start
o.postrun = {"script": "Remove-Item \"$env:TEMP\\myapp-test\" -Recurse -ErrorAction SilentlyContinue"}

# Ad-hoc during a test. Returns stdout, and raises with stderr on non-zero exit
out = driver.execute_script("powerShell", {"command": "Get-Process MyApp -ErrorAction SilentlyContinue"})
```

Prerun runs **before** the WAD session starts. If it fails, the session isn't created. Postrun
failures are only logged. Keep paths in env vars (`$env:...`), not literals.

## 7. App-type specifics

| App type | `app` value | Gotchas |
|---|---|---|
| UWP / Store (Calculator, Photos) | AUMID | Slow first launch: raise `createSessionTimeout` / `ms:waitForAppLaunch`. Sandboxed, so no `appArguments` for most apps |
| WPF | exe path | AutomationId comes from `x:Name` / `AutomationProperties.AutomationId`. Virtualized lists only expose visible rows, so scroll first |
| WinForms | exe path | AutomationId = control `Name`. Owner-drawn/custom controls may be invisible to UIA |
| Win32 | exe path | Often only Name/ClassName available. Expect more `name` and occasional XPath |
| Apps that self-relaunch or use a launcher | `appTopLevelWindow` or `Root` | The launched PID exits, so WAD loses the window. Attach to the real window instead |
| Elevated (admin) apps | n/a | UIA can't drive an elevated window from a non-elevated process. Run Appium elevated too, or don't elevate the app |

## 8. Things to avoid

- Running tests while someone uses the mouse/keyboard, or with the screen locked or the RDP window
  minimized. WAD needs an active, unlocked interactive desktop.
- Hardcoded window handles, RuntimeIds, absolute screen coordinates.
- Name-based locators in suites that run on machines with different display languages.

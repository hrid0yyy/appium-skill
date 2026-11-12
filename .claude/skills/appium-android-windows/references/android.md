# Android: UiAutomator2 driver (4.2.9 on Appium 2.x)

All capability names and `mobile:` signatures below are copied from the README and
`execute-method-map` of `appium-uiautomator2-driver@4.2.9`. The Python property names were checked
against `Appium-Python-Client` 6.1.5.

## 1. Capabilities

`UiAutomator2Options()` already sets `platformName=Android` and
`appium:automationName=UiAutomator2`. Every property below serializes to its `appium:` name.

### Device selection

| Scenario | Set | Python property | Env var (template) |
|---|---|---|---|
| Real device | `appium:udid` = serial from `adb devices -l` | `o.udid` | `ANDROID_UDID` |
| Emulator that Appium should boot | `appium:avd` = AVD name (`emulator -list-avds`) | `o.avd` | `ANDROID_AVD` |
| Already-running emulator | `appium:udid` = `emulator-5554` | `o.udid` | `ANDROID_UDID` |
| Only one device attached | nothing. The driver uses the first device | n/a | n/a |

Useful extras:

| Capability | Property | Notes |
|---|---|---|
| `appium:avdLaunchTimeout` / `appium:avdReadyTimeout` | `avd_launch_timeout` / `avd_ready_timeout` | ms, default 60000. Raise to 180000 on a slow host's cold boot |
| `appium:avdArgs` | `avd_args` | e.g. `"-no-snapshot-load"`. `-wipe-data` kills and wipes the emulator first |
| `appium:isHeadless` | `is_headless` | emulator without a window (only if Appium starts it) |
| `appium:platformVersion` | `platform_version` | only used to auto-pick a device when `udid` is unset |
| `appium:deviceName` | `device_name` | **not used for selection**. Use `udid`/`avd` instead |
| `appium:systemPort` | `system_port` | host port 8200–8299. Must be unique per parallel session |

### App under test

| Approach | Capabilities | When |
|---|---|---|
| Install from file | `appium:app` = absolute path to `.apk`/`.apks` **on the Appium host** (URL also allowed) | CI, fresh builds |
| Already installed | `appium:appPackage` + `appium:appActivity` | Preinstalled/system apps, faster runs |
| Splash/redirect activity | add `appium:appWaitActivity` (wildcards OK: `com.example.*`) and/or `appium:appWaitPackage` | Session fails with "never started" |

Find the package/activity of the foreground app:

```powershell
adb shell dumpsys window displays | findstr "mCurrentFocus mFocusedApp"
# mCurrentFocus=Window{... u0 io.appium.android.apis/io.appium.android.apis.ApiDemos}
# (mCurrentFocus can be null on Android 14+; mFocusedApp still shows pkg/activity)
```

Reset behaviour:

| Goal | Caps |
|---|---|
| Default (stop the app and clear its data at start; with `app`, reinstall only if needed) | neither `noReset` nor `fullReset` |
| Keep the app state between sessions (logged-in user etc.) | `no_reset = True` |
| Uninstall + reinstall every session | `full_reset = True` (needs `app`) |
| Always restart the app even with `noReset` | `set_capability("appium:forceAppLaunch", True)` |

Other common ones: `auto_grant_permissions` (`appium:autoGrantPermissions`),
`new_command_timeout` (seconds, default 60), `app_wait_duration` (ms, default 20000),
`android_install_timeout` (ms, default 90000), `uiautomator2_server_launch_timeout`
(ms, default 30000), `uiautomator2_server_install_timeout` (ms, default 20000),
`adb_exec_timeout` (ms, default 20000), `disable_window_animation`, `skip_unlock`,
`ignore_hidden_api_policy_error`. Capabilities without a typed property:
`o.set_capability("appium:hideKeyboard", True)` and `o.set_capability("appium:autoLaunch", False)`.

### Builder (env-driven, Android-only object)

```python
from appium.options.android import UiAutomator2Options

def build_android_options(cfg) -> UiAutomator2Options:
    o = UiAutomator2Options()
    if cfg.android_udid:
        o.udid = cfg.android_udid
    if cfg.android_avd:
        o.avd = cfg.android_avd
        o.avd_launch_timeout = cfg.android_avd_launch_timeout_ms
        o.avd_ready_timeout = cfg.android_avd_launch_timeout_ms
    if cfg.android_app:                       # path comes from env, never a literal
        o.app = cfg.android_app
    elif cfg.android_app_package and cfg.android_app_activity:
        o.app_package = cfg.android_app_package
        o.app_activity = cfg.android_app_activity
    else:
        raise ValueError("Set ANDROID_APP or ANDROID_APP_PACKAGE + ANDROID_APP_ACTIVITY")
    if cfg.android_app_wait_activity:
        o.app_wait_activity = cfg.android_app_wait_activity
    o.no_reset = cfg.android_no_reset
    o.auto_grant_permissions = cfg.android_auto_grant_permissions
    o.new_command_timeout = cfg.new_command_timeout
    return o
```

## 2. Locator priority

| # | Strategy | Python | Maps to | Notes |
|---|---|---|---|---|
| 1 | accessibility id | `AppiumBy.ACCESSIBILITY_ID, "Login"` | `content-desc` | Fastest and most stable. React Native `accessibilityLabel` lands here |
| 2 | id | `AppiumBy.ID, "com.example:id/login"` | `resource-id` | Package prefix is auto-added if omitted. Jetpack Compose `testTag` + `testTagsAsResourceId` lands here |
| 3 | -android uiautomator | `AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Login")'` | UiSelector | When there's no desc/id. Also handles scroll-into-view. Google plans to deprecate UiSelector, so prefer 1–2 |
| 4 | class name | `AppiumBy.CLASS_NAME, "android.widget.EditText"` | widget class | Only when the class is unique on screen, or combined with `find_elements` + index |
| 5 | xpath | `AppiumBy.XPATH, "..."` | page-source XML | **Last resort**. Slow and brittle. Always add a `# XPath because …` comment |

```python
# XPath because: the row has no content-desc or resource-id, and its text is duplicated
# in a header, so we anchor on the parent list's id. Ask devs to add a content-desc.
ROW = (AppiumBy.XPATH, '//*[@resource-id="com.example:id/list"]/*[3]')
```

Text-based locators (UiSelector `.text()`, XPath `@text`) break when the device language
changes. Prefer content-desc/resource-id, which aren't localized.

If an element is missing from `driver.page_source`, the problem is app state, a different window,
or a WebView context, not the selector syntax. Settings that help (`driver.update_settings({...})`):
`allowInvisibleElements`, `ignoreUnimportantViews`, `enableMultiWindows`, `snapshotMaxDepth`,
`disableIdLocatorAutocompletion` (for ids without a package prefix).

## 3. Gestures: `mobile:` extensions (preferred over raw W3C actions)

Call them as `driver.execute_script("mobile: <name>", {args})`. `elementId` takes `element.id`.
`percent` is a float from 0 to 1. Directions are `up`/`down`/`left`/`right`.

| Gesture | Name | Required args | Optional args |
|---|---|---|---|
| Tap | `mobile: clickGesture` | none | `elementId`, `x`, `y` |
| Double tap | `mobile: doubleClickGesture` | none | `elementId`, `x`, `y` |
| Long press | `mobile: longClickGesture` | none | `elementId`, `x`, `y`, `duration` (ms) |
| Drag | `mobile: dragGesture` | none | `elementId`, `startX`, `startY`, `endX`, `endY`, `speed` |
| Swipe | `mobile: swipeGesture` | `direction`, `percent` | `elementId` or `left`,`top`,`width`,`height`; `speed` |
| Scroll | `mobile: scrollGesture` | `direction`, `percent` | `elementId` or area; `speed`. Returns `True` while more scrolling is possible |
| Fling | `mobile: flingGesture` | `direction` | `elementId` or area; `speed` |
| Pinch open / close | `mobile: pinchOpenGesture` / `pinchCloseGesture` | `percent` | `elementId` or area; `speed` |
| Scroll until found | `mobile: scroll` | `strategy` (`accessibility id`, `class name`, `-android uiautomator`), `selector` | `elementId`, `maxSwipes` |

```python
# Long-press an element
el = wait.until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, "Item 1")))
driver.execute_script("mobile: longClickGesture", {"elementId": el.id, "duration": 1000})

# Scroll a list until a target appears (bounded loop, no sleeps)
lst = driver.find_element(AppiumBy.ID, "android:id/list")
for _ in range(10):
    if driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "WebView"):
        break
    if not driver.execute_script("mobile: scrollGesture",
                                 {"elementId": lst.id, "direction": "down", "percent": 0.8}):
        break   # reached the end

# One-shot alternative using UiScrollable
driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
    'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView('
    'new UiSelector().description("WebView"))')
```

Avoid hardcoded coordinates. If you must use them, compute them from `el.rect` or
`driver.get_window_size()`. `TouchAction`/`MultiAction` are gone. Use the gestures above, or W3C
actions via `ActionChains` + `PointerInput(interaction.POINTER_TOUCH, "finger")`.

## 4. App state handling

| Need | Call |
|---|---|
| Bring to foreground / launch | `driver.activate_app(pkg)` or `mobile: activateApp {appId}` |
| Stop | `driver.terminate_app(pkg)` or `mobile: terminateApp {appId, timeout?}` |
| State | `driver.query_app_state(pkg)` → `0` not installed, `1` not running, `3` background, `4` foreground |
| Background for N s then restore | `mobile: backgroundApp {seconds}` (negative = stay in background) |
| Install / remove | `mobile: installApp {appPath, grantPermissions?, replace?, timeout?}` / `mobile: removeApp {appId, keepData?}` |
| Installed? | `mobile: isAppInstalled {appId}` |
| Clear data (`pm clear`) | `mobile: clearApp {appId}` (app must not be running) |
| Start a specific activity | `mobile: startActivity {intent: "pkg/.Activity", wait?, stop?, extras?}` |
| Deep link | `mobile: deepLink {url, package?, waitForLaunch?}` |
| Current activity/package | `mobile: getCurrentActivity`, `mobile: getCurrentPackage` |

Wait for state changes with an explicit wait, never a sleep:

```python
WebDriverWait(driver, 15).until(lambda d: d.query_app_state(pkg) == 4)
```

For test isolation, prefer `noReset=True` plus targeted cleanup (`mobile: clearApp`, deep link to
the start screen) over a full reinstall per test.

## 5. Permissions

- At session start: `o.auto_grant_permissions = True` (needs targetSdk ≥ 23 on Android 6+).
- At runtime:

```python
driver.execute_script("mobile: changePermissions", {
    "permissions": ["android.permission.ACCESS_FINE_LOCATION"],   # or "all"
    "appPackage": cfg.android_app_package,                        # default: app under test
    "action": "grant",                                            # or "revoke"
})
granted = driver.execute_script("mobile: getPermissions", {"type": "granted"})
```

- Special appops permissions (notifications access, etc.): `"target": "appops"` with
  `"action": "allow"`. This **requires** `--allow-insecure uiautomator2:adb_shell`.
- System permission dialogs: on Google-certified devices the package is
  `com.google.android.permissioncontroller`, but the resource-ids keep the AOSP prefix:
  `com.android.permissioncontroller:id/permission_allow_button`,
  `…:id/permission_allow_foreground_only_button` ("While using the app"),
  `…:id/permission_allow_one_time_button` ("Only this time"), `…:id/permission_deny_button`.
  Android 9 and older use `com.android.packageinstaller:id/permission_allow_button`. OEM skins
  (MIUI, One UI) may differ, so confirm on the target device. Prefer `auto_grant_permissions` /
  `mobile: changePermissions` to avoid the dialog entirely.

## 6. Keyboard

| Need | How |
|---|---|
| Type into a field | `el.clear(); el.send_keys(text)` |
| Real "keyboard" typing, Unicode | focus the field, then `mobile: type {text}` |
| Hide keyboard | `driver.hide_keyboard()` or `mobile: hideKeyboard` (returns `False` if already hidden) |
| Keyboard visible? | `driver.is_keyboard_shown()` / `mobile: isKeyboardShown` |
| Press a key (Enter, Back) | `driver.press_keycode(66)` or `mobile: pressKey {keycode: 66}` (66=ENTER, 4=BACK) |
| IME action (Search/Done/Go) | `mobile: performEditorAction {action: "search"}` |
| Never show the soft keyboard | `o.set_capability("appium:hideKeyboard", True)` (replaces legacy `unicodeKeyboard`). Exploratory use only |

## 7. Device utilities

- `mobile: shell {command, args?, timeout?, includeStderr?}` needs
  `--allow-insecure uiautomator2:adb_shell`. Use it for setup only, never for test assertions on UI.
- `mobile: getDeviceTime {format?}`, `mobile: deviceInfo`, `mobile: batteryInfo`.
- Screenshots: `driver.get_screenshot_as_file(path)`. Page source: `driver.page_source`.
- Hybrid apps: `driver.contexts` → `driver.switch_to.context("WEBVIEW_<pkg>")`, and switch back
  to `"NATIVE_APP"`. A Chromedriver mismatch is fixed with `appium:chromedriverExecutable` or
  `appium:chromedriverExecutableDir`, not by changing locators.

## 8. Parallel runs (multiple devices on one host)

Give each session a unique `udid` (or `avd`) **and** a unique `appium:systemPort` (8200–8299).
Add `appium:chromedriverPort` for WebViews and `appium:mjpegServerPort` if you record video.
One Appium server can manage several sessions.

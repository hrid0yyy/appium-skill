# Android / UiAutomator2 facts audit (Appium 2.19.0 + uiautomator2@4.2.9 + Appium-Python-Client 6.1.5)

Path abbreviations used in the citations below. All are local files, already downloaded:
- `SP` = /tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad
- `UIA2` = SP/appium-test/home/node_modules/appium-uiautomator2-driver (installed 4.2.9, package.json `"version": "4.2.9"`)
- `README` = SP/pkgs/x-appium-uiautomator2-driver@4.2.9/package/README.md
- `AAD` = UIA2/node_modules/appium-android-driver (10.3.12)
- `ADB` = UIA2/node_modules/appium-adb
- `APPIUM` = SP/appium-test/node_modules/appium (2.19.0)
- `PYC` = Appium-Python-Client 6.1.5 in SP/venv (checked with `python -I`)
- `APK` = SP/pkgs/x-apidemos/package/apks/ApiDemos-debug.apk (android-apidemos 5.0.0)

Skill files audited: references/android.md, references/troubleshooting.md (Android section), references/setup.md (Android lines), templates/.../pages/android/api_demos_page.py, tests/android/test_api_demos.py.

Verdict summary: most facts are CONFIRMED. The ones that are WRONG or misleading:
1. troubleshooting.md: `java.lang.SecurityException: Permission Denial: starting Intent`. The driver does not surface this text as the session error. It throws `The permission to start '<activity>' activity has been denied.Make sure the activity/package names are correct.`
2. troubleshooting.md: `Timed out waiting for UiAutomator2 server`. This string does not exist. The real text is `The instrumentation process cannot be initialized within <N>ms timeout. ... You could also try to increase the value of 'uiautomator2ServerLaunchTimeout' capability`.
3. troubleshooting.md: `Could not find a connected Android device`. The real text adds a suffix, `... in <N>ms`. When `udid` is set but the device is absent, the error is `Device <udid> was not in the list of connected devices`.
4. troubleshooting.md: the emulator timeout row names no message. The real messages are `Emulator is not ready within <N>ms` and `'<avd>' Emulator has failed to boot: ...`.
5. troubleshooting.md: `appium driver run uiautomator2 reset` also uninstalls `io.appium.settings`, which the row does not mention. Otherwise the row is correct.
6. android.md §5 names the permission dialog package `com.google.android.permissioncontroller`, but the resource-id example uses the prefix `com.android.permissioncontroller`. Both are right, and this is worth stating explicitly: the package is `com.google.*` on GMS devices, while resource-ids keep the `com.android.permissioncontroller:id/` prefix.
7. setup.md: "Node 20 LTS or 22 LTS". Node 20 reached end of life on 2026-04-30, so as of Nov 2026 the advice should be 22 or 24 LTS.
8. setup.md: "must end with `0 required fixes needed`". The text appears mid-line (`### Diagnostic completed, 0 required fixes needed, N optional fixes possible. ###`) and is not the last line.
9. setup.md §3: the SDK component list omits **Android SDK Command-line Tools**. The required doctor check looks for `apkanalyzer` (Windows: `apkanalyzer.bat`) and fails without it.
10. android.md §1 says the options object sets `appium:automationName=UiAutomator2`. Python 6.1.5 actually sends `'UIAutomator2'`. This is cosmetic, because matching is case-insensitive.

## 1. Permission dialog resource-ids (android.md §5)

### Takeaway
CONFIRMED. `com.android.permissioncontroller:id/permission_allow_button`, `permission_allow_foreground_only_button` and `permission_allow_one_time_button` all exist in current AOSP PermissionController layouts. Android 9 and older used `com.android.packageinstaller:id/permission_allow_button`. Google's CTS uses the `com.android.permissioncontroller:id/` prefix, so that prefix is right on GMS devices too, even though the GMS app package is `com.google.android.permissioncontroller`.

### Cited Findings
- `res/layout/grant_permissions.xml` in the Android 15-based PermissionController (LineageOS 22.2 mirror of packages/modules/Permission) declares these ids: `permission_allow_button`, `permission_allow_foreground_only_button`, `permission_allow_one_time_button`, `permission_allow_all_button`, `permission_allow_selected_button`, `permission_deny_button`, `permission_deny_and_dont_ask_again_button`, `permission_no_upgrade_button`, `permission_no_upgrade_and_dont_ask_again_button`, `permission_no_upgrade_one_time_button`, `permission_dont_allow_more_selected_button`, plus location-accuracy radio ids. The lineage-21.0 (Android 14) branch has the same list — [grant_permissions.xml lineage-22.2](https://raw.githubusercontent.com/LineageOS/android_packages_modules_Permission/lineage-22.2/PermissionController/res/layout/grant_permissions.xml), [lineage-21.0](https://raw.githubusercontent.com/LineageOS/android_packages_modules_Permission/lineage-21.0/PermissionController/res/layout/grant_permissions.xml)
- The PermissionController manifest declares `package="com.android.permissioncontroller"` — [AndroidManifest.xml lineage-22.2](https://raw.githubusercontent.com/LineageOS/android_packages_modules_Permission/lineage-22.2/PermissionController/AndroidManifest.xml)
- The permission CTS (which runs on GMS devices) hard-codes `const val ALLOW_BUTTON = "com.android.permissioncontroller:id/permission_allow_button"`, `ALLOW_FOREGROUND_BUTTON = "com.android.permissioncontroller:id/permission_allow_foreground_only_button"`, `DENY_BUTTON = "com.android.permissioncontroller:id/permission_deny_button"` and `DENY_AND_DONT_ASK_AGAIN_BUTTON = ".../permission_deny_and_dont_ask_again_button"`. For Automotive and Watch it locates buttons by text instead — [BaseUsePermissionTest.kt](https://raw.githubusercontent.com/LineageOS/android_packages_modules_Permission/lineage-22.2/tests/cts/permissionui/src/android/permissionui/cts/BaseUsePermissionTest.kt)
- Android 9 (pie-release) PackageInstaller has manifest `package="com.android.packageinstaller"`. Its `grant_permissions.xml` has ids `permission_allow_button`, `permission_deny_button`, `do_not_ask_checkbox` and `permission_more_info_button`. In android10-release the same repo's manifest changes to `package="com.android.permissioncontroller"` — [pie layout](https://raw.githubusercontent.com/aosp-mirror/platform_packages_apps_PackageInstaller/pie-release/res/layout/grant_permissions.xml), [pie manifest](https://raw.githubusercontent.com/aosp-mirror/platform_packages_apps_PackageInstaller/pie-release/AndroidManifest.xml), [android10 manifest](https://raw.githubusercontent.com/aosp-mirror/platform_packages_apps_PackageInstaller/android10-release/AndroidManifest.xml)
- AOSP describes the GMS PermissionController module package as `com.google.android.permissioncontroller` — [source.android.com PermissionController module](https://source.android.com/docs/core/ota/modular-system/permissioncontroller?hl=en) (seen through a search summary; not fetched directly)
- Community usage of the old id: `find_element_by_id('com.android.packageinstaller:id/permission_allow_button')` — [Stack Overflow mirror](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/48541141/how-to-grant-android-system-permissions-using-python)

### Inferences
- The skill's advice to confirm ids on the target OS is correct. A robust pattern tries `permission_allow_foreground_only_button`, then `permission_allow_button`, then `permission_allow_one_time_button` under `com.android.permissioncontroller:id/`, and falls back to `com.android.packageinstaller:id/permission_allow_button` on API 28 and below.
- On Android 10 and later, the "Allow" option for location is `permission_allow_foreground_only_button` ("While using the app"). `permission_allow_button` is usually absent from that dialog.

### Gaps
- OEM skins (MIUI/HyperOS, One UI) may override the layout. I found no primary source listing OEM ids.

## 2. Xiaomi/MIUI "Install via USB" and "USB debugging (Security settings)" (troubleshooting.md)

### Takeaway
CONFIRMED by consistent community sources. No primary source from Xiaomi was found. The claim "needs a SIM/Mi account" is commonly reported but not verified by a primary source.

### Cited Findings
- Fix for `INSTALL_FAILED_USER_RESTRICTED`: Settings > Additional settings > Developer options, then enable "Install via USB" and "USB debugging (Security settings)" — [Stack Overflow mirror](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/40534271/android-studio-failure-install-failed-user-restricted), [installation via USB is disabled](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/57986113/install-failed-user-restricted-installation-via-usb-is-disabled)
- An Appium forum thread recommends "USB debugging (Security settings)" for the Xiaomi `WRITE_SECURE_SETTINGS` permission-denial error — [discuss.appium.io](https://discuss.appium.io/t/permission-denial-writing-to-settings-requires-android-permission-write-secure-settings-on-xiaomi-device/32095)
- On Android 15 the toggle's description reads "Allow granting permissions and simulating input via USB debugging" — [Reddit (mirror)](https://redlib.hbubli.cc/r/AndroidQuestions/comments/1jk6vct/adb_grant_permission_on_android_15)

### Inferences
- The "taps ignored" symptom fits the toggle's description ("simulating input"), so the row is sound. A common extra fix is to disable "MIUI optimization", but that comes only from community answers.
- Xiaomi devices also commonly fail with `Permission denial: writing to settings requires: android.permission.WRITE_SECURE_SETTINGS`. Consider adding that symptom to the same row.

### Gaps
- The SIM card / Mi account requirement is widely reported but unverified here.

## 3. `appium driver doctor uiautomator2` output (setup.md)

### Takeaway
The summary text "0 required fixes needed" is CONFIRMED. The claim that the output "must end with" it is WRONG. The summary appears mid-line, and later lines follow it.

### Cited Findings
- APPIUM/build/lib/doctor/doctor.js:53: `this.log.info(\`### Diagnostic completed, ${this.buildFixMessage()}. ###\`)`. Line 195 has `buildFixMessage()` return `${pluralize('required fix', n, true)} needed, ${pluralize('optional fix', m, true)} possible`. `pluralize('required fix',0,true)` gives `0 required fixes`, so the line reads `### Diagnostic completed, 0 required fixes needed, 2 optional fixes possible. ###`.
- If nothing at all needs fixing, the next line is `Everything looks good, bye!` (doctor.js `reportSuccess`). With only optional issues, an `### Optional Manual Fixes ###` section follows.
- Required checks (UIA2/build/lib/doctor/required-checks.js, re-exported from AAD): `androidHomeCheck`, `javaHomeCheck`, `javaHomeValueCheck`, `androidSdkCheck`. Optional checks: `optionalFfmpegCheck`, `optionalGstreamerCheck`, `optionalBundletoolCheck`. These match setup.md's list.
- AAD/build/lib/doctor/checks.js: `exports.androidHomeCheck = new EnvVarAndPathCheck('ANDROID_HOME', ...)`, and `AndroidSdkCheck.TOOL_NAMES = ['adb', 'emulator', apkanalyzer(.bat on Windows)]` with `isOptional() { return false; }`. The SDK binary lookup paths include `cmdline-tools/latest/bin` (ADB/build/lib/tools/system-calls.js:95-102).
- `does not export any doctor checks` is CONFIRMED (APPIUM/build/lib/cli/extension-command.js:699: `The ${this.type} "${installSpec}" does not export any doctor checks`).

### Inferences
- setup.md should say: look for `0 required fixes needed` in the `### Diagnostic completed ...` line.
- setup.md §3 should add "Android SDK Command-line Tools (latest)" to the SDK Manager list. Without it, the required doctor check fails (`apkanalyzer.bat could NOT be found in '<sdk>'!`).
- The doctor's `androidHomeCheck` checks `ANDROID_HOME` specifically, while the runtime accepts `ANDROID_SDK_ROOT` as a fallback (ADB/build/lib/helpers.js:70 `process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT`). setup.md's "Prefer ANDROID_HOME" is therefore correct and important.

## 4. Error message wordings in troubleshooting.md

### Takeaway
Mixed. Four messages are CONFIRMED, and three are WRONG or reworded. Details follow.

### Cited Findings
- `instrumentation process is not running (probably crashed)`: CONFIRMED. UIA2/build/lib/uiautomator2.js:29-31: `'${method} ${url}' cannot be proxied to UiAutomator2 server because the instrumentation process is not running (probably crashed). Check the server log and/or the logcat output for more details`.
- `'<pkg>/<activity>' or '<pkg>/<waitActivity>' never started`: CONFIRMED. ADB/build/lib/tools/app-commands.js:1020-1022: `${possibleActivityNames.map(name => \`'${name}'\`).join(' or ')} never ${waitForStop ? 'stopped' : 'started'}. Consider checking the driver's troubleshooting documentation.`
- `java.lang.SecurityException: Permission Denial: starting Intent`: WRONG as an Appium error string. ADB app-commands.js:849-852 detects `java.lang.SecurityException` in `am start` stdout and throws `The permission to start '${activity}' activity has been denied.Make sure the activity/package names are correct.` (sic, no space after the period). The raw `Permission Denial` text may still appear in the adb/am output in the server log. Related messages at lines 841-847: `Activity name '<x>' used to start the app doesn't exist or cannot be launched! Make sure it exists and is a launchable activity`.
- `Could not find a connected Android device`: CONFIRMED as a prefix. The actual text is `Could not find a connected Android device in ${timeoutMs}ms` (ADB/build/lib/tools/system-calls.js:356). With `udid` set but missing: `Device ${udid} was not in the list of connected devices` (AAD, line 79).
- Emulator timeout wording: ADB system-calls.js:919 `'${avdName}' Emulator has failed to boot: ...`, line 991 `Emulator is not ready within ${timeoutMs}ms`, and line 1020 `Emulator is not ready within ${timeoutMs}ms ...`. `launchAVD` defaults are `launchTimeout = 60000, readyTimeout = 60000` (line 857).
- `No Chromedriver found that can automate Chrome 'X'`: CONFIRMED. UIA2/node_modules/appium-chromedriver/build/lib/chromedriver.js:435 `No Chromedriver found that can automate Chrome '${chromeVersion}'.` plus an autodownload suggestion. The feature name `chromedriver_autodownload` is CONFIRMED (AAD/build/lib/commands/context/helpers.js `CHROMEDRIVER_AUTODOWNLOAD_FEATURE = 'chromedriver_autodownload'`).
- `Timed out waiting for UiAutomator2 server`: WRONG, because no such string exists in UIA2, AAD or ADB. The real messages are in UIA2/build/lib/uiautomator2.js:264-266, `The instrumentation process cannot be initialized within ${timeout}ms timeout. Make sure the application under test does not crash and investigate the logcat output. You could also try to increase the value of 'uiautomator2ServerLaunchTimeout' capability`, and line 274, `The instrumentation process cannot be initialized. Make sure the application under test does not crash...`.
- `Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported`: CONFIRMED (ADB/build/lib/helpers.js:84).
- `Potentially insecure feature 'adb_shell' has not been enabled`: CONFIRMED (APPIUM's @appium/base-driver/build/lib/basedriver/core.js:239 `Potentially insecure feature '${name}' has not been enabled. If you want to enable this feature and accept the security ramifications...`).
- `JAVA_HOME is not set`: not a literal string. The doctor says `JAVA_HOME environment variable must be set` (AAD doctor checks).
- `socket hang up`: comes from Node's http layer (`err = new Error('socket hang up')`), not from Appium. Plausible as a symptom.

### Inferences
- Because the agent may grep logs for these strings, troubleshooting.md should use the actual strings: `The instrumentation process cannot be initialized`, `has been denied`, `Emulator is not ready within`, `was not in the list of connected devices`.

## 5. `appium driver run uiautomator2 reset`

### Takeaway
CONFIRMED that it exists. It uninstalls three packages, not two, on every device in `device` state.

### Cited Findings
- UIA2/package.json `"appium": { ... "scripts": { "reset": "scripts/reset.js" } }`.
- UIA2/scripts/reset.js: `SERVER_PKGS = ['io.appium.uiautomator2.server', 'io.appium.uiautomator2.server.test', 'io.appium.settings']`. It gets `adb.getConnectedDevices()`, filters `state === 'device'`, and calls `uninstallApk(pkgId)` for each package on each device.

## 6. Java, Node versions (setup.md / troubleshooting.md)

### Takeaway
The Java facts are CONFIRMED (README: Java 8 for SDK below API 30, Java 9+ for API 30+), and JDK 17 is a reasonable recommendation. The Appium `engines` string is CONFIRMED. "Node 20 LTS" is OUTDATED, because Node 20 is end of life as of Nov 2026. I found no evidence that Node 24 breaks Appium 2.19, but I did not test it at runtime.

### Cited Findings
- README line 26: "Java JDK must be installed and JAVA_HOME environment variable must be set. Android SDK below API 30 requires Java 8. Android SDK 30 and above requires Java 9 or newer."
- APPIUM/package.json: `"engines": { "node": "^14.17.0 || ^16.13.0 || >=18.0.0", "npm": ">=8" }`. UIA2/package.json: `"engines": { "node": ">=14", "npm": ">=8" }` and `"peerDependencies": { "appium": "^2.4.1 || ^3.0.0-beta.0" }`.
- The Node release schedule lists v20 end-of-life 2026-04-30, v22 maintenance LTS until 2027-04-30, v24 LTS (maintenance from 2026-10-20) until 2028-04-30, and v26 LTS from 2026-10-28 — [nodejs/Release schedule.json](https://raw.githubusercontent.com/nodejs/Release/main/schedule.json)
- Appium 3 supports `^20.19.0 || ^22.12.0 || >=24.0.0` — [HeadSpin Appium 3 guide](https://headspin.io/blog/appium-3-guide) (secondary source)
- A Node 20.12.2 security fix on Windows broke how older Appium 2.x invoked npm. This affected installs on early 2.5.x — [discuss.appium.io](https://discuss.appium.io/t/appium-driver-install-fails-while-checking-drivers-compatibility/42209)
- The local test environment installed and ran Appium 2.19.0 with Node v22.23.4 (seen in node error output in this session).

### Inferences
- Recommend Node 22 LTS (verified locally) or 24 LTS. Drop 20, which is EOL.
- A JDK 17 recommendation fits current Android command-line tools, which `apkanalyzer` needs. I did not verify this against a primary source in this session.

### Gaps
- Node 24 + Appium 2.19 was not tested at runtime, and I found no reports of it either working or breaking.

## 7. UiAutomator2Options Python properties and driver methods (android.md §1, §4, §6, §7)

### Takeaway
CONFIRMED. Every property name listed exists in PYC 6.1.5. `force_app_launch`, `hide_keyboard` and `auto_launch` do NOT exist as typed properties, and the skill correctly uses `set_capability` for them. All the driver methods listed exist.

### Cited Findings
- `hasattr(UiAutomator2Options, p)` is True for: udid, avd, avd_launch_timeout, avd_ready_timeout, avd_args, is_headless, platform_version, device_name, system_port, app, app_package, app_activity, app_wait_activity, app_wait_package, no_reset, full_reset, auto_grant_permissions, new_command_timeout, app_wait_duration, android_install_timeout, uiautomator2_server_launch_timeout, uiautomator2_server_install_timeout, adb_exec_timeout, disable_window_animation, skip_unlock, ignore_hidden_api_policy_error, no_sign, chromedriver_executable, chromedriver_executable_dir, chromedriver_port, mjpeg_server_port. It is False for force_app_launch, hide_keyboard and auto_launch. (Local check: `SP/venv/bin/python -I`, Appium-Python-Client 6.1.5.)
- Setters take ints in the capability's native unit, or a `timedelta`. For example, `avd_launch_timeout` setter: `self.set_capability(AVD_LAUNCH_TIMEOUT, int(value.total_seconds() * 1000) if isinstance(value, timedelta) else value)`. `new_command_timeout` takes "timedelta instance or an integer number of seconds". Getters return `timedelta`. (PYC options/android/common/avd/avd_launch_timeout_option.py, options/common/new_command_timeout_option.py)
- W3C output: `{'appium:automationName': 'UIAutomator2', 'platformName': 'Android', 'appium:udid': 'x'}`. The default automationName is the string `'UIAutomator2'` (PYC options/android/uiautomator2/base.py:218), not `UiAutomator2`.
- WebDriver has activate_app, terminate_app, query_app_state, hide_keyboard, is_keyboard_shown, press_keycode, current_package, current_activity, start_recording_screen, get_log, update_settings, contexts, switch_to and background_app (hasattr True).
- The `logcat` log type is supported by the driver (AAD/build/lib/commands/log.js:21 `logcat: {`).
- Capability defaults in android.md are CONFIRMED against the README: avdLaunchTimeout and avdReadyTimeout `60000` ms (lines 123-124); avdArgs `-wipe-data` "then the emulator is going to be killed on automated session startup in order to wipe its data" (125); isHeadless "only applied if the emulator is not running before the test starts" (129); platformVersion "used for device autodetection if udid is not provided" (46); deviceName "actually, it is not used to select a device under test" (45); systemPort "first free port from 8200..8299" (56); appWaitDuration `20000` (74); androidInstallTimeout `90000` (75); uiautomator2ServerLaunchTimeout `30000` (58); uiautomator2ServerInstallTimeout `20000` (59); adbExecTimeout `20000` (106); newCommandTimeout `60` seconds (192); hideKeyboard "Use it instead of the legacy appium:unicodeKeyboard ... Only use this feature for special/exploratory cases" (112); autoGrantPermissions "targetSdkVersion ... must be greater or equal to 23 and ... Android 6" (85); forceAppLaunch (82); noSign (141).
- Default reset is CONFIRMED. @appium/base-driver driver.js:281 `this.opts.fastReset = !this.opts.fullReset && !this.opts.noReset`. AAD app-management.js:362-380 runs `forceStop` and then `adb.clear(appPackage)`, logged as "Performed fast reset ... (stop and clear)". UIA2 driver.js:627 has `'Full reset requires an app capability...'`, which confirms that "full_reset needs app".
- `query_app_state` values are CONFIRMED: AAD app-management.js:36-41 `NOT_INSTALLED: 0, NOT_RUNNING: 1, RUNNING_IN_BACKGROUND: 3, RUNNING_IN_FOREGROUND: 4`. Foreground is detected when an `mCurrentFocus`/`mFocusedApp` line contains `<pkg>/` (lines 82-86).

## 8. `mobile:` extensions and settings (android.md §2–§7, troubleshooting.md)

### Takeaway
CONFIRMED. Every name and argument in the android.md tables matches UIA2/build/lib/execute-method-map.js. The scrollGesture return value is confirmed by the driver's gestures doc.

### Cited Findings (from `executeMethodMap` in the installed 4.2.9)
- clickGesture/doubleClickGesture: optional `elementId,x,y`. longClickGesture: optional `elementId,x,y,duration`. dragGesture: optional `elementId,startX,startY,endX,endY,speed`. swipeGesture/scrollGesture: required `direction,percent`, optional `elementId,left,top,width,height,speed`. flingGesture: required `direction`. pinchOpen/CloseGesture: required `percent`. `scroll`: required `strategy,selector`, optional `elementId,maxSwipes`.
- activateApp `{appId}`; terminateApp `{appId, timeout?}`; backgroundApp `{seconds?}`; installApp required `appPath`, optional `checkVersion,timeout,allowTestPackages,useSdcard,grantPermissions,replace,noIncremental`; removeApp `{appId, timeout?, keepData?, skipInstallCheck?}`; isAppInstalled `{appId, user?}`; clearApp `{appId}`; startActivity (all optional, incl. `intent,wait,stop,extras`); deepLink required `url`, optional `package,waitForLaunch`; getCurrentActivity/getCurrentPackage; changePermissions required `permissions`, optional `appPackage,action,target`; getPermissions optional `type,appPackage`; type `{text}`; hideKeyboard; isKeyboardShown; pressKey required `keycode`, optional `metastate,flags,isLongPress`; performEditorAction `{action}`; shell required `command`, optional `args,timeout,includeStderr`; getDeviceTime `{format?}`; deviceInfo; batteryInfo; queryAppState `{appId}`.
- scrollGesture return: "The returned value is a boolean one and equals to `true` if the object can still scroll in the given direction" — [android-mobile-gestures.md v4.2.9](https://raw.githubusercontent.com/appium/appium-uiautomator2-driver/v4.2.9/docs/android-mobile-gestures.md). The implementation returns the proxied boolean (`return /** @type {boolean} */ (await this.uiautomator2.jwproxy.command('/appium/gestures/scroll', ...))`, SP/pkgs/.../build/lib/commands/gestures.js:238-245).
- mobile: scroll: "strategy ... `accessibility id` (UiSelector().description), `class name` (UiSelector().className), `-android uiautomator` (UiSelector)". For elementId: "It is required this element is a valid scrollable container and it was located by `-android uiautomator` strategy. If this property is not provided then the first currently available scrollable view is selected" (README §mobile: scroll).
- backgroundApp: "Any negative value means to not restore the app after putting it to background (the default behavior)" (README). The default `seconds = -1` is in AAD app-management.js:346. android.md's "(negative = stay in background)" is correct. Note that omitting `seconds` also leaves the app in the background.
- clearApp: "The app should be accessible, should not be running, and should exist on the device" (README).
- changePermissions: "`action` Either `grant` (the default action) or `revoke` if `target` is set to `pm`, otherwise one of: `allow` (default), `deny`, `ignore`, `default`"; "`target` Either `pm` (default) or `appops` ... requires *adb_shell* server security option"; the `all` magic string applies when target is pm (README).
- getPermissions: `type` is "one of: `denied`, `granted` or `requested` (the default value)" (README).
- hideKeyboard returns "`true` if the keyboard was successfully hidden or `false` if it was already invisible" (README).
- performEditorAction: supported names are `normal, unspecified, none, go, search, send, next, done, previous` (README).
- installApp checkVersion: "Set to true, in order to skip the application installation if the device under test has a greater or equal to the application version. It may help to avoid `INSTALL_FAILED_VERSION_DOWNGRADE`" (README). Note that installApp's `timeout` default is documented as "6000ms" (sic).
- startActivity `intent` example: `com.some.package.name/.YourActivityClassName` (README).
- Settings exist in the README Settings API table: allowInvisibleElements (line 303, default false), ignoreUnimportantViews (304), enableMultiWindows (306), waitForIdleTimeout (312, "`10000` ms by default ... Consider lowering"), enforceXPath1 (326), disableIdLocatorAutocompletion (328), snapshotMaxDepth (331, default 70, range 1–500).
- The id locator's package prefix is added automatically: "Package identifier prefix is added automatically if unset and is equal to the identifier of the current application under test" (README line 252). accessibilityId maps to `By.desc`, and React Native `accessibilityLabel` lands there (line 253).

### Inferences
- enforceXPath1 is documented for XPath2 interpreter issues ([appium#16142](https://github.com/appium/appium/issues/16142)). The README does not specifically mention `ClassCastException`, so the troubleshooting row's symptom wording is an unverified detail. The fix itself is valid.
- The README does not support android.md's "Google plans to deprecate UiSelector". It is unverified; consider softening or removing it.
- The README does not mention Compose `testTagsAsResourceId`. It is unverified here, though it is commonly documented by Android (not checked).

## 9. ApiDemos app facts (templates)

### Takeaway
CONFIRMED. Package `io.appium.android.apis`, main activity `.ApiDemos`. The same `ApiDemos` ListActivity renders the home list and every sub-list (Views etc.) through `SimpleAdapterWithDesc`, whose `getView` sets each row's content-desc to its text. "Animation" and "WebView" both exist under Views, so the accessibility-id locators in the page objects are correct.

### Cited Findings (androguard on APK; scripts in SP/scripts/ad2.py and ad3.py)
- `pkg io.appium.android.apis main io.appium.android.apis.ApiDemos ver 5.0.0 minSdk 17 target 33`.
- `SimpleAdapterWithDesc.getView`: `invoke-super SimpleAdapter->getView`, `check-cast TextView`, `getText()`, then `setContentDescription(text)`.
- `ApiDemos.onCreate` reads the `io.appium.android.apis.Path` extra (default `""`), calls `getData(path)` and sets `new SimpleAdapterWithDesc(...)` with `from = {"title","contentDescription"}`. Sub-lists are opened through `browseIntent(path)`, which restarts `ApiDemos.class` with that extra, so the Views sub-list uses the same adapter.
- Labels of top-level SAMPLE_CODE activities: Accessibility, Animation, App, Content, Graphics, Media, NFC, OS, Preference, Text, Views. getData also adds an extra row "Access'ibility" next to "Accessibility".
- The Views sub-list has 42 entries starting with 'Animation', 'Auto Complete', 'Buttons', ... and ending 'Visibility', 'WebView', 'WebView2', 'WebView3'. WebView is at index 39 of 42 (alphabetical by Collator), so the test must scroll to reach it. The accessibility-id lookup is an exact `By.desc` match, so "WebView" does not match "WebView2" or "WebView3".
- `queryAppState == 4` for the foreground app is CONFIRMED (section 7).

### Inferences
- `ViewsPage.wait_until_loaded` waits on "Animation", which is the first row, so it is visible without scrolling. Correct.
- `mobile: scroll` with `strategy: "accessibility id"` maps to `UiSelector().description("WebView")`, which is an exact match. Correct.

## 10. `npm pack android-apidemos` + `tar` on Windows (template README)

### Takeaway
CONFIRMED. `npm pack android-apidemos` downloads `android-apidemos-5.0.0.tgz`. It extracts to `package/apks/ApiDemos-debug.apk`. `tar.exe` (bsdtar) ships with Windows 10 1803+ (it first appeared in Insider build 17063).

### Cited Findings
- `npm view android-apidemos version dist.tarball` gives `version = '5.0.0'`, `dist.tarball = 'https://registry.npmjs.org/android-apidemos/-/android-apidemos-5.0.0.tgz'`. The extracted tree is `SP/pkgs/x-apidemos/package/apks/ApiDemos-debug.apk` (6,419,064 bytes).
- "Beginning in Insider Build 17063, we're introducing two command-line tools to the Windows toolchain: curl and bsdtar" — [Microsoft Command Line blog](https://devblogs.microsoft.com/commandline/tar-and-curl-come-to-windows/). tar.exe is at `%windir%\System32\tar.exe`, shipped from Windows 10 1803 — [Medium write-up](https://medium.com/@boutnaru/the-windows-process-journey-tar-exe-bsd-tar-archive-tool-d307a4412c46) (secondary source)

### Inferences
- `tar -xzf (Get-ChildItem android-apidemos-*.tgz).Name` is valid PowerShell syntax, provided exactly one tgz is present.

## 11. `adb shell dumpsys window | findstr mCurrentFocus` (android.md §1, troubleshooting.md)

### Takeaway
MOSTLY CONFIRMED. Plain `dumpsys window` (without `windows`) still contains `mCurrentFocus` and `mFocusedApp` on modern Android. On Android 10+ `dumpsys window windows` dropped them. `mCurrentFocus` can be `null` in some states, such as during transitions or on some Android 14 builds, so the safer advice is to filter for both: `findstr "mCurrentFocus mFocusedApp"` (findstr treats space-separated words as OR).

### Cited Findings
- appium-adb itself switches commands by API level: `const dumpsysArg = apiLevel >= 29 ? 'displays' : 'windows'; const cmd = ['dumpsys', 'window', dumpsysArg];` (ADB/build/lib/tools/app-commands.js:871-876). The driver's `queryAppState` matches lines containing either `mCurrentFocus` or `mFocusedApp` (AAD app-management.js:84).
- `dumpsys window windows` no longer includes the focus fields on Android 10, but plain `dumpsys window` still does — [Mozilla bug 1615280](https://bugzilla.mozilla.org/show_bug.cgi?id=1615280) (seen through a search summary)
- `mCurrentFocus` shows `null` on Android 14 in some cases — [openatx/uiautomator2#952](https://www.github.com/openatx/uiautomator2/issues/952) (seen through a search summary)

### Inferences
- Recommend `adb shell dumpsys window displays | findstr "mCurrentFocus mFocusedApp"`, which mirrors what Appium does on API 29+. Alternatively, call `driver.current_activity` / `mobile: getCurrentActivity` from a session.

## 12. Other android.md details checked

### Cited Findings
- `--allow-insecure uiautomator2:adb_shell` is needed for `mobile: shell` (AAD/build/lib/commands/shell.js:13 `this.assertFeatureEnabled(utils_1.ADB_SHELL_FEATURE)`, `ADB_SHELL_FEATURE = 'adb_shell'`) and for changePermissions with target appops (AAD permissions.d.ts: "'adb_shell' server security option to be enabled"). CONFIRMED.
- `appWaitPackage` exists (README line 73). appWaitActivity wildcards (`com.example.*`) are described in docs/activity-startup.md, which is not in the npm package and was not verified here. The ADB `waitForActivity` builds `possibleActivityNames` from a comma-separated list, and the long-standing documented behaviour supports `*`.
- `chromedriverExecutableDir` (README line 174), `chromedriverPort` (170) and `mjpegServerPort` (157) exist. CONFIRMED.
- The UiAutomator2 4.x minimum Android version (setup.md: "Android 5.0+ (API 21)") was not re-verified in this pass.

### Gaps
- appWaitActivity wildcard syntax was not verified against a primary source in this session (docs/activity-startup.md is not in the npm tarball).
- UiSelector deprecation claim: no source found.
- The android.googlesource.com host is blocked in this session (DNS/proxy refusal). AOSP facts were checked through the LineageOS and aosp-mirror GitHub mirrors instead.

# One-time Windows host setup

Target host: **Windows 10/11 PC, local Appium 2.x server.** (The Windows driver README officially
lists Windows 10 only. Windows 11 works in practice, but isn't officially supported.) Run everything in a normal
PowerShell window unless a step says "elevated" (Run as Administrator).

## Version matrix (checked against npm registry metadata, Nov 2026)

| Component | Version to install | Why this version |
|---|---|---|
| Node.js | **22 LTS** (24 LTS also fine) | Appium 2.19.0 `engines`: `^14.17.0 \|\| ^16.13.0 \|\| >=18.0.0`. Node 20 is end-of-life (Apr 2026). Node 26 (the current "LTS" channel) is untested with Appium 2.19. `install-wad` needs Node ≥ 20 |
| Appium server | `appium@2.19.0` (last 2.x) | npm `latest` is 3.x. Pin `@2` to stay on Appium 2 |
| UiAutomator2 driver | `uiautomator2@4.2.9` | 4.x is the last line with peer `appium ^2.4.1`. 5.x–8.x need Appium 3, 9.x needs Appium 4 |
| Windows driver | `windows@4.4.7` | 4.x is the last line with peer `appium ^2.4.0`. 5.x+ need Appium 3 |
| WinAppDriver | latest stable from Microsoft (installed by the driver script) | Windows driver ≥3.0.0 no longer installs it automatically |
| Python | 3.10+ | `Appium-Python-Client` 6.x requires `>=3.10` |
| Java JDK | 17 (any JDK ≥ 9 works for SDK 30+) | UiAutomator2 needs `JAVA_HOME`. SDK below 30 needs Java 8 |

> **Pitfall:** on Appium 2.x, `appium driver install uiautomator2` with no version resolves to the
> newest driver and fails with
> `cannot be installed because the server version it requires (^4.0.0-beta.6) does not meet the currently installed one (2.19.0)`.
> Always install with an explicit `@version`.

## 1. Node.js + Appium server

```powershell
# Install Node.js 22 LTS from https://nodejs.org/en/download (pick v22 explicitly;
# the generic "LTS" download / winget LTS package now gives Node 26).
node -v                   # v22.x

npm -v

npm install -g appium@2.19.0
appium --version          # -> 2.19.0
```

Defaults (Appium 2): address `0.0.0.0`, port `4723`, **base path empty**. Clients connect to
`http://127.0.0.1:4723`, with no `/wd/hub`.

## 2. Drivers (pinned)

```powershell
appium driver install uiautomator2@4.2.9
appium driver install windows@4.4.7
appium driver list --installed
#  - uiautomator2@4.2.9 [installed (npm)]
#  - windows@4.4.7 [installed (npm)]
```

**Don't use `appium driver update` on this stack.** It stays within the current major version and
does **not** check server compatibility. With these pins it stops with
`The driver 'uiautomator2' has a major revision update (4.2.9 => 9.0.2) … re-run with --unsafe`.
**Never** add `--unsafe`, because that installs a driver that needs Appium 3/4 and breaks the server.
To change versions, uninstall and then install a pinned 4.x version:

```powershell
appium driver list --installed --updates          # see what's available (read-only)
appium driver uninstall uiautomator2
appium driver install uiautomator2@4.2.9
```

## 3. Android SDK, adb, Java

1. Install Android Studio, or only the command-line tools, from https://developer.android.com/studio.
2. In SDK Manager (SDK Tools tab) install: **Android SDK Platform-Tools** (adb),
   **Android SDK Build-Tools**, **Android SDK Command-line Tools (latest)** (required: the doctor
   check looks for `cmdline-tools\latest\bin\apkanalyzer.bat`), **Android Emulator**, and at least
   one **system image** if you will use emulators.
3. Set environment variables (User scope is fine). Open a **new** terminal afterwards:

```powershell
setx ANDROID_HOME "$env:LOCALAPPDATA\Android\Sdk"
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17"     # adjust to your JDK
# Add to PATH (System Properties > Environment Variables > Path):
#   %ANDROID_HOME%\platform-tools
#   %ANDROID_HOME%\emulator
#   %JAVA_HOME%\bin
```

UiAutomator2 accepts `ANDROID_HOME` or `ANDROID_SDK_ROOT`, but `appium driver doctor` checks
`ANDROID_HOME` specifically. Always set `ANDROID_HOME`.

### Emulator

```powershell
emulator -list-avds                 # names you can put in ANDROID_AVD
emulator -avd Pixel_7_API_34        # optional: start it yourself...
# ...or set ANDROID_AVD and let Appium boot it (appium:avd)
```

### Real device

1. On the phone: Settings → About phone → tap *Build number* 7× → Developer options →
   enable **USB debugging**. Some vendors (e.g. Xiaomi/MIUI) also need
   *USB debugging (Security settings)* and *Install via USB*.
2. Plug in the device and accept the RSA fingerprint prompt.
3. `adb devices -l` must show the device as `device`. If it shows `unauthorized` or `offline`, see
   troubleshooting.md.
4. Copy the serial into `ANDROID_UDID`.

UiAutomator2 4.x supports Android 5.0+ (API 21). Android 6.0+ is recommended.

## 4. Windows driver prerequisites

1. **Enable Developer Mode**: run `start ms-settings:developers` (works on every version) and
   switch *Developer Mode* on. The menu path varies: Windows 10 is Update & Security → For developers,
   Windows 11 is System → For developers, and Windows 11 25H2+ is System → Advanced → For developers.
2. **Install WinAppDriver** through the driver script. Run it from an **elevated** terminal: it runs
   the WAD installer silently (`/install /quiet /norestart`) into Program Files, so there is no UAC prompt:

   ```powershell
   appium driver run windows install-wad            # latest stable WinAppDriver
   appium driver run windows install-wad 1.2.1      # or a specific version
   ```

   You can also download the installer from https://github.com/microsoft/WinAppDriver/releases
   (1.2.1 is the last stable release). Default install path:
   `C:\Program Files (x86)\Windows Application Driver\WinAppDriver.exe`, which the driver checks first,
   then `%PROGRAMFILES%`. For a custom location, set `APPIUM_WAD_PATH` to the full exe path.
3. **Do not start WinAppDriver.exe yourself.** The Appium Windows driver spawns it on a free port
   in 4724–4824 for each session. A manually started WAD listens on 127.0.0.1:4723 by default and
   **collides with Appium's own port**. Only run WAD yourself if you also set `appium:wadUrl`.
4. Locator tools (pick one):
   - **Inspect.exe**: ships with the Windows SDK, typically
     `C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\inspect.exe`.
   - **Accessibility Insights for Windows**: https://accessibilityinsights.io.

> The Windows driver (and WinAppDriver) is in maintenance/deprecated status upstream. It still
> works with Appium 2 + driver 4.4.7. See troubleshooting.md for what to do when WAD misbehaves.

## 5. Python client

```powershell
# If scripts are blocked ("running scripts is disabled on this system"), allow local scripts
# once. This also unblocks the npm `appium.ps1` shim:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

py -3 -m venv .venv               # any installed Python >= 3.10 (py --list shows them)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt       # Appium-Python-Client, pytest, python-dotenv
```

## 6. Start the server

```powershell
# Plain:
appium

# With the insecure features this skill sometimes uses. QUOTE the list: in PowerShell an
# unquoted comma list becomes an array and may reach Appium mangled. The prefix must be the
# lowercase driver name (uiautomator2 / windows). "UiAutomator2:adb_shell" is silently ignored.
appium --allow-insecure "uiautomator2:adb_shell,windows:power_shell"

# Recommended when you are NOT running parallel sessions:
appium --session-override --log-timestamp --log appium.log
```

| Feature name | Unlocks |
|---|---|
| `uiautomator2:adb_shell` | `mobile: shell`, `mobile: changePermissions` with `target: appops` |
| `windows:power_shell` | `appium:prerun` / `appium:postrun`, `execute_script("powerShell", …)` |
| `windows:modify_fs` | `windows: deleteFile`, `windows: deleteFolder`, `driver.push_file()` |

Bare names (`adb_shell`) are still accepted by Appium 2.x and apply to all drivers.
`--relaxed-security` enables everything. Avoid it except on throwaway machines.

## 7. Health check (run after setup and whenever things break)

```powershell
appium --version                         # 2.19.0
appium driver list --installed           # uiautomator2@4.2.9, windows@4.4.7
appium driver doctor uiautomator2        # look for "### Diagnostic completed, 0 required fixes needed, …"
adb version
adb devices -l                           # every target listed as "device"
echo $env:ANDROID_HOME; echo $env:JAVA_HOME
```

- `appium driver doctor uiautomator2` checks `ANDROID_HOME`, the Android SDK tools and
  `JAVA_HOME` (all required), plus optional ffmpeg, gstreamer and bundletool. Optional warnings don't block.
- `appium driver doctor windows` reports *"does not export any doctor checks"*. That is expected
  for driver 4.4.7. Check the Windows side by hand:

```powershell
Test-Path "$env:ProgramFiles\Windows Application Driver\WinAppDriver.exe"
Test-Path "${env:ProgramFiles(x86)}\Windows Application Driver\WinAppDriver.exe"
# Developer Mode = 1:
Get-ItemPropertyValue 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock' AllowDevelopmentWithoutDevLicense
# Calculator AUMID (any UWP app works the same way):
Get-StartApps | Where-Object Name -like '*Calc*'
```

Server smoke test once `appium` is running:

```powershell
Invoke-RestMethod http://127.0.0.1:4723/status    # value.ready = True
```

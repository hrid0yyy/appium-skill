# Appium 2.x sample project: Android (UiAutomator2) + Windows (WinAppDriver)

Python + pytest skeleton with one Android suite (official Appium **ApiDemos** app) and one
Windows suite (built-in **Calculator**). Host: Windows PC with a local Appium 2.x server.
One-time host setup is in `../../references/setup.md`.

```
appium-pytest-project/
├── .env.example            # every machine-specific value lives here (copy to .env)
├── pytest.ini              # markers: android, windows; logging to console + artifacts/
├── requirements.txt
├── config/settings.py      # env/.env → typed Settings
├── core/
│   ├── driver_factory.py   # build_android_options / build_windows_options / create_driver
│   └── waits.py            # explicit-wait helpers (no sleeps)
├── pages/
│   ├── base_page.py
│   ├── android/api_demos_page.py
│   └── windows/calculator_page.py
└── tests/
    ├── conftest.py         # driver fixture: marker → platform, screenshot+source on failure, quit
    ├── android/test_api_demos.py
    └── windows/test_calculator.py
```

## 1. Install

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## 2. Start Appium (separate terminal)

```powershell
appium --session-override --log appium.log
```

## 3. Android test (ApiDemos)

```powershell
# Get the official ApiDemos APK from npm (once):
mkdir $env:USERPROFILE\appium-apps -Force; cd $env:USERPROFILE\appium-apps
npm pack android-apidemos
tar -xzf (Get-ChildItem android-apidemos-*.tgz).Name
#  -> package\apks\ApiDemos-debug.apk
```

Edit `.env`:

```
ANDROID_APP=C:\Users\<you>\appium-apps\package\apks\ApiDemos-debug.apk
ANDROID_AVD=Pixel_7_API_34        # or ANDROID_UDID=<serial from adb devices -l>
```

```powershell
adb devices -l                  # real device: must be "device"
pytest -m android -v
```

## 4. Windows test (Calculator)

`.env` already has `WINDOWS_APP=Microsoft.WindowsCalculator_8wekyb3d8bbwe!App`.
Developer Mode must be on and WinAppDriver installed (`appium driver run windows install-wad`,
elevated). Don't start WinAppDriver yourself, because the driver launches it.

```powershell
pytest -m windows -v
```

Keep the desktop unlocked and don't touch mouse/keyboard while it runs.

## 5. Useful variations

```powershell
pytest -m android -k scroll                 # a single test
pytest tests/windows/test_calculator.py     # by path
$env:ANDROID_UDID="emulator-5556"; pytest -m android   # env vars override .env
```

On failure, `artifacts/` gets `<test>-<timestamp>.png` and the page-source `.xml`, and
`artifacts/test-run.log` has DEBUG logs including the capabilities sent.

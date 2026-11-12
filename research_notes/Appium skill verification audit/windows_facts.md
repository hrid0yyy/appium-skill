# Windows-desktop facts audit (Appium 2.19.0 + appium-windows-driver 4.4.7 + WinAppDriver, Appium-Python-Client 6.1.5)

Files audited (not modified): `references/windows.md`, `references/setup.md`, `references/troubleshooting.md`, `templates/appium-pytest-project/pages/windows/calculator_page.py` under `/home/user/appium-skill/.claude/skills/appium-android-windows/`.

Local sources used:
- DRV = `/tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/pkgs/x-appium-windows-driver@4.4.7/package/`
- Python venv `/tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/venv/bin/python -I` (Appium-Python-Client 6.1.5 confirmed via importlib.metadata)
- Downloaded copies in `/tmp/claude-0/-home-user-appium-skill/99c4f702-c143-5696-86fb-454bb7a0e841/scratchpad/wad`, `/calc`, `/msdocs`

Network limits: learn.microsoft.com, accessibilityinsights.io, the GitHub REST API for microsoft/WinAppDriver (releases, issue comments) and github.com HTML pages for that repo all returned 403 through the proxy. raw.githubusercontent.com, `git ls-remote`, GitHub search/code and search/issues, and npm all worked. Microsoft docs were read from their GitHub source repos (MicrosoftDocs/*) instead.

## Q1. Windows Calculator AutomationIds, display Name, and Standard mode

### Takeaway
CONFIRMED: all the ids (`num0Button`..`num9Button`, `plusButton`, `minusButton`, `multiplyButton`, `equalButton`, `clearButton`, `CalculatorResults`) and the "Display is N" Name. `clearButton` exists in Standard mode next to `clearEntryButton`, and both are always visible there. In Scientific mode the two buttons swap: `clearButton` is only visible while the input is empty. The page object never forces Standard mode. Microsoft's own sample does, so the template is fragile if Calculator was last left in a different mode.

### Cited Findings
- `NumberPad.xaml` defines `AutomationProperties.AutomationId="num0Button"` through `"num9Button"`. — [microsoft/calculator NumberPad.xaml](https://raw.githubusercontent.com/microsoft/calculator/main/src/Calculator/Views/NumberPad.xaml)
- `CalculatorStandardOperators.xaml` defines `clearButton`, `clearEntryButton`, `equalButton`, `minusButton`, `multiplyButton` and `plusButton`. For example: `<controls:CalculatorButton x:Name="ClearButton" ... AutomationProperties.AutomationId="clearButton" ... ButtonId="Clear" Content="C"/>`, preceded by `x:Name="ClearEntryButton" ... AutomationProperties.AutomationId="clearEntryButton" ... Content="CE"`. Neither has a Visibility binding in Standard. — [CalculatorStandardOperators.xaml](https://raw.githubusercontent.com/microsoft/calculator/main/src/Calculator/Views/CalculatorStandardOperators.xaml)
- In Scientific mode: `ClearEntryButton ... Visibility="{x:Bind ViewModel.IsInputEmpty, ... BooleanToVisibilityNegationConverter}"` and `ClearButton ... Visibility="{x:Bind ViewModel.IsInputEmpty, ... BooleanToVisibilityConverter}"`. So C is shown only when the input is empty, and CE is shown otherwise. — [CalculatorScientificOperators.xaml](https://raw.githubusercontent.com/microsoft/calculator/main/src/Calculator/Views/CalculatorScientificOperators.xaml)
- `Calculator.xaml` sets `AutomationProperties.AutomationId="CalculatorResults"` (and `CalculatorAlwaysOnTopResults` for always-on-top mode). — [Calculator.xaml](https://raw.githubusercontent.com/microsoft/calculator/main/src/Calculator/Views/Calculator.xaml)
- The en-US resource is `Format_CalculatorResults` = `Display is %1`, with the comment "%1 = Localized display value, e.g. "50"". `Format_CalculatorResults_Decimal` = `Display is %1 point` (after pressing the decimal separator). — [Resources.resw en-US](https://raw.githubusercontent.com/microsoft/calculator/main/src/Calculator/Resources/en-US/Resources.resw)
- Microsoft's own UI test framework uses the same ids: `TryFindElementByAccessibilityId("num0Button")`…`("num9Button")`, `"plusButton"`, `"minusButton"`, `"multiplyButton"`, `"equalButton"`, `"clearEntryButton"`, `"clearButton"`. It reads the result with `CalculatorResult.Text.Replace("Display is", string.Empty).Trim()`. — [StandardOperatorsPanel.cs](https://raw.githubusercontent.com/microsoft/calculator/main/src/CalculatorUITestFramework/StandardOperatorsPanel.cs), [NumberPad.cs](https://raw.githubusercontent.com/microsoft/calculator/main/src/CalculatorUITestFramework/NumberPad.cs), [CalculatorResults.cs](https://raw.githubusercontent.com/microsoft/calculator/main/src/CalculatorUITestFramework/CalculatorResults.cs)
- Mode switching in Microsoft's tests: click `TogglePaneButton`, wait for the `SplitViewPane` class, then click the AutomationId `"Standard"` (also `"Scientific"`, `"Programmer"`, `"Date"`, ...). The header has AutomationId `Header`. — [NavigationMenu.cs](https://raw.githubusercontent.com/microsoft/calculator/main/src/CalculatorUITestFramework/NavigationMenu.cs), [CalculatorApp.cs](https://raw.githubusercontent.com/microsoft/calculator/main/src/CalculatorUITestFramework/CalculatorApp.cs)
- The WinAppDriver sample ensures Standard mode explicitly in ClassInitialize: "// Ensure that calculator is in standard mode", `if (!header.Text.Equals("Standard"...)) { ...FindElementByAccessibilityId("TogglePaneButton").Click(); ... splitViewPane.FindElementByName("Standard Calculator").Click(); }`. It uses `FindElementByAccessibilityId("num8Button")`, `"divideButton"`, `"equalButton"`, `"minusButton"`, `"CalculatorResults"`, and `.Text.Replace("Display is", string.Empty).Trim()`. — [WinAppDriver Samples/C#/CalculatorTest/ScenarioStandard.cs](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Samples/C%23/CalculatorTest/ScenarioStandard.cs)
- The WAD Python sample uses `desired_caps["app"] = "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"` and `find_element_by_accessibility_id("CalculatorResults").text` then `.strip("Display is ")`. It uses legacy Selenium 3 APIs (`find_element_by_*`), which no longer exist in Appium-Python-Client 6.x. — [Samples/Python/calculatortest.py](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Samples/Python/calculatortest.py)
- The AUMID `Microsoft.WindowsCalculator_8wekyb3d8bbwe!App` is used verbatim in the driver README: "for example `Microsoft.WindowsCalculator_8wekyb3d8bbwe!App`". — DRV `README.md` (appium:app row)

### Inferences
- `calculator_page.py` locators are all correct for Standard mode (and for Scientific, except `clearButton` after digits are entered). Recommended fix: add an `ensure_standard_mode()` step. Read `Header` text, and if it isn't "Standard", click `TogglePaneButton` and then the accessibility id `Standard`. This matches Microsoft's own tests. Calculator remembers the last-used mode across launches, so a user who last used Scientific, Programmer, a converter or Graphing mode breaks the test.
- Programmer mode: digits come from the shared NumberPad, but `CalculatorProgrammerOperators.xaml` does not contain `plusButton` and similar ids. Converter, Date and Graphing modes have no such buttons at all.
- `result()` regex `-?[\d.,]+\s*$`: works for "Display is 3" and "Display is 1,234". It may fail for locales whose grouping separator is a (narrow) no-break space, and for "Display is 7 point". Locale-sensitive but acceptable. The docstring "Display is 3" is correct.

### Gaps
- Could not test on a live Windows machine. The Store build may lag behind the `main` branch, but these ids have been stable since at least the WAD sample era (2017–2019) and are still present on main.
- Whether the Name contains invisible Unicode direction marks (e.g. U+202D/U+202C) around negative numbers is unverified.

## Q2. WinAppDriver multi-window behaviour

### Takeaway
CONFIRMED with nuances. `window_handles` returns the top-level windows of the app/process under test, and `switch_to.window` works between them. Switching to another process's window fails with "Window handle does not belong to the same process/application". A `Root` session has **0** window handles: you search from the desktop root instead of switching. The `appTopLevelWindow` attach workaround is documented by Microsoft.

### Cited Findings
- "One test session typically corresponds to one app top level window ... Windows Application Driver supports all these scenarios by exposing the entire desktop through a **Root** session" (`appCapabilities.SetCapability("app", "Root")`). — [WinAppDriver Docs/FAQ.md](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Docs/FAQ.md)
- FAQ, "When and how to attach to an existing App Window": "create a new session ... by providing the application top level window handle as a hex string (E.g. `0xB822E2`). This window handle can be retrieved from various methods including the Desktop Session". Example: `GetAttribute("NativeWindowHandle")`, then `int.Parse(...).ToString("x")`, then `SetCapability("appTopLevelWindow", ...)`. "This mechanism can also be used for applications that have unusually long startup times." — [FAQ.md](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Docs/FAQ.md)
- Splash-screen case in the FAQ: "// Return all window handles associated with this process/application. var allWindowHandles = session.WindowHandles; ... You can repeat this logic with any top window with the same process id ... session.SwitchTo().Window(allWindowHandles[0]);" — [FAQ.md](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Docs/FAQ.md)
- The WAD test `GetWindowHandles_Desktop` asserts `Assert.AreEqual(0, handles.Count);` for a Root session. `SwitchWindows` asserts that switching between handles of the same app works. `SwitchWindowsError_ForeignWindowHandle` expects "Window handle does not belong to the same process/application". `SwitchWindowsError_NonTopLevelWindowHandle` expects a message ending "is not a top level window handle" (handles must be hex, e.g. `0x00880088`). — [Tests/WebDriverAPI/Window.cs](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Tests/WebDriverAPI/Window.cs)
- SupportedAPIs.md lists `GET /window_handle`, `GET /window_handles`, `POST /window` (switch) and `DELETE /window` (close). — [Docs/SupportedAPIs.md](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Docs/SupportedAPIs.md)
- `AppiumAppLaunch.cs` Launch_ModernApp: "This will create a new calculator window and point the current active session to it", `Assert.AreEqual(originalWindowHandlesCount + 1, session.WindowHandles.Count)`. — [AppiumAppLaunch.cs](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Tests/WebDriverAPI/AppiumAppLaunch.cs)
- `AppiumAppClose.cs`: after `session.CloseApp()`, `Assert.AreEqual(0, session.WindowHandles.Count)`. A second CloseApp raises NoSuchWindow. — [AppiumAppClose.cs](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Tests/WebDriverAPI/AppiumAppClose.cs)
- Driver docstrings: `windowsLaunchApp` "(Re)launch app under test in the same session ... Generally this API would create a new app window and point the current active session to it". `windowsCloseApp` "Close the active window of the app under test ... After the current app window is closed it is required to use the above API to switch to another active window if there is any; this API does not perform the switch automatically." — DRV `build/lib/commands/app-management.js`

### Inferences
- windows.md §4 is accurate. One addition worth making: with `app="Root"`, `driver.window_handles` is empty. Find the window element from the desktop, read `NativeWindowHandle` (decimal), convert it with `hex()`, and start a new session with `appTopLevelWindow`. This is exactly Microsoft's FAQ pattern, so the "then attach" wording is correct.
- "windows: launchApp ... (may create a new window)" is correct, and the session switches to the new window automatically.

### Gaps
- None material.

## Q3. `get_attribute("Value.Value")` and `el.text`

### Takeaway
`Value.Value` is the right attribute naming scheme (`<Pattern>.<Property>`, as Inspect shows it). WAD's own test uses the sibling `SelectionItem.IsSelected`, but several open WAD issues report `Value.Value` returning null for some controls. `el.text` is MISLEADINGLY described: WAD returns the *text value* for TextBox and TextBlock, the selected item for lists, and Name for buttons and pivot items. `el.text` is therefore the primary way to read a TextBox, with `Value.Value` as a fallback.

### Cited Findings
- WAD `ElementText.cs` comments and assertions: "// Pivot Item element returns the name", "// Button element returns the button name", "// TextBlock element returns the text value", "// List element returns the value of the selected list item", "// TextBox element returns the text value". After `textBox.SendKeys("Test alarm name text box!")` it asserts `Assert.AreEqual("Test alarm name text box!", textBox.Text)`. — [Tests/WebDriverAPI/ElementText.cs](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Tests/WebDriverAPI/ElementText.cs)
- WAD `ElementAttribute.cs` asserts the attributes `Name`, `LegacyName` ("Shows as Legacy|Accessible.Name in inspect.exe"), `AutomationId`, `FrameworkId`, `ClassName`, `IsEnabled`, `IsKeyboardFocusable`, `IsControlElement`, `ProcessId`, `RuntimeId`, `ClickablePoint`, `BoundingRectangle`, `SelectionItem.IsSelected` and `IsSelectionItemPatternAvailable`. `GetAttribute("InvalidAttribute")` returns null rather than throwing. — [Tests/WebDriverAPI/ElementAttribute.cs](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Tests/WebDriverAPI/ElementAttribute.cs)
- Issue #1049 (open): "not able to get the value of an element using Value.Value and is returning null" (WAD v1.1). Issue #2030 (open): "Not able to get Value Attribute using ... getAttribute("Value.Value") and ... ("LegacyValue")" for a UWP text box. Issue #567: XPath `//*[@Value.Value='01']` fails to compile, because a dot in an attribute name breaks XPath. — [#1049](https://github.com/microsoft/WinAppDriver/issues/1049), [#2030](https://github.com/microsoft/WinAppDriver/issues/2030), [#567](https://github.com/microsoft/WinAppDriver/issues/567) (bodies read via the GitHub search API)

### Inferences
- Suggested replacement for the windows.md §5 last paragraph: "`el.text` returns Name for buttons and labels, but the text content for TextBox/TextBlock (WAD ElementText test). If it comes back empty, try `el.get_attribute("Value.Value")`, then `el.get_attribute("LegacyValue")`. `get_attribute` returns None for unknown attributes. Don't use `Value.Value` inside XPath."

### Gaps
- There is no single authoritative WAD list of supported attribute names. SupportedAPIs.md only lists the endpoint.

## Q4. Developer Mode registry key and Settings path

### Takeaway
The registry key and value are CONFIRMED. The Settings path in setup.md is OUTDATED for Windows 11 25H2+, where it is **System > Advanced > For developers**. The universal shortcut is `start ms-settings:developers`.

### Cited Findings
- "To enable developer mode, set the values of this `DWORD` to `1`: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock\AllowDevelopmentWithoutDevLicense`". Also `reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"` (run in an admin PowerShell). — [MicrosoftDocs windows-dev-docs hub/advanced-settings/developer-mode.md (ms.date 11/12/2025)](https://raw.githubusercontent.com/MicrosoftDocs/windows-dev-docs/docs/hub/advanced-settings/developer-mode.md)
- Same doc: "Prior to Windows 11 25H2, these settings appear on the **For developers** page in Windows settings. In Windows 11 25H2 and later, they appear in the **For developers** section of the Advanced settings page." Also "go to **[System > Advanced](ms-settings:developers)**". — same source
- The WAD README requires Developer Mode ("Enable Developer Mode in Windows settings"). The driver README says "Developer mode must be enabled". — [WinAppDriver README](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/README.md); DRV `README.md`

### Inferences
- setup.md §4.1: "Settings → System → For developers (Windows 11)" is correct before 25H2. Add "(Windows 11 25H2+: Settings → System → Advanced → For developers; or run `start ms-settings:developers`)".

### Gaps
- None.

## Q5. Get-StartApps

### Takeaway
CONFIRMED: it returns `Name` and `AppID`, and the AppID is the AppUserModelID (AUMID).

### Cited Findings
- "The **Get-StartApps** cmdlet gets the names and AppIDs of installed apps of the current user. An AppID is an AppUserModelID. You can specify a particular app by using its name, or ... the wildcard character (*)." The output table columns are `Name AppID`. — [MicrosoftDocs windows-powershell-docs Get-StartApps.md](https://raw.githubusercontent.com/MicrosoftDocs/windows-powershell-docs/main/docset/winserver2022-ps/StartLayout/Get-StartApps.md)

### Inferences
- It is per current user. It also lists classic Start-menu apps, whose AppID is not a UWP AUMID (it can be a path or a custom AUMID). Use `!App`-style AppIDs only for packaged apps. `Get-StartApps -Name '*Calc*'` also works, as an alternative to `Where-Object`.

### Gaps
- None.

## Q6. Inspect.exe location and Accessibility Insights URL

### Takeaway
CONFIRMED. Inspect lives in `\bin\<version>\<platform>` under the Windows SDK root, which defaults to `C:\Program Files (x86)\Windows Kits\10`. Accessibility Insights for Windows is downloaded from https://accessibilityinsights.io.

### Cited Findings
- "*Inspect.exe* is located in the *\bin\<version>\<platform>* folder of the SDK installation path. You don't typically need to run it as administrator." — [MicrosoftDocs win32 desktop-src/WinAuto/inspect-objects.md](https://raw.githubusercontent.com/MicrosoftDocs/win32/docs/desktop-src/WinAuto/inspect-objects.md)
- The older WAD doc says "typically `C:\Program Files (x86)\Windows Kits\10\bin\x86`" (pre-versioned SDK layout). — [WinAppDriver Docs/AuthoringTestScripts.md](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Docs/AuthoringTestScripts.md)
- "You can download and install the application from https://accessibilityinsights.io." — [microsoft/accessibility-insights-windows README](https://raw.githubusercontent.com/microsoft/accessibility-insights-windows/main/README.md)

### Inferences
- setup.md's `C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\inspect.exe` is correct for a default x64 SDK install.

### Gaps
- None.

## Q7. Ports, WAD spawning, install-wad, WAD install paths, latest WAD version

### Takeaway
Ports are CONFIRMED: WAD listens on `127.0.0.1:4723` by default, and driver 4.4.7 spawns it on the first free port in 4724–4824, or on `systemPort`. The driver never checks for admin rights. The admin requirement for install-wad is an inference (a silent per-machine installer), not documented. The install-path order in setup.md is reversed: the driver checks `%ProgramFiles(x86)%` first, and that is Microsoft's documented default. The latest WAD tags are `v1.2.1` and `v1.2.99`. setup.md's example `install-wad 1.2.1` is valid.

### Cited Findings
- `const WAD_PORT_RANGE = [4724, 4824];` ... `this.port = await (0, portscanner_1.findAPortNotInUse)(startPort, endPort);` with the error "Could not find any free port in range ${startPort}..${endPort}. Please check your system firewall settings or set 'systemPort' capability". Spawn args: `[`${this.port}${this.base}`]`, plus `'/forcequit'` when `ms:forcequit` is set. A lock-file guard `wad_port_guard` in the OS temp dir serializes port allocation. — DRV `build/lib/winappdriver.js` lines 19–90
- When `wadUrl` is set: "If this URL is provided explicitly then the driver won't try to either autodetect or start WinAppDriver automatically". The error is "WinAppDriver server is not listening at ${url}. Make sure it is running and the provided wadUrl is correct". — DRV `README.md`; DRV `build/lib/winappdriver.js` line 256
- README `appium:systemPort`: "The default starting port number for a new Appium Windows Driver session is `4724`. If this port is already busy then the next free port will be automatically selected." — DRV `README.md`
- WAD README: "listening to requests on the default IP address and port (`127.0.0.1:4723`)" and "Run `WinAppDriver.exe` from the installation directory (E.g. `C:\Program Files (x86)\Windows Application Driver`)". Also "You must run `WinAppDriver.exe` as **administrator** to listen to a different IP address and port." — [WinAppDriver README](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/README.md)
- Driver path detection: `APPIUM_WAD_PATH` env first, then `POSSIBLE_WAD_INSTALL_ROOTS = [process.env['ProgramFiles(x86)'], process.env.ProgramFiles, `${process.env.SystemDrive || 'C:'}\\\\Program Files`]` joined with `Windows Application Driver\WinAppDriver.exe`, then an MSI uninstall-registry lookup (`DisplayName` = `Windows Application Driver`). — DRV `build/lib/installer.js`
- `isAdmin()` (fsutil dirty query) is exported from installer.js but not called anywhere in the 4.4.7 package (grep of `build/`, `lib/` and `scripts/`). `scripts/install-wad.mjs` throws on non-win32 ("WinAppDriver is only supported on Windows"). It lists GitHub releases, takes the highest non-draft, non-prerelease release for `stable`, picks the `win-<arch>.` asset when there are several ("Since v 1.2.99 installers for multiple OS architectures are provided"), then runs `shellExec(installerPath, ['/install', '/quiet', '/norestart'])`. There is no elevation check or prompt. — DRV `scripts/install-wad.mjs`
- `git ls-remote --tags https://github.com/microsoft/WinAppDriver`: the highest tags are `refs/tags/v1.2.1` and `refs/tags/v1.2.99`, which point to the same commit `a6f3d7bc…`. There are no later tags as of 2026-11-12. — git ls-remote output (run in this session)
- The older driver `appium-windows-driver@2.12.0` hard-coded `const WAD_VER = '1.2.99'` and downloaded `WindowsApplicationDriver-${WAD_VER}-win-${wadArch}.exe`. — `npm pack appium-windows-driver@2.12.0`, `build/lib/installer.js` line 16
- WAD issues mention 1.2.99 in use from 2021-07 (#1556 "WinAppDriver v1.2.99 Internal Error") through 2023 (#1936). — GitHub search/issues API

### Inferences
- setup.md "Run it **elevated**, because it runs an MSI installer" is a sensible recommendation. A `/quiet` per-machine install into Program Files cannot show a UAC prompt, so from a non-elevated shell it will most likely fail. Strictly, though, the driver neither checks nor documents this, and the 1.2.99 assets are `.exe` bootstrappers rather than MSIs. Suggested wording: "Run it from an elevated (Administrator) terminal: it runs the WinAppDriver installer silently (`/install /quiet /norestart`), which can't show a UAC prompt."
- setup.md "Default install path: `%PROGRAMFILES%\Windows Application Driver\WinAppDriver.exe` (or `Program Files (x86)`)" should be reversed: the documented default is `C:\Program Files (x86)\Windows Application Driver\WinAppDriver.exe`, and the driver checks the x86 location first. The two Test-Path lines in setup.md are fine.
- "latest stable" for install-wad is 1.2.1 or 1.2.99, depending on whether GitHub marks v1.2.99 as a pre-release (see Gaps). Either way, `install-wad 1.2.1` and `install-wad 1.2.99` are both valid version arguments (`semver.coerce` matching).
- The README states "Appium Windows Driver only supports Windows 10 as the host" and the WAD FAQ says "Windows 10 ... and Windows Server 2016". Windows 11 is not officially listed by either, though it works in practice (community reports). The skill's "Windows 10/11" is acceptable but unofficial.

### Gaps
- Could not read the GitHub releases API or page for microsoft/WinAppDriver (proxy 403), so I cannot confirm whether v1.2.99 is flagged pre-release, which decides what `install-wad` with no version installs. (From memory, not verified: v1.2.1 is "Latest" and v1.2.99 is marked pre-release.)
- Exact installer behaviour when not elevated was not observed.

## Q8. Error message wordings in troubleshooting.md

### Takeaway
"WinAppDriver.exe has not been found in any of these locations" is CONFIRMED (driver source). "WinAppDriver tests only run on Windows" is CONFIRMED (driver source). "Failed to locate opened application window with appId: … and processId: …" is CONFIRMED as quoted in the driver README; it comes from WAD itself (closed source), and the README's exact text has a comma: "appId: X, and processId: N". The Developer Mode text is WAD console output: "Developer mode is not enabled. Enable it through Settings and restart Windows Application Driver".

### Cited Findings
- `throw new WADNotFoundError(`${WAD_EXE_NAME} has not been found in any of these locations: ${pathCandidates}. Use the following driver script to install it: 'appium driver run windows install-wad <optional_wad_version>'. ...`)` — DRV `build/lib/installer.js`
- `if (!support_1.system.isWindows()) { throw new Error('WinAppDriver tests only run on Windows'); }` — DRV `build/lib/driver.js` line 149
- README createSessionTimeout row: "workaround for the long startup times of UWP applications (aka `Failed to locate opened application window with appId: TestCompany.my_app4!App, and processId: 8480`)". This string is not in the driver JS, so it is a WAD-side message. — DRV `README.md` line 43; grep of DRV `build/`
- WAD console message quoted by users: "Developer mode is not enabled. Enable it through Settings and restart Windows Application Driver" (#165). The same message is followed by "Failed to initialize: 0x80004005" (#524). — [WinAppDriver #165](https://github.com/microsoft/WinAppDriver/issues/165), [#524](https://github.com/microsoft/WinAppDriver/issues/524)
- Other driver errors worth listing: "WinAppDriver server '${executablePath}' is not listening at ${serverUrl}" (winappdriver.js line 211); "Could not start WinAppDriver session within ${createSessionTimeout} ms." (line 299); "Could not find any free port in range 4724..4824" (line 81); "'prerun' capability value must either contain 'script' or 'command' entry of string type" (driver.js); "Power Shell commands cannot contain line breaks" (commands/powershell.js). — DRV sources as cited
- The Python 6.1.5 `WindowsOptions` serializes `automationName: 'Windows'`. The driver README says "Must be set to `windows` (case-insensitive)". OK.

### Inferences
- troubleshooting.md row "Session fails and WAD says Developer Mode is required": recommend quoting the real text "Developer mode is not enabled. Enable it through Settings and restart Windows Application Driver" (seen in Appium server log lines from WAD stdout). The "WinAppDriver server ... is not listening at http://127.0.0.1:47xx" driver error typically follows it.
- The `EADDRINUSE 4723` row (a manual WAD collides with Appium) is consistent with WAD's 127.0.0.1:4723 default.

### Gaps
- "The system cannot find the file specified" (bad app path or AUMID) is a WAD/Win32 message. It is plausible but I found no primary source quote. UNVERIFIABLE.

## Q9. Elevated apps / UIPI, WinForms and WPF AutomationId

### Takeaway
Elevated-app limitation: CONFIRMED, since a medium-IL process cannot access elevated UI. WinForms AutomationId = Control.Name: CONFIRMED (dotnet/winforms test). WPF: CONFIRMED with a nuance. Precedence is `AutomationProperties.AutomationId` → `x:Uid` → `Name`/`x:Name`, so windows.md's "only if x:Name or AutomationProperties.AutomationId" omits `x:Uid`.

### Cited Findings
- "An application that doesn't have UIAccess in the manifest starts with medium IL and cannot access elevated ("medium+" IL) process UI." "An application has UI Access and is launched by an admin user starts as "high" IL and can access elevated UI because it has the same IL." — [MicrosoftDocs win32 uiauto-securityoverview.md](https://raw.githubusercontent.com/MicrosoftDocs/win32/docs/desktop-src/WinAuto/uiauto-securityoverview.md)
- WPF `FrameworkElementAutomationPeer.GetAutomationIdCore()`: "// 1. fetch AutomationProperties.AutomationIdProperty ... // 2. fetch x:Uid ... // 3. fetch FrameworkElement.NameProperty". — [dotnet/wpf FrameworkElementAutomationPeer.cs](https://raw.githubusercontent.com/dotnet/wpf/main/src/Microsoft.DotNet.Wpf/src/PresentationFramework/System/Windows/Automation/Peers/FrameworkElementAutomationPeer.cs)
- WinForms test: `new Button { Name = "Button1", AccessibleName = "TestName" }`, then `UIA_AutomationIdPropertyId` == `"Button1"` and `UIA_NamePropertyId` == `"TestName"`. — [dotnet/winforms Button.ButtonAccessibleObjectTests.cs](https://raw.githubusercontent.com/dotnet/winforms/main/src/test/unit/System.Windows.Forms/System/Windows/Forms/AccessibleObjects/Button.ButtonAccessibleObjectTests.cs)
- UIA docs: AutomationId "must be the same in any instance of the application, regardless of the local language ... not guaranteed to be stable across different releases or builds". — [uiauto-automation-element-propids.md](https://raw.githubusercontent.com/MicrosoftDocs/win32/docs/desktop-src/WinAuto/uiauto-automation-element-propids.md)
- WAD locator mapping: accessibility id → AutomationId; class name → ClassName; id → "RuntimeId (decimal)" e.g. `42.333896.3.1`; name → Name; tag name → "LocalizedControlType (upper camel case)"; xpath → Any. — [AuthoringTestScripts.md](https://raw.githubusercontent.com/microsoft/WinAppDriver/master/Docs/AuthoringTestScripts.md)

### Inferences
- windows.md §2's locator table matches the WAD docs exactly.
- "Run Appium elevated too" is correct in effect. Appium spawns WAD, which then runs at the same high IL. Strictly, it is WAD (the UIA client) that must be elevated, and it inherits elevation from Appium/node.
- The "AutomationId comes from `x:Name`" claim for UWP/WinUI also holds in practice: Calculator uses explicit `AutomationProperties.AutomationId` alongside `x:Name`. The UWP XAML fallback to x:Name was not verified from source.
- The WinForms claim is verified for modern .NET WinForms. For .NET Framework WinForms the behaviour (Name → AutomationId via the Win32 proxy) is widely relied on but was not verified from a primary source here.

### Gaps
- No primary source for .NET Framework WinForms AutomationId = Name.

## Q10. WindowsOptions property names (Appium-Python-Client 6.1.5)

### Takeaway
CONFIRMED: all ten listed properties exist and map to the right capabilities. `wad_url` and `force_quit` do NOT exist, so windows.md correctly uses `set_capability` for those. Types: `create_session_timeout` int = milliseconds, `wait_for_app_launch` int = seconds, `new_command_timeout` int = seconds. The getters return `timedelta`.

### Cited Findings
- Run with `venv/bin/python -I`: `hasattr(WindowsOptions, p)` is True for `app, app_arguments, app_top_level_window, app_working_dir, create_session_timeout, wait_for_app_launch, experimental_webdriver, prerun, postrun, system_port, new_command_timeout`, and False for `wad_url, force_quit`. — local venv run
- `to_capabilities()` output: `{'automationName': 'Windows', 'platformName': 'Windows', 'appium:app': 'x', 'appium:appArguments': 'a', 'appium:appTopLevelWindow': '0x1', 'appium:appWorkingDir': 'd', 'appium:createSessionTimeout': 1, 'ms:waitForAppLaunch': 2, 'ms:experimental-webdriver': True, 'appium:prerun': {'command': 'x'}, 'appium:postrun': {'script': 'y'}, 'appium:systemPort': 4730, 'appium:newCommandTimeout': 60}`. With `timedelta(seconds=5)`: `createSessionTimeout: 5000`, `ms:waitForAppLaunch: 5.0`, `newCommandTimeout: 5.0`. After setting ints, the getters return `timedelta(microseconds=1000)` for create_session_timeout=1 (ms), `timedelta(seconds=2)` and `timedelta(seconds=60)`. — local venv run
- Driver capability constraints: `app, appArguments, appTopLevelWindow, appWorkingDir` (string), `createSessionTimeout` (number), `ms:waitForAppLaunch` (number, "in seconds"), `ms:forcequit` (boolean), `ms:experimental-webdriver` (boolean), `systemPort` (number), `prerun`/`postrun` (object), `wadUrl` (string). — DRV `build/lib/desired-caps.js`
- README: `ms:waitForAppLaunch` "The limit for this is 50 seconds". `createSessionTimeout` "Default value is `20000`". `newCommandTimeout` "`60` seconds by default". `ms:experimental-webdriver` "`false` by default". `ms:forcequit` "start[s WAD] with the `/forcequit` command line argument which will forcefully kill the application process during session termination". — DRV `README.md`

### Inferences
- windows.md §1 table and builder are correct. The builder relies on int semantics (ms for create_session_timeout, s for wait_for_app_launch), which matches. Note for agents: reading `o.create_session_timeout` back gives a `timedelta`, not an int.

### Gaps
- None.

## Q11. Other checks on windows.md / setup.md content

### Takeaway
Everything else checked out: the `windows:` extension table, prerun/postrun semantics, `powerShell` execute, scroll direction, defaults, and driver 4.x peer `appium ^2.4.0`. The only additional caveat: `command` PowerShell strings must be single-line.

### Cited Findings
- executeMethodMap params: click `elementId,x,y,button,modifierKeys,durationMs,times,interClickDelayMs`; scroll `elementId,x,y,deltaX,deltaY,modifierKeys`; clickAndDrag/hover `startElementId,startX,startY,endElementId,endX,endY,modifierKeys,durationMs`; keys `actions` (required); setClipboard `b64Content` (required) + `contentType`; getClipboard `contentType`; deleteFile/deleteFolder `remotePath` (required); launchApp/closeApp no params; start/stopRecordingScreen params as listed. — DRV `build/lib/execute-method-map.js`
- Defaults: `windowsClickAndDrag(..., durationMs = 5000)`, `windowsHover(..., durationMs = 500)`, `windowsClick(... button = LEFT, ..., times = 1, interClickDelayMs = 100)`. Buttons are `'left' | 'middle' | 'right' | 'back' | 'forward'`. Modifier keys are matched lowercased against `{shift, ctrl, alt, win}`. Keys actions accept exactly one of `pause`, `text` or `virtualKeyCode` (+`down`). — DRV `build/lib/commands/gestures.js`, `commands/winapi/user32.js`
- Scroll: "deltaY ... A positive value indicates that the wheel was rotated forward, away from the user; a negative value indicates that the wheel was rotated backward, toward the user. Either this value or deltaX must be provided, but not both." So the skill's "-5 = scroll down" is correct. — DRV `README.md` line 318
- `const POWER_SHELL_SCRIPT = 'powerShell'`, gated by `assertFeatureEnabled(POWER_SHELL_FEATURE)`. execPowerShell "@returns ... The actual stdout", "@throws {Error} If the exit code ... is not zero. The actual stderr output is set to the error message value". It also throws "Power Shell commands cannot contain line breaks" for `command`. — DRV `build/lib/commands/execute.js`, `commands/powershell.js`
- Prerun runs inside createSession's try block before `startWinAppDriverSession()`; on error, `deleteSession()` runs and the error is rethrown. Postrun errors are caught with `this.log.error(e.message)`. — DRV `build/lib/driver.js` lines 147–206
- `"peerDependencies": { "appium": "^2.4.0" }` (4.4.7). `appium-windows-driver@5.4.x` peer is `^3.0.0-rc.2`. The npm `latest` tag is `6.3.1`. — DRV `package.json`; `npm view`
- Driver README warns: "WinAppDriver server has not been maintained by Microsoft for years. Consider trying NovaWindows Driver ... as a modern drop-in replacement". — DRV `README.md` lines 17–21

### Inferences
- setup.md "maintenance/deprecated status upstream" is a fair paraphrase of the README warning about WAD.
- No other factual errors found in windows.md.

### Gaps
- Live behaviour on Windows 11 24H2/25H2 was not tested.

## Summary verdict table

| Claim | Verdict | Correct value / note |
|---|---|---|
| Calculator ids num0..9Button, plus/minus/multiply/equalButton, clearButton, CalculatorResults | CONFIRMED | microsoft/calculator XAML + MS UI tests |
| CalculatorResults Name "Display is 3" | CONFIRMED | resw `Display is %1`; also "Display is 7 point" after a decimal |
| clearButton in Standard mode | CONFIRMED | C and CE both exist and are visible in Standard; in Scientific, C is visible only when input is empty |
| Standard mode required | MISSING IN TEMPLATE | MS sample forces Standard; add ensure-standard step (`TogglePaneButton` → accessibility id `Standard`) |
| window_handles = app's top-level windows; switch works; other process not listed | CONFIRMED | foreign handle error "Window handle does not belong to the same process/application"; Root session has 0 handles |
| appTopLevelWindow / Root workaround | CONFIRMED | WAD FAQ |
| `Value.Value` for text boxes | PARTLY MISLEADING | valid naming, but known null cases; `el.text` returns TextBox text per WAD test |
| `el.text` returns Name | MISLEADING | Name for buttons; text value for TextBox/TextBlock; selected value for lists |
| Dev Mode reg key AllowDevelopmentWithoutDevLicense=1 | CONFIRMED | |
| Dev Mode Settings path | OUTDATED (Win11 25H2+) | System → Advanced → For developers; `ms-settings:developers` |
| Get-StartApps Name + AppID (AUMID) | CONFIRMED | |
| Inspect.exe path | CONFIRMED | `\bin\<version>\<platform>` |
| accessibilityinsights.io | CONFIRMED | |
| WAD default 127.0.0.1:4723 | CONFIRMED | |
| Driver spawns WAD on 4724–4824 | CONFIRMED | first free port, or systemPort |
| install-wad needs admin | UNVERIFIABLE (likely) | driver does not check; silent per-machine install |
| WAD default path | ORDER WRONG in setup.md | default is `C:\Program Files (x86)\Windows Application Driver`; driver checks x86 first |
| Latest WAD release | v1.2.1 / v1.2.99 (same commit) | pre-release status of 1.2.99 unverified |
| "WinAppDriver.exe has not been found in any of these locations" | CONFIRMED | |
| "Failed to locate opened application window with appId: …, and processId: …" | CONFIRMED (WAD msg, per README) | note the comma before "and" |
| Developer Mode error text | VAGUE | actual: "Developer mode is not enabled. Enable it through Settings and restart Windows Application Driver" |
| Elevated app / UIPI | CONFIRMED | |
| WinForms AutomationId = Name | CONFIRMED (.NET) | |
| WPF x:Name → AutomationId | CONFIRMED w/ nuance | precedence AutomationProperties.AutomationId → x:Uid → Name |
| WindowsOptions property names | CONFIRMED | no `wad_url`/`force_quit` properties; use set_capability |

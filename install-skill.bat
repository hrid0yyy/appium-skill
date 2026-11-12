@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem ===========================================================================
rem  install-skill.bat - install the "appium-android-windows" agent skill GLOBALLY
rem
rem  Copies .claude\skills\appium-android-windows from this repo into the
rem  user-level skills folder so it is available in every project:
rem
rem      %USERPROFILE%\.agents\skills\appium-android-windows\
rem
rem  Usage (run from anywhere; no admin rights needed):
rem      install-skill.bat              install / update in %USERPROFILE%\.agents\skills
rem      install-skill.bat --claude     also install in %USERPROFILE%\.claude\skills
rem                                     (the global folder Claude Code reads)
rem      install-skill.bat --uninstall  remove it from both locations
rem ===========================================================================

set "SKILL_NAME=appium-android-windows"
set "SRC=%~dp0.claude\skills\%SKILL_NAME%"
set "AGENTS_DEST=%USERPROFILE%\.agents\skills\%SKILL_NAME%"
set "CLAUDE_DEST=%USERPROFILE%\.claude\skills\%SKILL_NAME%"

set "DO_CLAUDE=0"
set "DO_UNINSTALL=0"
for %%A in (%*) do (
    if /I "%%~A"=="--claude"    set "DO_CLAUDE=1"
    if /I "%%~A"=="--uninstall" set "DO_UNINSTALL=1"
    if /I "%%~A"=="--help"      goto :usage
)

if "%DO_UNINSTALL%"=="1" goto :uninstall

if not exist "%SRC%\SKILL.md" (
    echo [ERROR] Skill source not found: "%SRC%\SKILL.md"
    echo         Run this script from the root of the appium-skill repository.
    exit /b 1
)

echo Installing skill "%SKILL_NAME%"
echo   from: "%SRC%"
call :install_to "%AGENTS_DEST%" || exit /b 1
if "%DO_CLAUDE%"=="1" (
    call :install_to "%CLAUDE_DEST%" || exit /b 1
)

echo.
echo Done. Start a NEW agent session so the skill is picked up.
echo It triggers on requests mentioning Appium, Android/APK/emulator/adb, UiAutomator2,
echo Windows desktop apps, WinAppDriver, WPF, WinForms or UWP.
if "%DO_CLAUDE%"=="0" (
    echo Tip: Claude Code reads global skills from %%USERPROFILE%%\.claude\skills -
    echo      re-run with --claude to install there as well.
)
exit /b 0

rem ---------------------------------------------------------------------------
:install_to
set "DEST=%~1"
if exist "%DEST%" (
    echo   updating: "%DEST%"
) else (
    echo   to:       "%DEST%"
)
rem /MIR mirrors the folder (removes files deleted from the repo on update).
rem Local junk from trying the template is excluded.
robocopy "%SRC%" "%DEST%" /MIR /NFL /NDL /NJH /NJS /NP /R:1 /W:1 ^
    /XD __pycache__ .pytest_cache .venv venv artifacts ^
    /XF .env *.pyc >nul
set "RC=%ERRORLEVEL%"
rem robocopy: exit codes 0-7 mean success, 8+ mean failure.
if %RC% GEQ 8 (
    echo [ERROR] Copy to "%DEST%" failed ^(robocopy exit code %RC%^).
    exit /b 1
)
if not exist "%DEST%\SKILL.md" (
    echo [ERROR] "%DEST%\SKILL.md" missing after copy.
    exit /b 1
)
echo   OK:       "%DEST%\SKILL.md"
exit /b 0

rem ---------------------------------------------------------------------------
:uninstall
for %%D in ("%AGENTS_DEST%" "%CLAUDE_DEST%") do (
    if exist "%%~D" (
        rmdir /S /Q "%%~D" && echo Removed "%%~D"
    ) else (
        echo Not installed: "%%~D"
    )
)
exit /b 0

rem ---------------------------------------------------------------------------
:usage
echo Usage: %~nx0 [--claude] [--uninstall]
echo   (no args)    install/update into %%USERPROFILE%%\.agents\skills\%SKILL_NAME%
echo   --claude     also install into %%USERPROFILE%%\.claude\skills\%SKILL_NAME%
echo   --uninstall  remove from both locations
exit /b 0

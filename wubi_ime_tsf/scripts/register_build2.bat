@echo off
chcp 65001 >nul
setlocal

:: Administrator rights required
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Please run this script as Administrator.
    pause
    exit /b 1
)

set "DLL=%~dp0..\build2\bin\WubiIME_TSF.dll"
if not exist "%DLL%" (
    echo DLL not found: %DLL%
    echo Please build with build_tsf_in_venv2.py first.
    pause
    exit /b 1
)

del /f /q "%TEMP%\WubiIME_Register.log" 2>nul
echo Registering TSF IME from build2...
regsvr32 /s "%DLL%"
if %errorlevel% neq 0 (
    echo Registration failed.
    echo See %TEMP%\WubiIME_Register.log for details.
    pause
    exit /b 1
)

echo Registration succeeded.
echo Please sign out and sign back in (or restart) to refresh the language bar,
echo then add keyboard "Wubi IME (TSF)" in Settings.
pause

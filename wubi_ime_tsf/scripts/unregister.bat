@echo off
chcp 936 >nul
setlocal

:: Run as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ??????????????§Õ?????
    pause
    exit /b 1
)

set "DLL=%~dp0..\build\bin\WubiIME_TSF.dll"
if not exist "%DLL%" (
    echo ????? DLL: %DLL%
    pause
    exit /b 1
)

del /f /q "%TEMP%\WubiIME_Register.log" 2>nul
echo ????§Ø?? TSF ????...
regsvr32 /u /s "%DLL%"
if %errorlevel% neq 0 (
    echo §Ø??????
    pause
    exit /b 1
)

echo §Ø??????
pause

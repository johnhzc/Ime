@echo off
chcp 936 >nul
setlocal

:: Run as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 请以管理员身份运行此脚本。
    pause
    exit /b 1
)

set "DLL=%~dp0..\build\bin\WubiIME_TSF.dll"
if not exist "%DLL%" (
    echo 找不到 DLL: %DLL%
    pause
    exit /b 1
)

del /f /q "%TEMP%\WubiIME_Register.log" 2>nul
echo 正在卸载 TSF 输入法...
regsvr32 /u /s "%DLL%"
if %errorlevel% neq 0 (
    echo 卸载失败。
    echo 详细错误信息请查看 %TEMP%\WubiIME_Register.log
    pause
    exit /b 1
)

echo 卸载成功。
pause

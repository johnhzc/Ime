@echo off
chcp 65001 >nul
setlocal

:: 需要管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 请以管理员身份运行此脚本。
    pause
    exit /b 1
)

set "DLL=%~dp0..\build\bin\WubiIME_TSF.dll"
if not exist "%DLL%" (
    echo 找不到 DLL: %DLL%
    echo 请先使用 CMake/Visual Studio 构建项目。
    pause
    exit /b 1
)

del /f /q "%TEMP%\WubiIME_Register.log" 2>nul
echo 正在注册 TSF 输入法...
regsvr32 /s "%DLL%"
if %errorlevel% neq 0 (
    echo 注册失败。
    echo 详细错误信息请查看 %TEMP%\WubiIME_Register.log
    pause
    exit /b 1
)

echo 注册成功。请注销并重新登录（或重启）以刷新语言栏，然后添加键盘"五笔输入法 (TSF)"。
pause

@echo off
chcp 936 >nul
setlocal

set "ROOT=%~dp0"
set "BUILD=%ROOT%build"
set "CMAKE=%ROOT%cmake\bin\cmake.exe"

if not exist "%CMAKE%" (
    echo 找不到 CMake: %CMAKE%
    echo 请确认已解压 cmake-portable.zip 到 %ROOT%cmake 目录。
    pause
    exit /b 1
)

if not exist "%BUILD%" mkdir "%BUILD%"

echo [1/4] 正在设置 Visual Studio 环境...
call "D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

echo [2/4] VS 环境已设置。cl.exe 路径：
where cl.exe

echo [3/4] 正在运行 CMake...
cd /d "%BUILD%"
"%CMAKE%" .. -G "Ninja" -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=cl.exe -DCMAKE_CXX_COMPILER=cl.exe
if %errorlevel% neq 0 (
    echo CMake 配置失败。
    pause
    exit /b 1
)

echo [4/4] 正在构建...
"%CMAKE%" --build . --config Release
if %errorlevel% neq 0 (
    echo 构建失败。
    pause
    exit /b 1
)

echo 构建完成。
pause

@echo off
chcp 65001 >nul
echo [1/4] Setting up VS environment...
call "D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo [2/4] VS environment set. cl.exe path:
where cl.exe
echo [3/4] Running CMake...
cd /d "D:\BeansWorkingSpace\lyt\2026中山大学学生第二课堂\coding\wubi_ime_tsf\build"
"..\cmake\bin\cmake.exe" .. -G "Ninja" -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=cl.exe -DCMAKE_CXX_COMPILER=cl.exe
echo [4/4] CMake done.

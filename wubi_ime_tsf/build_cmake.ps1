[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$vs_bat = "D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

Write-Host "[1/5] Setting up VS environment..."
$env_list = cmd /c "`"$vs_bat`" && set"
foreach ($line in $env_list) {
    if ($line -match '^(.*?)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

Write-Host "[2/5] cl.exe path:"
Get-Command cl.exe | Select-Object -ExpandProperty Source

Write-Host "[3/5] Running CMake configure..."
$build_dir = Join-Path $PSScriptRoot "build"
if (!(Test-Path $build_dir)) {
    New-Item -ItemType Directory -Path $build_dir | Out-Null
}
Set-Location $build_dir
$cmake_exe = Join-Path (Join-Path (Join-Path $PSScriptRoot "cmake") "bin") "cmake.exe"
& "$cmake_exe" .. -G "Ninja" -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=cl.exe -DCMAKE_CXX_COMPILER=cl.exe
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/5] Running CMake build..."
& "$cmake_exe" --build . --config Release
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[5/5] Done."

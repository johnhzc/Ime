[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$vs_bat = "D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$env_list = cmd /c "`"$vs_bat`" && set"
foreach ($line in $env_list) {
    if ($line -match '^(.*?)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
Write-Host "INCLUDE=$env:INCLUDE"
Write-Host "LIB=$env:LIB"
Write-Host "WindowsSdkDir=$env:WindowsSdkDir"

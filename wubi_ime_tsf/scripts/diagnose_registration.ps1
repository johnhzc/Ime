[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

$clsid = "{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}"
$profile = "{C3D4E5F6-A7B8-9012-3456-789012CDEF01}"
$langIdHex = "0x{0:X4}" -f 0x0804

Write-Host "===== WubiIME TSF 注册诊断 ====="
Write-Host ""

function Test-RegKey($path, $name) {
    try {
        $key = Get-ItemProperty -Path $path -Name $name -ErrorAction Stop
        return $key.$name
    } catch {
        return $null
    }
}

# COM CLSID
$clsidPath = "Registry::HKEY_CLASSES_ROOT\CLSID\$clsid"
if (Test-Path $clsidPath) {
    Write-Host "[OK] COM CLSID 已注册: $clsid"
    $default = Test-RegKey $clsidPath ""
    Write-Host "     默认名称: $default"
    $inproc = Test-RegKey "$clsidPath\InprocServer32" ""
    Write-Host "     InprocServer32: $inproc"
    $model = Test-RegKey "$clsidPath\InprocServer32" "ThreadingModel"
    Write-Host "     ThreadingModel: $model"
} else {
    Write-Host "[FAIL] COM CLSID 未注册: $clsid"
}
Write-Host ""

# TSF profile (per-user)
$tipPath = "Registry::HKEY_CURRENT_USER\Software\Microsoft\CTF\TIP\$clsid"
if (Test-Path $tipPath) {
    Write-Host "[OK] TSF TIP 注册表项已存在: $clsid"
    Get-ChildItem $tipPath -Recurse -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Name | ForEach-Object { Write-Host "     $_" }
} else {
    Write-Host "[FAIL] TSF TIP 注册表项不存在（注册可能未成功）"
}
Write-Host ""

# Profile enable state
$profilePath = "Registry::HKEY_CURRENT_USER\Software\Microsoft\CTF\TIP\$clsid\LanguageProfile\$langIdHex\$profile"
if (Test-Path $profilePath) {
    Write-Host "[OK] 语言资料注册表项已存在"
    Get-ItemProperty $profilePath | Out-String | Write-Host
} else {
    Write-Host "[FAIL] 语言资料注册表项不存在"
}
Write-Host ""

# Registration log
$log = "$env:TEMP\WubiIME_Register.log"
if (Test-Path $log) {
    Write-Host "[INFO] 注册日志内容 ($log):"
    Get-Content $log -Tail 30 | ForEach-Object { Write-Host "     $_" }
} else {
    Write-Host "[INFO] 未找到注册日志: $log"
}

Write-Host ""
Write-Host "===== 诊断结束 ====="
pause

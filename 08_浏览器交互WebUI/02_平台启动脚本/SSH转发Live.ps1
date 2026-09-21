param([string]$GpuIp = "11.11.10.16", [int]$LocalPort = 8765)
$ErrorActionPreference = "Continue"
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " LagerNVS Live SSH 转发" -ForegroundColor Cyan
Write-Host " 请在此窗口输入平台二次验证码/OTP" -ForegroundColor Yellow
Write-Host " 成功后保持窗口开着" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "本地 http://127.0.0.1:$LocalPort  ->  ${GpuIp}:8765"
# kill anything else on port
Get-NetTCPConnection -LocalPort $LocalPort -State Listen -EA SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue }
ssh -L "${LocalPort}:${GpuIp}:8765" -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -N ustc-lager
Write-Host "SSH 已退出: $LASTEXITCODE" -ForegroundColor Red
pause

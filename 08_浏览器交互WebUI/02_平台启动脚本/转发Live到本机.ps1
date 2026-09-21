# 本机：把平台 A100 WebUI 转到 localhost:8765
# 用法：.\转发Live到本机.ps1 -GpuIp 11.11.10.xx

param(
  [Parameter(Mandatory = $true)][string]$GpuIp,
  [int]$LocalPort = 8765
)

Write-Host "转发 http://127.0.0.1:$LocalPort  ->  ${GpuIp}:8765"
Write-Host "保持此窗口开着；浏览器打开 http://127.0.0.1:$LocalPort/"
Write-Host "门户: http://127.0.0.1:8766/?v=me  → 自由视角 / Live"
ssh -L "${LocalPort}:${GpuIp}:8765" -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes ustc-lager -N

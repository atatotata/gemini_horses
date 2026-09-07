$host.UI.RawUI.WindowTitle = 'AI Reference Match - Live Activity Log'
Clear-Host
Write-Host '===================================================' -ForegroundColor Cyan
Write-Host '    AI Reference Match - Live Activity Log         ' -ForegroundColor White
Write-Host '===================================================' -ForegroundColor Cyan
Write-Host 'Streaming pipeline steps in real time. Close this window to stop.' -ForegroundColor Gray
Get-Content -Wait -Tail 50 -LiteralPath 'C:\TMP\AIRefMatch_live.log'
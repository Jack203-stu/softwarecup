Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName
if (-not (Get-Process python -ErrorAction SilentlyContinue)) {
    Write-Host "No python running. Starting..."
    cd d:\softwarecup\softwarecup\backend
    python main.py
}

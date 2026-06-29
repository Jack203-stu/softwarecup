Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
netstat -ano | findstr :8000
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing on 8000. Starting main.py"
    cd d:\softwarecup\softwarecup\backend
    python main.py
} else {
    Write-Host "Port 8000 already in use"
}

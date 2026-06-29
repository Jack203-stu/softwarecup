Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
cd d:\softwarecup\softwarecup\backend
python _minimal_server.py

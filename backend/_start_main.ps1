Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
cd d:\softwarecup\softwarecup\backend
python main.py 2>&1

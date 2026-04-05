.\venv\Scripts\python.exe -m py_compile handlers/start.py
.\venv\Scripts\python.exe -m py_compile config.py
.\venv\Scripts\python.exe -m py_compile utils/admin_notify.py
Write-Host "All files clean!"

git add .
git commit -m "Add admin Telegram notifications for new users"
git push origin main

@echo off
cd /d "C:\Users\admin\Downloads\The Scraper\cost-monitor"
call venv\Scripts\activate.bat
python manage.py detect_anomalies > detection_log.txt 2>&1
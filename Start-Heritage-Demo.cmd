@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 scripts\demo\start_heritage_local.py
goto done
:use_python
python scripts\demo\start_heritage_local.py
:done
if errorlevel 1 pause

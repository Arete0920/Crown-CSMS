@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 Install-and-Start-Heritage.py
goto done
:use_python
python Install-and-Start-Heritage.py
:done
if errorlevel 1 pause

@echo off
setlocal EnableExtensions

set "REPO=C:\Users\JMega\OneDrive\Desktop\Crown2026_pr884_clean"
set "PY=%REPO%\.venv\Scripts\python.exe"
set "BASE=%~1"

if "%BASE%"=="" (
  echo ERROR: missing evidence root argument
  exit /b 2
)

if not exist "%PY%" (
  echo ERROR: missing python executable: %PY%
  exit /b 2
)

if not exist "%BASE%" (
  mkdir "%BASE%" >nul 2>&1
)

set "OUT08=%BASE%\08_admissions_endpoints.txt"
echo === ADMISSIONS ENDPOINTS (CANONICAL CMD RUNNER) ===> "%OUT08%"
"%PY%" -m pytest "%REPO%\backend\applications\tests\test_admissions_endpoints.py" -q -s >> "%OUT08%" 2>&1
set "EC=%ERRORLEVEL%"
echo admissions_endpoints_exit=%EC%>> "%OUT08%"
if not "%EC%"=="0" exit /b %EC%

set "OUT09=%BASE%\09_aftercare.txt"
echo === AFTERCARE (CANONICAL CMD RUNNER) ===> "%OUT09%"
"%PY%" -m pytest "%REPO%\backend\aftercare" -q -s >> "%OUT09%" 2>&1
set "EC=%ERRORLEVEL%"
echo aftercare_exit=%EC%>> "%OUT09%"
if not "%EC%"=="0" exit /b %EC%

set "OUT10=%BASE%\10_later_tier_metrics.txt"
echo === LATER TIER METRICS (CANONICAL CMD RUNNER) ===> "%OUT10%"
"%PY%" -m pytest "%REPO%\backend\tests\test_later_tier_metrics_api.py" -q -s >> "%OUT10%" 2>&1
set "EC=%ERRORLEVEL%"
echo later_tier_metrics_exit=%EC%>> "%OUT10%"
exit /b %EC%

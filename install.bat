@echo off
REM Install opencode-py on Windows Server 2016 + Python 3.8. No admin required.
REM Run from the folder containing this file. Uses py -3.8 if available.
setlocal
chcp 65001 >nul

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py -3.8"
) else (
  set "PY=python"
)

%PY% --version
%PY% -m pip install --upgrade pip

REM Offline-first: use vendor\ wheels + dist\ wheel if present (for servers without internet).
if exist vendor\pytermgui-*.whl (
  echo Installing dependencies from vendor\ (offline)...
  %PY% -m pip install --no-index --find-links vendor -r requirements-py38.txt
) else (
  echo Installing dependencies from PyPI (online)...
  %PY% -m pip install -r requirements-py38.txt
)

if exist dist\opencode_py-*.whl (
  %PY% -m pip install --no-index --find-links dist opencode-py
) else (
  %PY% -m pip install .
)

%PY% -m opencode_py --show-config
echo.
echo Next: opencode-py --init
echo   (writes %%USERPROFILE%%\.opencode-py\config.json with base_url + api_key + model)
endlocal

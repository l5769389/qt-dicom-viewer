@echo off
setlocal

where uv >nul 2>&1
if errorlevel 1 (
    echo uv was not found. Install uv, reopen the terminal, and try again.
    exit /b 1
)

pushd "%~dp0.." || exit /b 1
set "UV_PROJECT_ENVIRONMENT=%CD%\.venv-build-windows"
set "PYTHONUTF8=1"
uv run --locked --python 3.13 --no-dev --group build --no-editable python scripts/build_windows.py %*
set "BUILD_EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %BUILD_EXIT_CODE%

@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_build.ps1" %*
exit /b %ERRORLEVEL%

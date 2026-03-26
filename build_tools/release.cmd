@echo off
call "%~dp0run_build.cmd" release
exit /b %ERRORLEVEL%

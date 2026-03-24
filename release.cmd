@echo off
call build_tools\run_build.cmd release
exit /b %ERRORLEVEL%

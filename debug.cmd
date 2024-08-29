@echo off
popd
start /wait build_tools\debug.cmd
if errorlevel 1 (
    echo Debug script encountered an error.
    pause
)
exit
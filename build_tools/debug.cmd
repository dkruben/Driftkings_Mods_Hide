@echo off
:::git checkout develop
C:\Python27\python.exe build_tools/compiler.py -p C:/PJOrion/PjOrion.exe -d scripts/client/ -o build/scripts/client/ source/scripts/client/
C:\Python27\python.exe build_tools/packer.py -q -v build_data/GAME_VERSION build_data/wotmods/ build/wotmods/
"C:\Program Files\Beyond Compare 4\BCompare.exe"
if ERRORLEVEL 1 (
    echo Beyond Compare not found on PATH, skipping...
    goto not_found
)
where /Q "build_data:debug_targets.txt"
if ERRORLEVEL 1 (
    echo Debug targets not found, skipping...
    goto not_found
)
echo Launching Beyond Compare...
set /p ver=<build_data\GAME_VERSION
for /F "tokens=*" %%A in (build_data\debug_targets.txt) do ("C:\Program Files\Beyond Compare 4\BCompare.exe" build\wotmods\ "%%A\mods\%ver%\" /solo)
:not_found
echo Exiting.
pause
exit

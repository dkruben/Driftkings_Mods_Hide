@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "MODE=%~1"
if not defined MODE set "MODE=debug"

set "ROOT_DIR=%~dp0.."
pushd "%ROOT_DIR%"

if /I not "%MODE%"=="debug" if /I not "%MODE%"=="release" (
    echo Invalid mode "%MODE%". Use "debug" or "release".
    popd
    exit /b 2
)

if not defined DK_PJORION set "DK_PJORION=F:/Programas/PJOrion/PjOrion.exe"
if not defined DK_BCOMPARE_DEBUG set "DK_BCOMPARE_DEBUG=C:\Program Files\Beyond Compare 5\BCompare.exe"
if not defined DK_BCOMPARE_RELEASE set "DK_BCOMPARE_RELEASE=C:\Program Files\Beyond Compare 4\BCompare.exe"
if not defined DK_7ZIP set "DK_7ZIP=C:\Program Files\7-Zip\7z.exe"

call :resolve_python
if ERRORLEVEL 1 (
    echo Python 2.7 was not found. Set DK_PYTHON27 to a valid python.exe path.
    popd
    exit /b 1
)

echo Running %MODE% build from "%CD%"

if /I "%MODE%"=="debug" goto debug_build
if /I "%MODE%"=="release" goto release_build

:debug_build
call :prepare_wotmods
if ERRORLEVEL 1 goto build_failed

echo [3/4] Optional debug sync...
if exist "%DK_BCOMPARE_DEBUG%" (
    if exist "build_data\debug_targets.txt" (
        set /p GAME_VER=<build_data\GAME_VERSION
        for /F "usebackq delims=" %%A in ("build_data\debug_targets.txt") do (
            "%DK_BCOMPARE_DEBUG%" build\wotmods\ "%%~A\mods\!GAME_VER!\" /solo
        )
    ) else (
        echo debug_targets.txt not found. Skipping debug sync.
    )
) else (
    echo Beyond Compare for debug not found. Skipping debug sync.
)

echo [4/4] Optional Sixth Sense audio package...
if exist "res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk" (
    if exist "%DK_7ZIP%" (
        "%DK_7ZIP%" a -tzip "res\audioww\driftkings_sixthsense.wotmod" "res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk" >nul
    ) else (
        echo 7-Zip not found. Skipping audio package step.
    )
) else (
    echo Generated Sixth Sense bank not found. Skipping audio package step.
)

goto build_ok

:release_build
call :prepare_wotmods
if ERRORLEVEL 1 goto build_failed

echo [3/4] Packing release archives...
call %PYTHON_CMD% build_tools/packer.py -q -v build_data/GAME_VERSION build_data/archives/ build/archives/
if ERRORLEVEL 1 goto build_failed

echo [4/4] Optional release comparison...
if exist "%DK_BCOMPARE_RELEASE%" (
    if exist "build_data\release_targets.txt" (
        for /F "usebackq delims=" %%A in ("build_data\release_targets.txt") do (
            start "" "%DK_BCOMPARE_RELEASE%" build\archives\ "%%~A"
        )
    ) else (
        echo release_targets.txt not found. Skipping release comparison.
    )
) else (
    echo Beyond Compare for release not found. Skipping release comparison.
)

goto build_ok

:build_failed
echo Build failed.
popd
exit /b 1

:build_ok
echo Build finished.
popd
exit /b 0

:prepare_wotmods
echo [1/4] Compiling Python sources...
call %PYTHON_CMD% build_tools/compiler.py -p "%DK_PJORION%" -d scripts/client/ -o build/scripts/client/ source/scripts/client/
if ERRORLEVEL 1 exit /b 1

echo [2/4] Packing wotmods...
call %PYTHON_CMD% build_tools/packer.py -q -v build_data/GAME_VERSION build_data/wotmods/ build/wotmods/
if ERRORLEVEL 1 exit /b 1

exit /b 0

:resolve_python
if defined DK_PYTHON27 (
    set "PYTHON_CMD="%DK_PYTHON27%""
    exit /b 0
)

py -2 -V >nul 2>nul
if not ERRORLEVEL 1 (
    set "PYTHON_CMD=py -2"
    exit /b 0
)

python -c "import sys; sys.exit(0 if sys.version_info[:2] == (2, 7) else 1)" >nul 2>nul
if not ERRORLEVEL 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

exit /b 1

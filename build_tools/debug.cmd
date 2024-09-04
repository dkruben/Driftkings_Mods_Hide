@echo off
set logfile=debug_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
echo [%date% %time%] Debug script started > %logfile%

echo [%date% %time%] Running compiler... >> %logfile%
F:\Python27\python.exe build_tools/compiler.py -p F:/Programas/PJOrion/PjOrion.exe -d scripts/client/ -o build/scripts/client/ source/scripts/client/
echo [%date% %time%] Compiler finished >> %logfile%

echo [%date% %time%] Running packer... >> %logfile%
F:\Python27\python.exe build_tools/packer.py -q -v build_data/GAME_VERSION build_data/wotmods/ build/wotmods/
echo [%date% %time%] Packer finished >> %logfile%

echo [%date% %time%] Checking for Beyond Compare... >> %logfile%
"C:\Program Files\Beyond Compare 4\BCompare.exe"
if ERRORLEVEL 1 (
    echo [%date% %time%] Beyond Compare not found on PATH, skipping... >> %logfile%
    goto not_found
)

echo [%date% %time%] Checking for debug targets... >> %logfile%
where /Q "build_data:debug_targets.txt"
if ERRORLEVEL 1 (
    echo [%date% %time%] Debug targets not found, skipping... >> %logfile%
    goto not_found
)

echo [%date% %time%] Launching Beyond Compare... >> %logfile%
set /p ver=<build_data\GAME_VERSION
for /F "tokens=*" %%A in (build_data\debug_targets.txt) do (
    echo [%date% %time%] Comparing: %%A >> %logfile%
    "C:\Program Files\Beyond Compare 4\BCompare.exe" build\wotmods\ "%%A\mods\%ver%\" /solo
)

if not exist "res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk" (
    echo [%date% %time%] File not found: res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk >> %logfile%
)
else (
    "C:\Program Files\7-Zip\7z.exe" a -tzip "res\audioww\driftkings_sixthsense.wotmod" "res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk"
    if %errorlevel%==0 (
        echo [%date% %time%] Zipping finished successfully >> %logfile%
    ) else (
        echo [%date% %time%] Zipping failed with error level %errorlevel% >> %logfile%
    )
)

:not_found
echo [%date% %time%] Debug script finished >> %logfile%
echo Exiting. Log file: %logfile%
exit

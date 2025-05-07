@echo off
F:\Python27\python.exe build_tools/compiler.py -p F:/Programas/PJOrion/PjOrion.exe -d scripts/client/ -o build/scripts/client/ source/scripts/client/
F:\Python27\python.exe build_tools/packer.py -q -v build_data/GAME_VERSION build_data/wotmods/ build/wotmods/

"C:\Program Files\Beyond Compare 5\BCompare.exe"
if ERRORLEVEL 1 goto not_found

where /Q "build_data:debug_targets.txt"
if ERRORLEVEL 1 goto not_found

set /p ver=<build_data\GAME_VERSION
for /F "tokens=*" %%A in (build_data\debug_targets.txt) do (
    "C:\Program Files\Beyond Compare 5\BCompare.exe" build\wotmods\ "%%A\mods\%ver%\" /solo
)

if exist "res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk" (
    "C:\Program Files\7-Zip\7z.exe" a -tzip "res\audioww\driftkings_sixthsense.wotmod" "res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk"
)

:not_found
exit

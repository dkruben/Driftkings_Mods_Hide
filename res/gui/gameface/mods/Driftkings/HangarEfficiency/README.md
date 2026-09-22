# HangarEfficiency

Gameface panel for the random hangar, using OpenWG 1.1.6 on WoT EU 2.4.0.1.
Edit `efficiency.js` and `efficiency.css` here; no SWF compilation is needed.
Temporarily inactive. The Gameface recovery source is `source/scripts/client/gui/.removed/mod_HangarEfficiency_gameface.py`. Both build manifests are disabled. The old implementation and active placeholder have been removed. This module is excluded from compilation and packaging. Assets and configurations remain available for future recovery.

Statistics use the selected vehicle's random-battle dossier. No-battle averages display `--`; gun marks are limited to tier V and above, and stun is shown for SPGs only. Settings control each statistic. Position X is an offset from horizontal center; Y is an offset from the default position above the carousel. Negative values move left/up. The panel hides outside the random hangar and does not intercept clicks.

Configuration: `res/configs/Driftkings/HangarEfficiency/HangarEfficiency.json`.
Installed path: `mods/configs/Driftkings/HangarEfficiency/HangarEfficiency.json`.

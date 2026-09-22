# MarksOnGunHangar — Gameface

Target: WoT EU 2.4.0.1 with OpenWG Gameface 1.1.6. This implementation uses the legacy resource map, not the WoT 2.4.1 `R.mods` API.

- `marks.js`: panel rendering, model subscription, position/dragging and cleanup.
- `marks.css`: appearance and compact layout.
- `model.html`: empty layout used to attach the injected model to the hangar.
- Resource declaration: `res/mods/configs/res_map/DriftkingsMarksOnGunHangar.json`.
- Python: `source/scripts/client/gui/mods/mod_MarksOnGunHangar.py` includes goal calculations, per-account observed history, dossier data, tooltip and the Gameface bridge.

The card is a child of `RandomHangar` and is hidden when that view is hidden. Other modes with a separate hangar class are not hooked. Marks require tier V or higher; mastery remains available below tier V. Damage targets are proportional estimates, not server thresholds or next-battle predictions.

Position settings retain the previous anchor conventions: X increases to the right and Y increases downward. Dragging the header saves the same X/Y settings; locking disables dragging. Compact mode hides the average and observed history.

Build with `build_tools/run_build.ps1 -Mode release -NoSync`. The resulting `build/archives/MarksOnGunHangar.zip` includes this mod and its shared dependencies. The mod's WOTMOD contains a single Python module plus the Gameface assets; the old SWF and separate progress module are excluded. Historical AS3 sources are retained for reference and skipped by the normal Flash build.

Close the game before replacing the package. OpenWG may request an additional restart when it registers the new layout. Existing settings and per-account history are retained. Validate vehicle switching, settings, drag/lock, leaving the hangar and returning from battle in the game client; browser tests cannot validate WULF integration or `coui://` game icons.

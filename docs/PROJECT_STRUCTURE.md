# Project Structure

This repository is organized around four main areas:

## Root folders

- `source/`
  Contains the Python source code loaded by the game client.
- `res/`
  Contains runtime assets, Flash projects, configs, images, audio, and packed dependencies.
- `build_data/`
  Contains archive manifests, version metadata, and build target lists.
- `build_tools/`
  Contains the Python build utilities and command runners used to compile and package the project.

## Source layout

- `source/scripts/client/DriftkingsCore/`
  Shared core utilities, config loading, hooks, events, and delayed helpers.
- `source/scripts/client/DriftkingsInject/`
  Runtime injection helpers and battle view bridge code.
- `source/scripts/client/DriftkingsStats/`
  Stats-related helpers and cache consumers.
- `source/scripts/client/gui/mods/`
  Individual mod entry points loaded by World of Tanks.

## Resource layout

- `res/configs/Driftkings/`
  End-user configuration files and localization resources.
- `res/flash/`
  ActionScript projects and source files for UI components.
- `res/res/`
  Images, icons, models, and visual assets used by mods.
- `res/sound_bank_wwise/`
  Wwise source projects and generated sound-bank inputs.
- `res/wotmods/`
  External runtime dependencies bundled with the project.

## Build layout

- `build_data/wotmods/`
  Packaging manifests for `.wotmod` outputs.
- `build_data/archives/`
  Packaging manifests for release archives.
- `build_data/debug_targets.txt`
  Local install targets used by debug sync workflows.
- `build_data/release_targets.txt`
  Output comparison targets used by release workflows.
- `build_data/GAME_VERSION`
  Current World of Tanks version used during packaging.

## Recommended conventions

- Add new Python gameplay code under the closest existing package in `source/scripts/client/`.
- Add new mod entry points only in `source/scripts/client/gui/mods/`.
- Add user-facing configs in `res/configs/Driftkings/<ModName>/`.
- Add packaging metadata in `build_data/wotmods/Driftkings/` or `build_data/archives/`.
- Keep root-level files limited to repository metadata and simple entry points.

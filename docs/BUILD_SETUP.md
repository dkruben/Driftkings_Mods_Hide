# Build Setup

The repository now exposes a single build runner through the root scripts:

- `debug.cmd`
- `release.cmd`

Both call `build_tools/run_build.cmd` and accept an optional mode argument internally.

## Required tools

- Python 2.7
- Git
- Optional: PJOrion
- Optional: Beyond Compare
- Optional: 7-Zip

## Supported environment variables

Configure these in your shell or in a local wrapper before running builds:

- `DK_PYTHON27`
  Full path to `python.exe`. If omitted, the runner tries `py -2` first and then `python`.
- `DK_PJORION`
  Full path to `PjOrion.exe`.
- `DK_BCOMPARE_DEBUG`
  Full path to Beyond Compare for debug sync.
- `DK_BCOMPARE_RELEASE`
  Full path to Beyond Compare for release comparison.
- `DK_7ZIP`
  Full path to `7z.exe`.

## Default behavior

### Debug build

1. Compiles `source/scripts/client/` into `build/scripts/client/`.
2. Packs `build_data/wotmods/` into `build/wotmods/`.
3. Optionally compares or syncs output with targets from `build_data/debug_targets.txt`.
4. Optionally rebuilds the Sixth Sense audio `.wotmod` if the generated bank exists.

### Release build

1. Compiles `source/scripts/client/` into `build/scripts/client/`.
2. Packs `build_data/wotmods/` into `build/wotmods/`.
3. Packs `build_data/archives/` into `build/archives/`.
4. Optionally opens Beyond Compare against targets from `build_data/release_targets.txt`.

## Notes

- The new runner avoids hardcoded drive letters in the root entry points.
- Existing Python build tools remain unchanged.
- If optional dependencies are missing, the runner skips those steps with a message instead of failing immediately.

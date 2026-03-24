# Driftkings Installer

This folder contains the Windows installer source for the Driftkings modpack.

## Output

The build script publishes a self-contained executable installer:

- `build/installer/Driftkings_Mods_Installer_EU_NA.exe`

## Features

- Modern desktop installer UI
- EU and NA region presets
- Installs directly into the game root folder
- Lets the user select which mod archives to install
- Embeds the selected release archives into the executable

## Build

Run:

```powershell
powershell -ExecutionPolicy Bypass -File build_tools/build_installer.ps1
```

The script will:

1. Collect enabled archives from `build_data/archives/`
2. Copy the corresponding `.zip` files from `build/archives/`
3. Generate installer images
4. Publish the WPF installer as a single-file executable

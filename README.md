# Driftkings Mods for World of Tanks

![WOT Version](https://img.shields.io/badge/WOT-2.4.0.1-red.svg)
[![Python 2.7.18](https://img.shields.io/badge/Python-2.7.18-blue.svg)](https://www.python.org/downloads/release/python-2718/)
[![PyCharm 2024.3](https://img.shields.io/badge/PyCharm-2024.3-green.svg)](https://www.jetbrains.com/pycharm/)
[![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-](https://code.visualstudio.com/)

A collection of Driftkings mods for World of Tanks, covering battle UI, hangar improvements, aiming tools, stats, sound customization, and quality-of-life features.

## Contents
- [Overview](#overview)
- [Installation](#installation)
- [Active Mods](#active-mods)
- [Tech Stack](#tech-stack)
- [Acknowledgments](#acknowledgments)

## Overview
- **Project period:** 2020 - 2026
- **Supported WOT version:** 2.4.0.1
- **Support:** driftkingsmods@gmail.com
- **Patreon:** [patreon.com/driftkings_mods](https://www.patreon.com/driftkings_mods/)

This repository contains the source, assets, configs, and build data used to maintain the Driftkings mod pack.

## Installation
1. Open the mod distribution link.
2. Enter the `zip` folder.
3. Download the desired mod archive.
4. Extract the archive into your `World_of_Tanks` directory.

## Build and configurations

Run `build_tools/run_build.ps1 -Mode release -NoSync` to build without copying packages to a game installation. Python 2.7 compiles client modules; Python 3 checks configuration defaults and translations. Compiled SWFs are published to `res/flash`; temporary compiler output stays in `build/flash`.

Configuration sources live in `res/configs/Driftkings/<mod>/`, with translations in `i18n/<locale>.json`. Release ZIPs include the complete configuration directories under `mods/configs/Driftkings`. Existing repository settings are retained when missing defaults are added using `python build_tools/sync_configs_from_mods.py`; extracting a ZIP can replace installed configuration files.

The EU client currently declares these languages in `game_info.xml`: `cs`, `de`, `en`, `es`, `fr`, `hu`, `it`, `pl`, `ru`, `tr`, `uk`. The list is recorded in `build_data/locales.json`. All 43 catalog groups include these 11 languages. Translations are machine-generated and need native-speaker terminology review. `python build_tools/localize_configs.py --check` validates catalogs offline; `--translate` explicitly regenerates them online and sends only UI text fragments to the translation service.

Use `python build_tools/sync_configs_from_mods.py --check` and `python build_tools/audit_project.py --check all` before publishing. The package audit also compares shipped JSON files and SWFs with their repository sources. Runtime behavior still requires testing inside the EU client.

## Active Mods
- **AccountManager** - Quick account switching for login management.
- **AimingAngles** - Shows gun elevation and depression limits.
- **ArcadeZoom** - Adds extra zoom control in arcade mode.
- **ArmorCalculator** - Displays effective armor and penetration assistance.
- **ArtySplash** - Shows HE splash and stun range.
- **AutoAimOptimize** - Improves auto-aim against targets behind obstacles.
- **AutoClaimClan** - Automatically claims clan-related rewards.
- **BattleEfficiency** - Displays battle efficiency during and after a match.
- **BattleOptions** - Hides and tweaks multiple battle UI elements.
- **BattleStat** - Adds extra battle statistics.
- **ColorMessages** - Adds colored system and battle messages.
- **CreditCalc** - Calculates credit performance in hangar and battle.
- **CrewSettings** - Adds crew return and related crew helpers.
- **DispersionCircle** - Replaces the standard aiming info circle with a dispersion circle.
- **DispersionTimer** - Shows the real gun dispersion time.
- **DistanceMarker** - Displays distance to enemy targets.
- **FlightTimer** - Shows shell flight time.
- **HangarOptions** - Removes hangar clutter, adds auto-login, and other lobby tweaks.
- **InfoPanel** - Shows extended player information.
- **LogsSwapper** - Reorders the damage log for XVM-style layouts.
- **MainGun** - Displays Main Gun progress in battle.
- **MarksOnGunBattle** - Shows Marks of Excellence progress in battle.
- **MarksOnGunHangar** - Gameface hangar card with MoE objectives, observed progress, mastery icons, WN8 and win rate. Its calculations are included in the main Python module; no separate progress module or SWF is packaged.
- **MarksOnGunTechTree** - Shows MoE percentages and mastery badges in the EU Gameface tech tree.
- **MinimapPlugins** - Adds names, destroyed vehicles, and extra minimap tools.
- **OwnHealth** - Displays the player's HP.
- **PlayersPanelHP** - Shows HP values in the players panel.
- **RatingPlayersInBattle** - Displays player ratings during battle.
- **RepairExtended** - Adds quick repair and crew healing helpers.
- **SafeShot** - Blocks shots that would damage allies.
- **ServerReticle** - Enables server reticle support.
- **ServerTurretExtended** - Adds server turret sync, wheel auto-speed, and stop-to-fire behavior.
- **SixthSense** - Adds a custom Sixth Sense icon, sounds, and battle message.
- **SpottedExtendedLight** - Shows detection and spotting-damage messages above the minimap.
- **SpottedStatus** - Shows detection status in the players panel.
- **SystemColor** - Customizes system message colors.
- **TotalLog** - Adds an extended battle log with efficiency details.
- **VehicleExperience** - Shows vehicle, module, and mission experience progress.
- **ZoomExtended** - Extends zoom up to x30, with a maximum of x45.

## Tech Stack
- Python 2.7.18
- ActionScript 3.0
- FlashDevelop 5.3.3
- Adobe Animate CC 2024
- PyCharm Community Edition 2024.1.3
- JetBrains AI Assistant (Codex 5.3)
- Monica IA Assistant (Sonnet 4.5)

## Acknowledgments
- **Izebrg** (Renat Iliev)
- **Poliroid** (Andrii Andrushchyshyn)
- **PolyacovYury**
- **Spoter** (Peter Rastorguev)
- **CH4MPi** (Alexander Kuznetsov)

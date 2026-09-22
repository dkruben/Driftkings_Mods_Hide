# Driftkings Mods for World of Tanks

Battle tools, hangar improvements and interface customization for the **World of Tanks EU client**.

![WoT EU target](https://img.shields.io/badge/WoT_EU-2.4.0.1-bb3535)
![Client runtime](https://img.shields.io/badge/Python-2.7.18-3776AB)
![UI](https://img.shields.io/badge/UI-Scaleform_%2B_Gameface-6554C0)

[Installation](#installation) · [Mod catalog](#mod-catalog) · [Development](#development) · [Support](#support)

This repository contains the Python sources, ActionScript projects, Gameface assets, configurations and build tooling for the Driftkings mod collection. Each enabled release manifest produces a standalone ZIP with its required dependencies.

## Compatibility

| Component | Repository target |
| --- | --- |
| Game client | World of Tanks **EU 2.4.0.1** |
| Reference source dump | **2.4.0.5450** |
| Client scripts | Python **2.7.18** |
| Interface | Scaleform / ActionScript 3 and Gameface / HTML, CSS, JavaScript |
| Localization | **11 EU client languages** |

The version and local build paths are defined in [build_config.json](build_data/build_config.json). Build validation checks source syntax, resources and package contents; behavior inside the game must also be tested against the target client.

## Installation

1. Obtain the ZIP for the desired mod. When building from source, release archives are generated in `build/archives/` using the [release build](#release-build) below.
2. Close the game and preserve any customized files in `mods/configs/Driftkings/` before replacing them.
3. Extract the ZIP into the World of Tanks EU installation directory, preserving its folder structure.
4. Start the client and configure the mod through the mod settings interface, where available.

The resulting installation follows this structure:

```text
World_of_Tanks_EU/
└── mods/
    ├── 2.4.0.1/
    │   ├── Driftkings/
    │   │   └── <mod>.wotmod
    │   └── <required API>.wotmod
    └── configs/
        └── Driftkings/
            └── <mod>/
                ├── <mod>.json
                └── i18n/
```

Use the generated mod ZIP for installation. GitHub's **Download ZIP** contains the repository sources, not a ready-to-install mod distribution. There is no standalone installer in this project.

## Mod catalog

The following **40 release packages** are enabled in [build_data/archives](build_data/archives). This includes shared support packages used by other mods.

<details>
<summary><strong>View the available packages</strong></summary>

| Package | Purpose |
| --- | --- |
| **AccountManager** | Quick account switching for login management. |
| **AimingAngles** | Shows gun elevation and depression limits. |
| **ArcadeZoom** | Adds extra zoom control in arcade mode. |
| **ArmorCalculator** | Displays effective armor and penetration assistance. |
| **ArtySplash** | Shows HE splash and stun range. |
| **AutoAimOptimize** | Improves auto-aim against targets behind obstacles. |
| **AutoClaimClan** | Automatically claims clan-related rewards. |
| **BanksLoader** | Loads and manages custom sound-bank resources. |
| **BattleEfficiency** | Displays battle efficiency during and after a match. |
| **BattleOptions** | Hides and tweaks multiple battle UI elements. |
| **BattleStat** | Adds extra battle statistics. |
| **ColorMessages** | Adds colored system and battle messages. |
| **CreditCalc** | Calculates credit performance in hangar and battle. |
| **CrewSettings** | Adds crew return and related crew helpers. |
| **DispersionCircle** | Replaces the standard aiming info circle with a dispersion circle. |
| **DispersionTimer** | Shows the real gun dispersion time. |
| **DistanceMarker** | Displays distance to enemy targets. |
| **DriftkingsPlayersPanelAPI** | Shared players-panel integration used by dependent mods. |
| **FlightTimer** | Shows shell flight time. |
| **HangarOptions** | Removes hangar clutter, adds auto-login, and other lobby tweaks. |
| **InfoPanel** | Shows extended player information. |
| **LogsSwapper** | Reorders the damage log for XVM-style layouts. |
| **MainGun** | Displays Main Gun progress in battle. |
| **MarksOnGunBattle** | Shows Marks of Excellence progress in battle. |
| **MarksOnGunHangar** | Gameface hangar card with MoE objectives, observed progress, mastery icons, WN8 and win rate. Its calculations are included in the main Python module; no separate progress module or SWF is packaged. |
| **MarksOnGunTechTree** | Shows MoE percentages and mastery badges in the EU Gameface tech tree. |
| **MinimapPlugins** | Adds names, destroyed vehicles, and extra minimap tools. |
| **OwnHealth** | Displays the player's HP. |
| **PlayersPanelHP** | Shows HP values in the players panel. |
| **RatingPlayersInBattle** | Displays player ratings during battle. |
| **RepairExtended** | Adds quick repair and crew healing helpers. |
| **SafeShot** | Blocks shots that would damage allies. |
| **ServerReticle** | Enables server reticle support. |
| **ServerTurretExtended** | Adds server turret sync, wheel auto-speed, and stop-to-fire behavior. |
| **SixthSense** | Adds a custom Sixth Sense icon, sounds, and battle message. |
| **SpottedExtendedLight** | Shows detection and spotting-damage messages above the minimap. |
| **SpottedStatus** | Shows detection status in the players panel. |
| **SystemColor** | Customizes system message colors. |
| **TotalLog** | Adds an extended battle log with efficiency details. |
| **ZoomExtended** | Adds configurable extended zoom. |

</details>

### Inactive modules

| Module | Status |
| --- | --- |
| HangarEfficiency | Gameface recovery source is preserved in [`.removed`](source/scripts/client/gui/.removed/mod_HangarEfficiency_gameface.py). Compilation and packaging are disabled; assets and configurations remain available for future work. |
| VehicleExperience | Source is retained, but the release ZIP is disabled. |

`MarksOnGunHangar` and `MarksOnGunTechTree` use Gameface. Their previous Flash projects have been removed. Active Flash projects and their compiled SWFs remain in `res/flash/`.

## Configuration and localization

Repository defaults live in [`res/configs/Driftkings`](res/configs/Driftkings):

```text
<mod>/
├── <mod>.json
└── i18n/
    ├── en.json
    └── <locale>.json
```

Release ZIPs include the complete configuration directories required by each package. The installed location is `mods/configs/Driftkings/`.

The client language list is recorded in [locales.json](build_data/locales.json):

| Code | Language | Code | Language |
| --- | --- | --- | --- |
| `cs` | Czech | `it` | Italian |
| `de` | German | `pl` | Polish |
| `en` | English | `ru` | Russian |
| `es` | Spanish | `tr` | Turkish |
| `fr` | French | `uk` | Ukrainian |
| `hu` | Hungarian | | |

All **43 catalog groups** include these languages. Catalog coverage also includes retained configurations for inactive modules. Translations are machine-generated and still need native-speaker terminology review.

To synchronize source defaults and English catalog keys while preserving existing configured values:

```powershell
py -3 build_tools/sync_configs_from_mods.py
```

To check configurations and translations without changing files or accessing the translation service:

```powershell
py -3 build_tools/sync_configs_from_mods.py --check
py -3 build_tools/localize_configs.py --check
```

`localize_configs.py --translate` regenerates translated catalogs online. It sends UI text fragments to the translation service and caches intermediate results in `build/localization/`.

## Development

### Repository layout

| Path | Contents |
| --- | --- |
| [`source/scripts/client`](source/scripts/client) | Python client modules and shared libraries |
| [`res/flash`](res/flash) | Active ActionScript projects and published SWFs |
| [`res/flash/swc`](res/flash/swc) | EU client SWC libraries and their hash manifest |
| [`res/gui/gameface/mods/Driftkings`](res/gui/gameface/mods/Driftkings) | Editable Gameface HTML, CSS and JavaScript |
| [`res/mods/configs/res_map`](res/mods/configs/res_map) | Gameface resource registration |
| [`res/configs/Driftkings`](res/configs/Driftkings) | Default settings and localization catalogs |
| [`res/wotmods`](res/wotmods) | Bundled third-party API dependencies |
| [`build_data`](build_data) | Build settings and package manifests |
| [`build_tools`](build_tools) | Compilation, packaging and validation tools |
| `build/` | Generated packages, compiler output and local reports |

### Prerequisites

- Windows, PowerShell and Git.
- Python **2.7** for client compilation and Python **3** for configuration checks, available through the Windows `py` launcher.
- A Flex SDK with `mxmlc.jar`, Java, and `playerglobal.swc` for ActionScript compilation.
- A matching EU source dump for the full dependency audit, configured through `reference_source` in `build_data/build_config.json`.

The Flash compiler supports `DK_FLEX_HOME`, `DK_MXMLC_JAR`, `DK_PLAYERGLOBAL` and `DK_JAVA` to override local tool paths. `DK_PYTHON27` can override the Python 2.7 executable; the build still uses `py -3` for checks. See [build_flash.py](build_tools/build_flash.py) and [run_build.ps1](build_tools/run_build.ps1) for the defaults.

### Release build

Run from the repository root:

```powershell
.uild_tools
un_build.ps1 -Mode release -NoSync
```

The build validates configurations, compiles the active Flash and Python sources, and creates the enabled packages. `-NoSync` disables the optional copying/comparison steps against local installations.

| Output | Location |
| --- | --- |
| Published SWFs | `res/flash/` |
| Temporary Flash output and logs | `build/flash/` |
| Compiled Python | `build/scripts/client/` |
| Individual mod packages | `build/wotmods/Driftkings/` |
| Installable release ZIPs | `build/archives/` |

Gameface assets are packaged directly from their source directories. They do not require SWF compilation. Rebuilding Flash can change tracked SWFs, so review generated changes before committing.

### Validation

After a release build:

```powershell
py -3 build_tools/audit_project.py --check all
```

The audit checks Python 2.7 syntax, dependencies, JSON resources, package integrity, shipped configuration contents, published SWFs and SWC hashes. Its report is written to `audit_mods/project_inventory.json`.

The [GitHub Actions workflow](.github/workflows/python-package.yml) checks configurations, localization, JSON, Python syntax and Gameface JavaScript. It does not run the game or build the complete release packages.

### Bundled dependencies

| Library | Bundled version |
| --- | --- |
| GUIFlash — gambiter | `0.6.5` |
| ModsSettingsAPI — izeberg | `1.7.0` |
| ModsListAPI — poliroid | `1.7.9` |
| OpenWG Gameface | `1.1.6` |

Each release manifest selects its required dependencies from [`res/wotmods`](res/wotmods).

## Support

For a bug report, include the game version, mod name, steps to reproduce and the relevant excerpt from **`game.log`**. A screenshot is useful for visual issues.

- [Open an issue](https://github.com/dkruben/Driftkings_Mods_Hide/issues)
- Email: [driftkingsmods@gmail.com](mailto:driftkingsmods@gmail.com)
- Support development: [Patreon](https://www.patreon.com/driftkings_mods/)

## License and credits

License documents: [English](LICENSE_EN.md) · [Português](LICENSE_PT.md).

Thanks to **Izebrg (Renat Iliev)**, **Poliroid (Andrii Andrushchyshyn)**, **PolyacovYury**, **Spoter (Peter Rastorguev)** and **CH4MPi (Alexander Kuznetsov)** for their original work and contributions.

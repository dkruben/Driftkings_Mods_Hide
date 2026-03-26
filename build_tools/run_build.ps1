param(
    [ValidateSet("debug", "release")]
    [string]$Mode = "debug"
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$buildConfigPath = Join-Path $repoRoot "build_data\build_config.json"
if (-not (Test-Path $buildConfigPath)) {
    Write-Error "Build config not found: $buildConfigPath"
    exit 1
}

$cfg = Get-Content -Raw $buildConfigPath | ConvertFrom-Json
$gameVersion = [string]$cfg.game_version
if ([string]::IsNullOrWhiteSpace($gameVersion)) {
    Write-Error "build_data/build_config.json must define game_version."
    exit 1
}

$protectWithPjOrion = $false
if ($null -ne $cfg.protect_with_pjorion) {
    $protectWithPjOrion = [bool]$cfg.protect_with_pjorion
}

$debugTargets = @()
if ($cfg.PSObject.Properties.Name -contains "debug_targets" -and $cfg.debug_targets) {
    $debugTargets = @($cfg.debug_targets)
}

$releaseTargets = @()
if ($cfg.PSObject.Properties.Name -contains "release_targets" -and $cfg.release_targets) {
    $releaseTargets = @($cfg.release_targets)
}

if (-not $env:DK_PJORION) { $env:DK_PJORION = "F:/Programas/PJOrion/PjOrion.exe" }
if (-not $env:DK_BCOMPARE_DEBUG) { $env:DK_BCOMPARE_DEBUG = "C:\Program Files\Beyond Compare 5\BCompare.exe" }
if (-not $env:DK_BCOMPARE_RELEASE) { $env:DK_BCOMPARE_RELEASE = "C:\Program Files\Beyond Compare 4\BCompare.exe" }
if (-not $env:DK_7ZIP) { $env:DK_7ZIP = "C:\Program Files\7-Zip\7z.exe" }

$pythonExe = $null
$pythonPrefix = @()

if ($env:DK_PYTHON27) {
    $pythonExe = $env:DK_PYTHON27
} else {
    cmd /c "py -2 -V >nul 2>nul"
    if ($LASTEXITCODE -eq 0) {
        $pythonExe = "py"
        $pythonPrefix = @("-2")
    } else {
        cmd /c "python -c ""import sys; sys.exit(0 if sys.version_info[:2] == (2, 7) else 1)"" >nul 2>nul"
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = "python"
        }
    }
}

if (-not $pythonExe) {
    Write-Error "Python 2.7 was not found. Set DK_PYTHON27 to a valid python.exe path."
    exit 1
}

function Invoke-Python27 {
    param([string[]]$PythonArgs)
    $null = & $pythonExe @pythonPrefix @PythonArgs
    return [int]$LASTEXITCODE
}

function Prepare-Wotmods {
    Write-Host "[1/4] Compiling Python sources..."
    $compileArgs = @(
        "build_tools/compiler.py"
    )
    if ($protectWithPjOrion) {
        $compileArgs += @("-p", $env:DK_PJORION)
    }
    $compileArgs += @("-d", "scripts/client/", "-o", "build/scripts/client/", "source/scripts/client/")
    $code = Invoke-Python27 -PythonArgs $compileArgs
    if ($code -ne 0) { return $code }

    Write-Host "[2/4] Packing wotmods..."
    $code = Invoke-Python27 -PythonArgs @("build_tools/packer.py", "-q", "-v", "build_data/build_config.json", "build_data/wotmods/", "build/wotmods/")
    return $code
}

Write-Host "Running $Mode build from `"$repoRoot`""
Write-Host "Game version: $gameVersion"
Write-Host "Protect with PJOrion: $protectWithPjOrion"

$code = Prepare-Wotmods
if ($code -ne 0) {
    Write-Host "Build failed."
    exit 1
}

if ($Mode -eq "debug") {
    Write-Host "[3/4] Optional debug sync..."
    if (Test-Path $env:DK_BCOMPARE_DEBUG) {
        if ($debugTargets.Count -gt 0) {
            foreach ($target in $debugTargets) {
                & $env:DK_BCOMPARE_DEBUG "build\wotmods\" "$target\mods\$gameVersion\" "/solo"
            }
        } else {
            Write-Host "No debug targets configured. Skipping debug sync."
        }
    } else {
        Write-Host "Beyond Compare for debug not found. Skipping debug sync."
    }

    Write-Host "[4/4] Optional Sixth Sense audio package..."
    $bankPath = "res\sound_bank_wwise\SixthSense\GeneratedSoundBanks\Windows\driftkings_sixthsense.bnk"
    if (Test-Path $bankPath) {
        if (Test-Path $env:DK_7ZIP) {
            & $env:DK_7ZIP "a" "-tzip" "res\audioww\driftkings_sixthsense.wotmod" $bankPath *> $null
        } else {
            Write-Host "7-Zip not found. Skipping audio package step."
        }
    } else {
        Write-Host "Generated Sixth Sense bank not found. Skipping audio package step."
    }
} else {
    Write-Host "[3/4] Packing release archives..."
    $code = Invoke-Python27 -PythonArgs @("build_tools/packer.py", "-q", "-v", "build_data/build_config.json", "build_data/archives/", "build/archives/")
    if ($code -ne 0) {
        Write-Host "Build failed."
        exit 1
    }

    Write-Host "[4/4] Optional release comparison..."
    if (Test-Path $env:DK_BCOMPARE_RELEASE) {
        if ($releaseTargets.Count -gt 0) {
            foreach ($target in $releaseTargets) {
                Start-Process -FilePath $env:DK_BCOMPARE_RELEASE -ArgumentList @("build\archives\", $target) | Out-Null
            }
        } else {
            Write-Host "No release targets configured. Skipping release comparison."
        }
    } else {
        Write-Host "Beyond Compare for release not found. Skipping release comparison."
    }
}

Write-Host "Build finished."
exit 0

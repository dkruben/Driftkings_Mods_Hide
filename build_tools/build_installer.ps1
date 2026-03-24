param(
    [string]$Configuration = "Release",
    [string]$Runtime = "win-x64"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$projectDir = Join-Path $repoRoot "installer\DriftkingsInstaller"
$payloadDir = Join-Path $projectDir "Payload"
$archivePayloadDir = Join-Path $payloadDir "archives"
$outputDir = Join-Path $repoRoot "build\installer"
$publishDir = Join-Path $outputDir "publish"
$manifestPath = Join-Path $payloadDir "payload_manifest.json"
$gameVersion = (Get-Content (Join-Path $repoRoot "build_data\GAME_VERSION") -Raw).Trim()

New-Item -ItemType Directory -Force -Path $archivePayloadDir | Out-Null
Get-ChildItem $archivePayloadDir -File -ErrorAction SilentlyContinue | Remove-Item -Force

$archiveManifests = Get-ChildItem (Join-Path $repoRoot "build_data\archives") -Filter *.json | Sort-Object Name
$packages = @()
$needsReleaseBuild = $false

foreach ($manifestFile in $archiveManifests) {
    $manifest = Get-Content $manifestFile.FullName -Raw | ConvertFrom-Json
    if (-not $manifest.enabled) {
        continue
    }

    $zipName = [System.IO.Path]::GetFileNameWithoutExtension($manifestFile.Name) + ".zip"
    $sourceZip = Join-Path $repoRoot ("build\archives\" + $zipName)
    if (-not (Test-Path $sourceZip)) {
        $needsReleaseBuild = $true
        break
    }
}

if ($needsReleaseBuild) {
    Write-Host "Release archives not found. Running release build first..."
    cmd /c release.cmd
    if ($LASTEXITCODE -ne 0) {
        throw "Release build failed while preparing installer payload."
    }
}

foreach ($manifestFile in $archiveManifests) {
    $manifest = Get-Content $manifestFile.FullName -Raw | ConvertFrom-Json
    if (-not $manifest.enabled) {
        continue
    }

    $zipName = [System.IO.Path]::GetFileNameWithoutExtension($manifestFile.Name) + ".zip"
    $sourceZip = Join-Path $repoRoot ("build\archives\" + $zipName)
    if (-not (Test-Path $sourceZip)) {
        throw "Archive not found for installer payload: $zipName"
    }

    Copy-Item $sourceZip (Join-Path $archivePayloadDir $zipName) -Force

    $packages += [ordered]@{
        id          = [System.IO.Path]::GetFileNameWithoutExtension($manifestFile.Name)
        displayName = [regex]::Replace([System.IO.Path]::GetFileNameWithoutExtension($manifestFile.Name), "([a-z0-9])([A-Z])", '$1 $2')
        fileName    = $zipName
        description = "Instala o pacote " + ([System.IO.Path]::GetFileNameWithoutExtension($manifestFile.Name))
        sizeBytes   = (Get-Item $sourceZip).Length
        recommended = $true
        isMaintenance = $false
    }
}

$packages = @(
    [ordered]@{
        id            = "__clear_cache__"
        displayName   = "Limpar Cache do Jogo"
        fileName      = ""
        description   = "Limpa caches seguras em AppData\\Roaming\\Wargaming.net\\WorldOfTanks"
        sizeBytes     = 0
        recommended   = $false
        isMaintenance = $true
    }
) + $packages

$payload = [ordered]@{
    title          = "Driftkings Mods Installer"
    gameVersion    = $gameVersion
    packageVersion = (Get-Date -Format "yyyy.MM.dd.HHmm")
    packages       = $packages
}

$payload | ConvertTo-Json -Depth 4 | Set-Content -Path $manifestPath -Encoding UTF8

& (Join-Path $repoRoot "build_tools\generate_installer_assets.ps1") -ProjectRoot $repoRoot

New-Item -ItemType Directory -Force -Path $publishDir | Out-Null

dotnet publish (Join-Path $projectDir "DriftkingsInstaller.csproj") `
    -c $Configuration `
    -r $Runtime `
    -o $publishDir `
    -p:PublishSingleFile=true `
    -p:SelfContained=true `
    -p:IncludeAllContentForSelfExtract=true

$publishedExe = Join-Path $publishDir "DriftkingsInstaller.exe"
$finalExe = Join-Path $outputDir "Driftkings_Mods_Installer_EU_NA.exe"

if (-not (Test-Path $publishedExe)) {
    throw "Installer executable was not generated."
}

Copy-Item $publishedExe $finalExe -Force
Write-Host "Installer generated at $finalExe"

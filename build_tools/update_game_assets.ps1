param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$GameRoot
)
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$source = (Resolve-Path -LiteralPath $SourceRoot).Path
$game = (Resolve-Path -LiteralPath $GameRoot).Path
[xml]$versionXml = Get-Content -LiteralPath (Join-Path $game "version.xml") -Raw
if ($versionXml.'version.xml'.version -notmatch 'v\.(\d+\.\d+\.\d+\.\d+)') {
    throw "Cannot read client version from version.xml"
}
$gameVersion = $Matches[1]
$sourceVersion = (Get-Content -LiteralPath (Join-Path $source ".version_name") -Raw).Trim()
if (($sourceVersion.Split('.')[0..2] -join '.') -ne ($gameVersion.Split('.')[0..2] -join '.')) {
    throw "Client $gameVersion and source $sourceVersion belong to different versions."
}
$destination = Join-Path $repoRoot "res\flash\swc"
$libraries = @(Get-ChildItem -LiteralPath $destination -Filter *.swc)
# Validate the complete source set before replacing any library.
foreach ($library in $libraries) {
    $inputPath = Join-Path $source ("sources\res\gui\flash\swc\" + $library.Name)
    if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw "Missing SWC: $inputPath" }
}
$hashes = @()
foreach ($library in $libraries) {
    $inputPath = Join-Path $source ("sources\res\gui\flash\swc\" + $library.Name)
    Copy-Item -LiteralPath $inputPath -Destination $library.FullName -Force
    $hash = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $library.FullName -Algorithm SHA256).Hash -ne $hash) { throw "SWC verification failed" }
    $hashes += [ordered]@{ name = $library.Name; sha256 = $hash }
}
$encoding = New-Object System.Text.UTF8Encoding($false)
$configPath = Join-Path $repoRoot "build_data\build_config.json"
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$config.game_version = $gameVersion
$config | Add-Member -NotePropertyName reference_source_version -NotePropertyValue $sourceVersion -Force
$config | Add-Member -NotePropertyName reference_source -NotePropertyValue $source -Force
$config.debug_targets = @($game)
[IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 10) + "`n", $encoding)
$manifest = [ordered]@{ source_version = $sourceVersion; game_version = $gameVersion; libraries = $hashes }
[IO.File]::WriteAllText((Join-Path $destination "manifest.json"), ($manifest | ConvertTo-Json -Depth 10) + "`n", $encoding)
$readme = Join-Path $repoRoot "README.md"
$content = [IO.File]::ReadAllText($readme)
$content = $content -replace 'WOT-[\d.]+-red', "WOT-$gameVersion-red"
$content = $content -replace '(Supported WOT version:\*\* )[\d.]+', "`${1}$gameVersion"
[IO.File]::WriteAllText($readme, $content, $encoding)
Write-Host "Updated $($libraries.Count) SWCs from $sourceVersion; client version $gameVersion."

param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$assetsDir = Join-Path $ProjectRoot "installer\DriftkingsInstaller\Assets"
New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null

Add-Type -AssemblyName System.Drawing

function New-InstallerIcon {
    param(
        [string]$Path,
        [int]$Size
    )

    $bitmap = New-Object System.Drawing.Bitmap $Size, $Size
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb(0, 0, 0, 0))

    $rect = New-Object System.Drawing.Rectangle 0, 0, $Size, $Size
    $background = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect,
        ([System.Drawing.Color]::FromArgb(255, 5, 14, 22)),
        ([System.Drawing.Color]::FromArgb(255, 8, 34, 56)),
        90
    $graphics.FillEllipse($background, 28, 28, $Size - 56, $Size - 56)

    $glowPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 51, 216, 255), 16)
    $graphics.DrawEllipse($glowPen, 30, 30, $Size - 60, $Size - 60)

    $burstPoints = @(
        (New-Object System.Drawing.PointF ($Size * 0.14), ($Size * 0.56)),
        (New-Object System.Drawing.PointF ($Size * 0.26), ($Size * 0.38)),
        (New-Object System.Drawing.PointF ($Size * 0.20), ($Size * 0.24)),
        (New-Object System.Drawing.PointF ($Size * 0.38), ($Size * 0.30)),
        (New-Object System.Drawing.PointF ($Size * 0.50), ($Size * 0.14)),
        (New-Object System.Drawing.PointF ($Size * 0.61), ($Size * 0.30)),
        (New-Object System.Drawing.PointF ($Size * 0.80), ($Size * 0.24)),
        (New-Object System.Drawing.PointF ($Size * 0.74), ($Size * 0.40)),
        (New-Object System.Drawing.PointF ($Size * 0.88), ($Size * 0.55)),
        (New-Object System.Drawing.PointF ($Size * 0.70), ($Size * 0.63)),
        (New-Object System.Drawing.PointF ($Size * 0.74), ($Size * 0.82)),
        (New-Object System.Drawing.PointF ($Size * 0.53), ($Size * 0.74)),
        (New-Object System.Drawing.PointF ($Size * 0.37), ($Size * 0.84)),
        (New-Object System.Drawing.PointF ($Size * 0.34), ($Size * 0.66))
    )
    $burstBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(145, 17, 27, 62))
    $graphics.FillPolygon($burstBrush, $burstPoints)

    $glowRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 48, 26))
    $shadowRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 123, 0, 9))
    $bodyPoints = @(
        (New-Object System.Drawing.PointF ($Size * 0.52), ($Size * 0.20)),
        (New-Object System.Drawing.PointF ($Size * 0.68), ($Size * 0.30)),
        (New-Object System.Drawing.PointF ($Size * 0.75), ($Size * 0.49)),
        (New-Object System.Drawing.PointF ($Size * 0.66), ($Size * 0.78)),
        (New-Object System.Drawing.PointF ($Size * 0.40), ($Size * 0.82)),
        (New-Object System.Drawing.PointF ($Size * 0.24), ($Size * 0.63)),
        (New-Object System.Drawing.PointF ($Size * 0.26), ($Size * 0.39))
    )
    $graphics.FillClosedCurve($shadowRed, $bodyPoints, [System.Drawing.Drawing2D.FillMode]::Winding, 0.45)
    $graphics.FillClosedCurve($glowRed, $bodyPoints, [System.Drawing.Drawing2D.FillMode]::Winding, 0.45)

    $hornBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 38, 9, 20))
    $horn1 = @(
        (New-Object System.Drawing.PointF ($Size * 0.42), ($Size * 0.22)),
        (New-Object System.Drawing.PointF ($Size * 0.36), ($Size * 0.05)),
        (New-Object System.Drawing.PointF ($Size * 0.47), ($Size * 0.17))
    )
    $horn2 = @(
        (New-Object System.Drawing.PointF ($Size * 0.60), ($Size * 0.20)),
        (New-Object System.Drawing.PointF ($Size * 0.67), ($Size * 0.04)),
        (New-Object System.Drawing.PointF ($Size * 0.66), ($Size * 0.19))
    )
    $graphics.FillPolygon($hornBrush, $horn1)
    $graphics.FillPolygon($hornBrush, $horn2)

    $eyeBrush = [System.Drawing.Brushes]::White
    $irisBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 74, 184, 255))
    $pupilBrush = [System.Drawing.Brushes]::Black
    $graphics.FillEllipse($eyeBrush, $Size * 0.35, $Size * 0.28, $Size * 0.10, $Size * 0.12)
    $graphics.FillEllipse($eyeBrush, $Size * 0.53, $Size * 0.28, $Size * 0.10, $Size * 0.12)
    $graphics.FillEllipse($irisBrush, $Size * 0.39, $Size * 0.32, $Size * 0.045, $Size * 0.05)
    $graphics.FillEllipse($irisBrush, $Size * 0.55, $Size * 0.32, $Size * 0.045, $Size * 0.05)
    $graphics.FillEllipse($pupilBrush, $Size * 0.405, $Size * 0.34, $Size * 0.018, $Size * 0.022)
    $graphics.FillEllipse($pupilBrush, $Size * 0.566, $Size * 0.34, $Size * 0.018, $Size * 0.022)

    $smilePen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 48, 0, 12), 6)
    $graphics.DrawArc($smilePen, $Size * 0.42, $Size * 0.38, $Size * 0.16, $Size * 0.08, 15, 150)

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)

    $smilePen.Dispose()
    $irisBrush.Dispose()
    $hornBrush.Dispose()
    $glowRed.Dispose()
    $shadowRed.Dispose()
    $burstBrush.Dispose()
    $glowPen.Dispose()
    $background.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}

function New-HeroImage {
    param(
        [string]$Path,
        [string]$IconPath,
        [int]$Width,
        [int]$Height
    )

    $bitmap = New-Object System.Drawing.Bitmap $Width, $Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $rect = New-Object System.Drawing.Rectangle 0, 0, $Width, $Height

    $background = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect,
        ([System.Drawing.Color]::FromArgb(255, 6, 12, 22)),
        ([System.Drawing.Color]::FromArgb(255, 10, 40, 70)),
        20
    $graphics.FillRectangle($background, $rect)

    $sparkBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(170, 76, 227, 255))
    $rand = New-Object System.Random 42
    for ($i = 0; $i -lt 120; $i++) {
        $x = $rand.Next(0, $Width)
        $y = $rand.Next(0, $Height)
        $s = $rand.Next(2, 7)
        $graphics.FillEllipse($sparkBrush, $x, $y, $s, $s)
    }

    $iconImage = [System.Drawing.Image]::FromFile($IconPath)
    $iconSize = 420
    $iconX = [int](($Width - $iconSize) / 2)
    $iconY = [int](($Height - $iconSize) / 2) - 24
    $graphics.DrawImage($iconImage, $iconX, $iconY, $iconSize, $iconSize)

    $titleFont = New-Object System.Drawing.Font("Segoe UI Semibold", 54)
    $subtitleFont = New-Object System.Drawing.Font("Segoe UI", 22)
    $whiteBrush = [System.Drawing.Brushes]::White
    $softBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(220, 214, 244, 255))
    $graphics.DrawString("DRIFTKINGS", $titleFont, $whiteBrush, 36, ($Height * 0.67))
    $graphics.DrawString("EU / NA MOD INSTALLER", $subtitleFont, $softBrush, 40, ($Height * 0.81))

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)

    $softBrush.Dispose()
    $titleFont.Dispose()
    $subtitleFont.Dispose()
    $iconImage.Dispose()
    $sparkBrush.Dispose()
    $background.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}

$iconPath = Join-Path $assetsDir "icon.png"
$packPath = Join-Path $assetsDir "pack.png"
$heroPath = Join-Path $assetsDir "hero.png"

New-InstallerIcon -Path $iconPath -Size 512
Copy-Item $iconPath $packPath -Force
New-HeroImage -Path $heroPath -IconPath $iconPath -Width 1400 -Height 720

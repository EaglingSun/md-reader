# md-reader release build pipeline.
# 1) PyInstaller bundles app/ + Python runtime + PyQt6 -> dist/md-reader/
# 2) Inno Setup wraps that into dist/installer/md-reader-setup-X.Y.Z.exe
#
# Usage (from project root or anywhere):
#   powershell -ExecutionPolicy Bypass -File packaging\build.ps1
#
# Prerequisites:
#   - Python 3.13 (auto-detected)
#   - Inno Setup 6 (https://jrsoftware.org/isinfo.php) - optional, only needed
#     for step 2. If missing, the PyInstaller bundle is still produced.

$ErrorActionPreference = "Stop"
$PackagingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot  = Split-Path -Parent $PackagingDir

Write-Host "=== md-reader build ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"
Write-Host ""

# --- 1. Locate Python ----------------------------------------------------
$PyCandidates = @(
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe",
    "C:\Program Files\Python313\python.exe"
)
$Py = $null
foreach ($c in $PyCandidates) { if (Test-Path $c) { $Py = $c; break } }
if (-not $Py) {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) { $Py = & py.exe -3.13 -c "import sys; print(sys.executable)" 2>$null }
}
if (-not $Py -or -not (Test-Path $Py)) {
    Write-Host "[X] Python 3.13 not found." -ForegroundColor Red
    exit 1
}
Write-Host "[1/4] Python: $Py" -ForegroundColor Green

# --- 2. Install build dependencies --------------------------------------
$env:PYTHONPATH = ""
& $Py -m pip install --quiet --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { Write-Host "[X] pyinstaller install failed" -ForegroundColor Red; exit 1 }
& $Py -m pip install --quiet -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Host "[X] requirements install failed" -ForegroundColor Red; exit 1 }
Write-Host "[2/4] Build dependencies ready" -ForegroundColor Green

# --- 3. Run PyInstaller -------------------------------------------------
$BuildDir   = Join-Path $ProjectRoot "build"
$DistDir    = Join-Path $ProjectRoot "dist"
$BundleDir  = Join-Path $DistDir "md-reader"
# Clean only the regeneratable parts. Don't nuke dist/installer/ - the existing
# .exe there might be locked by Defender/Explorer, and Inno Setup will overwrite
# it at the end anyway.
if (Test-Path $BuildDir)  { Remove-Item -Recurse -Force $BuildDir }
if (Test-Path $BundleDir) { Remove-Item -Recurse -Force $BundleDir }

$Spec = Join-Path $PackagingDir "md-reader.spec"
Push-Location $ProjectRoot
try {
    & $Py -m PyInstaller --noconfirm $Spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}

$Bundle = Join-Path $DistDir "md-reader\md-reader.exe"
if (-not (Test-Path $Bundle)) { Write-Host "[X] Bundle not produced" -ForegroundColor Red; exit 1 }
Write-Host "[3/4] PyInstaller bundle: $Bundle" -ForegroundColor Green

# --- 4. Run Inno Setup --------------------------------------------------
$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:LocalAppData}\Programs\Inno Setup 6\ISCC.exe"   # winget per-user install
)
$Iscc = $null
foreach ($c in $IsccCandidates) { if (Test-Path $c) { $Iscc = $c; break } }
if (-not $Iscc) {
    Write-Host ""
    Write-Host "[!] Inno Setup 6 not found - skipping installer build." -ForegroundColor Yellow
    Write-Host "    Install from https://jrsoftware.org/isinfo.php and re-run."
    Write-Host "    PyInstaller bundle remains at: $DistDir\md-reader\"
    Write-Host "    (You can zip that folder for ad-hoc distribution.)"
    exit 0
}

$Iss = Join-Path $PackagingDir "installer.iss"
& $Iscc $Iss
if ($LASTEXITCODE -ne 0) { Write-Host "[X] Inno Setup compile failed" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "[4/4] Installer built." -ForegroundColor Green
Get-ChildItem (Join-Path $DistDir "installer") -Filter "*.exe" | ForEach-Object {
    $sizeMB = [math]::Round($_.Length / 1MB, 1)
    Write-Host "  $($_.Name)  ($sizeMB MB)" -ForegroundColor White
}
Write-Host ""
Write-Host "Distribute the file above. End users just double-click it." -ForegroundColor Cyan

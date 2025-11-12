<#
.SYNOPSIS
    Installs the GTK/Pango/Cairo runtime required by WeasyPrint on Windows.

.DESCRIPTION
    Downloads the latest 64-bit GTK runtime installer from the official
    project (https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
    and performs a silent installation to the specified directory. The script
    then records the installation path in `BGLApp_Portable\gtk_runtime_path.txt`
    so that the portable launcher can extend PATH automatically on launch.

.PARAMETER InstallPath
    Target directory for the GTK runtime. Defaults to %LOCALAPPDATA%\GTK3-Runtime.

.PARAMETER Force
    Overwrite an existing installation directory if it already exists.
#>
param(
    [string]$InstallPath = (Join-Path $env:LOCALAPPDATA "GTK3-Runtime"),
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -notlike "*Windows*") {
    Write-Error "هذا السكربت مخصص لأنظمة Windows فقط."
    exit 1
}

$installDir = Resolve-Path -LiteralPath (Split-Path $InstallPath -Parent) -ErrorAction SilentlyContinue
if (-not $installDir) {
    $null = New-Item -ItemType Directory -Path (Split-Path $InstallPath -Parent) -Force
}

if (Test-Path $InstallPath -PathType Container) {
    if (-not $Force) {
        Write-Host "⚠️  المسار $InstallPath موجود بالفعل. استخدم -Force لإعادة التثبيت." -ForegroundColor Yellow
        exit 0
    }
    Remove-Item -Recurse -Force $InstallPath
}

$releaseApi = "https://api.github.com/repos/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/latest"
Write-Host "📥 تحميل معلومات الإصدار من $releaseApi..."
$release = Invoke-RestMethod -Uri $releaseApi -Headers @{ "User-Agent" = "BGLAppPortable" }
$asset = $release.assets | Where-Object { $_.name -match "win64\.exe$" } | Select-Object -First 1

if (-not $asset) {
    Write-Error "تعذر العثور على المثبّت 64-بت في الإصدار الأخير."
    exit 1
}

$tempInstaller = Join-Path $env:TEMP $asset.name
Write-Host "⬇️  تحميل $($asset.name)..."
Invoke-WebRequest -Uri $asset.browser_download_url -UseBasicParsing -OutFile $tempInstaller

Write-Host "⚙️  تشغيل المثبّت في الوضع الصامت..."
$arguments = @("/S", "/D=$InstallPath")
Start-Process -FilePath $tempInstaller -ArgumentList $arguments -Wait

if (-not (Test-Path (Join-Path $InstallPath "bin"))) {
    Write-Error "لم يتم العثور على مجلد bin داخل $InstallPath. تحقق يدويًا من التثبيت."
    exit 1
}

Remove-Item $tempInstaller -ErrorAction SilentlyContinue

$markerPath = Join-Path $PSScriptRoot "..\gtk_runtime_path.txt"
Set-Content -Path $markerPath -Value $InstallPath -Encoding UTF8 -Force

Write-Host "✅ تم تثبيت GTK runtime في $InstallPath"
Write-Host "ℹ️ سيتم تضمين المسار تلقائيًا عند تشغيل BGLApp Portable."

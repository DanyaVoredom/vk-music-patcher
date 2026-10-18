[CmdletBinding()]
param(
    [string]$Package = "com.uma.musicvk",
    [string]$OutDir = "build\pulled",
    [string]$ApksOut = "pulled.apks"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Get-Device {
    $devices = @(& adb devices | Select-Object -Skip 1 | Where-Object { $_ -match "\sdevice$" })
    if ($devices.Count -eq 0) { throw "no adb device" }
    return $devices[0].Split("`t")[0]
}

$device = Get-Device
Write-Host "device: $device" -ForegroundColor Green

$paths = @(& adb shell pm path $Package | ForEach-Object { $_.Trim() -replace "^package:", "" })
if ($paths.Count -eq 0) { throw "package not installed: $Package" }

$target = Join-Path $Root $OutDir
if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
New-Item -ItemType Directory -Path $target -Force | Out-Null

$map = @{}
foreach ($remote in $paths) {
    if ($remote -match "split_(.+)\.apk$") {
        $name = Split-Path $remote -Leaf
    }
    elseif ($remote -match "/base\.apk$") {
        $name = "base.apk"
    }
    else {
        $name = Split-Path $remote -Leaf
    }
    & adb pull $remote (Join-Path $target $name) | Out-Null
    $map[$name] = $remote
    Write-Host "pulled: $name"
}

$apksPath = Join-Path $Root $ApksOut
if (Test-Path -LiteralPath $apksPath) { Remove-Item -LiteralPath $apksPath -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($target, $apksPath)
Write-Host "wrote: $apksPath" -ForegroundColor Cyan
[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$NoLaunch,
    [switch]$Install,
    [int]$WaitSeconds = 25,
    [string]$LogDir = "logs"
)

$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$ApkToolJar = "C:\Windows\apktool.jar"
$BuildTools = "C:\Android\Sdk\build-tools\36.1.0"
$Keystore = Join-Path $Root "patch.keystore"
$KeyAlias = "vkmpatch"
$KeyPass = "patchvk123"

$Package = "com.uma.musicvk.patched"
$Activity = "com.vk.music.screens.main.MainActivity"
$SrcBase = Join-Path $Root "work_845_base"
$SrcSplit = Join-Path $Root "work_845_arm64"
$Apks = Join-Path $Root "VK Музыка_8.45.apks"
$OrigSplit = Join-Path $Root "build\apks_845\split_config.arm64_v8a.apk"

$script:SignedBase = Join-Path $Root "build\signed_base.apk"
$script:SignedSplit = Join-Path $Root "build\signed_split.apk"

function Write-Step { param([string]$Text) Write-Host "== $Text" -ForegroundColor Cyan }

function Unpack-Apks {
    if (-not (Test-Path -LiteralPath $Apks)) { throw "missing apks: $Apks" }
    $tmp = Join-Path $Root "build\apks_845"
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($Apks, $tmp)
    $base = Join-Path $tmp "base.apk"
    $split = Join-Path $tmp "split_config.arm64_v8a.apk"

    Write-Step "apktool d base"
    if (Test-Path -LiteralPath $SrcBase) { Remove-Item -LiteralPath $SrcBase -Recurse -Force }
    & java -Xmx6g "-Duser.language=en" "-Dfile.encoding=UTF8" -jar $ApkToolJar d $base -o $SrcBase -f
    if ($LASTEXITCODE -ne 0) { throw "apktool base failed" }

    Write-Step "extract arm64 split libs"
    if (Test-Path -LiteralPath $SrcSplit) { Remove-Item -LiteralPath $SrcSplit -Recurse -Force }
    New-Item -ItemType Directory -Path $SrcSplit -Force | Out-Null
    [System.IO.Compression.ZipFile]::ExtractToDirectory($split, $SrcSplit)
}

function Invoke-Patch {
    Write-Step "patch package"
    & python (Join-Path $Root "patch_package_845.py") "work_845_base"
    if ($LASTEXITCODE -ne 0) { throw "patch_package failed" }

    Write-Step "patch subscription"
    & python (Join-Path $Root "patch_subscription_845.py") "work_845_base"
    if ($LASTEXITCODE -ne 0) { throw "patch_subscription failed" }

    Write-Step "patch migration"
    & python (Join-Path $Root "patch_migration_845.py") "work_845_base"
    if ($LASTEXITCODE -ne 0) { throw "patch_migration failed" }

    Write-Step "patch native (split)"
    & python (Join-Path $Root "patch_native_845.py") "work_845_arm64"
    if ($LASTEXITCODE -ne 0) { throw "patch_native failed" }
}

function Invoke-AppBuild {
    $unsignedBase = Join-Path $Root "build\unsigned_base.apk"
    New-Item -ItemType Directory -Path (Join-Path $Root "build") -Force | Out-Null

    Write-Step "apktool b base"
    & java -Xmx6g "-Duser.language=en" "-Dfile.encoding=UTF8" -jar $ApkToolJar b $SrcBase -o $unsignedBase
    if ($LASTEXITCODE -ne 0) { throw "apktool base build failed" }

    Write-Step "sign base"
    & (Join-Path $BuildTools "apksigner.bat") sign --ks $Keystore --ks-key-alias $KeyAlias --ks-pass "pass:$KeyPass" --key-pass "pass:$KeyPass" --v2-signing-enabled true --v3-signing-enabled true --out $script:SignedBase $unsignedBase
    if ($LASTEXITCODE -ne 0) { throw "apksigner base failed" }

    Write-Step "repack arm64 split"
    $repacked = Join-Path $Root "build\split_repacked.apk"
    & python (Join-Path $Root "repack_split.py") $OrigSplit (Join-Path $SrcSplit "lib\arm64-v8a\libvkcore.so") $repacked
    if ($LASTEXITCODE -ne 0) { throw "repack split failed" }

    Write-Step "align + sign split"
    $alignedSplit = Join-Path $Root "build\split_aligned.apk"
    & (Join-Path $BuildTools "zipalign.exe") -f -p 4 $repacked $alignedSplit
    if ($LASTEXITCODE -ne 0) { throw "zipalign split failed" }
    & (Join-Path $BuildTools "apksigner.bat") sign --ks $Keystore --ks-key-alias $KeyAlias --ks-pass "pass:$KeyPass" --key-pass "pass:$KeyPass" --v2-signing-enabled true --v3-signing-enabled true --out $script:SignedSplit $alignedSplit
    if ($LASTEXITCODE -ne 0) { throw "apksigner split failed" }
}

function Install-Split {
    Write-Step "install-multiple"
    $parts = @(
        (Join-Path $Root "build\final_base.apk"),
        (Join-Path $Root "build\final_arm64.apk"),
        (Join-Path $Root "build\final_dpi.apk"),
        (Join-Path $Root "build\final_ru.apk")
    )
    foreach ($p in $parts) { if (-not (Test-Path -LiteralPath $p)) { throw "missing $p" } }
    $text = (& adb install-multiple -r @parts 2>&1 | Out-String)
    Write-Host $text.Trim()
    if ($LASTEXITCODE -ne 0) { throw "install failed" }
}

if ($Build) {
    Unpack-Apks
    Invoke-Patch
    Invoke-AppBuild
}

if ($Install) {
    Install-Split
    if ($NoLaunch) { return }
    & adb shell am force-stop $Package
    & adb logcat -b all -c
    & adb shell am start -W -n "$Package/$Activity"
    Start-Sleep -Seconds $WaitSeconds
    $pid = (& adb shell pidof $Package 2>$null | Out-String).Trim()
    if ($pid) { Write-Host "process alive pid $pid" -ForegroundColor Green }
    else { Write-Host "process dead" -ForegroundColor Red }
}
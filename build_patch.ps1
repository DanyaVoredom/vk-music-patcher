[CmdletBinding()]
param(
    [string]$Package = "com.uma.musicvk",
    [string]$Apks = "pulled.apks",
    [switch]$Pull,
    [switch]$Build,
    [switch]$Install,
    [switch]$NoLaunch,
    [string]$KsPass = $env:VKM_KS_PASS,
    [int]$WaitSeconds = 25
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$ApkToolJar = "C:\Windows\apktool.jar"
$BuildTools = "C:\Android\Sdk\build-tools\36.1.0"
$Keystore = Join-Path $Root "patch.keystore"
$KeyAlias = "vkmpatch"
$OutPackage = "$Package.patched"
$Activity = "com.vk.music.screens.main.MainActivity"
$Work = Join-Path $Root "work"
$BuildDir = Join-Path $Root "build"
$ApksPath = Join-Path $Root $Apks

function Write-Step { param([string]$T) Write-Host "== $T" -ForegroundColor Cyan }

function Invoke-Pull {
    Write-Step "pull $Package"
    & pwsh -NoProfile -File (Join-Path $Root "pull_apks.ps1") -Package $Package -ApksOut $Apks
    if ($LASTEXITCODE -ne 0) { throw "pull failed" }
}

function Invoke-Unpack {
    Write-Step "unpack apks"
    $tmp = Join-Path $BuildDir "apks"
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ApksPath, $tmp)

    $base = Join-Path $tmp "base.apk"
    if (-not (Test-Path -LiteralPath $base)) { throw "no base.apk in $Apks" }

    if (Test-Path -LiteralPath $Work) { Remove-Item -LiteralPath $Work -Recurse -Force }
    & java -Xmx6g "-Duser.language=en" "-Dfile.encoding=UTF8" -jar $ApkToolJar d $base -o $Work -f
    if ($LASTEXITCODE -ne 0) { throw "apktool failed" }

    $script:SplitDir = Join-Path $BuildDir "split"
    if (Test-Path -LiteralPath $script:SplitDir) { Remove-Item -LiteralPath $script:SplitDir -Recurse -Force }
    New-Item -ItemType Directory -Path $script:SplitDir -Force | Out-Null

    $abiSplit = Join-Path $tmp "split_config.arm64_v8a.apk"
    if (Test-Path -LiteralPath $abiSplit) {
        [System.IO.Compression.ZipFile]::ExtractToDirectory($abiSplit, (Join-Path $script:SplitDir "arm64"))
    }
}

function Invoke-Patch {
    Write-Step "patch package"
    & python (Join-Path $Root "vk_package.py") "work"
    if ($LASTEXITCODE -ne 0) { throw "vk_package failed" }

    Write-Step "patch code"
    & python (Join-Path $Root "vk_patch.py") "work"
    if ($LASTEXITCODE -ne 0) { throw "vk_patch failed" }

    $so = Join-Path $script:SplitDir "arm64\lib\arm64-v8a\libvkcore.so"
    if (Test-Path -LiteralPath $so) {
        Write-Step "patch native"
        & python (Join-Path $Root "patch_native.py") (Join-Path $script:SplitDir "arm64")
        if ($LASTEXITCODE -ne 0) { throw "patch_native failed" }
    }
}

function Invoke-Build {
    if (-not $KsPass) { throw "set -KsPass or VKM_KS_PASS" }
    $unsigned = Join-Path $BuildDir "unsigned_base.apk"
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null

    Write-Step "apktool b base"
    & java -Xmx6g "-Duser.language=en" "-Dfile.encoding=UTF8" -jar $ApkToolJar b $Work -o $unsigned
    if ($LASTEXITCODE -ne 0) { throw "apktool build failed" }

    Write-Step "sign base"
    $script:FinalBase = Join-Path $BuildDir "final_base.apk"
    & (Join-Path $BuildTools "apksigner.bat") sign --ks $Keystore --ks-key-alias $KeyAlias --ks-pass "pass:$KsPass" --key-pass "pass:$KsPass" --v2-signing-enabled true --v3-signing-enabled true --out $script:FinalBase $unsigned
    if ($LASTEXITCODE -ne 0) { throw "apksigner base failed" }

    $script:FinalParts = @($script:FinalBase)
    $tmp = Join-Path $BuildDir "apks"
    foreach ($split in @("split_config.arm64_v8a.apk", "split_config.xxhdpi.apk", "split_config.ru.apk")) {
        $src = Join-Path $tmp $split
        if (-not (Test-Path -LiteralPath $src)) { continue }
        Write-Step "split $split"
        $name = [System.IO.Path]::GetFileNameWithoutExtension($split)
        $p = Join-Path $BuildDir "p_$name.apk"
        $a = @($src, $p, $Package, $OutPackage)
        if ($split -eq "split_config.arm64_v8a.apk") {
            $a += "lib/arm64-v8a/libvkcore.so=$(Join-Path $script:SplitDir 'arm64\lib\arm64-v8a\libvkcore.so')"
        }
        & python (Join-Path $Root "axml_rename.py") @a
        if ($LASTEXITCODE -ne 0) { throw "axml_rename failed for $split" }
        $al = "$p.aligned"
        & (Join-Path $BuildTools "zipalign.exe") -f -p 4 $p $al | Out-Null
        $final = Join-Path $BuildDir "final_$name.apk"
        & (Join-Path $BuildTools "apksigner.bat") sign --ks $Keystore --ks-key-alias $KeyAlias --ks-pass "pass:$KsPass" --key-pass "pass:$KsPass" --v2-signing-enabled true --v3-signing-enabled true --out $final $al | Out-Null
        Remove-Item -LiteralPath $p, $al -Force
        $script:FinalParts += $final
    }
}

function Invoke-Install {
    Write-Step "install-multiple"
    $text = (& adb install-multiple -r @script:FinalParts 2>&1 | Out-String)
    Write-Host $text.Trim()
    if ($LASTEXITCODE -ne 0) { throw "install failed" }
    if ($NoLaunch) { return }
    & adb shell am force-stop $OutPackage
    & adb logcat -b all -c
    & adb shell am start -W -n "$OutPackage/$Activity"
    Start-Sleep -Seconds $WaitSeconds
    $pid = (& adb shell pidof $OutPackage 2>$null | Out-String).Trim()
    if ($pid) { Write-Host "process alive pid $pid" -ForegroundColor Green }
    else { Write-Host "process dead" -ForegroundColor Red }
}

if ($Pull) { Invoke-Pull }
if ($Build) {
    Invoke-Unpack
    Invoke-Patch
    Invoke-Build
}
if ($Install) { Invoke-Install }
[CmdletBinding()]
param(
    [ValidateSet("side", "samepkg")]
    [string]$Variant = "side",
    [switch]$Build,
    [switch]$Fresh,
    [switch]$NoLaunch,
    [switch]$Trace,
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
$Activity = "com.vk.music.screens.main.MainActivity"

$Target = switch ($Variant) {
    "side" {
        [pscustomobject]@{
            Variant  = "side"
            Package  = "com.uma.musicvk.patched"
            Work     = Join-Path $Root "work"
            Apk      = Join-Path $Root "VK Музыка_8.44_patched.apk"
        }
    }
    "samepkg" {
        [pscustomobject]@{
            Variant  = "samepkg"
            Package  = "com.uma.musicvk"
            Work     = Join-Path $Root "work_samepkg"
            Apk      = Join-Path $Root "VK Музыка_8.44_patched_samepkg.apk"
        }
    }
}

function Write-Step {
    param([string]$Text)
    Write-Host "== $Text" -ForegroundColor Cyan
}

function Get-Device {
    $devices = @(& adb devices | Select-Object -Skip 1 | Where-Object { $_ -match "\sdevice$" })
    if ($devices.Count -eq 0) {
        Write-Host "device not found" -ForegroundColor Red
        $mdns = @(& adb mdns services 2>$null | Where-Object { $_ -match "_adb-tls-connect" })
        if ($mdns.Count -gt 0) {
            Write-Host "mdns endpoints:" -ForegroundColor Yellow
            $mdns | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
        }
        throw "no adb device"
    }
    return $devices[0].Split("`t")[0]
}

function Invoke-AppBuild {
    param([string]$WorkDir, [string]$Package, [bool]$WithTrace)

    if (-not (Test-Path -LiteralPath $WorkDir)) {
        throw "missing work dir: $WorkDir"
    }
    $unsigned = Join-Path $Root "build\unsigned.apk"
    $aligned = Join-Path $Root "build\aligned.apk"
    New-Item -ItemType Directory -Path (Join-Path $Root "build") -Force | Out-Null

    Write-Step "patch subscription"
    & python (Join-Path $Root "patch_subscription.py") (Split-Path -Leaf $WorkDir)
    if ($LASTEXITCODE -ne 0) { throw "patch_subscription failed" }

    Write-Step "patch migration"
    & python (Join-Path $Root "patch_migration.py") (Split-Path -Leaf $WorkDir)
    if ($LASTEXITCODE -ne 0) { throw "patch_migration failed" }

    if ($WithTrace) {
        Write-Step "patch trace"
        & python (Join-Path $Root "patch_trace.py") (Split-Path -Leaf $WorkDir) $Package
        if ($LASTEXITCODE -ne 0) { throw "patch_trace failed" }
    }
    else {
        & python (Join-Path $Root "patch_trace.py") (Split-Path -Leaf $WorkDir) --clean | Out-Null
    }

    Write-Step "patch native"
    & python (Join-Path $Root "patch_native.py") (Split-Path -Leaf $WorkDir)
    if ($LASTEXITCODE -ne 0) { throw "patch_native failed" }

    Write-Step "apktool build"
    & java -Xmx5g "-Duser.language=en" "-Dfile.encoding=UTF8" -jar $ApkToolJar b $WorkDir -o $unsigned
    if ($LASTEXITCODE -ne 0) { throw "apktool build failed" }

    Write-Step "zipalign"
    & (Join-Path $BuildTools "zipalign.exe") -f -p 4 $unsigned $aligned
    if ($LASTEXITCODE -ne 0) { throw "zipalign failed" }

    Write-Step "apksigner"
    & (Join-Path $BuildTools "apksigner.bat") sign --ks $Keystore --ks-key-alias $KeyAlias --ks-pass "pass:$KeyPass" --key-pass "pass:$KeyPass" --v2-signing-enabled true --v3-signing-enabled true --out $Target.Apk $aligned
    if ($LASTEXITCODE -ne 0) { throw "apksigner failed" }

    Write-Step "verify patch"
    & python (Join-Path $Root "verify_patch.py") $Target.Apk
    if ($LASTEXITCODE -ne 0) { throw "verify_patch failed" }

    Remove-Item -LiteralPath $unsigned, $aligned -Force
}

function Install-Apk {
    param([string]$Apk, [string]$Package, [bool]$Fresh)

    Write-Step "install"
    if ($Fresh) {
        & adb uninstall $Package | Out-Null
        $text = (& adb install $Apk 2>&1 | Out-String)
        Write-Host $text.Trim()
        if ($LASTEXITCODE -ne 0) { throw "install failed" }
        return
    }

    $text = (& adb install -r $Apk 2>&1 | Out-String)
    Write-Host $text.Trim()
    if ($LASTEXITCODE -eq 0) { return }
    if ($text -notmatch "UPDATE_INCOMPATIBLE") { throw "install failed" }

    Write-Step "signature mismatch, uninstall $Package and retry"
    & adb uninstall $Package | Out-Null
    $text = (& adb install $Apk 2>&1 | Out-String)
    Write-Host $text.Trim()
    if ($LASTEXITCODE -ne 0) { throw "install failed after uninstall" }
}

function Start-App {
    param([string]$Package)

    Write-Step "launch"
    & adb shell am force-stop $Package
    & adb logcat -b all -c
    & adb shell am start -W -n "$Package/$Activity"
    Start-Sleep -Seconds $WaitSeconds
}

function Save-Artifacts {
    param([string]$Package, [string]$Directory, [string]$Stamp, [bool]$WithTrace)

    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $remote = "/sdcard/vk_debug_$Stamp.png"
    & adb shell screencap -p $remote | Out-Null
    $screenshot = Join-Path $Directory "screen-$Stamp.png"
    & adb pull $remote $screenshot | Out-Null
    & adb shell rm -f $remote | Out-Null

    $logcat = Join-Path $Directory "logcat-$Stamp.log"
    & adb logcat -b all -d -v time | Out-File -FilePath $logcat -Encoding utf8

    $exitInfo = Join-Path $Directory "exit-info-$Stamp.txt"
    & adb shell dumpsys activity exit-info $Package 2>&1 | Out-File -FilePath $exitInfo -Encoding utf8

    $result = [pscustomobject]@{
        Screenshot = $screenshot
        Logcat     = $logcat
        ExitInfo   = $exitInfo
        Trace      = $null
    }

    if ($WithTrace) {
        $remoteTrace = "/sdcard/Android/data/$Package/files/trace.txt"
        $trace = Join-Path $Directory "trace-$Stamp.txt"
        & adb pull $remoteTrace $trace 2>&1 | Out-Null
        $result.Trace = $trace
    }

    return $result
}

function Show-Status {
    param([string]$Package, [string]$Directory, [string]$Stamp, [bool]$WithTrace)

    $procId = (& adb shell pidof $Package 2>$null | Out-String).Trim()
    $top = (& adb shell dumpsys activity activities 2>$null | Select-String "topResumedActivity" | Select-Object -First 1)

    Write-Step "status"
    if ($procId) {
        Write-Host "process: alive, pid $procId" -ForegroundColor Green
    }
    else {
        Write-Host "process: dead" -ForegroundColor Red
    }
    if ($top) {
        Write-Host "top: $($top.Line.Trim())" -ForegroundColor Yellow
    }

    Write-Step "exit info"
    & adb shell dumpsys activity exit-info $Package 2>&1 |
        Select-String "timestamp=|reason=" |
        Select-Object -First 6 |
        ForEach-Object { Write-Host "  $($_.Line.Trim())" }

    $artifacts = Save-Artifacts -Package $Package -Directory $Directory -Stamp $Stamp -WithTrace $WithTrace

    Write-Step "artifacts"
    Write-Host "  screen:    $($artifacts.Screenshot)"
    Write-Host "  logcat:    $($artifacts.Logcat)"
    Write-Host "  exit-info: $($artifacts.ExitInfo)"
    if ($artifacts.Trace) {
        Write-Host "  trace:     $($artifacts.Trace)"
    }

    if ($artifacts.Trace -and (Test-Path -LiteralPath $artifacts.Trace)) {
        Write-Step "trace"
        Get-Content -LiteralPath $artifacts.Trace -Encoding utf8 |
            Select-Object -First 12 |
            ForEach-Object { Write-Host "  $_" -ForegroundColor Magenta }
    }

    Write-Step "log highlights"
    $lines = Get-Content -LiteralPath $artifacts.Logcat -Encoding utf8
    $hits = $lines | Select-String -Pattern "VerifyError|AndroidRuntime|FATAL|Exception|ERROR|musicvk|uma.musicvk" | Select-Object -First 40
    if ($hits) {
        $hits | ForEach-Object { Write-Host "  $($_.Line)" -ForegroundColor DarkGray }
    }
    else {
        Write-Host "  no app lines in logcat" -ForegroundColor DarkGray
    }
}

$device = Get-Device
Write-Host "device: $device" -ForegroundColor Green
Write-Host "variant: $($Target.Variant), package: $($Target.Package)" -ForegroundColor Green

if ($Build) {
    Invoke-AppBuild -WorkDir $Target.Work -Package $Target.Package -WithTrace $Trace.IsPresent
}
elseif (-not (Test-Path -LiteralPath $Target.Apk)) {
    throw "missing apk: $($Target.Apk), run with -Build"
}

Install-Apk -Apk $Target.Apk -Package $Target.Package -Fresh $Fresh

if ($NoLaunch) {
    return
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if ($Trace) {
    & adb shell mkdir -p "/sdcard/Android/data/$($Target.Package)/files" | Out-Null
    & adb shell rm -f "/sdcard/Android/data/$($Target.Package)/files/trace.txt" | Out-Null
}
Start-App -Package $Target.Package
Show-Status -Package $Target.Package -Directory (Join-Path $Root $LogDir) -Stamp $stamp -WithTrace $Trace.IsPresent

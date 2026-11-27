#requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$NoBuild,
    [switch]$NoInstall,
    [switch]$Force,
    [switch]$NoLaunch,
    [switch]$RegisterTask,
    [switch]$UnregisterTask,
    [switch]$SetPassword,
    [switch]$SetCodebergToken,
    [switch]$Publish,
    [switch]$DraftRelease,
    [string]$CodebergRepo = "DanyaVoredom/VK",
    [string]$CodebergApi = "https://codeberg.org/api/v1",
    [string]$CodebergToken = $env:CODEBERG_TOKEN,
    [string]$CodebergTokenFile = "",
    [string]$TaskName = "VKMusicModAutoUpdate",
    [string]$TaskTime = "10:00",
    [string]$SourcePage = "https://norobot.ru/vk-music/",
    [string]$ApkUrl = "",
    [string]$ExpectedVersion = "",
    [string]$DownloadDir = "",
    [string]$BuildTools = "C:\Android\Sdk\build-tools\36.1.0",
    [string]$ApkToolJar = "C:\Windows\apktool.jar",
    [string]$KeyAlias = "vkmpatch",
    [string]$ModRevision = $env:VKM_MOD_REVISION,
    [string]$Package = "com.uma.musicvk",
    [string]$PatchedPackage = "com.uma.musicvk.patched",
    [string]$SignerSha256 = "59f04db2cce0467ef340ba22aeddebb49b6be80bb2be6fa6982467358fcdcc5a",
    [string]$KsPass = $env:VKM_KS_PASS,
    [string]$KsPassFile = "",
    [int]$DownloadRetries = 3,
    [int]$WaitDeviceSeconds = 0
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
if (-not $DownloadDir) { $DownloadDir = $Root }
if (-not $KsPassFile) { $KsPassFile = Join-Path $Root "patch.kspass" }
if (-not $CodebergTokenFile) { $CodebergTokenFile = Join-Path $Root "codeberg.token" }
$LogDir = Join-Path $Root "logs"
$LogPath = Join-Path $LogDir "update.log"
$BuildDir = Join-Path $Root "build"
$BuiltApk = Join-Path $BuildDir "VK_Music_patched.apk"
if (-not $ModRevision) { $ModRevision = "0" }
if ($ModRevision -notmatch "^\d+$") { throw "ModRevision must be an integer" }

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $DownloadDir -Force | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line -Encoding utf8
}

function Get-ToolPath {
    param([string]$Name)
    if ($IsWindows) { return (Join-Path $BuildTools "$Name.exe") }
    return (Join-Path $BuildTools $Name)
}

function Get-ApkInfo {
    param([string]$Path)
    $aapt = Get-ToolPath "aapt"
    if (-not (Test-Path -LiteralPath $aapt)) { throw "aapt not found: $aapt" }
    $badging = & $aapt dump badging $Path 2>$null
    if ($LASTEXITCODE -ne 0) { throw "aapt failed for $Path" }
    $line = $badging | Where-Object { $_ -like "package:*" } | Select-Object -First 1
    if (-not $line) { throw "aapt did not report package metadata for $Path" }
    $match = [regex]::Match($line, "name='([^']+)'\s+versionCode='([^']+)'\s+versionName='([^']+)'")
    if (-not $match.Success) { throw "cannot parse aapt output for $Path" }
    return [pscustomobject]@{
        Package = $match.Groups[1].Value
        VersionCode = [int]$match.Groups[2].Value
        VersionName = $match.Groups[3].Value
    }
}

function Get-ApkSigner {
    param([string]$Path)
    $apksigner = Get-ToolPath "apksigner"
    if (-not (Test-Path -LiteralPath $apksigner)) { throw "apksigner not found: $apksigner" }
    $output = & $apksigner verify --print-certs $Path 2>&1
    if ($LASTEXITCODE -ne 0) { throw "apksigner rejected $Path" }
    $text = $output -join "`n"
    $match = [regex]::Match($text, "Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]+)")
    if (-not $match.Success) { throw "cannot read signer certificate from $Path" }
    return $match.Groups[1].Value.ToLowerInvariant()
}

function Get-TargetRelease {
    if ($ApkUrl) {
        $version = $ExpectedVersion
        if (-not $version) {
            $match = [regex]::Match($ApkUrl, "VK[-_]Music[-_]([0-9]+(?:\.[0-9]+)+)")
            if ($match.Success) { $version = $match.Groups[1].Value }
        }
        if (-not $version) { throw "pass -ExpectedVersion when -ApkUrl has no version" }
        return [pscustomobject]@{ Version = $version; Url = $ApkUrl }
    }

    Write-Log "check $SourcePage"
    $response = Invoke-WebRequest -Uri $SourcePage -UseBasicParsing -TimeoutSec 60 -Headers @{
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"
        "Cache-Control" = "no-cache"
    }
    $html = [string]$response.Content

    $versionMatch = [regex]::Match($html, "Версия:\s*([0-9]+(?:\.[0-9]+)+)")
    if (-not $versionMatch.Success) { throw "cannot find version on $SourcePage" }
    $version = $versionMatch.Groups[1].Value
    if ($ExpectedVersion -and $version -ne $ExpectedVersion) {
        throw "source reports $version, expected $ExpectedVersion"
    }

    $urlMatch = [regex]::Match($html, "https://files\.norobot\.ru/VK-Music-([0-9]+(?:\.[0-9]+)+)\.apk")
    if ($urlMatch.Success) {
        $urlVersion = $urlMatch.Groups[1].Value
        if ($urlVersion -ne $version) {
            throw "source page has version $version but APK URL has $urlVersion"
        }
        $url = $urlMatch.Value
    }
    else {
        $url = "https://files.norobot.ru/VK-Music-$version.apk"
    }
    return [pscustomobject]@{ Version = $version; Url = $url }
}

function Invoke-Download {
    param([string]$Url, [string]$Path)
    $part = "$Path.part"
    for ($attempt = 1; $attempt -le $DownloadRetries; $attempt++) {
        try {
            Write-Log "download $Url (attempt $attempt/$DownloadRetries)"
            Invoke-WebRequest -Uri $Url -OutFile $part -UseBasicParsing -TimeoutSec 900
            Move-Item -LiteralPath $part -Destination $Path -Force
            Write-Log "saved $Path"
            return
        }
        catch {
            Remove-Item -LiteralPath $part -Force -ErrorAction SilentlyContinue
            if ($attempt -eq $DownloadRetries) { throw }
            Start-Sleep -Seconds (5 * $attempt)
        }
    }
}

function Test-DeviceConnected {
    $adb = Get-Command adb -ErrorAction SilentlyContinue
    if (-not $adb) { return $false }
    $output = & $adb.Source devices 2>$null
    return [bool]($output -match "(?m)\tdevice\s*$")
}

function Wait-ForDevice {
    if (Test-DeviceConnected) { return $true }
    if ($WaitDeviceSeconds -le 0) { return $false }
    $deadline = (Get-Date).AddSeconds($WaitDeviceSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        if (Test-DeviceConnected) { return $true }
    }
    return $false
}

function Get-InstalledVersionCode {
    if (-not (Test-DeviceConnected)) { return $null }
    $adb = Get-Command adb -ErrorAction SilentlyContinue
    $dump = & $adb.Source shell dumpsys package $PatchedPackage 2>$null
    $match = [regex]::Match(($dump -join "`n"), "versionCode=(\d+)")
    if ($match.Success) { return [int]$match.Groups[1].Value }
    return $null
}

function Read-KsPassword {
    if (-not (Test-Path -LiteralPath $KsPassFile)) { return "" }
    if (-not $IsWindows) { throw "encrypted password file is supported only on Windows" }
    $encrypted = Get-Content -Raw -LiteralPath $KsPassFile
    $secure = ConvertTo-SecureString $encrypted
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Read-CodebergToken {
    if (-not (Test-Path -LiteralPath $CodebergTokenFile)) { return "" }
    if (-not $IsWindows) { throw "encrypted token file is supported only on Windows" }
    $encrypted = Get-Content -Raw -LiteralPath $CodebergTokenFile
    $secure = ConvertTo-SecureString $encrypted
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Invoke-BuildPatch {
    param([string]$ApkPath)
    $script = Join-Path $Root "build_patch.ps1"
    $pwshPath = if ($IsWindows) { Join-Path $PSHOME "pwsh.exe" } else { (Get-Command pwsh).Source }
    $arguments = @(
        "-NoProfile", "-File", $script, "-Apk", $ApkPath, "-Build",
        "-BuildTools", $BuildTools, "-ApkToolJar", $ApkToolJar, "-KeyAlias", $KeyAlias
    )
    if (-not $NoInstall) { $arguments += "-Install" }
    if ($NoLaunch) { $arguments += "-NoLaunch" }
    Write-Log ("run build_patch: " + ($arguments -join " "))
    & $pwshPath @arguments
    if ($LASTEXITCODE -ne 0) { throw "build_patch failed with exit code $LASTEXITCODE" }
}

function Write-ReleaseMetadata {
    param([pscustomobject]$Info, [string]$ApkPath)
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
    $assetName = "VK_Music_$($Info.VersionName)_patched.apk"
    $releaseApk = Join-Path $BuildDir $assetName
    Copy-Item -LiteralPath $ApkPath -Destination $releaseApk -Force
    $hash = (Get-FileHash -LiteralPath $releaseApk -Algorithm SHA256).Hash.ToLowerInvariant()
    $commit = $env:GITHUB_SHA
    if (-not $commit) {
        try { $commit = (& git -C $Root rev-parse HEAD 2>$null | Out-String).Trim() } catch { $commit = "" }
    }
    $metadata = [ordered]@{
        versionName = $Info.VersionName
        versionCode = $Info.VersionCode
        modRevision = [int]$ModRevision
        apk = $assetName
        sha256 = $hash
        size = (Get-Item -LiteralPath $releaseApk).Length
        commit = $commit
    }
    $path = Join-Path $BuildDir "update.json"
    $metadata | ConvertTo-Json | Set-Content -LiteralPath $path -Encoding utf8
    Write-Log "release metadata: $path"
}

function Publish-CodebergRelease {
    if (-not $CodebergToken) { $CodebergToken = Read-CodebergToken }
    if (-not $CodebergToken) { throw "set CODEBERG_TOKEN or run -SetCodebergToken" }
    $metaPath = Join-Path $BuildDir "update.json"
    if (-not (Test-Path -LiteralPath $metaPath)) { throw "missing $metaPath" }
    $meta = Get-Content -Raw -LiteralPath $metaPath | ConvertFrom-Json
    $tag = "vk-$($meta.versionName)-$($meta.modRevision)"
    $base = "$CodebergApi/repos/$CodebergRepo/releases"
    $headers = @{
        Authorization = "token $CodebergToken"
        "User-Agent" = "vk-music-patcher"
    }
    $existing = Invoke-WebRequest -Method Get -Uri "$base/tags/$tag" -Headers $headers -SkipHttpErrorCheck
    if ($existing.StatusCode -eq 200) {
        Write-Log "release $tag already exists"
        return
    }
    $body = [ordered]@{
        tag_name = $tag
        target_commitish = $meta.commit
        name = "VK Music $($meta.versionName) mod $($meta.modRevision)"
        body = "VK Music $($meta.versionName), mod revision $($meta.modRevision), commit $($meta.commit)"
        draft = [bool]$DraftRelease
        prerelease = $false
    } | ConvertTo-Json
    Write-Log "create release $tag"
    $release = Invoke-RestMethod -Method Post -Uri $base -Headers $headers -ContentType "application/json" -Body $body
    $releaseId = $release.id
    if (-not $releaseId) { throw "release id missing" }
    foreach ($file in @((Join-Path $BuildDir $meta.apk), $metaPath)) {
        $name = Split-Path -Leaf $file
        $uri = "$base/$releaseId/assets?name=$([uri]::EscapeDataString($name))"
        Write-Log "upload $name"
        Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Form @{ attachment = Get-Item -LiteralPath $file } | Out-Null
    }
    Write-Log "published $tag"
}

function Install-BuiltApk {
    $adb = Get-Command adb -ErrorAction SilentlyContinue
    if (-not $adb) { throw "adb not found" }
    Write-Log "install $BuiltApk"
    $output = & $adb.Source install -r $BuiltApk 2>&1
    Write-Host ($output -join "`n")
    if ($LASTEXITCODE -ne 0) { throw "adb install failed" }
}

if ($SetPassword) {
    if (-not $IsWindows) { throw "-SetPassword is supported only on Windows" }
    $secure = Read-Host "Keystore password" -AsSecureString
    $secure | ConvertFrom-SecureString | Set-Content -LiteralPath $KsPassFile -NoNewline -Encoding utf8
    Write-Log "password saved to $KsPassFile"
    return
}

if ($SetCodebergToken) {
    if (-not $IsWindows) { throw "-SetCodebergToken is supported only on Windows" }
    $secure = Read-Host "Codeberg token" -AsSecureString
    $secure | ConvertFrom-SecureString | Set-Content -LiteralPath $CodebergTokenFile -NoNewline -Encoding utf8
    Write-Log "token saved to $CodebergTokenFile"
    return
}

if ($UnregisterTask) {
    if (-not $IsWindows) { throw "-UnregisterTask is supported only on Windows" }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Log "task removed: $TaskName"
    return
}

if ($RegisterTask) {
    if (-not $IsWindows) { throw "-RegisterTask is supported only on Windows" }
    $at = [datetime]::ParseExact($TaskTime, "HH:mm", $null)
    $pwshPath = Join-Path $PSHOME "pwsh.exe"
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -NoLaunch"
    if ($NoInstall) { $arguments += " -NoInstall" }
    if ($Publish) { $arguments += " -Publish" }
    $action = New-ScheduledTaskAction -Execute $pwshPath -Argument $arguments -WorkingDirectory $Root
    $trigger = New-ScheduledTaskTrigger -Daily -At $at
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
        -Description "VK Music mod auto-update" -Force | Out-Null
    Write-Log "task registered: $TaskName at $TaskTime"
    return
}

$release = Get-TargetRelease
Write-Log "latest source version: $($release.Version)"

$apkPath = Join-Path $DownloadDir "VK_Music_$($release.Version).apk"
if ((Test-Path -LiteralPath $apkPath) -and -not $Force) {
    Write-Log "cached $apkPath"
}
else {
    if ((Test-Path -LiteralPath $apkPath) -and $Force) {
        Remove-Item -LiteralPath $apkPath -Force
    }
    Invoke-Download -Url $release.Url -Path $apkPath
}

$info = Get-ApkInfo $apkPath
if ($info.Package -ne $Package) {
    throw "unexpected package $($info.Package), expected $Package"
}
if ($info.VersionName -ne $release.Version) {
    throw "APK version $($info.VersionName), expected $($release.Version)"
}
$signer = Get-ApkSigner $apkPath
if ($signer -ne $SignerSha256.ToLowerInvariant()) {
    throw "unexpected signer $signer"
}
Write-Log "verified $Package $($info.VersionName) versionCode $($info.VersionCode)"

$installedCode = Get-InstalledVersionCode
if ($null -ne $installedCode -and $installedCode -ge $info.VersionCode -and -not $Force) {
    Write-Log "up to date: installed versionCode $installedCode"
    return
}
if ($CheckOnly) {
    if ($null -eq $installedCode) {
        Write-Log "target ready: $($info.VersionName) versionCode $($info.VersionCode), installed version unknown"
    }
    else {
        Write-Log "update available: $($info.VersionName) versionCode $($info.VersionCode)"
    }
    return
}
if (-not $NoInstall) {
    if (-not (Wait-ForDevice)) { throw "no adb device connected" }
    if ($null -ne $installedCode) {
        Write-Log "installed versionCode $installedCode, target $($info.VersionCode)"
    }
    else {
        Write-Log "patched package is not installed, target $($info.VersionCode)"
    }
}

if ($NoBuild) {
    if (-not (Test-Path -LiteralPath $BuiltApk)) { throw "missing built APK: $BuiltApk" }
    $built = Get-ApkInfo $BuiltApk
    if ($built.VersionCode -lt $info.VersionCode) {
        throw "built APK versionCode $($built.VersionCode) is older than $($info.VersionCode)"
    }
    Write-Log "using existing $BuiltApk"
    Write-ReleaseMetadata -Info $built -ApkPath $BuiltApk
    if ($Publish) { Publish-CodebergRelease }
    if (-not $NoInstall) { Install-BuiltApk }
    return
}

if (-not $KsPass) { $KsPass = Read-KsPassword }
if (-not $KsPass) { throw "set VKM_KS_PASS or run -SetPassword" }
$env:VKM_KS_PASS = $KsPass
$env:VKM_MOD_REVISION = $ModRevision

Invoke-BuildPatch -ApkPath $apkPath
Write-ReleaseMetadata -Info $info -ApkPath $BuiltApk
if ($Publish) { Publish-CodebergRelease }
Write-Log "update finished: $($info.VersionName) versionCode $($info.VersionCode) modRevision $ModRevision"

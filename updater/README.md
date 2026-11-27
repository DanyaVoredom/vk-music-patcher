# Updater

`UpdateChecker.java` is the in-app update checker. It queries the latest GitHub release, compares `versionCode` and `modRevision`, downloads the release APK, verifies its SHA-256, and opens the package installer through the existing `<package>.fileprovider`.

The build does not compile Java. `vk_updater.py` copies the prebuilt smali from `updater/smali`, writes `res/values/vk_mod_revision.xml`, adds the install permission, and injects the call into `MainActivity.onCreate`.

## Regenerate smali

Use Android build-tools with `d8` and `baksmali` 2.5+:

```bash
SDK=/home/danypc/Android/Sdk
rm -rf /tmp/updater && mkdir -p /tmp/updater/classes /tmp/updater/dex /tmp/updater/smali
javac -source 8 -target 8 -encoding UTF-8 \
  -classpath "$SDK/platforms/android-36/android.jar" \
  -d /tmp/updater/classes updater/src/com/vk/music/updater/UpdateChecker.java
"$SDK/build-tools/36.1.0/d8" --min-api 28 \
  --lib "$SDK/platforms/android-36/android.jar" \
  --output /tmp/updater/dex $(find /tmp/updater/classes -name '*.class')
baksmali d /tmp/updater/dex/classes.dex -o /tmp/updater/smali
rm -rf updater/smali/com/vk/music/updater
mkdir -p updater/smali/com/vk/music/updater
cp /tmp/updater/smali/com/vk/music/updater/*.smali updater/smali/com/vk/music/updater/
```

The repository slug is substituted from `VKM_UPDATE_REPO` at build time. Local builds default to `FANATFANATA/vk-music-patcher`.

## Release manifest

The updater expects the latest release to contain `update.json`:

```json
{
  "versionName": "8.53",
  "versionCode": 15193,
  "modRevision": 123,
  "apk": "VK_Music_8.53_patched.apk",
  "sha256": "..."
}
```

`sha256` is checked before the installer is opened. The package installer then enforces the signing certificate match.

# Repository guidance

- This is a Windows PowerShell APK patching pipeline, not a Gradle project. `build_patch.ps1` orchestrates pulling split APKs, unpacking, patching, rebuilding, signing, and optional installation.
- Keep the project on the single `main` branch; there is no deployment target.
- Resolve smali targets from the exact APK being patched. `vk_targets.py` uses `.source` filenames and method signatures because obfuscated class names change between app versions.
- `patch_native.py` contains ABI-specific offsets and expected bytes. Derive and verify them against the matching APK's native libraries; never carry offsets forward without checking.
- The build script expects Windows, PowerShell 7+, JDK 21+, Python 3.10+, apktool, Android build-tools, `adb`, and `rg`. Tool paths are configured in `build_patch.ps1`.
- Set `VKM_KS_PASS` and provide a local `patch.keystore` for signing. Never commit keystores or passwords.
- `update_mod.ps1` is the PC auto-update entry point: it reads the latest version from the configured source page, validates package/versionCode and the pinned official signer, then calls `build_patch.ps1` for build and adb install. Scheduled tasks use a DPAPI-encrypted `patch.kspass`, which is gitignored.
- `updater/src/com/vk/music/updater/UpdateChecker.java` is the in-app updater. Builds use the prebuilt smali in `updater/smali`; after Java changes regenerate it as described in `updater/README.md`. `vk_updater.py` copies it, writes `res/values/vk_mod_revision.xml`, adds `REQUEST_INSTALL_PACKAGES`, and injects the call into `MainActivity.onCreate`.
- Primary release path is Codeberg: `.forgejo/workflows/build-release.yml` runs daily at 00:00 MSK on the local `self-hosted` Forgejo runner, compares upstream with `vk-` tags, builds with `update_mod.ps1`, and publishes the APK plus `update.json` to GitHub `DanyaVoredom/DanyExternal-Releases`. Codeberg secrets: `GH_RELEASES_TOKEN`, `VKM_KS_BASE64`, `VKM_KS_PASS`, optional `VKM_KS_ALIAS`. Codeberg Releases are not used because of the asset quota.
- `.github/workflows/build-release.yml` is preserved as a GitHub Actions alternative on `windows-latest`; it also publishes to `DanyaVoredom/DanyExternal-Releases` and needs a `RELEASES_TOKEN` secret. The in-app updater filters releases by the `vk-` tag prefix so unrelated releases in the shared releases repository are ignored.
- `build_patch.ps1` accepts `-ApkToolJar`, `-BuildTools`, and `-KeyAlias` so CI can use runner-provided tools.
- Before changing version-specific patches, inspect the target APK and update the patch and verification definitions together. `verify_patch.py` encodes expected DEX classes and methods; `verify_package.py` currently has APK paths in its source.
- Current targets and native offsets are verified against VK Music 8.53 (versionCode 15193). Recheck them for every new APK instead of assuming they still apply.
- CI on `main` runs `python -m compileall -q .` and parses every `.ps1` file with PowerShell. Full build and install checks require the Windows Android toolchain, a matching APK, a device or emulator, and the local signing keystore.

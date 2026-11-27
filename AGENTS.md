# Repository guidance

- This is a Windows PowerShell APK patching pipeline, not a Gradle project. `build_patch.ps1` orchestrates pulling split APKs, unpacking, patching, rebuilding, signing, and optional installation.
- Keep the project on the single `main` branch; there is no deployment target.
- Resolve smali targets from the exact APK being patched. `vk_targets.py` uses `.source` filenames and method signatures because obfuscated class names change between app versions.
- `patch_native.py` contains ABI-specific offsets and expected bytes. Derive and verify them against the matching APK's native libraries; never carry offsets forward without checking.
- The build script expects Windows, PowerShell 7+, JDK 21+, Python 3.10+, apktool, Android build-tools, `adb`, and `rg`. Tool paths are configured in `build_patch.ps1`.
- Set `VKM_KS_PASS` and provide a local `patch.keystore` for signing. Never commit keystores or passwords.
- Before changing version-specific patches, inspect the target APK and update the patch and verification definitions together. `verify_patch.py` encodes expected DEX classes and methods; `verify_package.py` currently has APK paths in its source.
- Current targets and native offsets are verified against VK Music 8.53 (versionCode 15193). Recheck them for every new APK instead of assuming they still apply.
- CI on `main` runs `python -m compileall -q .` and parses every `.ps1` file with PowerShell. Full build and install checks require the Windows Android toolchain, a matching APK, a device or emulator, and the local signing keystore.

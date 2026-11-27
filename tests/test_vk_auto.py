from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vk_auto


def write_class(
    work: Path,
    relative: str,
    declaration: str,
    source: str,
    methods: list[tuple[str, str]],
    implements: str | None = None,
) -> None:
    path = work / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [declaration, f'.source "{source}"']
    if implements:
        lines.append(f".implements {implements}")
    for header, body in methods:
        lines.append(f".method {header}")
        lines.extend(body.strip("\n").split("\n"))
        lines.append(".end method")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def bool_body(value: int) -> str:
    return f"    .locals 1\n\n    const/4 v0, 0x{value:x}\n\n    return v0"


def long_body() -> str:
    return "    .locals 2\n\n    const-wide/16 v0, 0x0\n\n    return-wide v0"


def build_fixture(work: Path) -> None:
    write_class(
        work,
        "smali/test/Provider.smali",
        ".class public abstract interface Ltest/Provider;",
        "MusicSubscriptionProvider.kt",
        [
            ("public abstract b()Z", ""),
            ("public abstract e()J", ""),
        ],
    )
    write_class(
        work,
        "smali/test/Impl.smali",
        ".class public final Ltest/Impl;",
        "MusicSubscriptionProviderImpl.kt",
        [
            ("public final b()Z", bool_body(0)),
            ("public final e()J", long_body()),
        ],
        implements="Ltest/Provider;",
    )
    write_class(
        work,
        "smali/test/Stub.smali",
        ".class public final Ltest/Stub;",
        "MusicSubscriptionProvider.kt",
        [
            ("public final b()Z", bool_body(0)),
            ("public final e()J", long_body()),
        ],
        implements="Ltest/Provider;",
    )
    write_class(
        work,
        "smali/test/Account.smali",
        ".class public final Ltest/Account;",
        "CurrentAccountInformation.kt",
        [
            (
                "public constructor <init>(ZJ)V",
                """
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-boolean p1, p0, Ltest/Account;->a:Z

    iput-wide p2, p0, Ltest/Account;->b:J

    return-void
""",
            )
        ],
    )
    write_class(
        work,
        "smali/test/Flags.smali",
        ".class public final Ltest/Flags;",
        "ContextFlags.kt",
        [
            (
                "public static final b(I)Z",
                """
    .locals 0

    and-int/lit8 p0, p0, 0x2

    if-eqz p0, :cond_0

    const/4 p0, 0x1

    return p0

    :cond_0
    const/4 p0, 0x0

    return p0
""",
            ),
            (
                "public static final d(I)Z",
                """
    .locals 1

    const/4 v0, 0x1

    and-int/2addr p0, v0

    if-eqz p0, :cond_0

    return v0

    :cond_0
    const/4 p0, 0x0

    return p0
""",
            ),
            (
                "public static final e(I)Z",
                """
    .locals 0

    and-int/lit8 p0, p0, 0x8

    if-eqz p0, :cond_0

    const/4 p0, 0x1

    return p0

    :cond_0
    const/4 p0, 0x0

    return p0
""",
            ),
            (
                "public static final f(I)Z",
                """
    .locals 0

    and-int/lit8 p0, p0, 0x4

    if-eqz p0, :cond_0

    const/4 p0, 0x1

    return p0

    :cond_0
    const/4 p0, 0x0

    return p0
""",
            ),
        ],
    )
    write_class(
        work,
        "smali_classes2/com/vk/dto/music/MusicTrack.smali",
        ".class public final Lcom/vk/dto/music/MusicTrack;",
        "MusicTrack.kt",
        [
            (
                "public final x5()I",
                """
    .locals 1

    iget v0, p0, Lcom/vk/dto/music/MusicTrack;->f:I

    return v0
""",
            ),
            (
                "public final r()Z",
                """
    .locals 1

    iget v0, p0, Lcom/vk/dto/music/MusicTrack;->f:I

    if-eqz v0, :cond_0

    const/4 v0, 0x1

    return v0

    :cond_0
    const/4 v0, 0x0

    return v0
""",
            ),
        ],
    )
    write_class(
        work,
        "smali/test/Player.smali",
        ".class public final Ltest/Player;",
        "PlayerModelImpl.kt",
        [
            (
                "public static B(Ltest/Source;Ljava/util/List;)Z",
                bool_body(1),
            )
        ],
    )
    write_class(
        work,
        "smali/com/vk/toggle/d.smali",
        ".class public final Lcom/vk/toggle/d;",
        "FeaturesHelper.kt",
        [
            (
                "public static z(Z)Z",
                """
    .locals 1

    sget-object v0, Lcom/vk/toggle/features/VideoFeatures;->VIDEO_MUSIC_PLAYER:Lcom/vk/toggle/features/VideoFeatures;

    const/4 v0, 0x0

    return v0
""",
            )
        ],
    )
    write_class(
        work,
        "smali/test/TrackExt.smali",
        ".class public final Ltest/TrackExt;",
        "MusicTrackExt.kt",
        [
            (
                "public static final d(Lcom/vk/dto/music/MusicTrack;)Z",
                """
    .locals 1

    invoke-virtual {p0}, Lcom/vk/dto/music/MusicTrack;->r()Z

    move-result v0

    return v0
""",
            )
        ],
    )
    write_class(
        work,
        "smali/test/Configure.smali",
        ".class public final Ltest/Configure;",
        "MusicConfigureInformationProvider.kt",
        [
            (
                "public final a()Z",
                """
    .locals 1

    const-string v0, "isAudioAdAvailable = "

    const/4 v0, 0x0

    return v0
""",
            )
        ],
    )
    write_class(
        work,
        "smali/test/Callback.smali",
        ".class public final Ltest/Callback;",
        "VkMusicApiCallback.kt",
        [],
    )
    write_class(
        work,
        "smali/test/Callback$1.smali",
        ".class public final Ltest/Callback$1;",
        "VkMusicApiCallback.kt",
        [
            (
                "public final c(Ljava/lang/String;Ltest/User;Ljava/lang/Throwable;Lkotlin/jvm/functions/Function0;)V",
                """
    .locals 1

    const-string v0, "account.unregisterDevice"

    const-string v0, "account.managePushDeviceMulti"

    return-void
""",
            )
        ],
    )
    write_class(
        work,
        "smali/com/vk/core/preference/Preference.smali",
        ".class public final Lcom/vk/core/preference/Preference;",
        "Preference.kt",
        [
            (
                "public static s(Ljava/lang/String;Ljava/lang/String;Lcom/vk/core/preference/Preference$Type;Ljava/lang/Object;)Ltest/Pref;",
                """
    .locals 2

    sget-object v0, Lcom/vk/core/preference/Preference;->o:Ljava/util/concurrent/locks/ReentrantReadWriteLock;

    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock;->readLock()Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;

    move-result-object v0

    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;->lock()V

    invoke-static {p0}, Lcom/vk/core/preference/Preference;->d(Ljava/lang/String;)Landroid/content/SharedPreferences;

    move-result-object v1

    invoke-static {v1, p2, p0, p1, p3}, Lcom/vk/core/preference/Preference;->b(Landroid/content/SharedPreferences;Lcom/vk/core/preference/Preference$Type;Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;)Ltest/Pref;

    move-result-object p0

    return-object p0
""",
            ),
            (
                "public static d(Ljava/lang/String;)Landroid/content/SharedPreferences;",
                """
    .locals 1

    invoke-static {p0}, Lcom/vk/core/preference/Preference;->k(Ljava/lang/String;)Landroid/content/SharedPreferences;

    move-result-object v0

    return-object v0
""",
            ),
            (
                "public static k(Ljava/lang/String;)Landroid/content/SharedPreferences;",
                """
    .locals 1

    const/4 v0, 0x0

    return-object v0
""",
            ),
            (
                "public static b(Landroid/content/SharedPreferences;Lcom/vk/core/preference/Preference$Type;Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;)Ltest/Pref;",
                """
    .locals 1

    const/4 p0, 0x0

    return-object p0
""",
            ),
            (
                "public static final u(Ljava/lang/String;Ljava/lang/String;)V",
                """
    .locals 1

    invoke-static {p0}, Lcom/vk/core/preference/Preference;->d(Ljava/lang/String;)Landroid/content/SharedPreferences;

    move-result-object p0

    invoke-interface {p0, p1}, Landroid/content/SharedPreferences;->contains(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_0

    invoke-interface {p0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p0

    invoke-interface {p0, p1}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    move-result-object p0

    invoke-interface {p0}, Landroid/content/SharedPreferences$Editor;->apply()V

    :cond_0
    return-void
""",
            ),
        ],
    )
    write_class(
        work,
        "smali/test/Scope.smali",
        ".class public final Ltest/Scope;",
        "R8$$SyntheticClass",
        [
            (
                "public final invoke(Ljava/lang/Object;)Ljava/lang/Object;",
                """
    .locals 1

    const-string v0, "encrypted_session_management"

    const-string v0, "plain_session_management"

    const-string v0, "session_management_unencrypted"

    const/4 v0, 0x0

    return-object v0
""",
            )
        ],
    )
    write_class(
        work,
        "smali/test/Migration.smali",
        ".class public final Ltest/Migration;",
        "FromStandalone2UpdateTask.kt",
        [
            (
                "public final invokeSuspend(Ljava/lang/Object;)Ljava/lang/Object;",
                """
    .locals 1

    instance-of p1, p1, Lkotlin/Result$Failure;

    xor-int/2addr p1, v3

    return-object p1
""",
            )
        ],
    )


EXPECTED = {
    "subscription Ltest/Impl; b()Z",
    "subscription Ltest/Impl; e()J",
    "subscription Ltest/Stub; b()Z",
    "subscription Ltest/Stub; e()J",
    "account information constructor",
    "context flag 0x1",
    "context flag 0x2",
    "context flag 0x4",
    "context flag 0x8",
    "MusicTrack f int",
    "MusicTrack f bool",
    "player restriction",
    "video music player",
    "track restriction",
    "audio ad availability",
    "credentials callback",
    "preference session getter",
    "preference session remover",
    "session preference scope",
    "migration force result",
}


class AutoPatchResolveTest(unittest.TestCase):
    def test_resolve_all_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            build_fixture(work)
            result = vk_auto.resolve(work)
            names = {patch.name for patch in result.patches}
            self.assertEqual(20, len(result.patches))
            self.assertEqual(EXPECTED, names)
            manifest = result.manifest()["smali"]
            self.assertEqual(20, len(manifest))
            self.assertTrue(all(entry["class"] and entry["method"] for entry in manifest))


if __name__ == "__main__":
    unittest.main()

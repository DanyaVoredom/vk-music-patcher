from __future__ import annotations

FAR_FUTURE = "0xf4865680L"

BOOL_TRUE = "bool:1"
BOOL_FALSE = "bool:0"
LONG_FAR = "long"
CTOR_ACCOUNT = "ctor_account"
VOID = "void"
SESSION_KEY_PREFS = "session_key_prefs"
SESSION_KEY_REMOVE = "session_key_remove"

TARGETS: list[dict] = [
    {"source": "MusicSubscriptionProviderImpl.kt", "method": ".method public final b()Z", "body": BOOL_TRUE},
    {"source": "MusicSubscriptionProviderImpl.kt", "method": ".method public final e()J", "body": LONG_FAR},
    {"source": "MusicSubscriptionProvider.kt", "method": ".method public final b()Z", "body": BOOL_TRUE},
    {"source": "MusicSubscriptionProvider.kt", "method": ".method public final e()J", "body": LONG_FAR},
    {"source": "CurrentAccountInformation.kt", "method": ".method public constructor <init>(ZJ)V", "body": CTOR_ACCOUNT},
    {"source": "ContextFlags.kt", "method": ".method public static final b(I)Z", "body": BOOL_TRUE},
    {"source": "ContextFlags.kt", "method": ".method public static final d(I)Z", "body": BOOL_FALSE},
    {"source": "ContextFlags.kt", "method": ".method public static final e(I)Z", "body": BOOL_FALSE},
    {"source": "ContextFlags.kt", "method": ".method public static final f(I)Z", "body": BOOL_FALSE},
    {"source": "MusicTrackExt.kt", "method": ".method public static final d(Lcom/vk/dto/music/MusicTrack;)Z", "body": BOOL_FALSE},
    {"source": "MusicConfigureInformationProvider.kt", "method": ".method public final a()Z", "body": BOOL_FALSE},
    {"source": "FeaturesHelper.kt", "method": ".method public static z(Z)Z", "body": BOOL_TRUE},
    {
        "source": "VkMusicApiCallback.kt",
        "method": ".method public final c(Ljava/lang/String;Lcom/vk/dto/common/id/UserId;Ljava/lang/Throwable;Lkotlin/jvm/functions/Function0;)V",
        "body": VOID,
    },
    {
        "source": "Preference.kt",
        "method": ".method public static s(Ljava/lang/String;Ljava/lang/String;Lcom/vk/core/preference/Preference$Type;Ljava/lang/Object;)Lxsna/ktl;",
        "body": SESSION_KEY_PREFS,
    },
    {
        "source": "Preference.kt",
        "method": ".method public static final u(Ljava/lang/String;Ljava/lang/String;)V",
        "body": SESSION_KEY_REMOVE,
    },
]

PLAYER_TARGETS: list[dict] = [
    {"source": "PlayerModelImpl.kt", "method": ".method public static B(Lxsna/o0q;Ljava/util/List;)Z", "body": BOOL_FALSE},
]

MUSICTRACK_TARGETS: list[dict] = [
    {"path": "com/vk/dto/music/MusicTrack.smali", "method": ".method public final x5()I", "body": BOOL_FALSE},
    {"path": "com/vk/dto/music/MusicTrack.smali", "method": ".method public final r()Z", "body": BOOL_FALSE},
]

PREFERENCE_SCOPE = {
    "path": "xsna/ue4.smali",
    "source": "R8$$SyntheticClass",
    "method": ".method public final invoke(Ljava/lang/Object;)Ljava/lang/Object;",
    "old": '"session_management_unencrypted"',
    "new": '"session_management"',
}

MIGRATION = {
    "source": "FromStandalone2UpdateTask.kt",
    "start": "    instance-of p1, p1, Lkotlin/Result$Failure;",
    "end": "    xor-int/2addr p1, v3",
    "replacement": "    const/4 p1, 0x1",
}


def bool_body(value: int) -> str:
    return f"    .locals 1\n\n    const/4 v0, 0x{value:x}\n\n    return v0\n"


def long_body() -> str:
    return f"    .locals 2\n\n    const-wide v0, {FAR_FUTURE}\n\n    return-wide v0\n"


def void_body() -> str:
    return "    .locals 0\n\n    return-void\n"


def session_key_prefs_body(cls: str) -> str:
    return (
        "    .locals 2\n\n"
        f"    sget-object v0, L{cls};->o:Ljava/util/concurrent/locks/ReentrantReadWriteLock;\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock;->readLock()Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;\n\n"
        "    move-result-object v0\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;->lock()V\n\n"
        "    :try_start\n"
        '    const-string v1, "EncryptedPreferenceMeta"\n\n'
        "    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v1\n\n"
        "    if-eqz v1, :scoped\n\n"
        '    const-string v1, "encrypted_key.authorized"\n\n'
        "    invoke-virtual {v1, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v1\n\n"
        "    if-eqz v1, :scoped\n\n"
        '    const-string v1, "plain_session_management"\n\n'
        f"    invoke-static {{v1}}, L{cls};->k(Ljava/lang/String;)Landroid/content/SharedPreferences;\n\n"
        "    move-result-object v1\n\n"
        "    goto :resolved\n\n"
        "    :scoped\n"
        f"    invoke-static {{p0}}, L{cls};->d(Ljava/lang/String;)Landroid/content/SharedPreferences;\n\n"
        "    move-result-object v1\n\n"
        "    :resolved\n"
        f"    invoke-static {{v1, p2, p0, p1, p3}}, L{cls};->b(Landroid/content/SharedPreferences;L{cls}$Type;Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;)Lxsna/ktl;\n\n"
        "    move-result-object p0\n"
        "    :try_end\n"
        "    .catchall {:try_start .. :try_end} :catchall\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;->unlock()V\n\n"
        "    return-object p0\n\n"
        "    :catchall\n"
        "    move-exception p0\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;->unlock()V\n\n"
        "    throw p0\n"
    )


def session_key_remove_body(cls: str) -> str:
    return (
        "    .locals 1\n\n"
        f"    sget-object v0, L{cls}$PreferenceUsingLogger$IOType;->Write:L{cls}$PreferenceUsingLogger$IOType;\n\n"
        f"    sget-object v0, L{cls};->i:Lxsna/z68;\n\n"
        "    invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;\n\n"
        '    const-string v0, "EncryptedPreferenceMeta"\n\n'
        "    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v0\n\n"
        "    if-eqz v0, :scoped\n\n"
        '    const-string v0, "encrypted_key.authorized"\n\n'
        "    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v0\n\n"
        "    if-eqz v0, :scoped\n\n"
        '    const-string v0, "plain_session_management"\n\n'
        f"    invoke-static {{v0}}, L{cls};->k(Ljava/lang/String;)Landroid/content/SharedPreferences;\n\n"
        "    move-result-object p0\n\n"
        "    goto :resolved\n\n"
        "    :scoped\n"
        f"    invoke-static {{p0}}, L{cls};->d(Ljava/lang/String;)Landroid/content/SharedPreferences;\n\n"
        "    move-result-object p0\n\n"
        "    :resolved\n"
        "    invoke-interface {p0, p1}, Landroid/content/SharedPreferences;->contains(Ljava/lang/String;)Z\n\n"
        "    move-result v0\n\n"
        "    if-eqz v0, :done\n\n"
        "    invoke-interface {p0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;\n\n"
        "    move-result-object p0\n\n"
        "    invoke-interface {p0, p1}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;\n\n"
        "    move-result-object p0\n\n"
        "    invoke-interface {p0}, Landroid/content/SharedPreferences$Editor;->apply()V\n\n"
        "    :done\n"
        "    return-void\n"
    )


def ctor_account_body(cls: str) -> str:
    return (
        "    .locals 0\n\n"
        "    invoke-direct {p0}, Ljava/lang/Object;-><init>()V\n\n"
        "    const/4 p1, 0x1\n\n"
        f"    const-wide p2, {FAR_FUTURE}\n\n"
        f"    iput-boolean p1, p0, L{cls};->a:Z\n\n"
        f"    iput-wide p2, p0, L{cls};->b:J\n\n"
        "    return-void\n"
    )


def body_for(kind: str, cls: str = "") -> str:
    if kind == BOOL_TRUE:
        return bool_body(1)
    if kind == BOOL_FALSE:
        return bool_body(0)
    if kind == LONG_FAR:
        return long_body()
    if kind == CTOR_ACCOUNT:
        return ctor_account_body(cls)
    if kind == VOID:
        return void_body()
    if kind == SESSION_KEY_PREFS:
        return session_key_prefs_body(cls)
    if kind == SESSION_KEY_REMOVE:
        return session_key_remove_body(cls)
    raise SystemExit(f"unknown body kind: {kind}")

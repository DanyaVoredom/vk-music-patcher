from __future__ import annotations

FAR_FUTURE = "0xf4865680L"

BOOL_TRUE = "bool:1"
BOOL_FALSE = "bool:0"
LONG_FAR = "long"
CTOR_ACCOUNT = "ctor_account"

TARGETS: list[dict] = [
    {"source": "MusicSubscriptionProviderImpl.kt", "method": ".method public final b()Z", "body": BOOL_TRUE},
    {"source": "MusicSubscriptionProviderImpl.kt", "method": ".method public final c()J", "body": LONG_FAR},
    {"source": "MusicSubscriptionProvider.kt", "method": ".method public final b()Z", "body": BOOL_TRUE},
    {"source": "MusicSubscriptionProvider.kt", "method": ".method public final c()J", "body": LONG_FAR},
    {"source": "CurrentAccountInformation.kt", "method": ".method public constructor <init>(ZJ)V", "body": CTOR_ACCOUNT},
    {"source": "ContextFlags.kt", "method": ".method public static final b(I)Z", "body": BOOL_TRUE},
    {"source": "ContextFlags.kt", "method": ".method public static final d(I)Z", "body": BOOL_FALSE},
    {"source": "ContextFlags.kt", "method": ".method public static final e(I)Z", "body": BOOL_FALSE},
    {"source": "ContextFlags.kt", "method": ".method public static final f(I)Z", "body": BOOL_FALSE},
    {"source": "MusicTrackExt.kt", "method": ".method public static final d(Lcom/vk/dto/music/MusicTrack;)Z", "body": BOOL_FALSE},
    {"source": "MusicConfigureInformationProvider.kt", "method": ".method public final a()Z", "body": BOOL_FALSE},
    {"source": "FeaturesHelper.kt", "method": ".method public static y(Z)Z", "body": BOOL_TRUE},
]

PLAYER_TARGETS: list[dict] = [
    {"source": "PlayerModelImpl.kt", "method": ".method public static E(Lxsna/zew;Ljava/util/List;)Z", "body": BOOL_FALSE},
]

MUSICTRACK_TARGETS: list[dict] = [
    {"path": "com/vk/dto/music/MusicTrack.smali", "method": ".method public final E6()I", "body": BOOL_FALSE},
    {"path": "com/vk/dto/music/MusicTrack.smali", "method": ".method public final l()Z", "body": BOOL_FALSE},
]

MIGRATION = {
    "source": "FromStandalone2UpdateTask.kt",
    "start": "    instance-of p1, p1, Lkotlin/Result$Failure;",
    "end": "    xor-int/2addr p1, v3",
    "replacement": "    const/4 p1, 0x1",
}


def bool_body(value: int) -> str:
    return f"    .locals 1\n\n    const/4 v1, 0x{value:x}\n\n    return v1\n"


def long_body() -> str:
    return f"    .locals 2\n\n    const-wide v1, {FAR_FUTURE}\n\n    return-wide v1\n"


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
    raise SystemExit(f"unknown body kind: {kind}")
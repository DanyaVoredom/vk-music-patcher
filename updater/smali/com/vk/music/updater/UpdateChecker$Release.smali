.class final Lcom/vk/music/updater/UpdateChecker$Release;
.super Ljava/lang/Object;
.source "UpdateChecker.java"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/vk/music/updater/UpdateChecker;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x1a
    name = "Release"
.end annotation


# instance fields
.field apkUrl:Ljava/lang/String;

.field modRevision:I

.field sha256:Ljava/lang/String;

.field versionCode:J

.field versionName:Ljava/lang/String;


# direct methods
.method private constructor <init>()V
    .registers 1

    .line 292
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method synthetic constructor <init>(Lcom/vk/music/updater/UpdateChecker$1;)V
    .registers 2

    .line 292
    invoke-direct {p0}, Lcom/vk/music/updater/UpdateChecker$Release;-><init>()V

    return-void
.end method

.class Lcom/vk/music/updater/UpdateChecker$1;
.super Ljava/lang/Object;
.source "UpdateChecker.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/vk/music/updater/UpdateChecker;->check(Landroid/app/Activity;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$activity:Landroid/app/Activity;

.field final synthetic val$app:Landroid/content/Context;

.field final synthetic val$prefs:Landroid/content/SharedPreferences;


# direct methods
.method constructor <init>(Landroid/content/Context;Landroid/content/SharedPreferences;Landroid/app/Activity;)V
    .registers 4
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 49
    iput-object p1, p0, Lcom/vk/music/updater/UpdateChecker$1;->val$app:Landroid/content/Context;

    iput-object p2, p0, Lcom/vk/music/updater/UpdateChecker$1;->val$prefs:Landroid/content/SharedPreferences;

    iput-object p3, p0, Lcom/vk/music/updater/UpdateChecker$1;->val$activity:Landroid/app/Activity;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 6

    .line 53
    :try_start_0
    # invokes: Lcom/vk/music/updater/UpdateChecker;->fetchLatest()Lcom/vk/music/updater/UpdateChecker$Release;
    invoke-static {}, Lcom/vk/music/updater/UpdateChecker;->access$000()Lcom/vk/music/updater/UpdateChecker$Release;

    move-result-object v0

    .line 54
    if-eqz v0, :cond_42

    iget-object v1, p0, Lcom/vk/music/updater/UpdateChecker$1;->val$app:Landroid/content/Context;

    # invokes: Lcom/vk/music/updater/UpdateChecker;->isNewer(Landroid/content/Context;Lcom/vk/music/updater/UpdateChecker$Release;)Z
    invoke-static {v1, v0}, Lcom/vk/music/updater/UpdateChecker;->access$100(Landroid/content/Context;Lcom/vk/music/updater/UpdateChecker$Release;)Z

    move-result v1

    if-nez v1, :cond_f

    goto :goto_42

    .line 57
    :cond_f
    iget-object v1, p0, Lcom/vk/music/updater/UpdateChecker$1;->val$prefs:Landroid/content/SharedPreferences;

    const-string v2, "skipped_code"

    const-wide/16 v3, -0x1

    invoke-interface {v1, v2, v3, v4}, Landroid/content/SharedPreferences;->getLong(Ljava/lang/String;J)J

    move-result-wide v1

    iget-wide v3, v0, Lcom/vk/music/updater/UpdateChecker$Release;->versionCode:J

    cmp-long v1, v1, v3

    if-nez v1, :cond_2d

    iget-object v1, p0, Lcom/vk/music/updater/UpdateChecker$1;->val$prefs:Landroid/content/SharedPreferences;

    const-string v2, "skipped_revision"

    .line 58
    const/4 v3, -0x1

    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I

    move-result v1

    iget v2, v0, Lcom/vk/music/updater/UpdateChecker$Release;->modRevision:I

    if-ne v1, v2, :cond_2d

    .line 59
    return-void

    .line 61
    :cond_2d
    nop

    .line 62
    new-instance v1, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v2

    invoke-direct {v1, v2}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    new-instance v2, Lcom/vk/music/updater/UpdateChecker$1$1;

    iget-object v3, p0, Lcom/vk/music/updater/UpdateChecker$1;->val$activity:Landroid/app/Activity;

    invoke-direct {v2, p0, v3, v0}, Lcom/vk/music/updater/UpdateChecker$1$1;-><init>(Lcom/vk/music/updater/UpdateChecker$1;Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    invoke-virtual {v1, v2}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z
    :try_end_41
    .catchall {:try_start_0 .. :try_end_41} :catchall_43

    .line 69
    goto :goto_44

    .line 55
    :cond_42
    :goto_42
    return-void

    .line 68
    :catchall_43
    move-exception v0

    .line 70
    :goto_44
    return-void
.end method

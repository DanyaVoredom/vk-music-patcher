.class Lcom/vk/music/updater/UpdateChecker$4;
.super Ljava/lang/Object;
.source "UpdateChecker.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/vk/music/updater/UpdateChecker;->downloadAndInstall(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$activity:Landroid/app/Activity;

.field final synthetic val$release:Lcom/vk/music/updater/UpdateChecker$Release;


# direct methods
.method constructor <init>(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    .registers 3
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 117
    iput-object p1, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$activity:Landroid/app/Activity;

    iput-object p2, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 6

    .line 120
    nop

    .line 122
    const/4 v0, 0x0

    :try_start_2
    new-instance v1, Ljava/io/File;

    iget-object v2, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$activity:Landroid/app/Activity;

    invoke-virtual {v2}, Landroid/app/Activity;->getCacheDir()Ljava/io/File;

    move-result-object v2

    const-string v3, "updates"

    invoke-direct {v1, v2, v3}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    .line 123
    invoke-virtual {v1}, Ljava/io/File;->exists()Z

    move-result v2

    if-nez v2, :cond_24

    invoke-virtual {v1}, Ljava/io/File;->mkdirs()Z

    move-result v2

    if-eqz v2, :cond_1c

    goto :goto_24

    .line 124
    :cond_1c
    new-instance v1, Ljava/lang/IllegalStateException;

    const-string v2, "cache"

    invoke-direct {v1, v2}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    throw v1

    .line 126
    :cond_24
    :goto_24
    new-instance v2, Ljava/io/File;

    const-string v3, "VK_Music_update.apk"

    invoke-direct {v2, v1, v3}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
    :try_end_2b
    .catchall {:try_start_2 .. :try_end_2b} :catchall_8a

    .line 127
    :try_start_2b
    iget-object v0, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    iget-object v0, v0, Lcom/vk/music/updater/UpdateChecker$Release;->apkUrl:Ljava/lang/String;

    # invokes: Lcom/vk/music/updater/UpdateChecker;->download(Ljava/lang/String;Ljava/io/File;)V
    invoke-static {v0, v2}, Lcom/vk/music/updater/UpdateChecker;->access$400(Ljava/lang/String;Ljava/io/File;)V

    .line 128
    # invokes: Lcom/vk/music/updater/UpdateChecker;->sha256(Ljava/io/File;)Ljava/lang/String;
    invoke-static {v2}, Lcom/vk/music/updater/UpdateChecker;->access$500(Ljava/io/File;)Ljava/lang/String;

    move-result-object v0

    .line 129
    iget-object v1, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    iget-object v1, v1, Lcom/vk/music/updater/UpdateChecker$Release;->sha256:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_7f

    .line 132
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "content://"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    iget-object v1, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$activity:Landroid/app/Activity;

    invoke-virtual {v1}, Landroid/app/Activity;->getPackageName()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, ".fileprovider/cache/updates/"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    .line 133
    invoke-virtual {v2}, Ljava/io/File;->getName()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    .line 132
    invoke-static {v0}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v0

    .line 134
    new-instance v1, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v3

    invoke-direct {v1, v3}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    new-instance v3, Lcom/vk/music/updater/UpdateChecker$4$1;

    iget-object v4, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$activity:Landroid/app/Activity;

    invoke-direct {v3, p0, v4, v0}, Lcom/vk/music/updater/UpdateChecker$4$1;-><init>(Lcom/vk/music/updater/UpdateChecker$4;Landroid/app/Activity;Landroid/net/Uri;)V

    invoke-virtual {v1, v3}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 150
    goto :goto_a3

    .line 130
    :cond_7f
    new-instance v0, Ljava/lang/IllegalStateException;

    const-string v1, "sha256"

    invoke-direct {v0, v1}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    throw v0
    :try_end_87
    .catchall {:try_start_2b .. :try_end_87} :catchall_87

    .line 140
    :catchall_87
    move-exception v0

    move-object v0, v2

    goto :goto_8b

    :catchall_8a
    move-exception v1

    .line 141
    :goto_8b
    if-eqz v0, :cond_90

    .line 142
    invoke-virtual {v0}, Ljava/io/File;->delete()Z

    .line 144
    :cond_90
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    new-instance v1, Lcom/vk/music/updater/UpdateChecker$4$2;

    iget-object v2, p0, Lcom/vk/music/updater/UpdateChecker$4;->val$activity:Landroid/app/Activity;

    invoke-direct {v1, p0, v2}, Lcom/vk/music/updater/UpdateChecker$4$2;-><init>(Lcom/vk/music/updater/UpdateChecker$4;Landroid/app/Activity;)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 151
    :goto_a3
    return-void
.end method

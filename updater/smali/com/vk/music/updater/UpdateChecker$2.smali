.class Lcom/vk/music/updater/UpdateChecker$2;
.super Ljava/lang/Object;
.source "UpdateChecker.java"

# interfaces
.implements Landroid/content/DialogInterface$OnClickListener;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/vk/music/updater/UpdateChecker;->showDialog(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
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

    .line 103
    iput-object p1, p0, Lcom/vk/music/updater/UpdateChecker$2;->val$activity:Landroid/app/Activity;

    iput-object p2, p0, Lcom/vk/music/updater/UpdateChecker$2;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onClick(Landroid/content/DialogInterface;I)V
    .registers 5

    .line 106
    iget-object p1, p0, Lcom/vk/music/updater/UpdateChecker$2;->val$activity:Landroid/app/Activity;

    const-string p2, "vk_mod_updater"

    const/4 v0, 0x0

    invoke-virtual {p1, p2, v0}, Landroid/app/Activity;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object p1

    invoke-interface {p1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    iget-object p2, p0, Lcom/vk/music/updater/UpdateChecker$2;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    iget-wide v0, p2, Lcom/vk/music/updater/UpdateChecker$Release;->versionCode:J

    .line 107
    const-string p2, "skipped_code"

    invoke-interface {p1, p2, v0, v1}, Landroid/content/SharedPreferences$Editor;->putLong(Ljava/lang/String;J)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    iget-object p2, p0, Lcom/vk/music/updater/UpdateChecker$2;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    iget p2, p2, Lcom/vk/music/updater/UpdateChecker$Release;->modRevision:I

    .line 108
    const-string v0, "skipped_revision"

    invoke-interface {p1, v0, p2}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;

    move-result-object p1

    .line 109
    invoke-interface {p1}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 110
    return-void
.end method

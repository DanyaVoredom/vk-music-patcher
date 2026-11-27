.class Lcom/vk/music/updater/UpdateChecker$3;
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

    .line 98
    iput-object p1, p0, Lcom/vk/music/updater/UpdateChecker$3;->val$activity:Landroid/app/Activity;

    iput-object p2, p0, Lcom/vk/music/updater/UpdateChecker$3;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onClick(Landroid/content/DialogInterface;I)V
    .registers 3

    .line 101
    iget-object p1, p0, Lcom/vk/music/updater/UpdateChecker$3;->val$activity:Landroid/app/Activity;

    iget-object p2, p0, Lcom/vk/music/updater/UpdateChecker$3;->val$release:Lcom/vk/music/updater/UpdateChecker$Release;

    # invokes: Lcom/vk/music/updater/UpdateChecker;->downloadAndInstall(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    invoke-static {p1, p2}, Lcom/vk/music/updater/UpdateChecker;->access$300(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    .line 102
    return-void
.end method

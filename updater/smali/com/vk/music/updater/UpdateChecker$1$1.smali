.class Lcom/vk/music/updater/UpdateChecker$1$1;
.super Ljava/lang/Object;
.source "UpdateChecker.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/vk/music/updater/UpdateChecker$1;->run()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/vk/music/updater/UpdateChecker$1;

.field final synthetic val$activity:Landroid/app/Activity;

.field final synthetic val$found:Lcom/vk/music/updater/UpdateChecker$Release;


# direct methods
.method constructor <init>(Lcom/vk/music/updater/UpdateChecker$1;Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    .registers 4
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010,
            0x1010,
            0x1010
        }
        names = {
            null,
            null,
            null
        }
    .end annotation

    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 62
    iput-object p2, p0, Lcom/vk/music/updater/UpdateChecker$1$1;->val$activity:Landroid/app/Activity;

    iput-object p3, p0, Lcom/vk/music/updater/UpdateChecker$1$1;->val$found:Lcom/vk/music/updater/UpdateChecker$Release;

    iput-object p1, p0, Lcom/vk/music/updater/UpdateChecker$1$1;->this$0:Lcom/vk/music/updater/UpdateChecker$1;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 3

    .line 65
    iget-object v0, p0, Lcom/vk/music/updater/UpdateChecker$1$1;->val$activity:Landroid/app/Activity;

    iget-object v1, p0, Lcom/vk/music/updater/UpdateChecker$1$1;->val$found:Lcom/vk/music/updater/UpdateChecker$Release;

    # invokes: Lcom/vk/music/updater/UpdateChecker;->showDialog(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    invoke-static {v0, v1}, Lcom/vk/music/updater/UpdateChecker;->access$200(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    .line 66
    return-void
.end method

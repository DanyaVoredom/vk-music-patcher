.class Lcom/vk/music/updater/UpdateChecker$4$1;
.super Ljava/lang/Object;
.source "UpdateChecker.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/vk/music/updater/UpdateChecker$4;->run()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/vk/music/updater/UpdateChecker$4;

.field final synthetic val$activity:Landroid/app/Activity;

.field final synthetic val$uri:Landroid/net/Uri;


# direct methods
.method constructor <init>(Lcom/vk/music/updater/UpdateChecker$4;Landroid/app/Activity;Landroid/net/Uri;)V
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

    .line 144
    iput-object p2, p0, Lcom/vk/music/updater/UpdateChecker$4$1;->val$activity:Landroid/app/Activity;

    iput-object p3, p0, Lcom/vk/music/updater/UpdateChecker$4$1;->val$uri:Landroid/net/Uri;

    iput-object p1, p0, Lcom/vk/music/updater/UpdateChecker$4$1;->this$0:Lcom/vk/music/updater/UpdateChecker$4;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 3

    .line 147
    iget-object v0, p0, Lcom/vk/music/updater/UpdateChecker$4$1;->val$activity:Landroid/app/Activity;

    iget-object v1, p0, Lcom/vk/music/updater/UpdateChecker$4$1;->val$uri:Landroid/net/Uri;

    # invokes: Lcom/vk/music/updater/UpdateChecker;->install(Landroid/app/Activity;Landroid/net/Uri;)V
    invoke-static {v0, v1}, Lcom/vk/music/updater/UpdateChecker;->access$600(Landroid/app/Activity;Landroid/net/Uri;)V

    .line 148
    return-void
.end method

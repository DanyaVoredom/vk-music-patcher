.class public final Lcom/vk/music/updater/UpdateChecker;
.super Ljava/lang/Object;
.source "UpdateChecker.java"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Lcom/vk/music/updater/UpdateChecker$Release;
    }
.end annotation


# static fields
.field private static final API:Ljava/lang/String; = "https://api.github.com/repos/FANATFANATA/vk-music-patcher/releases/latest"

.field private static final CHECK_INTERVAL_MS:J = 0x493e0L

.field private static final PREFS:Ljava/lang/String; = "vk_mod_updater"


# direct methods
.method private constructor <init>()V
    .registers 1

    .line 34
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 35
    return-void
.end method

.method static synthetic access$000()Lcom/vk/music/updater/UpdateChecker$Release;
    .registers 1
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 29
    invoke-static {}, Lcom/vk/music/updater/UpdateChecker;->fetchLatest()Lcom/vk/music/updater/UpdateChecker$Release;

    move-result-object v0

    return-object v0
.end method

.method static synthetic access$100(Landroid/content/Context;Lcom/vk/music/updater/UpdateChecker$Release;)Z
    .registers 2
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 29
    invoke-static {p0, p1}, Lcom/vk/music/updater/UpdateChecker;->isNewer(Landroid/content/Context;Lcom/vk/music/updater/UpdateChecker$Release;)Z

    move-result p0

    return p0
.end method

.method static synthetic access$200(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    .registers 2

    .line 29
    invoke-static {p0, p1}, Lcom/vk/music/updater/UpdateChecker;->showDialog(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    return-void
.end method

.method static synthetic access$300(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    .registers 2

    .line 29
    invoke-static {p0, p1}, Lcom/vk/music/updater/UpdateChecker;->downloadAndInstall(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    return-void
.end method

.method static synthetic access$400(Ljava/lang/String;Ljava/io/File;)V
    .registers 2
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 29
    invoke-static {p0, p1}, Lcom/vk/music/updater/UpdateChecker;->download(Ljava/lang/String;Ljava/io/File;)V

    return-void
.end method

.method static synthetic access$500(Ljava/io/File;)Ljava/lang/String;
    .registers 1
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 29
    invoke-static {p0}, Lcom/vk/music/updater/UpdateChecker;->sha256(Ljava/io/File;)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$600(Landroid/app/Activity;Landroid/net/Uri;)V
    .registers 2

    .line 29
    invoke-static {p0, p1}, Lcom/vk/music/updater/UpdateChecker;->install(Landroid/app/Activity;Landroid/net/Uri;)V

    return-void
.end method

.method public static check(Landroid/app/Activity;)V
    .registers 10

    .line 38
    if-nez p0, :cond_3

    .line 39
    return-void

    .line 41
    :cond_3
    invoke-virtual {p0}, Landroid/app/Activity;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    .line 42
    const-string v1, "vk_mod_updater"

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object v1

    .line 43
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    .line 44
    const-wide/16 v4, 0x0

    const-string v6, "last_check"

    invoke-interface {v1, v6, v4, v5}, Landroid/content/SharedPreferences;->getLong(Ljava/lang/String;J)J

    move-result-wide v4

    sub-long v4, v2, v4

    const-wide/32 v7, 0x493e0

    cmp-long v4, v4, v7

    if-gez v4, :cond_24

    .line 45
    return-void

    .line 47
    :cond_24
    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v4

    invoke-interface {v4, v6, v2, v3}, Landroid/content/SharedPreferences$Editor;->putLong(Ljava/lang/String;J)Landroid/content/SharedPreferences$Editor;

    move-result-object v2

    invoke-interface {v2}, Landroid/content/SharedPreferences$Editor;->apply()V

    .line 48
    new-instance v2, Ljava/lang/Thread;

    new-instance v3, Lcom/vk/music/updater/UpdateChecker$1;

    invoke-direct {v3, v0, v1, p0}, Lcom/vk/music/updater/UpdateChecker$1;-><init>(Landroid/content/Context;Landroid/content/SharedPreferences;Landroid/app/Activity;)V

    const-string p0, "vk-mod-update"

    invoke-direct {v2, v3, p0}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;Ljava/lang/String;)V

    .line 70
    invoke-virtual {v2}, Ljava/lang/Thread;->start()V

    .line 71
    return-void
.end method

.method private static download(Ljava/lang/String;Ljava/io/File;)V
    .registers 6
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 233
    new-instance v0, Ljava/net/URL;

    invoke-direct {v0, p0}, Ljava/net/URL;-><init>(Ljava/lang/String;)V

    invoke-virtual {v0}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;

    move-result-object p0

    check-cast p0, Ljava/net/HttpURLConnection;

    .line 234
    const/16 v0, 0x3a98

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setConnectTimeout(I)V

    .line 235
    const v0, 0xea60

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setReadTimeout(I)V

    .line 236
    const-string v0, "User-Agent"

    const-string v1, "VKMusicModUpdater"

    invoke-virtual {p0, v0, v1}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 238
    :try_start_1d
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getResponseCode()I

    move-result v0

    .line 239
    const/16 v1, 0xc8

    if-ne v0, v1, :cond_5f

    .line 242
    new-instance v0, Ljava/io/BufferedInputStream;

    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getInputStream()Ljava/io/InputStream;

    move-result-object v1

    invoke-direct {v0, v1}, Ljava/io/BufferedInputStream;-><init>(Ljava/io/InputStream;)V
    :try_end_2e
    .catchall {:try_start_1d .. :try_end_2e} :catchall_78

    .line 244
    :try_start_2e
    new-instance v1, Ljava/io/BufferedOutputStream;

    new-instance v2, Ljava/io/FileOutputStream;

    invoke-direct {v2, p1}, Ljava/io/FileOutputStream;-><init>(Ljava/io/File;)V

    invoke-direct {v1, v2}, Ljava/io/BufferedOutputStream;-><init>(Ljava/io/OutputStream;)V
    :try_end_38
    .catchall {:try_start_2e .. :try_end_38} :catchall_5a

    .line 246
    const/16 p1, 0x2000

    :try_start_3a
    new-array p1, p1, [B

    .line 248
    :goto_3c
    invoke-virtual {v0, p1}, Ljava/io/InputStream;->read([B)I

    move-result v2

    const/4 v3, -0x1

    if-eq v2, v3, :cond_48

    .line 249
    const/4 v3, 0x0

    invoke-virtual {v1, p1, v3, v2}, Ljava/io/BufferedOutputStream;->write([BII)V
    :try_end_47
    .catchall {:try_start_3a .. :try_end_47} :catchall_55

    goto :goto_3c

    .line 252
    :cond_48
    :try_start_48
    invoke-virtual {v1}, Ljava/io/BufferedOutputStream;->close()V
    :try_end_4b
    .catchall {:try_start_48 .. :try_end_4b} :catchall_5a

    .line 253
    nop

    .line 255
    :try_start_4c
    invoke-virtual {v0}, Ljava/io/InputStream;->close()V
    :try_end_4f
    .catchall {:try_start_4c .. :try_end_4f} :catchall_78

    .line 256
    nop

    .line 258
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->disconnect()V

    .line 259
    nop

    .line 260
    return-void

    .line 252
    :catchall_55
    move-exception p1

    :try_start_56
    invoke-virtual {v1}, Ljava/io/BufferedOutputStream;->close()V

    .line 253
    throw p1
    :try_end_5a
    .catchall {:try_start_56 .. :try_end_5a} :catchall_5a

    .line 255
    :catchall_5a
    move-exception p1

    :try_start_5b
    invoke-virtual {v0}, Ljava/io/InputStream;->close()V

    .line 256
    throw p1

    .line 240
    :cond_5f
    new-instance p1, Ljava/lang/IllegalStateException;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "http "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-direct {p1, v0}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    throw p1
    :try_end_78
    .catchall {:try_start_5b .. :try_end_78} :catchall_78

    .line 258
    :catchall_78
    move-exception p1

    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->disconnect()V

    .line 259
    throw p1
.end method

.method private static downloadAndInstall(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    .registers 4

    .line 116
    const-string v0, "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f"

    const/4 v1, 0x0

    invoke-static {p0, v0, v1}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;

    move-result-object v0

    invoke-virtual {v0}, Landroid/widget/Toast;->show()V

    .line 117
    new-instance v0, Ljava/lang/Thread;

    new-instance v1, Lcom/vk/music/updater/UpdateChecker$4;

    invoke-direct {v1, p0, p1}, Lcom/vk/music/updater/UpdateChecker$4;-><init>(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    const-string p0, "vk-mod-download"

    invoke-direct {v0, v1, p0}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;Ljava/lang/String;)V

    .line 152
    invoke-virtual {v0}, Ljava/lang/Thread;->start()V

    .line 153
    return-void
.end method

.method private static fetchLatest()Lcom/vk/music/updater/UpdateChecker$Release;
    .registers 9
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 170
    new-instance v0, Lorg/json/JSONObject;

    const-string v1, "https://api.github.com/repos/FANATFANATA/vk-music-patcher/releases/latest"

    invoke-static {v1}, Lcom/vk/music/updater/UpdateChecker;->get(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-direct {v0, v1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 171
    const-string v1, "assets"

    invoke-virtual {v0, v1}, Lorg/json/JSONObject;->getJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v0

    .line 172
    nop

    .line 173
    const/4 v1, 0x0

    move v2, v1

    :goto_14
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v3

    const-string v4, "browser_download_url"

    const-string v5, "name"

    const/4 v6, 0x0

    if-ge v2, v3, :cond_37

    .line 174
    invoke-virtual {v0, v2}, Lorg/json/JSONArray;->getJSONObject(I)Lorg/json/JSONObject;

    move-result-object v3

    .line 175
    const-string v7, "update.json"

    invoke-virtual {v3, v5}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v8

    invoke-virtual {v7, v8}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v7

    if-eqz v7, :cond_34

    .line 176
    invoke-virtual {v3, v4}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    .line 177
    goto :goto_38

    .line 173
    :cond_34
    add-int/lit8 v2, v2, 0x1

    goto :goto_14

    :cond_37
    move-object v2, v6

    .line 180
    :goto_38
    if-nez v2, :cond_3b

    .line 181
    return-object v6

    .line 183
    :cond_3b
    new-instance v3, Lorg/json/JSONObject;

    invoke-static {v2}, Lcom/vk/music/updater/UpdateChecker;->get(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    invoke-direct {v3, v2}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 184
    new-instance v2, Lcom/vk/music/updater/UpdateChecker$Release;

    invoke-direct {v2, v6}, Lcom/vk/music/updater/UpdateChecker$Release;-><init>(Lcom/vk/music/updater/UpdateChecker$1;)V

    .line 185
    const-string v7, "versionName"

    invoke-virtual {v3, v7}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    iput-object v7, v2, Lcom/vk/music/updater/UpdateChecker$Release;->versionName:Ljava/lang/String;

    .line 186
    const-string v7, "versionCode"

    invoke-virtual {v3, v7}, Lorg/json/JSONObject;->getLong(Ljava/lang/String;)J

    move-result-wide v7

    iput-wide v7, v2, Lcom/vk/music/updater/UpdateChecker$Release;->versionCode:J

    .line 187
    const-string v7, "modRevision"

    invoke-virtual {v3, v7, v1}, Lorg/json/JSONObject;->optInt(Ljava/lang/String;I)I

    move-result v7

    iput v7, v2, Lcom/vk/music/updater/UpdateChecker$Release;->modRevision:I

    .line 188
    const-string v7, "sha256"

    invoke-virtual {v3, v7}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    iput-object v7, v2, Lcom/vk/music/updater/UpdateChecker$Release;->sha256:Ljava/lang/String;

    .line 189
    const-string v7, "apk"

    invoke-virtual {v3, v7}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    .line 190
    nop

    :goto_70
    invoke-virtual {v0}, Lorg/json/JSONArray;->length()I

    move-result v7

    if-ge v1, v7, :cond_8e

    .line 191
    invoke-virtual {v0, v1}, Lorg/json/JSONArray;->getJSONObject(I)Lorg/json/JSONObject;

    move-result-object v7

    .line 192
    invoke-virtual {v7, v5}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v8

    invoke-virtual {v3, v8}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v8

    if-eqz v8, :cond_8b

    .line 193
    invoke-virtual {v7, v4}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    iput-object v0, v2, Lcom/vk/music/updater/UpdateChecker$Release;->apkUrl:Ljava/lang/String;

    .line 194
    return-object v2

    .line 190
    :cond_8b
    add-int/lit8 v1, v1, 0x1

    goto :goto_70

    .line 197
    :cond_8e
    return-object v6
.end method

.method private static get(Ljava/lang/String;)Ljava/lang/String;
    .registers 5
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 201
    new-instance v0, Ljava/net/URL;

    invoke-direct {v0, p0}, Ljava/net/URL;-><init>(Ljava/lang/String;)V

    invoke-virtual {v0}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;

    move-result-object p0

    check-cast p0, Ljava/net/HttpURLConnection;

    .line 202
    const/16 v0, 0x3a98

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setConnectTimeout(I)V

    .line 203
    const/16 v0, 0x4e20

    invoke-virtual {p0, v0}, Ljava/net/HttpURLConnection;->setReadTimeout(I)V

    .line 204
    const-string v0, "User-Agent"

    const-string v1, "VKMusicModUpdater"

    invoke-virtual {p0, v0, v1}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 205
    const-string v0, "Accept"

    const-string v1, "application/vnd.github+json"

    invoke-virtual {p0, v0, v1}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    .line 207
    :try_start_23
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getResponseCode()I

    move-result v0

    .line 208
    const/16 v1, 0xc8

    if-ne v0, v1, :cond_44

    .line 211
    new-instance v0, Ljava/io/BufferedInputStream;

    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->getInputStream()Ljava/io/InputStream;

    move-result-object v1

    invoke-direct {v0, v1}, Ljava/io/BufferedInputStream;-><init>(Ljava/io/InputStream;)V
    :try_end_34
    .catchall {:try_start_23 .. :try_end_34} :catchall_5d

    .line 213
    :try_start_34
    invoke-static {v0}, Lcom/vk/music/updater/UpdateChecker;->readText(Ljava/io/InputStream;)Ljava/lang/String;

    move-result-object v1
    :try_end_38
    .catchall {:try_start_34 .. :try_end_38} :catchall_3f

    .line 215
    :try_start_38
    invoke-virtual {v0}, Ljava/io/InputStream;->close()V
    :try_end_3b
    .catchall {:try_start_38 .. :try_end_3b} :catchall_5d

    .line 218
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->disconnect()V

    .line 213
    return-object v1

    .line 215
    :catchall_3f
    move-exception v1

    :try_start_40
    invoke-virtual {v0}, Ljava/io/InputStream;->close()V

    .line 216
    throw v1

    .line 209
    :cond_44
    new-instance v1, Ljava/lang/IllegalStateException;

    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v3, "http "

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-direct {v1, v0}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    throw v1
    :try_end_5d
    .catchall {:try_start_40 .. :try_end_5d} :catchall_5d

    .line 218
    :catchall_5d
    move-exception v0

    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->disconnect()V

    .line 219
    throw v0
.end method

.method private static install(Landroid/app/Activity;Landroid/net/Uri;)V
    .registers 4

    .line 156
    invoke-virtual {p0}, Landroid/app/Activity;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object v0

    invoke-virtual {v0}, Landroid/content/pm/PackageManager;->canRequestPackageInstalls()Z

    move-result v0

    if-nez v0, :cond_3a

    .line 157
    const-string p1, "\u0420\u0430\u0437\u0440\u0435\u0448\u0438\u0442\u0435 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0443 \u0438\u0437 \u044d\u0442\u043e\u0433\u043e \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f"

    const/4 v0, 0x1

    invoke-static {p0, p1, v0}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;

    move-result-object p1

    invoke-virtual {p1}, Landroid/widget/Toast;->show()V

    .line 158
    new-instance p1, Landroid/content/Intent;

    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "package:"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    .line 159
    invoke-virtual {p0}, Landroid/app/Activity;->getPackageName()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-static {v0}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v0

    const-string v1, "android.settings.MANAGE_UNKNOWN_APP_SOURCES"

    invoke-direct {p1, v1, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V

    .line 160
    invoke-virtual {p0, p1}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V

    .line 161
    return-void

    .line 163
    :cond_3a
    new-instance v0, Landroid/content/Intent;

    const-string v1, "android.intent.action.VIEW"

    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    .line 164
    const-string v1, "application/vnd.android.package-archive"

    invoke-virtual {v0, p1, v1}, Landroid/content/Intent;->setDataAndType(Landroid/net/Uri;Ljava/lang/String;)Landroid/content/Intent;

    .line 165
    const p1, 0x10000001

    invoke-virtual {v0, p1}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;

    .line 166
    invoke-virtual {p0, v0}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V

    .line 167
    return-void
.end method

.method private static isNewer(Landroid/content/Context;Lcom/vk/music/updater/UpdateChecker$Release;)Z
    .registers 9
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 82
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object v0

    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object v1

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;

    move-result-object v0

    invoke-virtual {v0}, Landroid/content/pm/PackageInfo;->getLongVersionCode()J

    move-result-wide v0

    .line 83
    iget-wide v3, p1, Lcom/vk/music/updater/UpdateChecker$Release;->versionCode:J

    cmp-long v3, v3, v0

    const/4 v4, 0x1

    if-lez v3, :cond_19

    .line 84
    return v4

    .line 86
    :cond_19
    iget-wide v5, p1, Lcom/vk/music/updater/UpdateChecker$Release;->versionCode:J

    cmp-long v0, v5, v0

    if-nez v0, :cond_28

    iget p1, p1, Lcom/vk/music/updater/UpdateChecker$Release;->modRevision:I

    invoke-static {p0}, Lcom/vk/music/updater/UpdateChecker;->localRevision(Landroid/content/Context;)I

    move-result p0

    if-le p1, p0, :cond_28

    move v2, v4

    :cond_28
    return v2
.end method

.method private static localRevision(Landroid/content/Context;)I
    .registers 5

    .line 74
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    const-string v1, "integer"

    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object v2

    const-string v3, "vk_mod_revision"

    invoke-virtual {v0, v3, v1, v2}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result v0

    .line 75
    if-nez v0, :cond_14

    .line 76
    const/4 p0, 0x0

    return p0

    .line 78
    :cond_14
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object p0

    invoke-virtual {p0, v0}, Landroid/content/res/Resources;->getInteger(I)I

    move-result p0

    return p0
.end method

.method private static readText(Ljava/io/InputStream;)Ljava/lang/String;
    .registers 5
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 223
    new-instance v0, Ljava/io/ByteArrayOutputStream;

    invoke-direct {v0}, Ljava/io/ByteArrayOutputStream;-><init>()V

    .line 224
    const/16 v1, 0x2000

    new-array v1, v1, [B

    .line 226
    :goto_9
    invoke-virtual {p0, v1}, Ljava/io/InputStream;->read([B)I

    move-result v2

    const/4 v3, -0x1

    if-eq v2, v3, :cond_15

    .line 227
    const/4 v3, 0x0

    invoke-virtual {v0, v1, v3, v2}, Ljava/io/ByteArrayOutputStream;->write([BII)V

    goto :goto_9

    .line 229
    :cond_15
    const-string p0, "UTF-8"

    invoke-virtual {v0, p0}, Ljava/io/ByteArrayOutputStream;->toString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static sha256(Ljava/io/File;)Ljava/lang/String;
    .registers 6
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 263
    const-string v0, "SHA-256"

    invoke-static {v0}, Ljava/security/MessageDigest;->getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;

    move-result-object v0

    .line 264
    new-instance v1, Ljava/io/BufferedInputStream;

    new-instance v2, Ljava/io/FileInputStream;

    invoke-direct {v2, p0}, Ljava/io/FileInputStream;-><init>(Ljava/io/File;)V

    invoke-direct {v1, v2}, Ljava/io/BufferedInputStream;-><init>(Ljava/io/InputStream;)V

    .line 266
    const/16 p0, 0x2000

    :try_start_12
    new-array p0, p0, [B

    .line 268
    :goto_14
    invoke-virtual {v1, p0}, Ljava/io/InputStream;->read([B)I

    move-result v2

    const/4 v3, -0x1

    const/4 v4, 0x0

    if-eq v2, v3, :cond_20

    .line 269
    invoke-virtual {v0, p0, v4, v2}, Ljava/security/MessageDigest;->update([BII)V
    :try_end_1f
    .catchall {:try_start_12 .. :try_end_1f} :catchall_50

    goto :goto_14

    .line 272
    :cond_20
    invoke-virtual {v1}, Ljava/io/InputStream;->close()V

    .line 273
    nop

    .line 274
    invoke-virtual {v0}, Ljava/security/MessageDigest;->digest()[B

    move-result-object p0

    .line 275
    new-instance v0, Ljava/lang/StringBuilder;

    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 276
    array-length v1, p0

    :goto_31
    if-ge v4, v1, :cond_4b

    aget-byte v2, p0, v4

    .line 277
    and-int/lit16 v2, v2, 0xff

    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v2

    filled-new-array {v2}, [Ljava/lang/Object;

    move-result-object v2

    const-string v3, "%02x"

    invoke-static {v3, v2}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 276
    add-int/lit8 v4, v4, 0x1

    goto :goto_31

    .line 279
    :cond_4b
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 272
    :catchall_50
    move-exception p0

    invoke-virtual {v1}, Ljava/io/InputStream;->close()V

    .line 273
    throw p0
.end method

.method private static showDialog(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V
    .registers 5

    .line 90
    invoke-virtual {p0}, Landroid/app/Activity;->isFinishing()Z

    move-result v0

    if-nez v0, :cond_5d

    invoke-virtual {p0}, Landroid/app/Activity;->isDestroyed()Z

    move-result v0

    if-eqz v0, :cond_d

    goto :goto_5d

    .line 93
    :cond_d
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u0432\u0435\u0440\u0441\u0438\u044f "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    iget-object v1, p1, Lcom/vk/music/updater/UpdateChecker$Release;->versionName:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, ", \u0441\u0431\u043e\u0440\u043a\u0430 "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    iget v1, p1, Lcom/vk/music/updater/UpdateChecker$Release;->modRevision:I

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, "."

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    .line 94
    new-instance v1, Landroid/app/AlertDialog$Builder;

    invoke-direct {v1, p0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    .line 95
    const-string v2, "\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 VK \u041c\u0443\u0437\u044b\u043a\u0438"

    invoke-virtual {v1, v2}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    move-result-object v1

    .line 96
    invoke-virtual {v1, v0}, Landroid/app/AlertDialog$Builder;->setMessage(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;

    move-result-object v0

    new-instance v1, Lcom/vk/music/updater/UpdateChecker$3;

    invoke-direct {v1, p0, p1}, Lcom/vk/music/updater/UpdateChecker$3;-><init>(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    .line 97
    const-string v2, "\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c"

    invoke-virtual {v0, v2, v1}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    move-result-object v0

    new-instance v1, Lcom/vk/music/updater/UpdateChecker$2;

    invoke-direct {v1, p0, p1}, Lcom/vk/music/updater/UpdateChecker$2;-><init>(Landroid/app/Activity;Lcom/vk/music/updater/UpdateChecker$Release;)V

    .line 103
    const-string p0, "\u041f\u043e\u0437\u0436\u0435"

    invoke-virtual {v0, p0, v1}, Landroid/app/AlertDialog$Builder;->setNegativeButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    move-result-object p0

    .line 112
    invoke-virtual {p0}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;

    .line 113
    return-void

    .line 91
    :cond_5d
    :goto_5d
    return-void
.end method

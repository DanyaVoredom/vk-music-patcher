package com.vk.music.updater;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.StatFs;
import android.provider.Settings;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;

public final class UpdateChecker {
    private static final String API = "https://api.github.com/repos/DanyaVoredom/DanyExternal-Releases/releases?per_page=100";
    private static final String PREFS = "vk_mod_updater";
    private static final long CHECK_INTERVAL_MS = 5L * 60L * 1000L;

    private UpdateChecker() {
    }

    public static void check(final Activity activity) {
        if (activity == null) {
            return;
        }
        final Context app = activity.getApplicationContext();
        final SharedPreferences prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        long now = System.currentTimeMillis();
        if (now - prefs.getLong("last_check", 0L) < CHECK_INTERVAL_MS) {
            return;
        }
        prefs.edit().putLong("last_check", now).apply();
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    Release release = fetchLatest();
                    if (release == null || !isNewer(app, release)) {
                        return;
                    }
                    if (prefs.getLong("skipped_code", -1L) == release.versionCode
                            && prefs.getInt("skipped_revision", -1) == release.modRevision) {
                        return;
                    }
                    final Release found = release;
                    new Handler(Looper.getMainLooper()).post(new Runnable() {
                        @Override
                        public void run() {
                            showDialog(activity, found);
                        }
                    });
                } catch (Throwable ignored) {
                }
            }
        }, "vk-mod-update").start();
    }

    private static int localRevision(Context context) {
        int id = context.getResources().getIdentifier("vk_mod_revision", "integer", context.getPackageName());
        if (id == 0) {
            return 0;
        }
        return context.getResources().getInteger(id);
    }

    private static boolean isNewer(Context context, Release release) throws Exception {
        long localCode = context.getPackageManager().getPackageInfo(context.getPackageName(), 0).getLongVersionCode();
        if (release.versionCode > localCode) {
            return true;
        }
        return release.versionCode == localCode && release.modRevision > localRevision(context);
    }

    private static void showDialog(final Activity activity, final Release release) {
        if (activity.isFinishing() || activity.isDestroyed()) {
            return;
        }
        String message = "Доступна версия " + release.versionName + ", сборка " + release.modRevision + ".";
        new AlertDialog.Builder(activity)
                .setTitle("Обновление VK Музыки")
                .setMessage(message)
                .setPositiveButton("Обновить", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        downloadAndInstall(activity, release);
                    }
                })
                .setNegativeButton("Позже", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                                .putLong("skipped_code", release.versionCode)
                                .putInt("skipped_revision", release.modRevision)
                                .apply();
                    }
                })
                .show();
    }

    private static void downloadAndInstall(final Activity activity, final Release release) {
        long required = release.size > 0L ? release.size : 100L * 1024L * 1024L;
        long available = new StatFs(activity.getCacheDir().getAbsolutePath()).getAvailableBytes();
        if (available < required + 20L * 1024L * 1024L) {
            Toast.makeText(activity, "Недостаточно места для обновления", Toast.LENGTH_LONG).show();
            return;
        }
        Toast.makeText(activity, "Загрузка обновления", Toast.LENGTH_SHORT).show();
        new Thread(new Runnable() {
            @Override
            public void run() {
                File apk = null;
                try {
                    File dir = new File(activity.getCacheDir(), "updates");
                    if (!dir.exists() && !dir.mkdirs()) {
                        throw new IllegalStateException("cache");
                    }
                    apk = new File(dir, "VK_Music_update.apk");
                    if (apk.exists() && !apk.delete()) {
                        throw new IllegalStateException("delete");
                    }
                    download(release.apkUrl, apk);
                    String hash = sha256(apk);
                    if (!hash.equalsIgnoreCase(release.sha256)) {
                        throw new IllegalStateException("sha256");
                    }
                    final Uri uri = Uri.parse("content://" + activity.getPackageName()
                            + ".fileprovider/cache/updates/" + apk.getName());
                    new Handler(Looper.getMainLooper()).post(new Runnable() {
                        @Override
                        public void run() {
                            install(activity, uri);
                        }
                    });
                } catch (Throwable error) {
                    if (apk != null) {
                        apk.delete();
                    }
                    new Handler(Looper.getMainLooper()).post(new Runnable() {
                        @Override
                        public void run() {
                            Toast.makeText(activity, "Не удалось скачать обновление", Toast.LENGTH_LONG).show();
                        }
                    });
                }
            }
        }, "vk-mod-download").start();
    }

    private static void install(Activity activity, Uri uri) {
        if (Build.VERSION.SDK_INT >= 26 && !activity.getPackageManager().canRequestPackageInstalls()) {
            Toast.makeText(activity, "Разрешите установку из этого приложения", Toast.LENGTH_LONG).show();
            Intent settings = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + activity.getPackageName()));
            activity.startActivity(settings);
            return;
        }
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(uri, "application/vnd.android.package-archive");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
        activity.startActivity(intent);
    }

    private static Release fetchLatest() throws Exception {
        JSONArray releases = new JSONArray(get(API));
        for (int r = 0; r < releases.length(); r++) {
            JSONObject release = releases.getJSONObject(r);
            if (release.optBoolean("draft", false) || release.optBoolean("prerelease", false)) {
                continue;
            }
            String tag = release.optString("tag_name", "");
            if (!tag.startsWith("vk-")) {
                continue;
            }
            JSONArray assets = release.getJSONArray("assets");
            String manifestUrl = null;
            for (int i = 0; i < assets.length(); i++) {
                JSONObject asset = assets.getJSONObject(i);
                if ("update.json".equals(asset.getString("name"))) {
                    manifestUrl = asset.getString("browser_download_url");
                    break;
                }
            }
            if (manifestUrl == null) {
                continue;
            }
            JSONObject manifest = new JSONObject(get(manifestUrl));
            Release result = new Release();
            result.versionName = manifest.getString("versionName");
            result.versionCode = manifest.getLong("versionCode");
            result.modRevision = manifest.optInt("modRevision", 0);
            result.sha256 = manifest.getString("sha256");
            result.size = manifest.optLong("size", 0L);
            String apkName = manifest.getString("apk");
            for (int i = 0; i < assets.length(); i++) {
                JSONObject asset = assets.getJSONObject(i);
                if (apkName.equals(asset.getString("name"))) {
                    result.apkUrl = asset.getString("browser_download_url");
                    return result;
                }
            }
        }
        return null;
    }

    private static String get(String address) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(20000);
        connection.setRequestProperty("User-Agent", "VKMusicModUpdater");
        connection.setRequestProperty("Accept", "application/vnd.github+json");
        try {
            int code = connection.getResponseCode();
            if (code != 200) {
                throw new IllegalStateException("http " + code);
            }
            InputStream input = new BufferedInputStream(connection.getInputStream());
            try {
                return readText(input);
            } finally {
                input.close();
            }
        } finally {
            connection.disconnect();
        }
    }

    private static String readText(InputStream input) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int read;
        while ((read = input.read(buffer)) != -1) {
            output.write(buffer, 0, read);
        }
        return output.toString("UTF-8");
    }

    private static void download(String address, File target) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(60000);
        connection.setRequestProperty("User-Agent", "VKMusicModUpdater");
        try {
            int code = connection.getResponseCode();
            if (code != 200) {
                throw new IllegalStateException("http " + code);
            }
            InputStream input = new BufferedInputStream(connection.getInputStream());
            try {
                BufferedOutputStream output = new BufferedOutputStream(new FileOutputStream(target));
                try {
                    byte[] buffer = new byte[8192];
                    int read;
                    while ((read = input.read(buffer)) != -1) {
                        output.write(buffer, 0, read);
                    }
                } finally {
                    output.close();
                }
            } finally {
                input.close();
            }
        } finally {
            connection.disconnect();
        }
    }

    private static String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        InputStream input = new BufferedInputStream(new java.io.FileInputStream(file));
        try {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) {
                digest.update(buffer, 0, read);
            }
        } finally {
            input.close();
        }
        byte[] bytes = digest.digest();
        StringBuilder result = new StringBuilder(bytes.length * 2);
        for (byte value : bytes) {
            result.append(String.format("%02x", value & 0xff));
        }
        return result.toString();
    }

    private static final class Release {
        String versionName;
        long versionCode;
        int modRevision;
        String sha256;
        String apkUrl;
        long size;
    }
}

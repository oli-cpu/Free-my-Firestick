package org.freemytv.firetv;

import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.provider.Settings;
import android.util.Base64;
import android.webkit.JavascriptInterface;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.util.List;

/**
 * window.FireTV — replaces the webOS Luna calls of the original app.
 * All methods run on WebView's JavaBridge thread and never throw into JS.
 */
public final class Bridge {
    final MainActivity act;

    Bridge(MainActivity a) {
        act = a;
    }

    /** "package\tlabel\n" for every launchable app (Fire TV launcher entries first). */
    @JavascriptInterface
    public String listApps() {
        PackageManager pm = act.getPackageManager();
        StringBuilder sb = new StringBuilder();
        Intent i = new Intent("android.intent.action.MAIN");
        i.addCategory("android.intent.category.LEANBACK_LAUNCHER");
        append(pm, sb, pm.queryIntentActivities(i, 0));
        i = new Intent("android.intent.action.MAIN");
        i.addCategory("android.intent.category.LAUNCHER");
        append(pm, sb, pm.queryIntentActivities(i, 0));
        return sb.toString();
    }

    private static void append(PackageManager pm, StringBuilder sb, List l) {
        int n = l.size();
        for (int k = 0; k < n; k++) {
            ResolveInfo r = (ResolveInfo) l.get(k);
            sb.append(r.activityInfo.packageName);
            sb.append("\t");
            sb.append(r.loadLabel(pm));
            sb.append("\n");
        }
    }

    /** App banner (or icon) as a PNG data URI, "" if unavailable. */
    @JavascriptInterface
    public String icon(String pkg) {
        try {
            PackageManager pm = act.getPackageManager();
            Drawable d = pm.getApplicationBanner(pkg);
            if (d == null) d = pm.getApplicationIcon(pkg);
            int w = d.getIntrinsicWidth();
            int h = d.getIntrinsicHeight();
            if (w <= 0) w = 192;
            if (h <= 0) h = 192;
            Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            d.setBounds(0, 0, w, h);
            d.draw(new Canvas(b));
            ByteArrayOutputStream o = new ByteArrayOutputStream();
            b.compress(Bitmap.CompressFormat.PNG, 100, o);
            return "data:image/png;base64,".concat(Base64.encodeToString(o.toByteArray(), Base64.NO_WRAP));
        } catch (Throwable t) {
            return "";
        }
    }

    /** Starts an installed app; false if it is not installed / has no launcher entry. */
    @JavascriptInterface
    public boolean launch(String pkg) {
        try {
            PackageManager pm = act.getPackageManager();
            Intent i = pm.getLeanbackLaunchIntentForPackage(pkg);
            if (i == null) {
                i = pm.getLaunchIntentForPackage(pkg);
                if (i == null) return false;
            }
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
            act.startActivity(i);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    /** ACTION_VIEW on a URL (YouTube trailer, amzn:// Appstore page); pkg "" = any app. */
    @JavascriptInterface
    public boolean openUrl(String pkg, String url) {
        try {
            Intent i = new Intent("android.intent.action.VIEW", Uri.parse(url));
            if (pkg.length() != 0) i.setPackage(pkg);
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            act.startActivity(i);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    /** Generic intent (Fire TV settings, stock home, accessibility settings). */
    @JavascriptInterface
    public boolean startIntent(String action, String category, String pkg) {
        try {
            Intent i = new Intent(action);
            if (category.length() != 0) {
                i.addCategory(category);
                // Stock Fire TV home asked for: leave a marker so HomeService does not bounce it back.
                if ("android.intent.category.HOME".equals(category)) new File(act.getFilesDir(), "stock-home").createNewFile();
            }
            if (pkg.length() != 0) i.setPackage(pkg);
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            act.startActivity(i);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    /** Settings.Secure value (used to show whether the Home-button service is enabled). */
    @JavascriptInterface
    public String getSecure(String key) {
        try {
            String v = Settings.Secure.getString(act.getContentResolver(), key);
            if (v != null) return v;
        } catch (Throwable t) {
            // fall through
        }
        return "";
    }

    @JavascriptInterface
    public void showKeyboard() {
        act.runOnUiThread(act);
    }
}

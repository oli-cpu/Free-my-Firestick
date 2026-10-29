package org.freemytv.firetv;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.os.Handler;
import android.view.accessibility.AccessibilityEvent;

import java.io.File;

/**
 * Optional accessibility service: whenever the stock Fire TV home comes up (Home button,
 * boot, Back from an app), Free My TV is shown instead.
 * Fire OS handles the Home key before accessibility services see it, so the service
 * watches which window is in front instead of filtering keys. It runs in its own small
 * process (":home") so Fire OS does not kill it together with the WebView.
 * Only the package/class of the front window is read; no screen content.
 */
public class HomeService extends AccessibilityService implements Runnable {
    static final String STOCK_HOME = "com.amazon.tv.launcher.ui.HomeActivity";   // HomeActivity_vNext on Fire OS 7
    static final long RETRY_MS = 2000;

    /** True while the user is on the stock home they opened through the Fire TV Home tile. */
    static boolean sStock;
    /** True while the stock home is the window in front. */
    static boolean sOnHome;
    Handler handler;

    @Override
    public void onAccessibilityEvent(AccessibilityEvent e) {
        try {
            if (e.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
            CharSequence p = e.getPackageName();
            if (p == null) return;
            String pkg = p.toString();
            CharSequence c = e.getClassName();
            if (c != null && c.toString().startsWith(STOCK_HOME)) {
                // The stock Fire TV home came up (Home button, boot, Back from an app).
                sOnHome = true;
                if (sStock) return;
                // Opened on purpose through the Fire TV Home tile: keep it until another app comes up.
                if (new File(getFilesDir(), "stock-home").delete()) {
                    sStock = true;
                    return;
                }
                showFreeMyTv();
                return;
            }
            // Some other window. System UI (Home press feedback) changes nothing.
            if (pkg.equals("com.android.systemui")) return;
            sOnHome = false;
            // The launcher's own screens (Amazon settings, dialogs) keep a stock-home visit going;
            // any other app ends it.
            if (pkg.equals("com.amazon.tv.launcher")) return;
            sStock = false;
        } catch (Throwable t) {
            // ignore
        }
    }

    /** Retry while the stock home is still in front. */
    @Override
    public void run() {
        if (!sOnHome) return;
        if (sStock) return;
        showFreeMyTv();
    }

    /**
     * Starts Free My TV and checks again in RETRY_MS. Fire OS holds starts back for 5 s after
     * Home and drops a held start when Home is pressed again, hence the retries.
     */
    private void showFreeMyTv() {
        try {
            if (handler == null) handler = new Handler();
            handler.removeCallbacks(this);
            handler.postDelayed(this, RETRY_MS);
            Intent i = new Intent(this, MainActivity.class);
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
        } catch (Throwable t) {
            // ignore
        }
    }

    @Override
    public void onInterrupt() {
    }
}

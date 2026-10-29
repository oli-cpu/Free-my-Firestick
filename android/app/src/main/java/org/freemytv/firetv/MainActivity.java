package org.freemytv.firetv;

import android.app.Activity;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.inputmethod.InputMethodManager;
import android.webkit.WebSettings;
import android.webkit.WebView;

/**
 * Full-screen WebView that shows the Free My TV home screen (assets/www/index.html).
 * The page talks to the Fire TV through {@link Bridge}, exposed as window.FireTV.
 */
public class MainActivity extends Activity implements Runnable {
    /** True while the home screen is in front. */
    public static boolean sFront;
    WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        WebView w = new WebView(this);
        web = w;
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        // Lay the page out at its <meta viewport width=1920> and scale it to the screen
        // (Fire TV WebViews report only 960 CSS px at xhdpi otherwise).
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        // The bundled page (file://) calls Open-Meteo/TVMaze/TMDB directly, like on webOS.
        s.setAllowUniversalAccessFromFileURLs(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportZoom(false);
        w.setBackgroundColor(0xFF000000);
        w.addJavascriptInterface(new Bridge(this), "FireTV");
        w.loadUrl("file:///android_asset/www/index.html");
        setContentView(w);
        w.requestFocus();
    }

    @Override
    protected void onResume() {
        super.onResume();
        sFront = true;
        web.evaluateJavascript("window.fmtvResume&&fmtvResume()", null);
    }

    @Override
    protected void onPause() {
        sFront = false;
        super.onPause();
    }

    /** Back and Menu go to the page instead of closing the home screen. */
    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        int code = e.getKeyCode();
        if (code == KeyEvent.KEYCODE_BACK || code == KeyEvent.KEYCODE_MENU) {
            if (e.getAction() == KeyEvent.ACTION_UP) {
                web.evaluateJavascript(code == KeyEvent.KEYCODE_BACK
                        ? "window.fmtvKey&&fmtvKey('back')"
                        : "window.fmtvKey&&fmtvKey('menu')", null);
            }
            return true;
        }
        return super.dispatchKeyEvent(e);
    }

    /** Runs on the UI thread (Bridge.showKeyboard): opens the on-screen keyboard. */
    @Override
    public void run() {
        InputMethodManager imm = (InputMethodManager) getSystemService("input_method");
        web.requestFocus();
        imm.showSoftInput(web, 0);
    }
}

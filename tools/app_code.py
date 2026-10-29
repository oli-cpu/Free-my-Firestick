"""Dalvik bytecode for Free My TV (Fire TV).

Each method mirrors the Java source in android/app/src/main/java/org/freemytv/firetv/
one-to-one; the Java files are the readable reference, this file is what the
standalone build assembles into classes.dex.
"""
from dex import Dex, ClassDef, ACC_PUBLIC, ACC_PRIVATE, ACC_PROTECTED, ACC_STATIC, ACC_FINAL, ACC_CONSTRUCTOR

PKG = 'org/freemytv/firetv'
MAIN = 'L%s/MainActivity;' % PKG
BRIDGE = 'L%s/Bridge;' % PKG
HOME = 'L%s/HomeService;' % PKG

ACT = 'Landroid/app/Activity;'
WV = 'Landroid/webkit/WebView;'
WS = 'Landroid/webkit/WebSettings;'
INTENT = 'Landroid/content/Intent;'
PM = 'Landroid/content/pm/PackageManager;'
STR = 'Ljava/lang/String;'
SB = 'Ljava/lang/StringBuilder;'
KE = 'Landroid/view/KeyEvent;'
DRW = 'Landroid/graphics/drawable/Drawable;'
JSI = 'Landroid/webkit/JavascriptInterface;'

F_WEB = MAIN + '->web:' + WV
F_FRONT = MAIN + '->sFront:Z'
F_ACT = BRIDGE + '->act:' + MAIN
F_STOCK = HOME + '->sStock:Z'
F_ONHOME = HOME + '->sOnHome:Z'
HANDLER = 'Landroid/os/Handler;'
F_HANDLER = HOME + '->handler:' + HANDLER
RETRY_MS = 2000
AE = 'Landroid/view/accessibility/AccessibilityEvent;'
CS = 'Ljava/lang/CharSequence;'
FILE = 'Ljava/io/File;'
STOCK_HOME = 'com.amazon.tv.launcher.ui.HomeActivity'   # HomeActivity_vNext on Fire OS 7

NEW_TASK_HI = 0x1000          # FLAG_ACTIVITY_NEW_TASK = 0x10000000 (high 16 bits)
LAUNCH_FLAGS = 0x10200000     # NEW_TASK | RESET_TASK_IF_NEEDED


def build():
    d = Dex()

    # ------------------------------------------------------------ MainActivity
    c = d.add(ClassDef(MAIN, ACT, ['Ljava/lang/Runnable;']))
    c.field('sFront', 'Z', ACC_PUBLIC | ACC_STATIC)
    c.field('web', WV, 0)

    c.method('<init>', '()V', ACC_PUBLIC | ACC_CONSTRUCTOR, 0, [
        ('invoke-direct', ['p0'], ACT + '-><init>()V'),
        ('return-void',),
    ])

    c.method('onCreate', '(Landroid/os/Bundle;)V', ACC_PROTECTED, 4, [
        ('invoke-super', ['p0', 'p1'], ACT + '->onCreate(Landroid/os/Bundle;)V'),
        ('new-instance', 'v0', WV),
        ('invoke-direct', ['v0', 'p0'], WV + '-><init>(Landroid/content/Context;)V'),
        ('iput-object', 'v0', 'p0', F_WEB),
        ('invoke-virtual', ['v0'], WV + '->getSettings()' + WS),
        ('move-result-object', 'v1'),
        ('const/4', 'v2', 1),
        ('invoke-virtual', ['v1', 'v2'], WS + '->setJavaScriptEnabled(Z)V'),
        ('invoke-virtual', ['v1', 'v2'], WS + '->setDomStorageEnabled(Z)V'),
        # Lay the page out at its <meta viewport width=1920> and scale it to the screen
        # (Fire TV WebViews report only 960 CSS px at xhdpi otherwise).
        ('invoke-virtual', ['v1', 'v2'], WS + '->setUseWideViewPort(Z)V'),
        ('invoke-virtual', ['v1', 'v2'], WS + '->setLoadWithOverviewMode(Z)V'),
        # The bundled page (file://) calls Open-Meteo/TVMaze/TMDB directly, like on webOS.
        ('invoke-virtual', ['v1', 'v2'], WS + '->setAllowUniversalAccessFromFileURLs(Z)V'),
        ('const/4', 'v2', 0),
        ('invoke-virtual', ['v1', 'v2'], WS + '->setMediaPlaybackRequiresUserGesture(Z)V'),
        ('invoke-virtual', ['v1', 'v2'], WS + '->setSupportZoom(Z)V'),
        ('const/high16', 'v2', 0xFF00),   # 0xFF000000 = opaque black
        ('invoke-virtual', ['v0', 'v2'], WV + '->setBackgroundColor(I)V'),
        ('new-instance', 'v1', BRIDGE),
        ('invoke-direct', ['v1', 'p0'], BRIDGE + '-><init>(' + MAIN + ')V'),
        ('const-string', 'v2', 'FireTV'),
        ('invoke-virtual', ['v0', 'v1', 'v2'], WV + '->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V'),
        ('const-string', 'v2', 'file:///android_asset/www/index.html'),
        ('invoke-virtual', ['v0', 'v2'], WV + '->loadUrl(Ljava/lang/String;)V'),
        ('invoke-virtual', ['p0', 'v0'], MAIN + '->setContentView(Landroid/view/View;)V'),
        ('invoke-virtual', ['v0'], WV + '->requestFocus()Z'),
        ('return-void',),
    ])

    c.method('onResume', '()V', ACC_PROTECTED, 3, [
        ('invoke-super', ['p0'], ACT + '->onResume()V'),
        ('const/4', 'v0', 1),
        ('sput-boolean', 'v0', F_FRONT),
        ('iget-object', 'v0', 'p0', F_WEB),
        ('const-string', 'v1', 'window.fmtvResume&&fmtvResume()'),
        ('const/4', 'v2', 0),
        ('invoke-virtual', ['v0', 'v1', 'v2'], WV + '->evaluateJavascript(Ljava/lang/String;Landroid/webkit/ValueCallback;)V'),
        ('return-void',),
    ])

    c.method('onPause', '()V', ACC_PROTECTED, 1, [
        ('const/4', 'v0', 0),
        ('sput-boolean', 'v0', F_FRONT),
        ('invoke-super', ['p0'], ACT + '->onPause()V'),
        ('return-void',),
    ])

    c.method('dispatchKeyEvent', '(' + KE + ')Z', ACC_PUBLIC, 5, [
        ('invoke-virtual', ['p1'], KE + '->getKeyCode()I'),
        ('move-result', 'v0'),
        ('const/4', 'v1', 4),                 # KEYCODE_BACK
        ('if-eq', 'v0', 'v1', 'handle'),
        ('const/16', 'v1', 82),               # KEYCODE_MENU
        ('if-eq', 'v0', 'v1', 'handle'),
        ('invoke-super', ['p0', 'p1'], ACT + '->dispatchKeyEvent(' + KE + ')Z'),
        ('move-result', 'v0'),
        ('return', 'v0'),
        ('label', 'handle'),
        ('invoke-virtual', ['p1'], KE + '->getAction()I'),
        ('move-result', 'v1'),
        ('const/4', 'v2', 1),                 # ACTION_UP
        ('if-ne', 'v1', 'v2', 'done'),
        ('iget-object', 'v2', 'p0', F_WEB),
        ('const-string', 'v3', "window.fmtvKey&&fmtvKey('menu')"),
        ('const/4', 'v1', 4),
        ('if-ne', 'v0', 'v1', 'eval'),
        ('const-string', 'v3', "window.fmtvKey&&fmtvKey('back')"),
        ('label', 'eval'),
        ('const/4', 'v4', 0),
        ('invoke-virtual', ['v2', 'v3', 'v4'], WV + '->evaluateJavascript(Ljava/lang/String;Landroid/webkit/ValueCallback;)V'),
        ('label', 'done'),
        ('const/4', 'v0', 1),
        ('return', 'v0'),
    ])

    # Runnable.run(): executed on the UI thread to show the on-screen keyboard.
    c.method('run', '()V', ACC_PUBLIC, 3, [
        ('const-string', 'v0', 'input_method'),
        ('invoke-virtual', ['p0', 'v0'], MAIN + '->getSystemService(Ljava/lang/String;)Ljava/lang/Object;'),
        ('move-result-object', 'v0'),
        ('check-cast', 'v0', 'Landroid/view/inputmethod/InputMethodManager;'),
        ('iget-object', 'v1', 'p0', F_WEB),
        ('invoke-virtual', ['v1'], WV + '->requestFocus()Z'),
        ('const/4', 'v2', 0),
        ('invoke-virtual', ['v0', 'v1', 'v2'], 'Landroid/view/inputmethod/InputMethodManager;->showSoftInput(Landroid/view/View;I)Z'),
        ('return-void',),
    ])

    # ------------------------------------------------------------ Bridge (window.FireTV)
    b = d.add(ClassDef(BRIDGE, 'Ljava/lang/Object;', [], ACC_PUBLIC | ACC_FINAL))
    b.field('act', MAIN, ACC_FINAL)

    b.method('<init>', '(' + MAIN + ')V', ACC_CONSTRUCTOR, 0, [
        ('invoke-direct', ['p0'], 'Ljava/lang/Object;-><init>()V'),
        ('iput-object', 'p1', 'p0', F_ACT),
        ('return-void',),
    ])

    b.method('listApps', '()' + STR, ACC_PUBLIC, 5, [
        ('iget-object', 'v0', 'p0', F_ACT),
        ('invoke-virtual', ['v0'], MAIN + '->getPackageManager()' + PM),
        ('move-result-object', 'v0'),
        ('new-instance', 'v1', SB),
        ('invoke-direct', ['v1'], SB + '-><init>()V'),
        ('const-string', 'v3', 'android.intent.action.MAIN'),
        ('new-instance', 'v2', INTENT),
        ('invoke-direct', ['v2', 'v3'], INTENT + '-><init>(' + STR + ')V'),
        ('const-string', 'v3', 'android.intent.category.LEANBACK_LAUNCHER'),
        ('invoke-virtual', ['v2', 'v3'], INTENT + '->addCategory(' + STR + ')' + INTENT),
        ('const/4', 'v4', 0),
        ('invoke-virtual', ['v0', 'v2', 'v4'], PM + '->queryIntentActivities(' + INTENT + 'I)Ljava/util/List;'),
        ('move-result-object', 'v4'),
        ('invoke-static', ['v0', 'v1', 'v4'], BRIDGE + '->append(' + PM + SB + 'Ljava/util/List;)V'),
        ('const-string', 'v3', 'android.intent.action.MAIN'),
        ('new-instance', 'v2', INTENT),
        ('invoke-direct', ['v2', 'v3'], INTENT + '-><init>(' + STR + ')V'),
        ('const-string', 'v3', 'android.intent.category.LAUNCHER'),
        ('invoke-virtual', ['v2', 'v3'], INTENT + '->addCategory(' + STR + ')' + INTENT),
        ('const/4', 'v4', 0),
        ('invoke-virtual', ['v0', 'v2', 'v4'], PM + '->queryIntentActivities(' + INTENT + 'I)Ljava/util/List;'),
        ('move-result-object', 'v4'),
        ('invoke-static', ['v0', 'v1', 'v4'], BRIDGE + '->append(' + PM + SB + 'Ljava/util/List;)V'),
        ('invoke-virtual', ['v1'], SB + '->toString()' + STR),
        ('move-result-object', 'v0'),
        ('return-object', 'v0'),
    ], annotations=[JSI])

    b.method('append', '(' + PM + SB + 'Ljava/util/List;)V', ACC_PRIVATE | ACC_STATIC, 4, [
        ('invoke-interface', ['p2'], 'Ljava/util/List;->size()I'),
        ('move-result', 'v0'),
        ('const/4', 'v1', 0),
        ('label', 'loop'),
        ('if-ge', 'v1', 'v0', 'end'),
        ('invoke-interface', ['p2', 'v1'], 'Ljava/util/List;->get(I)Ljava/lang/Object;'),
        ('move-result-object', 'v2'),
        ('check-cast', 'v2', 'Landroid/content/pm/ResolveInfo;'),
        ('iget-object', 'v3', 'v2', 'Landroid/content/pm/ResolveInfo;->activityInfo:Landroid/content/pm/ActivityInfo;'),
        ('iget-object', 'v3', 'v3', 'Landroid/content/pm/ActivityInfo;->packageName:' + STR),
        ('invoke-virtual', ['p1', 'v3'], SB + '->append(' + STR + ')' + SB),
        ('const-string', 'v3', '\t'),
        ('invoke-virtual', ['p1', 'v3'], SB + '->append(' + STR + ')' + SB),
        ('invoke-virtual', ['v2', 'p0'], 'Landroid/content/pm/ResolveInfo;->loadLabel(' + PM + ')Ljava/lang/CharSequence;'),
        ('move-result-object', 'v3'),
        ('invoke-virtual', ['p1', 'v3'], SB + '->append(Ljava/lang/CharSequence;)' + SB),
        ('const-string', 'v3', '\n'),
        ('invoke-virtual', ['p1', 'v3'], SB + '->append(' + STR + ')' + SB),
        ('add-int/lit8', 'v1', 'v1', 1),
        ('goto/16', 'loop'),
        ('label', 'end'),
        ('return-void',),
    ])

    b.method('icon', '(' + STR + ')' + STR, ACC_PUBLIC, 8, [
        ('try', 'catch'),
        ('iget-object', 'v0', 'p0', F_ACT),
        ('invoke-virtual', ['v0'], MAIN + '->getPackageManager()' + PM),
        ('move-result-object', 'v0'),
        ('invoke-virtual', ['v0', 'p1'], PM + '->getApplicationBanner(' + STR + ')' + DRW),
        ('move-result-object', 'v1'),
        ('if-nez', 'v1', 'have'),
        ('invoke-virtual', ['v0', 'p1'], PM + '->getApplicationIcon(' + STR + ')' + DRW),
        ('move-result-object', 'v1'),
        ('label', 'have'),
        ('invoke-virtual', ['v1'], DRW + '->getIntrinsicWidth()I'),
        ('move-result', 'v2'),
        ('invoke-virtual', ['v1'], DRW + '->getIntrinsicHeight()I'),
        ('move-result', 'v3'),
        ('if-gtz', 'v2', 'wok'),
        ('const/16', 'v2', 192),
        ('label', 'wok'),
        ('if-gtz', 'v3', 'hok'),
        ('const/16', 'v3', 192),
        ('label', 'hok'),
        ('sget-object', 'v4', 'Landroid/graphics/Bitmap$Config;->ARGB_8888:Landroid/graphics/Bitmap$Config;'),
        ('invoke-static', ['v2', 'v3', 'v4'], 'Landroid/graphics/Bitmap;->createBitmap(IILandroid/graphics/Bitmap$Config;)Landroid/graphics/Bitmap;'),
        ('move-result-object', 'v4'),
        ('new-instance', 'v5', 'Landroid/graphics/Canvas;'),
        ('invoke-direct', ['v5', 'v4'], 'Landroid/graphics/Canvas;-><init>(Landroid/graphics/Bitmap;)V'),
        ('const/4', 'v6', 0),
        ('invoke-virtual', ['v1', 'v6', 'v6', 'v2', 'v3'], DRW + '->setBounds(IIII)V'),
        ('invoke-virtual', ['v1', 'v5'], DRW + '->draw(Landroid/graphics/Canvas;)V'),
        ('new-instance', 'v5', 'Ljava/io/ByteArrayOutputStream;'),
        ('invoke-direct', ['v5'], 'Ljava/io/ByteArrayOutputStream;-><init>()V'),
        ('sget-object', 'v6', 'Landroid/graphics/Bitmap$CompressFormat;->PNG:Landroid/graphics/Bitmap$CompressFormat;'),
        ('const/16', 'v7', 100),
        ('invoke-virtual', ['v4', 'v6', 'v7', 'v5'], 'Landroid/graphics/Bitmap;->compress(Landroid/graphics/Bitmap$CompressFormat;ILjava/io/OutputStream;)Z'),
        ('invoke-virtual', ['v5'], 'Ljava/io/ByteArrayOutputStream;->toByteArray()[B'),
        ('move-result-object', 'v5'),
        ('const/4', 'v6', 2),                  # Base64.NO_WRAP
        ('invoke-static', ['v5', 'v6'], 'Landroid/util/Base64;->encodeToString([BI)' + STR),
        ('move-result-object', 'v5'),
        ('const-string', 'v6', 'data:image/png;base64,'),
        ('invoke-virtual', ['v6', 'v5'], STR + '->concat(' + STR + ')' + STR),
        ('move-result-object', 'v5'),
        ('return-object', 'v5'),
        ('endtry',),
        ('label', 'catch'),
        ('const-string', 'v0', ''),
        ('return-object', 'v0'),
    ], annotations=[JSI])

    b.method('launch', '(' + STR + ')Z', ACC_PUBLIC, 3, [
        ('try', 'catch'),
        ('iget-object', 'v0', 'p0', F_ACT),
        ('invoke-virtual', ['v0'], MAIN + '->getPackageManager()' + PM),
        ('move-result-object', 'v0'),
        ('invoke-virtual', ['v0', 'p1'], PM + '->getLeanbackLaunchIntentForPackage(' + STR + ')' + INTENT),
        ('move-result-object', 'v1'),
        ('if-nez', 'v1', 'have'),
        ('invoke-virtual', ['v0', 'p1'], PM + '->getLaunchIntentForPackage(' + STR + ')' + INTENT),
        ('move-result-object', 'v1'),
        ('if-eqz', 'v1', 'catch'),
        ('label', 'have'),
        ('const', 'v2', LAUNCH_FLAGS),
        ('invoke-virtual', ['v1', 'v2'], INTENT + '->addFlags(I)' + INTENT),
        ('iget-object', 'v0', 'p0', F_ACT),
        ('invoke-virtual', ['v0', 'v1'], MAIN + '->startActivity(' + INTENT + ')V'),
        ('const/4', 'v0', 1),
        ('return', 'v0'),
        ('endtry',),
        ('label', 'catch'),
        ('const/4', 'v0', 0),
        ('return', 'v0'),
    ], annotations=[JSI])

    b.method('openUrl', '(' + STR + STR + ')Z', ACC_PUBLIC, 3, [
        ('try', 'catch'),
        ('const-string', 'v1', 'android.intent.action.VIEW'),
        ('invoke-static', ['p2'], 'Landroid/net/Uri;->parse(' + STR + ')Landroid/net/Uri;'),
        ('move-result-object', 'v2'),
        ('new-instance', 'v0', INTENT),
        ('invoke-direct', ['v0', 'v1', 'v2'], INTENT + '-><init>(' + STR + 'Landroid/net/Uri;)V'),
        ('invoke-virtual', ['p1'], STR + '->length()I'),
        ('move-result', 'v1'),
        ('if-eqz', 'v1', 'nopkg'),
        ('invoke-virtual', ['v0', 'p1'], INTENT + '->setPackage(' + STR + ')' + INTENT),
        ('label', 'nopkg'),
        ('const/high16', 'v1', NEW_TASK_HI),
        ('invoke-virtual', ['v0', 'v1'], INTENT + '->addFlags(I)' + INTENT),
        ('iget-object', 'v1', 'p0', F_ACT),
        ('invoke-virtual', ['v1', 'v0'], MAIN + '->startActivity(' + INTENT + ')V'),
        ('const/4', 'v0', 1),
        ('return', 'v0'),
        ('endtry',),
        ('label', 'catch'),
        ('const/4', 'v0', 0),
        ('return', 'v0'),
    ], annotations=[JSI])

    b.method('startIntent', '(' + STR + STR + STR + ')Z', ACC_PUBLIC, 4, [
        ('try', 'catch'),
        ('new-instance', 'v0', INTENT),
        ('invoke-direct', ['v0', 'p1'], INTENT + '-><init>(' + STR + ')V'),
        ('invoke-virtual', ['p2'], STR + '->length()I'),
        ('move-result', 'v1'),
        ('if-eqz', 'v1', 'nocat'),
        ('invoke-virtual', ['v0', 'p2'], INTENT + '->addCategory(' + STR + ')' + INTENT),
        # Stock Fire TV home asked for: leave a marker so HomeService does not bounce it back.
        ('const-string', 'v1', 'android.intent.category.HOME'),
        ('invoke-virtual', ['v1', 'p2'], STR + '->equals(Ljava/lang/Object;)Z'),
        ('move-result', 'v1'),
        ('if-eqz', 'v1', 'nocat'),
        ('iget-object', 'v1', 'p0', F_ACT),
        ('invoke-virtual', ['v1'], MAIN + '->getFilesDir()' + FILE),
        ('move-result-object', 'v1'),
        ('new-instance', 'v2', FILE),
        ('const-string', 'v3', 'stock-home'),
        ('invoke-direct', ['v2', 'v1', 'v3'], FILE + '-><init>(' + FILE + STR + ')V'),
        ('invoke-virtual', ['v2'], FILE + '->createNewFile()Z'),
        ('label', 'nocat'),
        ('invoke-virtual', ['p3'], STR + '->length()I'),
        ('move-result', 'v1'),
        ('if-eqz', 'v1', 'nopkg'),
        ('invoke-virtual', ['v0', 'p3'], INTENT + '->setPackage(' + STR + ')' + INTENT),
        ('label', 'nopkg'),
        ('const/high16', 'v1', NEW_TASK_HI),
        ('invoke-virtual', ['v0', 'v1'], INTENT + '->addFlags(I)' + INTENT),
        ('iget-object', 'v1', 'p0', F_ACT),
        ('invoke-virtual', ['v1', 'v0'], MAIN + '->startActivity(' + INTENT + ')V'),
        ('const/4', 'v0', 1),
        ('return', 'v0'),
        ('endtry',),
        ('label', 'catch'),
        ('const/4', 'v0', 0),
        ('return', 'v0'),
    ], annotations=[JSI])

    b.method('getSecure', '(' + STR + ')' + STR, ACC_PUBLIC, 2, [
        ('try', 'catch'),
        ('iget-object', 'v0', 'p0', F_ACT),
        ('invoke-virtual', ['v0'], MAIN + '->getContentResolver()Landroid/content/ContentResolver;'),
        ('move-result-object', 'v0'),
        ('invoke-static', ['v0', 'p1'], 'Landroid/provider/Settings$Secure;->getString(Landroid/content/ContentResolver;' + STR + ')' + STR),
        ('move-result-object', 'v0'),
        ('if-eqz', 'v0', 'catch'),
        ('return-object', 'v0'),
        ('endtry',),
        ('label', 'catch'),
        ('const-string', 'v0', ''),
        ('return-object', 'v0'),
    ], annotations=[JSI])

    b.method('showKeyboard', '()V', ACC_PUBLIC, 1, [
        ('iget-object', 'v0', 'p0', F_ACT),
        ('invoke-virtual', ['v0', 'v0'], MAIN + '->runOnUiThread(Ljava/lang/Runnable;)V'),
        ('return-void',),
    ], annotations=[JSI])

    # ------------------------------------------------------------ HomeService
    h = d.add(ClassDef(HOME, 'Landroid/accessibilityservice/AccessibilityService;', ['Ljava/lang/Runnable;']))
    h.field('sStock', 'Z', ACC_STATIC)
    h.field('sOnHome', 'Z', ACC_STATIC)
    h.field('handler', HANDLER, 0)
    h.method('<init>', '()V', ACC_PUBLIC | ACC_CONSTRUCTOR, 0, [
        ('invoke-direct', ['p0'], 'Landroid/accessibilityservice/AccessibilityService;-><init>()V'),
        ('return-void',),
    ])
    h.method('onAccessibilityEvent', '(' + AE + ')V', ACC_PUBLIC, 3, [
        ('try', 'done'),
        ('invoke-virtual', ['p1'], AE + '->getEventType()I'),
        ('move-result', 'v0'),
        ('const/16', 'v1', 32),               # TYPE_WINDOW_STATE_CHANGED
        ('if-ne', 'v0', 'v1', 'done'),
        ('invoke-virtual', ['p1'], AE + '->getPackageName()' + CS),
        ('move-result-object', 'v0'),
        ('if-eqz', 'v0', 'done'),
        ('invoke-interface', ['v0'], CS + '->toString()' + STR),
        ('move-result-object', 'v0'),
        ('invoke-virtual', ['p1'], AE + '->getClassName()' + CS),
        ('move-result-object', 'v1'),
        ('if-eqz', 'v1', 'other'),
        ('invoke-interface', ['v1'], CS + '->toString()' + STR),
        ('move-result-object', 'v1'),
        ('const-string', 'v2', STOCK_HOME),
        ('invoke-virtual', ['v1', 'v2'], STR + '->startsWith(' + STR + ')Z'),
        ('move-result', 'v1'),
        ('if-nez', 'v1', 'stock'),
        # Some other window. System UI (Home press feedback) changes nothing.
        ('label', 'other'),
        ('const-string', 'v1', 'com.android.systemui'),
        ('invoke-virtual', ['v0', 'v1'], STR + '->equals(Ljava/lang/Object;)Z'),
        ('move-result', 'v1'),
        ('if-nez', 'v1', 'done'),
        ('const/4', 'v1', 0),
        ('sput-boolean', 'v1', F_ONHOME),
        # The launcher's own screens (Amazon settings, dialogs) keep a stock-home visit going;
        # any other app ends it.
        ('const-string', 'v1', 'com.amazon.tv.launcher'),
        ('invoke-virtual', ['v0', 'v1'], STR + '->equals(Ljava/lang/Object;)Z'),
        ('move-result', 'v1'),
        ('if-nez', 'v1', 'done'),
        ('const/4', 'v1', 0),
        ('sput-boolean', 'v1', F_STOCK),
        ('goto/16', 'done'),
        # The stock Fire TV home came up (Home button, boot, Back from an app).
        ('label', 'stock'),
        ('const/4', 'v1', 1),
        ('sput-boolean', 'v1', F_ONHOME),
        ('sget-boolean', 'v1', F_STOCK),
        ('if-nez', 'v1', 'done'),
        # Opened on purpose through the Fire TV Home tile: keep it until another app comes up.
        ('invoke-virtual', ['p0'], HOME + '->getFilesDir()' + FILE),
        ('move-result-object', 'v1'),
        ('new-instance', 'v0', FILE),
        ('const-string', 'v2', 'stock-home'),
        ('invoke-direct', ['v0', 'v1', 'v2'], FILE + '-><init>(' + FILE + STR + ')V'),
        ('invoke-virtual', ['v0'], FILE + '->delete()Z'),
        ('move-result', 'v1'),
        ('if-eqz', 'v1', 'bounce'),
        ('const/4', 'v1', 1),
        ('sput-boolean', 'v1', F_STOCK),
        ('goto/16', 'done'),
        ('label', 'bounce'),
        ('invoke-direct', ['p0'], HOME + '->showFreeMyTv()V'),
        ('endtry',),
        ('label', 'done'),
        ('return-void',),
    ])
    # Runnable.run(): retry while the stock home is still in front.
    h.method('run', '()V', ACC_PUBLIC, 1, [
        ('sget-boolean', 'v0', F_ONHOME),
        ('if-eqz', 'v0', 'done'),
        ('sget-boolean', 'v0', F_STOCK),
        ('if-nez', 'v0', 'done'),
        ('invoke-direct', ['p0'], HOME + '->showFreeMyTv()V'),
        ('label', 'done'),
        ('return-void',),
    ])
    # Starts Free My TV and checks again in RETRY_MS. Fire OS holds starts back for 5 s after
    # Home and drops a held start when Home is pressed again, hence the retries.
    h.method('showFreeMyTv', '()V', ACC_PRIVATE, 3, [
        ('try', 'done'),
        ('iget-object', 'v0', 'p0', F_HANDLER),
        ('if-nez', 'v0', 'have'),
        ('new-instance', 'v0', HANDLER),
        ('invoke-direct', ['v0'], HANDLER + '-><init>()V'),
        ('iput-object', 'v0', 'p0', F_HANDLER),
        ('label', 'have'),
        ('invoke-virtual', ['v0', 'p0'], HANDLER + '->removeCallbacks(Ljava/lang/Runnable;)V'),
        ('const-wide/16', 'v1', RETRY_MS),
        ('invoke-virtual', ['v0', 'p0', 'v1', 'v2'], HANDLER + '->postDelayed(Ljava/lang/Runnable;J)Z'),
        ('const-class', 'v1', MAIN),
        ('new-instance', 'v0', INTENT),
        ('invoke-direct', ['v0', 'p0', 'v1'], INTENT + '-><init>(Landroid/content/Context;Ljava/lang/Class;)V'),
        ('const/high16', 'v1', NEW_TASK_HI),
        ('invoke-virtual', ['v0', 'v1'], INTENT + '->addFlags(I)' + INTENT),
        ('invoke-virtual', ['p0', 'v0'], HOME + '->startActivity(' + INTENT + ')V'),
        ('endtry',),
        ('label', 'done'),
        ('return-void',),
    ])
    h.method('onInterrupt', '()V', ACC_PUBLIC, 0, [
        ('return-void',),
    ])
    return d


if __name__ == '__main__':
    import sys
    open(sys.argv[1], 'wb').write(build().build())

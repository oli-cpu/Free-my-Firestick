"""Turns the webOS UI (app/index.html) into the Fire TV UI.

Every edit is an exact, asserted text replacement so the port can be re-run on
newer upstream versions and fails loudly if upstream code moved.
Usage: python3 port_ui.py <webos index.html> <output index.html>
"""
import re
import sys

src = open(sys.argv[1], encoding='utf-8').read()
out = src


def rep(old, new, count=1):
    global out
    n = out.count(old)
    assert n == count, 'expected %d x %r, found %d' % (count, old[:80], n)
    out = out.replace(old, new)


def rep_block(start, end, new, keep_end=True):
    """Replace text from `start` (inclusive) up to `end` (exclusive if keep_end)."""
    global out
    i = out.index(start)
    j = out.index(end, i)
    assert out.count(start) == 1, start
    out = out[:i] + new + (out[j:] if keep_end else out[j + len(end):])


# ---------------------------------------------------------------- head / CSS
rep('    <script src="webOSTV.js"></script>\n', '')
rep('        .app-icon img.tile-brand-logo { width: 76%; height: 76%; }\n',
    '        .app-icon img.tile-brand-logo { width: 76%; height: 76%; }\n'
    '        /* Fire TV: no focus rings from the Android WebView; focus is drawn via .focused */\n'
    '        :focus { outline: none; }\n'
    '        .app-toggle-item .not-installed { opacity: 0.55; }\n')

# The UI is laid out for 1920x1080. The Android WebView honours this width (useWideViewPort +
# loadWithOverviewMode) and scales to the real screen; desktop browsers ignore the tag.
rep('<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    '<meta name="viewport" content="width=1920">')

# ---------------------------------------------------------------- static HTML
rep('<div class="hero-desc" id="heroDesc">Navigate smoothly with Magic Remote D-Pad or pointer. Launch apps in 100ms with zero ads.</div>',
    '<div class="hero-desc" id="heroDesc">Navigate with your Fire TV remote. Launch apps instantly with zero ads.</div>')
rep('''                <div class="modal-section-title">2. HDMI Devices</div>
                <p style="color: var(--text-secondary); margin: 0 0 12px;">Press a port to cycle its device. Save &amp; Apply to keep your choices.</p>''',
    '''                <div class="modal-section-title">2. Home Button</div>
                <p style="color: var(--text-secondary); margin: 0 0 12px;">Let the Fire TV Home button open Free My TV. Press Home twice to reach the original Fire TV home.</p>''')

# ---------------------------------------------------------------- catalog
rep_block('        // --- Default Catalog of Apps ---', '        // Device artwork is bundled inline', r'''        // --- Fire TV bridge ---
        // window.FireTV is injected by the Android wrapper (see android/.../Bridge.java):
        // listApps(), icon(pkg), launch(pkg), openUrl(pkg, url), startIntent(action, category, pkg),
        // getSecure(key), showKeyboard(). In a desktop browser it is missing (preview mode).
        var FTV = window.FireTV || null;
        var SELF_PKG = 'org.freemytv.firetv';

        // --- Default Catalog of Apps (Fire TV package names; alt = other known package names) ---
        var DEFAULT_CATALOG = [
            { id: 'com.amazon.firetv.youtube', alt: ['com.google.android.youtube.tv', 'com.google.android.youtube'], title: 'YouTube', tag: 'Streaming', desc: 'Watch 4K videos, live streams, music, and coding radio.', color: '#ff0000', badge: 'YT', bg: 'linear-gradient(135deg, #ff0000, #b00000)' },
            { id: 'com.netflix.ninja', title: 'Netflix', tag: 'Movies & Series', desc: 'Unlimited movies, TV shows, and originals in 4K Dolby Vision.', color: '#e50914', badge: 'N', bg: 'linear-gradient(135deg, #1f1f1f, #080808)' },
            { id: 'com.amazon.firebat', alt: ['com.amazon.avod', 'com.amazon.avod.thirdpartyclient'], title: 'Prime Video', tag: 'Movies & Shows', desc: 'Watch Amazon Originals, popular movies, and live sports.', color: '#00a8e1', badge: 'prime', bg: 'linear-gradient(135deg, #00a8e1, #00628a)' },
            { id: 'com.disney.disneyplus', title: 'Disney+', tag: 'Streaming', desc: 'Disney, Pixar, Marvel, Star Wars, and National Geographic.', color: '#113ccf', badge: 'D+', bg: 'linear-gradient(135deg, #113ccf, #071961)' },
            { id: 'com.zattoo.player', title: 'Zattoo', tag: 'Live TV', desc: 'Live TV channels, replay, and recordings.', color: '#ff7a00', badge: 'Z', bg: 'linear-gradient(135deg, #ff7a00, #b34f00)' },
            { id: 'com.crunchyroll.crunchyroid', title: 'Crunchyroll', tag: 'Anime', desc: 'Stream the world\'s largest anime library and simulcasts.', color: '#f47521', badge: 'CR', bg: 'linear-gradient(135deg, #f47521, #c4570d)' },
            { id: 'com.plexapp.android', title: 'Plex', tag: 'Personal Media', desc: 'Stream your personal home cinema, movies, and music library.', color: '#e5a00d', badge: '>', bg: 'linear-gradient(135deg, #e5a00d, #9e6d00)' },
            { id: 'com.spotify.tv.android', alt: ['com.spotify.music'], title: 'Spotify', tag: 'Music', desc: 'Listen to millions of songs, albums, and podcasts on your TV.', color: '#1db954', badge: 'SP', bg: 'linear-gradient(135deg, #1db954, #0f7833)' },
            { id: 'com.globo.globotv', title: 'Globoplay', tag: 'Brazil Streaming', desc: 'Original series, live channels, sports, and cinema.', color: '#fb003f', badge: 'globo', bg: 'linear-gradient(135deg, #fb003f, #aa002a)' },
            { id: 'org.xbmc.kodi', title: 'Kodi', tag: 'Local Media', desc: 'Play your own media library from USB, NAS, or DLNA.', color: '#17b2e7', badge: 'KODI', bg: 'linear-gradient(135deg, #17b2e7, #0b6d8f)' },
            { id: 'org.videolan.vlc', title: 'VLC', tag: 'Local Media', desc: 'Play photos, videos, and music from USB or DLNA servers.', color: '#ff8800', badge: 'VLC', bg: 'linear-gradient(135deg, #ff8800, #b35f00)' },
            { id: 'com.amazon.cloud9', title: 'Silk Browser', tag: 'Internet', desc: 'Full-screen web browsing on your Fire TV.', color: '#5856d6', badge: 'WEB', bg: 'linear-gradient(135deg, #5856d6, #3634a3)' },
            { id: 'com.esaba.downloader', title: 'Downloader', tag: 'System', desc: 'Download and install apps from the web (sideloading).', color: '#f2a20c', badge: 'DL', bg: 'linear-gradient(135deg, #f2a20c, #a86f00)' },
            { id: 'fmtv:firetvhome', action: 'android.intent.action.MAIN', category: 'android.intent.category.HOME', art: 'home', title: 'Fire TV Home', tag: 'System', desc: 'Open the original Fire TV home screen (app library, Amazon settings).', color: '#ff9900', badge: 'HOME', bg: 'linear-gradient(135deg, #ff9900, #a35f00)' },
            { id: 'fmtv:settings', action: 'android.settings.SETTINGS', art: 'gear', title: 'Settings', tag: 'System', desc: 'Open the Fire TV settings.', color: '#8e8e93', badge: 'SET', bg: 'linear-gradient(135deg, #636366, #2c2c2e)' }
        ];

''')

rep('''                pc: '<rect x="15" y="26" width="90" height="61" rx="6" fill="none" stroke="white" stroke-width="6"/><path d="M60 88v13m-22 0h44M24 75h72" stroke="white" stroke-width="6"/>',''',
    '''                pc: '<rect x="15" y="26" width="90" height="61" rx="6" fill="none" stroke="white" stroke-width="6"/><path d="M60 88v13m-22 0h44M24 75h72" stroke="white" stroke-width="6"/>',
                home: '<path d="M22 58 60 24l38 34" fill="none" stroke="white" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><path d="M33 52v42h20V72h14v22h20V52" fill="none" stroke="white" stroke-width="7" stroke-linejoin="round"/>',
                gear: '<circle cx="60" cy="60" r="15" fill="none" stroke="white" stroke-width="7"/><path d="M60 18v14m0 56v14M18 60h14m56 0h14M30.3 30.3l9.9 9.9m39.6 39.6 9.9 9.9M30.3 89.7l9.9-9.9m39.6-39.6 9.9-9.9" stroke="white" stroke-width="7" stroke-linecap="round"/><circle cx="60" cy="60" r="31" fill="none" stroke="white" stroke-width="6"/>',''')

rep_block('        var APP_LOGOS = {', '        function addTileImage(', '''        var APP_LOGOS = {
            'com.amazon.firetv.youtube': 'youtube',
            'com.netflix.ninja': 'netflix',
            'com.plexapp.android': 'plex',
            'com.crunchyroll.crunchyroid': 'crunchyroll',
            'com.globo.globotv': 'globoplay',
            'com.amazon.firebat': 'amazonprime',
            'com.disney.disneyplus': 'disneyplus',
            'com.spotify.tv.android': 'spotify'
        };
''')

rep_block('        function launchPointIcon(lp) {', '        // Defaults favor', '''        // Installed apps without a bundled logo show their Fire TV banner/icon (PNG data URI
        // rendered by the Android side). Cached per package; one bridge call per app.
        var ICON_CACHE = {};
        function nativeIcon(app) {
            var pkg = app.installedPkg;
            if (!FTV || !pkg) return '';
            if (!Object.prototype.hasOwnProperty.call(ICON_CACHE, pkg)) {
                var uri = '';
                try { uri = String(FTV.icon(pkg) || ''); } catch (e) {}
                ICON_CACHE[pkg] = /^data:image\\/png;base64,[A-Za-z0-9+\\/=]+$/.test(uri) ? uri : '';
            }
            return ICON_CACHE[pkg];
        }

''')

rep_block('        var DEFAULT_FAVORITES = [', '        var FALLBACK_MOVIES', '''        var DEFAULT_FAVORITES = [
            'com.amazon.firetv.youtube',
            'com.netflix.ninja',
            'com.amazon.firebat',
            'com.disney.disneyplus',
            'com.zattoo.player',
            'com.spotify.tv.android',
            'fmtv:firetvhome',
            'fmtv:settings'
        ];

''')

rep("app: 'netflix'", "app: 'com.netflix.ninja'", 8)
rep("app: 'amazon'", "app: 'com.amazon.firebat'", 1)
rep("app: 'com.crunchyroll.webapp'", "app: 'com.crunchyroll.crunchyroid'", 1)
rep("items[i].app = 'youtube.leanback.v4';", "items[i].app = 'com.amazon.firetv.youtube';", 1)

rep("            favorites: JSON.parse(localStorage.getItem('fmtv_favorites') || 'null') || DEFAULT_FAVORITES.slice(),\n",
    "            favorites: JSON.parse(localStorage.getItem('fmtv_favorites') || 'null') || DEFAULT_FAVORITES.slice(),\n"
    "            favoritesSaved: !!localStorage.getItem('fmtv_favorites'),\n"
    "            nativeReady: false,\n")

# ---------------------------------------------------------------- discovery + launch
rep_block('        // --- Discover Installed Apps from LG webOS ---', '        // --- Native webOS App Launch ---', r'''        // --- Discover Installed Apps on the Fire TV ---
        // FireTV.listApps() returns "package<TAB>label" lines for every launchable app
        // (Fire TV/leanback launcher entries first, then phone-style launcher entries).
        function isAvailable(app) { return !!(app && (app.action || app.installedPkg)); }

        function discoverTVApps() {
            if (!FTV) return;
            var raw = '';
            try { raw = String(FTV.listApps() || ''); } catch (e) { return; }
            var seen = {};
            var found = [];
            raw.split('\n').forEach(function(line) {
                var tab = line.indexOf('\t');
                if (tab <= 0) return;
                var pkg = line.slice(0, tab);
                var title = line.slice(tab + 1).replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '');
                if (seen[pkg] || pkg === SELF_PKG || !/^[A-Za-z0-9_.]+$/.test(pkg)) return;
                seen[pkg] = true;
                found.push({ pkg: pkg, title: title || pkg });
            });
            if (!found.length) return;
            state.nativeReady = true;

            // Rebuilt on every call so newly installed / removed apps show up after returning home.
            var catalog = DEFAULT_CATALOG.map(function(entry) {
                var copy = shallowClone(entry);
                copy.installedPkg = null;
                var candidates = [entry.id].concat(entry.alt || []);
                for (var i = 0; i < candidates.length; i++) {
                    if (seen[candidates[i]]) { copy.installedPkg = candidates[i]; break; }
                }
                return copy;
            });
            found.forEach(function(f) {
                if (arrFind(catalog, function(c) { return c.installedPkg === f.pkg; })) return;
                catalog.push({
                    id: f.pkg,
                    installedPkg: f.pkg,
                    title: f.title,
                    tag: 'Installed App',
                    desc: 'Installed on this Fire TV.',
                    color: '#0a84ff',
                    badge: f.title.substring(0, 3).toUpperCase(),
                    bg: 'linear-gradient(135deg, #2a344a, #101420)'
                });
            });
            state.catalog = catalog;
            if (!state.favoritesSaved) state.favorites = smartDefaults();
            renderAppsShelf();
        }

        // First run: the default streaming apps that are actually installed, topped up with
        // other installed (non-Amazon-system) apps, plus the Fire TV Home and Settings tiles.
        function smartDefaults() {
            function byId(id) { return arrFind(state.catalog, function(c) { return c.id === id; }); }
            var actions = DEFAULT_FAVORITES.filter(function(id) { var a = byId(id); return a && a.action; });
            var picks = DEFAULT_FAVORITES.filter(function(id) { var a = byId(id); return a && !a.action && a.installedPkg; });
            state.catalog.forEach(function(a) {
                if (picks.length + actions.length < 8 && !a.action && a.installedPkg &&
                    picks.indexOf(a.id) === -1 && !/^com\.amazon\./.test(a.installedPkg)) {
                    picks.push(a.id);
                }
            });
            return picks.slice(0, 8 - actions.length).concat(actions);
        }

''')

rep_block('        // --- Native webOS App Launch ---', '        // --- Render App Shelf & Trending Row ---', r'''        // --- Native Fire TV App Launch ---
        var shelfEdit = null;
        var movingTileId = null;
        // Deep links: only these exact URL shapes are turned into a YouTube intent.
        var CONTENT_TARGET_RE = /^https:\/\/www\.youtube\.com\/tv\?v=[A-Za-z0-9_-]{6,15}$/;

        function candidatePackages(app, appId) {
            var list = [];
            if (app && app.installedPkg) list.push(app.installedPkg);
            [appId].concat((app && app.alt) || []).forEach(function(p) {
                if (list.indexOf(p) === -1) list.push(p);
            });
            return list.filter(function(p) { return /^[A-Za-z0-9_.]+$/.test(p); });
        }

        function launchApp(appId, contentTarget) {
            if (shelfEdit) return;
            var app = arrFind(state.catalog, function(item) { return item.id === appId; });
            var title = app ? t(app.title) : appId;
            if (!FTV) {
                showToast(t('Open %s on your Fire TV. Launching is unavailable in this preview.', title), 5000);
                return;
            }
            var ok = false;
            try {
                if (app && app.action) {
                    ok = FTV.startIntent(app.action, app.category || '', '');
                } else {
                    var pkgs = candidatePackages(app, appId);
                    if (contentTarget && CONTENT_TARGET_RE.test(contentTarget)) {
                        var url = 'https://www.youtube.com/watch?v=' + contentTarget.split('?v=')[1];
                        for (var i = 0; !ok && i < pkgs.length; i++) ok = FTV.openUrl(pkgs[i], url);
                    }
                    for (var j = 0; !ok && j < pkgs.length; j++) ok = FTV.launch(pkgs[j]);
                    if (!ok && pkgs.length) {
                        // Not installed: open its Amazon Appstore page instead.
                        if (FTV.openUrl('', 'amzn://apps/android?p=' + pkgs[0])) {
                            showToast(t('%s is not installed. Opening the Appstore…', title), 5000);
                            return;
                        }
                    }
                }
            } catch (e) { ok = false; }
            showToast(ok ? t('Opening %s…', title) : t('Could not open %s. Check that it is installed, then try again.', title), ok ? 2500 : 5000);
        }

''')

# ---------------------------------------------------------------- shelf rendering
rep('''                } else {
                    var fallback = document.createElement('span');
                    fallback.className = 'app-art-fallback';
                    fallback.textContent = app.title;
                    iconDiv.appendChild(fallback);
                    var logo = APP_LOGOS[app.id];
                    if (logo || app.iconUrl) {
                        addTileImage(iconDiv, logo ? 'assets/brands/' + logo + '.svg' : app.iconUrl, !!logo);
                    }
                }''', '''                } else if (app.art) {
                    iconDiv.innerHTML = deviceArtwork(app.art);
                } else {
                    var fallback = document.createElement('span');
                    fallback.className = 'app-art-fallback';
                    fallback.textContent = app.title;
                    iconDiv.appendChild(fallback);
                    var logo = APP_LOGOS[app.id];
                    var native = logo ? '' : nativeIcon(app);
                    if (logo || native) {
                        addTileImage(iconDiv, logo ? 'assets/brands/' + logo + '.svg' : native, !!logo);
                    }
                }''')
rep("                labelDiv.textContent = title + (device.title ? ' · ' + app.title : '');",
    "                labelDiv.textContent = t(title) + (device.title ? ' · ' + app.title : '');")

# ---------------------------------------------------------------- customize modal
rep_block('        function renderHDMIOptions() {', '        function closeSettingsModal() {', r'''        // Section 2: Home button (accessibility service HomeService). The Fire TV only lets the
        // user enable it; we show the state and jump to the accessibility settings.
        function homeServiceOn() {
            if (!FTV) return false;
            try { return String(FTV.getSecure('enabled_accessibility_services') || '').indexOf(SELF_PKG + '/') !== -1; }
            catch (e) { return false; }
        }
        function renderHDMIOptions() {
            var container = document.getElementById('hdmiOptions');
            container.innerHTML = '';
            var button = document.createElement('button');
            button.className = 'app-toggle-item modal-nav';
            button.textContent = t(homeServiceOn() ? 'Home button: On' : 'Home button: Off') + ' — ' + t('Open accessibility settings');
            button.addEventListener('click', function() {
                var ok = false;
                if (FTV) { try { ok = FTV.startIntent('android.settings.ACCESSIBILITY_SETTINGS', '', ''); } catch (e) {} }
                if (!ok) showToast(t('Not available here. See the README for the ADB command.'), 6000);
            });
            container.appendChild(button);
        }

''')

rep('''            state.catalog.forEach(function(app) {
                var isSelected = tempFavorites.indexOf(app.id) !== -1;''', '''            var list = state.catalog.slice();
            if (state.nativeReady) {
                list = list.filter(isAvailable).concat(list.filter(function(a) { return !isAvailable(a); }));
            }
            list.forEach(function(app) {
                var isSelected = tempFavorites.indexOf(app.id) !== -1;''')
rep('''                var titleSpan = document.createElement('span');
                titleSpan.textContent = app.title;''', '''                var titleSpan = document.createElement('span');
                titleSpan.textContent = t(app.title);
                if (state.nativeReady && !isAvailable(app)) {
                    titleSpan.textContent += ' · Appstore';
                    titleSpan.className = 'not-installed';
                }''')
rep("            state.favorites = tempFavorites.slice();\n            state.hdmiDevices",
    "            state.favorites = tempFavorites.slice();\n            state.favoritesSaved = true;\n            state.hdmiDevices")

# ---------------------------------------------------------------- keys
rep_block('        // --- Remote Control Key Handler ---', '        // --- Boot Sequence ---', r'''        // --- Remote Control Key Handler ---
        // Fire TV remote: the D-pad arrives as arrow keys and Select as Enter. Back and Menu are
        // intercepted by the Android wrapper (MainActivity.dispatchKeyEvent) and delivered via
        // window.fmtvKey(), so Back never drops out of the home screen.
        var KEY_BY_CODE = { 13: 'Enter', 23: 'Enter', 27: 'Escape', 37: 'ArrowLeft', 38: 'ArrowUp', 39: 'ArrowRight', 40: 'ArrowDown', 461: 'GoBack' };
        function normKey(e) {
            var k = e.key;
            if (!k || k === 'Unidentified' || k === 'Up' || k === 'Down' || k === 'Left' || k === 'Right' || k === 'Esc') {
                k = KEY_BY_CODE[e.keyCode] || k;
            }
            if (e.keyCode === 23) k = 'Enter';
            return k;
        }
        function isBackKey(key) { return key === 'GoBack' || key === 'Escape'; }
        var kbdInput = null;

        function moveModalFocus(step) {
            kbdInput = null;
            modalIndex = (modalIndex + step + modalNavItems.length) % modalNavItems.length;
            setModalFocus(modalNavItems[modalIndex]);
        }

        function handleKey(e) {
            var key = normKey(e);
            lastActivity = Date.now();
            if (screensaverOn) {
                exitScreensaver();
                e.preventDefault();
                return;
            }

            if (shelfEdit) {
                if (isBackKey(key)) {
                    finishShelfEdit(false); e.preventDefault(); return;
                }
                if (movingTileId) {
                    if (key === 'ArrowLeft' || key === 'ArrowRight') {
                        moveShelfTile(key === 'ArrowLeft' ? -1 : 1);
                    } else if (key === 'Enter' || key === 'ArrowUp' || key === 'ArrowDown') {
                        var id = movingTileId;
                        movingTileId = null;
                        renderAppsShelf();
                        if (key === 'Enter') focusShelfTile(id);
                        else setMainFocus(document.getElementById('saveShelfOrder'));
                    } else return;
                    e.preventDefault(); return;
                }
            }

            if (isBackKey(key)) {
                if (modalOpen) {
                    closeSettingsModal();
                    e.preventDefault();
                } else if (drawerOpen) {
                    closeDrawer();
                    e.preventDefault();
                }
                return;
            }

            if (drawerOpen) {
                if (key === 'Enter') {
                    closeDrawer();
                    e.preventDefault();
                }
                return;
            }

            if (modalOpen) {
                var active = modalNavItems[modalIndex];
                // Dropdowns cycle in place (Left/Right/OK) - native pickers are unreliable on TV WebViews.
                if (active && active.tagName === 'SELECT' && (key === 'ArrowLeft' || key === 'ArrowRight' || key === 'Enter')) {
                    var n = active.options.length;
                    if (n) active.selectedIndex = (active.selectedIndex + (key === 'ArrowLeft' ? -1 : 1) + n) % n;
                    e.preventDefault();
                    return;
                }
                if (key === 'ArrowRight' || key === 'ArrowDown') {
                    moveModalFocus(1);
                    e.preventDefault();
                } else if (key === 'ArrowLeft' || key === 'ArrowUp') {
                    moveModalFocus(-1);
                    e.preventDefault();
                } else if (key === 'Enter' && active) {
                    if (active.tagName === 'INPUT') {
                        // 1st OK opens the on-screen keyboard, the next OK (keyboard "Done") moves on.
                        if (kbdInput === active) {
                            active.blur();
                            moveModalFocus(1);
                            e.preventDefault();
                        } else {
                            kbdInput = active;
                            if (FTV) { try { FTV.showKeyboard(); } catch (err) {} }
                        }
                    } else {
                        active.click();
                        e.preventDefault();
                    }
                }
                return;
            }

            // Main Dashboard Spatial Navigation
            if (key === 'ArrowRight') {
                curIndex = (curIndex + 1) % mainNavItems.length;
                setMainFocus(mainNavItems[curIndex]);
                e.preventDefault();
            } else if (key === 'ArrowLeft') {
                curIndex = (curIndex - 1 + mainNavItems.length) % mainNavItems.length;
                setMainFocus(mainNavItems[curIndex]);
                e.preventDefault();
            } else if (key === 'ArrowDown') {
                moveFocusVertical(1);
                e.preventDefault();
            } else if (key === 'ArrowUp') {
                moveFocusVertical(-1);
                e.preventDefault();
            } else if (key === 'Enter') {
                if (mainNavItems[curIndex]) {
                    mainNavItems[curIndex].click();
                    e.preventDefault();
                }
            }
        }
        document.addEventListener('keydown', handleKey);

        // Called by MainActivity for the remote's Back and Menu (≡) buttons.
        window.fmtvKey = function(name) {
            if (name === 'menu') {
                lastActivity = Date.now();
                if (screensaverOn) { exitScreensaver(); return; }
                if (shelfEdit) return;
                if (modalOpen) { closeSettingsModal(); return; }
                if (drawerOpen) closeDrawer();
                openSettingsModal();
                return;
            }
            handleKey({ key: 'GoBack', keyCode: 461, preventDefault: function() {} });
        };

        // Called by MainActivity.onResume: pick up newly installed/removed apps and the
        // Home-button service state after returning from another app or the settings.
        window.fmtvResume = function() {
            markActivity();
            discoverTVApps();
            if (modalOpen) {
                renderHDMIOptions();
                refreshModalNavList();
            }
        };

''')

# ---------------------------------------------------------------- translations
NEW = {
    'Navigate with your Fire TV remote. Launch apps instantly with zero ads.': {
        'pt': 'Navegue com o controle do Fire TV. Abra apps na hora, sem anúncios.',
        'es': 'Navega con el mando del Fire TV. Abre apps al instante, sin anuncios.',
        'de': 'Mit der Fire-TV-Fernbedienung navigieren. Apps sofort starten, ganz ohne Werbung.',
        'fr': 'Naviguez avec la télécommande Fire TV. Lancez vos applis instantanément, sans publicité.'},
    '2. Home Button': {'pt': '2. Botão Home', 'es': '2. Botón de Inicio', 'de': '2. Home-Taste', 'fr': '2. Bouton Accueil'},
    'Let the Fire TV Home button open Free My TV. Press Home twice to reach the original Fire TV home.': {
        'pt': 'Faça o botão Home do Fire TV abrir o Free My TV. Aperte Home duas vezes para ir à tela inicial original.',
        'es': 'Haz que el botón de Inicio del Fire TV abra Free My TV. Pulsa Inicio dos veces para ir al inicio original.',
        'de': 'Die Home-Taste des Fire TV öffnet Free My TV. Zweimal Home drücken führt zur originalen Fire-TV-Startseite.',
        'fr': 'Le bouton Accueil du Fire TV ouvre Free My TV. Appuyez deux fois sur Accueil pour revenir à l’accueil Fire TV d’origine.'},
    'Home button: On': {'pt': 'Botão Home: Ligado', 'es': 'Botón Inicio: Activado', 'de': 'Home-Taste: An', 'fr': 'Bouton Accueil : activé'},
    'Home button: Off': {'pt': 'Botão Home: Desligado', 'es': 'Botón Inicio: Desactivado', 'de': 'Home-Taste: Aus', 'fr': 'Bouton Accueil : désactivé'},
    'Open accessibility settings': {'pt': 'Abrir ajustes de acessibilidade', 'es': 'Abrir ajustes de accesibilidad',
                                    'de': 'Bedienungshilfen öffnen', 'fr': 'Ouvrir les réglages d’accessibilité'},
    'Not available here. See the README for the ADB command.': {
        'pt': 'Indisponível aqui. Veja o README para o comando ADB.', 'es': 'No disponible aquí. Consulta el README para el comando ADB.',
        'de': 'Hier nicht verfügbar. Den ADB-Befehl finden Sie in der README.', 'fr': 'Indisponible ici. Consultez le README pour la commande ADB.'},
    'Open %s on your Fire TV. Launching is unavailable in this preview.': {
        'pt': 'Abra %s no seu Fire TV. A abertura não está disponível nesta prévia.',
        'es': 'Abre %s en tu Fire TV. No se puede abrir en esta vista previa.',
        'de': 'Öffnen Sie %s auf Ihrem Fire TV. Starten ist in dieser Vorschau nicht möglich.',
        'fr': 'Ouvrez %s sur votre Fire TV. Le lancement n’est pas disponible dans cet aperçu.'},
    '%s is not installed. Opening the Appstore…': {
        'pt': '%s não está instalado. Abrindo a Appstore…', 'es': '%s no está instalada. Abriendo la Appstore…',
        'de': '%s ist nicht installiert. Appstore wird geöffnet…', 'fr': '%s n’est pas installée. Ouverture de l’Appstore…'},
    'Full-screen web browsing on your Fire TV.': {
        'pt': 'Navegação web em tela cheia no seu Fire TV.', 'es': 'Navegación web a pantalla completa en tu Fire TV.',
        'de': 'Vollbild-Surfen auf Ihrem Fire TV.', 'fr': 'Navigation web en plein écran sur votre Fire TV.'},
    'Live TV': {'pt': 'TV ao Vivo', 'es': 'TV en Vivo', 'de': 'Live-TV', 'fr': 'TV en direct'},
    'Live TV channels, replay, and recordings.': {
        'pt': 'Canais de TV ao vivo, replay e gravações.', 'es': 'Canales de TV en vivo, replay y grabaciones.',
        'de': 'Live-TV-Sender, Replay und Aufnahmen.', 'fr': 'Chaînes TV en direct, replay et enregistrements.'},
    'Play your own media library from USB, NAS, or DLNA.': {
        'pt': 'Reproduza sua biblioteca de mídia via USB, NAS ou DLNA.', 'es': 'Reproduce tu biblioteca multimedia desde USB, NAS o DLNA.',
        'de': 'Eigene Mediathek von USB, NAS oder DLNA abspielen.', 'fr': 'Lisez votre médiathèque depuis USB, NAS ou DLNA.'},
    'Download and install apps from the web (sideloading).': {
        'pt': 'Baixe e instale apps da web (sideloading).', 'es': 'Descarga e instala apps desde la web (sideloading).',
        'de': 'Apps aus dem Web laden und installieren (Sideloading).', 'fr': 'Téléchargez et installez des applis depuis le web (sideloading).'},
    'Fire TV Home': {'pt': 'Início do Fire TV', 'es': 'Inicio de Fire TV', 'de': 'Fire-TV-Startseite', 'fr': 'Accueil Fire TV'},
    'Open the original Fire TV home screen (app library, Amazon settings).': {
        'pt': 'Abre a tela inicial original do Fire TV (biblioteca de apps, ajustes da Amazon).',
        'es': 'Abre el inicio original de Fire TV (biblioteca de apps, ajustes de Amazon).',
        'de': 'Öffnet die originale Fire-TV-Startseite (App-Bibliothek, Amazon-Einstellungen).',
        'fr': 'Ouvre l’accueil Fire TV d’origine (bibliothèque d’applis, réglages Amazon).'},
    'Settings': {'pt': 'Ajustes', 'es': 'Ajustes', 'de': 'Einstellungen', 'fr': 'Paramètres'},
    'Open the Fire TV settings.': {'pt': 'Abre os ajustes do Fire TV.', 'es': 'Abre los ajustes de Fire TV.',
                                   'de': 'Öffnet die Fire-TV-Einstellungen.', 'fr': 'Ouvre les paramètres du Fire TV.'},
    'Installed App': {'pt': 'App Instalado', 'es': 'App Instalada', 'de': 'Installierte App', 'fr': 'Appli installée'},
    'Installed on this Fire TV.': {'pt': 'Instalado neste Fire TV.', 'es': 'Instalada en este Fire TV.',
                                   'de': 'Auf diesem Fire TV installiert.', 'fr': 'Installée sur ce Fire TV.'},
}


def js_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


for lang in ('pt', 'es', 'de', 'fr'):
    # each language block ends with its 'Saved & Applied!' entry
    m = re.search(r"(\n            %s: \{.*?'Saved & Applied!': '[^']*')" % lang, out, re.S)
    assert m, lang
    extra = ',\n                ' + ',\n                '.join('%s: %s' % (js_str(k), js_str(v[lang])) for k, v in NEW.items())
    out = out[:m.end()] + extra + out[m.end():]

# old Magic Remote hero text keys were replaced above (6 = markup + 5 dict keys); make sure nothing LG-specific is left in code paths
for bad in ('webOS.service', 'luna://', 'ws://127.0.0.1:3000'):
    assert bad not in out, bad

open(sys.argv[2], 'w', encoding='utf-8').write(out)
print('ported UI written:', sys.argv[2], len(out), 'bytes')

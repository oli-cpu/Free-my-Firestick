# Free My TV – Fire TV Edition

Portierung von [Free My TV for LG webOS](https://github.com/danielthejoker18/FreeMyTvWebOS) (v1.3.1) auf den **Amazon Fire TV Stick**:
werbefreier Homescreen mit App-Leiste, Wetter mit Sonnenuntergangs-Themes, Film- und Serien-Trends und OLED-Bildschirmschoner.
Die Oberfläche ist dieselbe wie beim Original. Ersetzt wurde nur die webOS-Anbindung (Luna-Bus) durch eine kleine Android-App.

> **Kein Jailbreak, kein Root, kein Flashen.** Free My TV ist eine ganz normale App. Sie wird wie jede andere App installiert und lässt sich jederzeit wieder deinstallieren. Am Fire-TV-System wird nichts verändert.

---

## Inhalt

1. [Passt mein Gerät?](#1-passt-mein-gerät)
2. [Fire TV vorbereiten](#2-fire-tv-vorbereiten)
3. [App installieren](#3-app-installieren): ohne PC oder mit PC
4. [Home-Taste auf Free My TV umleiten](#4-home-taste-auf-free-my-tv-umleiten) (optional, braucht einmalig einen PC)
5. [Bedienung](#5-bedienung)
6. [Update, Probleme und Deinstallation](#6-update-probleme-und-deinstallation)
7. [Für Entwickler](#für-entwickler)

---

## 1. Passt mein Gerät?

| Gerät | Läuft? |
|---|---|
| Fire TV mit **Fire OS 5–8** (z. B. Fire TV Stick 4K / 4K Max, Stick Lite, Stick 2./3. Gen., Cube) | ✅ |
| Fire TV mit **Vega OS** (z. B. Fire TV Stick 4K Select und neuere Modelle) | ❌ Vega OS kann keine Android-Apps (APK) installieren |

So siehst du, was dein Gerät hat: **Einstellungen → Mein Fire TV → Info → Software-Version**.
Steht dort „Fire OS“, passt es.

---

## 2. Fire TV vorbereiten

Das musst du nur einmal machen.

1. **Entwickleroptionen freischalten:**
   **Einstellungen → Mein Fire TV → Info** öffnen. Den Eintrag mit dem **Gerätenamen** (ganz oben, z. B. „Fire TV Stick Lite“) **7× hintereinander** mit OK anklicken.
   Unten erscheint der Hinweis „Du bist jetzt Entwickler“.
2. Einmal **Zurück** drücken. Unter **Mein Fire TV** gibt es jetzt den Punkt **Entwickleroptionen**.

---

## 3. App installieren

Du hast zwei Möglichkeiten. **Variante A** geht direkt am Fernseher. **Variante B** brauchst du, wenn A nicht klappt oder wenn du später die Home-Taste umleiten willst (Schritt 4).

### Variante A: direkt am Fernseher (ohne PC)

1. Im Amazon Appstore die kostenlose App **Downloader** (orangenes Symbol, von AFTVnews) suchen und installieren.
2. **Einstellungen → Mein Fire TV → Entwickleroptionen → Apps unbekannter Herkunft installieren** öffnen und **Downloader** auf **AN** stellen.
   (Bei älteren Geräten heißt die Option einfach „Apps unbekannter Herkunft“ und gilt für alle Apps.)
3. **Downloader** öffnen, ins Adressfeld diese Adresse eingeben und auf **Go** drücken:
   ```
   https://github.com/DEIN-NAME/FreeMyTV-FireTV/releases/latest/download/FreeMyTV-FireTV.apk
   ```
4. Wenn der Download fertig ist, auf **Installieren** drücken. Danach **Fertig** wählen. Downloader fragt dann, ob die APK-Datei gelöscht werden soll, das kannst du bestätigen.

> Bei manchen neueren Fire-OS-8-Updates fehlt die Option „Apps unbekannter Herkunft“. Dann geht es nur mit Variante B.

### Variante B: vom PC aus (per ADB)

ADB ist ein kostenloses Programm von Google, mit dem der PC Apps auf den Fire TV schicken kann. PC und Fire TV müssen im **selben WLAN/Netzwerk** sein.

**Am Fire TV:**
1. **Einstellungen → Mein Fire TV → Entwickleroptionen → ADB-Debugging** auf **AN** stellen.
2. Die IP-Adresse des Fire TV notieren: **Einstellungen → Mein Fire TV → Info → Netzwerk** (z. B. `192.168.178.39`).

**Am PC:**
1. Die **[Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)** für dein System herunterladen und den ZIP-Ordner entpacken (z. B. nach `C:\platform-tools`). Eine Installation ist nicht nötig.
2. Die Datei **`FreeMyTV-FireTV.apk`** von der [Releases-Seite](../../releases/latest) herunterladen und in denselben Ordner legen.
3. In diesem Ordner ein Terminal öffnen:
   - **Windows:** im Explorer in die Adresszeile `cmd` tippen und Enter drücken.
   - **macOS / Linux:** Terminal öffnen und mit `cd` in den Ordner wechseln.
4. Verbinden (deine IP-Adresse einsetzen):
   ```bash
   adb connect 192.168.178.39:5555
   ```
   (Unter macOS/Linux ggf. `./adb` statt `adb` schreiben.)
5. **Am Fernseher** erscheint jetzt „USB-Debugging zulassen?“. Haken bei **„Von diesem Computer immer zulassen“** setzen und **OK** drücken.
   Kommt keine Meldung oder steht am PC `unauthorized`, den Befehl aus Schritt 4 einfach nochmal ausführen.
6. App installieren:
   ```bash
   adb install -r FreeMyTV-FireTV.apk
   ```
   Wenn `Success` erscheint, ist die App drauf.

### Danach

Free My TV findest du unter **Apps → App-Bibliothek** (das Symbol mit den drei Quadraten und dem Plus).
Tipp: Kachel auswählen, **Menü-Taste (☰) → Verschieben** und sie ganz nach vorne in die Favoritenzeile legen.

---

## 4. Home-Taste auf Free My TV umleiten

**Optional.** Ohne diesen Schritt ist Free My TV eine normale App, die du selbst öffnest.
Mit diesem Schritt erscheint **nach der Home-Taste, nach einem Neustart und beim Zurückgehen aus Apps automatisch Free My TV** statt der Amazon-Startseite.

Dafür bringt die App einen kleinen Bedienungshilfe-Dienst mit. Er liest **nur, welche App gerade vorne ist**, aber keine Bildschirminhalte, Eingaben oder Passwörter. Die Fire-TV-Einstellungen zeigen solche Dienste von Fremd-Apps meist nicht an, deshalb wird er einmalig per ADB eingeschaltet.

Dazu wie in [Variante B](#variante-b-vom-pc-aus-per-adb) mit `adb connect` verbinden und dann diese zwei Befehle ausführen:

```bash
adb shell settings put secure enabled_accessibility_services org.freemytv.firetv/org.freemytv.firetv.HomeService
adb shell settings put secure accessibility_enabled 1
```

Fertig. In Free My TV unter **Menü (☰) → Anpassen → 2. Home-Taste** siehst du, ob der Dienst läuft.

### So verhält sich die Home-Taste

- **Home einmal drücken und kurz warten.** Fire OS zeigt zuerst die Amazon-Startseite, nach **etwa 5 Sekunden** wechselt das Bild zu Free My TV.
- **Nicht mehrmals drücken.** Fire OS sperrt nach jedem Druck auf Home für 5 Sekunden das Öffnen anderer Apps. Jeder weitere Druck startet diese Sperre neu, dann dauert es entsprechend länger.
- Zur **originalen Amazon-Startseite** (z. B. für die App-Bibliothek) kommst du über die Kachel **Fire-TV-Startseite** in Free My TV. Sie bleibt offen, bis du eine andere App startest.
- **Langes Drücken** von Home öffnet wie gewohnt das Schnellmenü.

### Warum nicht ganz ohne Amazon-Startseite?

Ohne Root lässt sich die Amazon-Startseite auf Fire OS **weder deaktivieren noch deinstallieren**. Amazon blockiert alle Wege (`protected package`), und die Home-Taste zeigt fest auf Amazons Oberfläche. Die kurze Verzögerung ist eine Sperre von Fire OS, an der keine App vorbeikommt. Die Umleitung ist das Maximum, das ohne Root geht.

### Umleitung wieder ausschalten

```bash
adb shell settings put secure accessibility_enabled 0
```

Wenn du die App deinstallierst, ist der Dienst ebenfalls weg.

---

## 5. Bedienung

| Taste | Funktion |
|---|---|
| Steuerkreuz / OK | Kacheln wählen und Apps starten |
| **Zurück** | schließt Dialoge (verlässt den Homescreen nicht) |
| **Menü (☰)** | öffnet und schließt *Anpassen* |
| In *Anpassen* | ↑/↓ wechseln das Feld, ←/→ oder OK ändern Auswahllisten, OK auf einem Textfeld öffnet die Tastatur |

- Beim ersten Start werden automatisch deine installierten Apps auf die Leiste gelegt. Dazu kommen die Kacheln **Fire-TV-Startseite** (die originale Amazon-Oberfläche mit App-Bibliothek usw.) und **Einstellungen**.
- Unter *Anpassen* stehen alle installierten Apps. Bekannte, aber nicht installierte Apps sind mit „· Appstore“ markiert und öffnen beim Start ihre Amazon-Appstore-Seite.
- Wetter: Ort unter *Anpassen* eintragen. Film-Trends mit Postern gibt es mit einem kostenlosen [TMDB-API-Schlüssel](https://www.themoviedb.org/settings/api), Serien-Trends gehen auch ohne.
- Sprache: Sie folgt der Systemsprache. Unterstützt sind Deutsch, Englisch, Portugiesisch, Spanisch und Französisch.

---

## 6. Update, Probleme und Deinstallation

### Auf eine neue Version aktualisieren

Die neue APK genauso installieren wie beim ersten Mal (Downloader oder `adb install -r`). Deine Einstellungen bleiben erhalten.
**Wichtig:** Nach einem Update schaltet Android den Home-Tasten-Dienst ab. Die beiden Befehle aus [Schritt 4](#4-home-taste-auf-free-my-tv-umleiten) danach einfach nochmal ausführen.

### Häufige Probleme

| Problem | Lösung |
|---|---|
| `adb connect` meldet `failed to authenticate` / `unauthorized` | Am Fernseher die Meldung „USB-Debugging zulassen?“ bestätigen und `adb connect …` nochmal ausführen. |
| `adb connect` findet den Fire TV nicht | Ist **ADB-Debugging** an? Stimmt die IP-Adresse? Sind PC und Fire TV im selben Netzwerk (kein Gast-WLAN)? |
| Downloader: „App nicht installiert“ | **Apps unbekannter Herkunft** für Downloader einschalten (Schritt A2). Ist schon eine Version mit anderer Signatur installiert, die alte erst deinstallieren. |
| Nach Home bleibt die Amazon-Startseite | Ist der Dienst an (*Anpassen → 2. Home-Taste*)? Nach einem App-Update die Befehle aus Schritt 4 nochmal ausführen. Home nur **einmal** drücken und ~5 Sek. warten. |
| Eine andere Launcher-App (z. B. Projectivy, Wolf Launcher) ist installiert | Deren Home-Tasten-Funktion abschalten oder die App deinstallieren. Zwei Umleitungen stören sich gegenseitig. |

### Deinstallieren

- Am Fire TV: **Einstellungen → Anwendungen → Installierte Anwendungen verwalten → Free My TV → Deinstallieren**,
- oder per PC: `adb uninstall org.freemytv.firetv`

Danach ist der Fire TV wieder genau wie vorher. Wenn du ADB nicht mehr brauchst, kannst du unter **Entwickleroptionen** das **ADB-Debugging** wieder ausschalten.

---

## Netzwerkzugriffe und Datenschutz

Wie im Original: Open-Meteo (Wetter), TVMaze (Serien-Trends ohne Schlüssel), TMDB (nur mit eigenem Schlüssel) und ipapi.co (nur wenn eingeschaltet). **Keine Telemetrie, kein Konto, keine Werbung.**
Die App braucht nur die Berechtigung *Internet*. Der optionale Home-Tasten-Dienst liest ausschließlich, welche App gerade im Vordergrund ist.

---

## Für Entwickler

### Unterschiede zur LG-Version

- **HDMI-Kacheln entfallen**, weil der Fire TV Stick selbst keine Eingänge hat. Abschnitt 2 in *Anpassen* ist jetzt die Home-Tasten-Einstellung.
- Apps werden über Android erkannt und gestartet, nicht über webOS Luna. App-Icons und Banner kommen direkt vom Fire TV.
- Paketnamen sind auf die Fire-TV-Versionen umgestellt (Netflix, Prime Video, YouTube, Disney+, Zattoo, Kodi, VLC, Silk, Downloader …).
- YouTube-Trailer (nur mit TMDB-Schlüssel) werden per Deep Link geöffnet. Klappt das nicht, startet stattdessen die YouTube-App.

### Wie die Home-Umleitung funktioniert

Fire OS verarbeitet die Home-Taste im `FireTVKeyPolicyManager`, bevor Bedienungshilfen sie sehen. Tastenfilter funktionieren deshalb nicht.
`HomeService` beobachtet stattdessen `TYPE_WINDOW_STATE_CHANGED`. Erscheint `com.amazon.tv.launcher.ui.HomeActivity*`, startet er `MainActivity` und wiederholt das alle 2 s, solange die Amazon-Startseite vorne bleibt.
Nach Home hält Android Starts von Hintergrund-Apps 5 s zurück (App-Switch-Sperre) und verwirft einen zurückgehaltenen Start beim nächsten Home-Druck. Der Dienst läuft im eigenen Prozess `:home`, damit der Low-Memory-Killer ihn nicht zusammen mit dem WebView beendet.
Die Kachel *Fire-TV-Startseite* legt die Markierungsdatei `files/stock-home` an. So weiß der Dienst über Prozessgrenzen hinweg, dass die Amazon-Startseite gewollt ist.
`MainActivity` hat zusätzlich einen `HOME`-Intent-Filter und kann damit auf Geräten, auf denen der Stock-Launcher abschaltbar ist, echter Standard-Launcher sein.

### Selbst bauen

**Ohne Android-SDK:** Es reichen Python 3 und ein JDK (für `keytool` und `jarsigner`):
```bash
python3 tools/build_apk.py . FreeMyTV-FireTV.apk
```
`tools/` erzeugt `classes.dex`, `AndroidManifest.xml` und `resources.arsc` selbst. `tools/dexcheck.py` prüft das Ergebnis.
Der lesbare Java-Quellcode, aus dem der Bytecode 1:1 abgeleitet ist, liegt unter `android/app/src/main/java/`.

**Mit Android Studio:** den Ordner `android/` öffnen. Die Web-Oberfläche wird aus `web/www` eingebunden.

**Mit GitHub Actions:** `.github/workflows/build-apk.yml` baut das APK bei jedem Push und hängt es als Artefakt an.

**Oberfläche erneut portieren** (z. B. nach einem Update des LG-Originals):
`python3 tools/port_ui.py <LG-Repo>/app/index.html web/www/index.html`

### Release veröffentlichen

Damit der Downloader-Link aus Variante A funktioniert, muss die APK als **Release-Asset** mit genau dem Namen `FreeMyTV-FireTV.apk` hochgeladen werden:
GitHub → **Releases → Draft a new release** → Tag z. B. `v1.3.2` → `FreeMyTV-FireTV.apk` anhängen → **Publish release**.
Der Link `…/releases/latest/download/FreeMyTV-FireTV.apk` zeigt dann immer auf die neueste Version.

### Signatur

`signing/freemytv.keystore` (Passwort `freemytv`) ist ein selbst erzeugter Wegwerf-Schlüssel. Bewahre ihn auf: Updates lassen sich nur mit demselben Schlüssel über die installierte App installieren.
Wenn du das Projekt öffentlich stellst, erzeuge vorher einen eigenen Schlüssel (Datei löschen, dann wird beim nächsten Build ein neuer angelegt).

## Lizenz

MIT, wie das Original (siehe `LICENSE`). Markenlogos stammen von Simple Icons (siehe `web/www/assets/brands/`).

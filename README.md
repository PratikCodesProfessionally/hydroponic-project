# Hydroponik – Webanwendung zur pH-Überwachung

Dokumentation der Weboberfläche, der Direktverbindung zum Raspberry Pi über
Ethernet und der Auswertung der Messreihe.

Gemessen wird der pH-Wert einer Hydroponik-Anlage, korrigiert wird mit einer
Peristaltikpumpe für pH-Minus. Messung und Regelung laufen auf dem Raspberry
Pi; diese Webanwendung zeigt die Werte **live im Browser** an und erlaubt
manuelle Pumpentests. Sie ist bewusst **nicht** Teil des Regelkreises – fällt
sie aus, misst und regelt der Pi unverändert weiter.

---

## Inhalt

1. [Aufbau der Webanwendung](#1-aufbau-der-webanwendung)
2. [Webanwendung starten](#2-webanwendung-starten)
3. [Direktverbindung zum Pi über Ethernet](#3-direktverbindung-zum-pi-über-ethernet)
4. [Befehle auf dem Raspberry Pi](#4-befehle-auf-dem-raspberry-pi)
5. [Messreihe auswerten – Kurven plotten](#5-messreihe-auswerten--kurven-plotten)
6. [Fehlersuche](#6-fehlersuche)

---

## 1  Aufbau der Webanwendung

```
Pi-API (Port 5000)          Node-Server (Port 3000)         Browser
GET /api/sensors     ───►   server/server.js         ───►   public/
                            fragt alle 2 s ab,              Dashboard,
                            übersetzt die Feldnamen,        Live-Diagramm,
                            WebSocket-Broadcast,            Pumpensteuerung
                            Verlaufspuffer
```

### server/server.js

Der Node-Server hat vier Aufgaben:

| Aufgabe | Beschreibung |
| --- | --- |
| **Abfragen** | Holt alle 2 s `GET /api/sensors` von der Pi-API (`PI_API_BASE_URL`) |
| **Übersetzen** | Bildet die Feldnamen des Pi (`wasser_temp`, `ph_spannung`, …) auf das Datenmodell der Oberfläche ab; ungültige Messungen bleiben `null` und werden als `--` angezeigt – es wird bewusst kein alter Wert weitergeführt |
| **Verteilen** | Schickt jeden neuen Messwert per WebSocket an alle verbundenen Browser |
| **Puffern** | Hält die Messwerte der letzten rund 24 Stunden (`HISTORY_LIMIT`, Standard 43200 Einträge bei 2-s-Takt) für CSV-Export und Diagramm; das Diagramm zeigt nach einem Seiten-Reload die letzten 120 Punkte |

### Schnittstellen des Node-Servers

| Methode | Pfad | Zweck |
| --- | --- | --- |
| GET | `/api/sensors` | letzter bekannter Zustand als JSON |
| GET | `/api/history` | pH-Verlauf für das Diagramm (`?limit=…`, Standard 120) |
| GET | `/api/export.csv` | gesamten Verlaufspuffer als CSV herunterladen |
| POST | `/api/sensors` | Zustand von außen setzen (Push statt Poll) |
| POST | `/api/pump/dose` | `{ "seconds": 2 }` → zeitbegrenzter Pumpenlauf am Pi |
| POST | `/api/pump/stop` | Not-Aus der Pumpe |

Ein dauerhaftes Einschalten der Pumpe gibt es absichtlich nicht: der Pi kennt
nur zeitbegrenzte Läufe, damit die Pumpe bei einem Verbindungsabbruch stoppt.
`POST /api/pump/dose` antwortet erst nach Ablauf der Dosierzeit.

### Umgebungsvariablen

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `PORT` | `3000` | Port der Weboberfläche |
| `PI_API_BASE_URL` | – | Basis-URL der Pi-API; leer = Demobetrieb |
| `PI_SENSOR_POLL_INTERVAL_MS` | `2000` | Abfrageintervall zum Pi |
| `PUMP_MAX_SECONDS` | `10` | Obergrenze je Pumpenlauf (der Pi begrenzt zusätzlich) |
| `PH_TARGET` / `PH_TOLERANCE` | `5.8` / `0.2` | Zielbereich, falls der Pi ihn nicht mitliefert |
| `HISTORY_LIMIT` | `43200` | Größe des Verlaufspuffers (≈ 24 h bei 2-s-Takt); Diagramm zeigt die letzten 120 |

### public/ – das Dashboard

| Element | Funktion |
| --- | --- |
| Aktueller pH-Wert | Großanzeige mit Sensorspannung und Bewertung (im/über/unter Zielbereich) |
| pH-Verlauf | Live-Liniendiagramm mit Zielband, Tooltip, Tastaturbedienung (Pfeiltasten) und Tabellenansicht; „CSV exportieren“ lädt die Messwerte herunter, „Diagramm speichern“ das Bild als PNG |
| Peristaltikpumpe | Betriebsart, Dosierzähler (gesamt und 24 h), Sperrzeit, Testlauf mit Sekundenangabe, Not-Aus; rote Warnung, wenn die Mengenbegrenzung ausgelöst hat |
| Weitere Messwerte | Wassertemperatur, Lufttemperatur, Luftfeuchte, Kontaktsensor |

Die Verbindung läuft über WebSocket und baut sich nach einem Abbruch
selbstständig neu auf. Zeigt die Kopfzeile „Getrennt“, ist der Node-Server
aus – nicht der Pi.

---

## 2  Webanwendung starten

Einmalig, im Projektordner auf dem Windows-Rechner:

```powershell
cd C:\Users\prati\hydroponic-system
npm install
```

### Mit Raspberry Pi

```powershell
.\start-pi.ps1
```

Das Skript prüft zuerst die eigene Ethernet-Adresse und die Erreichbarkeit
des Pi, nennt bei einem Fehler die Ursache und startet dann den Server.
Von Hand geht es auch:

```powershell
$env:PI_API_BASE_URL = "http://192.168.10.1:5000"
npm start
```

Erfolgskontrolle im Terminal:

```
Pi-API: http://192.168.10.1:5000 (alle 2000 ms)
```

Dashboard: **http://localhost:3000** – die Betriebsart in der Pumpen-Karte
muss `messbetrieb` oder `regelung` zeigen, nicht `regelung (simuliert)`.

### Ohne Pi (Demobetrieb)

```powershell
npm start            # Terminal 1
npm run simulate     # Terminal 2
```

Der Simulator sendet dasselbe Datenformat wie der Pi, inklusive pH-Drift,
Dosierung und Sperrzeit. Zum Vorführen der Mengenbegrenzung, ohne
20 Dosierungen abzuwarten:

```powershell
$env:SIM_DOSE_LIMIT = "2"
npm run simulate
```

---

## 3  Direktverbindung zum Pi über Ethernet

Ein normales Patchkabel direkt zwischen Rechner und Pi – kein Router, kein
Hochschulnetz dazwischen. Damit ist die Pumpen-Schnittstelle von außen nicht
erreichbar. Beide Geräte bekommen feste Adressen im selben Subnetz:

| Gerät | Adresse |
| --- | --- |
| Raspberry Pi (eth0) | `192.168.10.1/24` |
| Rechner (USB-Ethernet-Adapter „Ethernet 2“) | `192.168.10.2/24` |

> **Wichtigste Fehlerquelle:** das `/24` am Ende. Ohne diese Angabe vergibt
> Linux `/32` – eine Adresse ohne Netz darumherum. Der Pi hat dann keine
> Route zur Gegenseite, und der Ping meldet „Das Netzwerk ist nicht
> erreichbar“.

### Windows-Seite (PowerShell **als Administrator**, einmalig)

```powershell
Get-NetAdapter                       # Adapternamen ablesen, hier: "Ethernet 2"
Set-NetIPInterface -InterfaceAlias "Ethernet 2" -Dhcp Disabled
New-NetIPAddress  -InterfaceAlias "Ethernet 2" -IPAddress 192.168.10.2 -PrefixLength 24
```

Der Name in `-InterfaceAlias` muss exakt der Spalte `Name` aus
`Get-NetAdapter` entsprechen. `Dhcp Disabled` verhindert, dass Windows auf
dem Kabel vergeblich nach einem DHCP-Server sucht und sich selbst eine
unbrauchbare `169.254`-Adresse gibt.

### Pi-Seite (einmalig)

Auf einem deutschsprachigen Raspberry Pi OS heißt das Ethernet-Profil
**„Kabelgebundene Verbindung 1“** (englisch: „Wired connection 1“) – den
tatsächlichen Namen zeigt `nmcli con show`:

```bash
sudo nmcli con mod "Kabelgebundene Verbindung 1" ipv4.method manual ipv4.addresses 192.168.10.1/24
sudo nmcli con up  "Kabelgebundene Verbindung 1"
ip -4 addr show eth0        # muss  inet 192.168.10.1/24  zeigen
```

Diese Konfiguration überlebt Neustarts. **Nicht** dauerhaft auf
`sudo ip addr add …` setzen – das gilt nur bis zum nächsten Neustart und war
in diesem Projekt die häufigste Ursache dafür, dass die Verbindung
„plötzlich wieder weg“ war. Zum kurzen Ausprobieren ist es in Ordnung:

```bash
sudo ip addr add 192.168.10.1/24 dev eth0     # wirkt sofort, hält bis zum Neustart
```

Bewusst **ohne Gateway**: das Kabel dient nur der Messdatenübertragung. Das
WLAN des Pi bleibt eingeschaltet – darüber kommen Updates und vor allem die
Uhrzeit; ohne Zeitserver stimmen die Zeitstempel im CSV-Log nach jedem
Neustart nicht, denn der Pi hat keine gepufferte Echtzeituhr.

### Verbindung prüfen (Windows)

```powershell
Test-NetConnection 192.168.10.1 -Port 5000
```

| Feld | Sollwert | Wenn nicht … |
| --- | --- | --- |
| `InterfaceAlias` | `Ethernet 2` | steht dort `WiFi`, fehlt die Windows-Adresse (siehe oben) |
| `PingSucceeded` | `True` | Pi-Adresse prüfen: `ip -4 addr show eth0` → steht dort `/24`? |
| `TcpTestSucceeded` | `True` | läuft das Messprogramm auf dem Pi? |

### Täglicher Ablauf nach der Einrichtung

Kabel steckt, Pi einschalten, auf dem Rechner:

```powershell
.\start-pi.ps1
```

Sonst nichts – vorausgesetzt, die feste IP ist per `nmcli` gesetzt und das
Messprogramm startet automatisch (Abschnitt 4).

---

## 4  Befehle auf dem Raspberry Pi

Falls das Messskript bei dir anders heißt (z. B. `ganzerCode.py`), den Namen
in den Befehlen entsprechend ersetzen.

### Messprogramm starten

```bash
cd ~/hydroponic-project
python3 iot/hydroponik.py --nur-messen     # Messbetrieb, Pumpe gesperrt
python3 iot/hydroponik.py --regeln         # mit aktiver pH-Regelung
python3 iot/hydroponik.py --kalibrieren    # nur Sensorspannung anzeigen
```

Läuft das Programm über SSH, beendet das Schließen des Fensters es mit.
Für längere Messreihen deshalb `tmux`:

```bash
tmux new -s hydro
python3 iot/hydroponik.py --nur-messen
# Ablösen: Strg+B, dann D          Zurückholen: tmux attach -t hydro
```

### Automatischer Start beim Hochfahren (empfohlen)

```bash
sudo cp iot/hydroponik.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hydroponik

systemctl status hydroponik        # Zustand ansehen
journalctl -u hydroponik -f        # Ausgaben live mitlesen
sudo systemctl restart hydroponik  # neu starten
```

Vorher in der Service-Datei `User`, `WorkingDirectory` und den Python-Pfad
an die eigene Installation anpassen.

### Dateien zwischen Rechner und Pi kopieren

```powershell
# Windows → Pi (Skript aktualisieren)
scp C:\Users\prati\hydroponic-system\iot\hydroponik.py pi@192.168.10.1:~/hydroponic-project/iot/

# Pi → Windows (Messdaten holen)
scp pi@192.168.10.1:~/hydroponic-project/hydroponik_log.csv C:\Users\prati\hydroponic-system\
```

### Python-Abhängigkeiten installieren (einmalig)

```bash
python3 -m venv --system-site-packages ~/hydro-venv
source ~/hydro-venv/bin/activate
pip install -r iot/requirements.txt
```

---

## 5  Messreihe auswerten – Kurven plotten

Das Skript [tools/plot_messreihe.py](tools/plot_messreihe.py) erzeugt aus der
CSV-Logdatei druckfertige Diagramme (PNG, 300 dpi). Es liest sowohl das
vollständige Log vom Pi (`hydroponik_log.csv`, per `scp` holen) als auch die
über „CSV exportieren“ aus der Weboberfläche heruntergeladene Datei – beide
verwenden dieselben Spaltennamen.

### Einrichtung (einmalig, auf dem Windows-Rechner)

```powershell
pip install -r tools\requirements.txt
```

### Aufrufe

```powershell
# Standardauswertung: Zeitverlauf + Kalibrier-Kennlinie
python tools\plot_messreihe.py hydroponik_log.csv

# nur einen Zeitraum auswerten (z. B. die Sprungantwort nach einer Dosierung)
python tools\plot_messreihe.py hydroponik_log.csv --von "2026-08-05 14:00:00" --bis "2026-08-05 15:00:00"

# zusätzlich die Titrationskurve aus einer eigenen Messdatei
python tools\plot_messreihe.py hydroponik_log.csv --titration titration.csv

# anderer Zielbereich oder Dateiname
python tools\plot_messreihe.py hydroponik_log.csv --sollwert 6.0 --toleranz 0.3 --praefix versuch1
```

### Die erzeugten Diagramme

| Datei | Inhalt | Achsen |
| --- | --- | --- |
| `…_verlauf.png` | pH-Wert und Wassertemperatur über der Zeit, untereinander mit gemeinsamer Zeitachse | x: Uhrzeit · y: pH-Wert bzw. Wassertemperatur in °C |
| `…_kennlinie.png` | Sensorspannung über pH mit Ausgleichsgerade; gibt Steilheit in mV/pH und R² aus | x: pH-Wert · y: Sensorspannung in V |
| `…_titration.png` | Dosis-Wirkungs-Kurve der pH-Minus-Lösung und deren Empfindlichkeit | x: Menge in ml/l bzw. pH-Wert · y: pH-Wert bzw. ΔpH je ml/l |

Darstellungsregeln, die das Skript bereits umsetzt:

- **Keine zweite y-Achse.** pH und Temperatur stehen untereinander, weil die
  Zuordnung zweier Skalen in einem Bild willkürlich ist und Zusammenhänge
  vortäuscht.
- **Messlücken bleiben sichtbar.** Fällt der Sensor aus, reißt die Linie ab,
  statt die Lücke zu überbrücken.
- Der **pH-Wert trägt keine Einheit** (er ist als Logarithmus definiert);
  alle anderen Achsen folgen dem Muster „Größe in Einheit“ (DIN 461).
- Die Kennlinie muss eine Gerade mit **50–59 mV/pH** ergeben
  (Nernst-Bereich); das Skript warnt, wenn die Steilheit außerhalb liegt.
  

### Format der Titrationsdatei

Von Hand angelegte CSV mit zwei Spalten – die zugegebene Menge auf das
Lösungsvolumen normiert, damit das Ergebnis übertragbar ist:

```
volumen_ml_pro_l,ph
0.0,6.85
0.5,6.51
1.0,6.22
```

Für die Sprungantwort vorher im Pi-Skript `LOG_INTERVALL_S = 2` setzen –
mit dem Standardwert (ein Logeintrag alle 30 s) ist die Auflösung für das
Einschwingverhalten zu grob.

---

## 6  Fehlersuche

| Symptom | Ursache | Lösung |
| --- | --- | --- |
| Dashboard zeigt `regelung (simuliert)` | Simulator läuft statt Pi | Simulator beenden, `.\start-pi.ps1` |
| `Pi-API nicht erreichbar: fetch failed` | Pi aus, Adresse weg oder Messprogramm gestoppt | `Test-NetConnection 192.168.10.1 -Port 5000`, dann Tabelle in Abschnitt 3 |
| `Test-NetConnection` zeigt `InterfaceAlias: WiFi` | Windows-Adresse fehlt → Pakete laufen ins WLAN | `New-NetIPAddress …` als Administrator (Abschnitt 3) |
| Ping scheitert, obwohl beide Seiten konfiguriert sind | `/32` statt `/24` auf dem Pi | `ip -4 addr show eth0` prüfen, per `nmcli` mit `/24` neu setzen |
| „Access is denied“ bei `New-NetIPAddress` | PowerShell ohne Administratorrechte | Win+X → Terminal (Administrator) |
| „Unbekannte Verbindung“ bei `nmcli` | Profilname ist deutsch | `nmcli con show`, Namen in Anführungszeichen verwenden |
| Verbindung nach Pi-Neustart weg | Adresse war nur mit `ip addr add` gesetzt | dauerhaft per `nmcli` konfigurieren (Abschnitt 3) |
| `npm start` meldet „Kein PI_API_BASE_URL gesetzt“ | Variable gilt nur im jeweiligen Fenster | `.\start-pi.ps1` verwenden |
| Port 3000 belegt | alter Node-Prozess läuft noch | `taskkill /F /IM node.exe`, dann neu starten |
| Skriptausführung von `start-pi.ps1` blockiert | PowerShell-Richtlinie | `Set-ExecutionPolicy -Scope Process -Bypass` |

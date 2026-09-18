# Gespraechsverlauf Hydroponik-Projekt

## Frage (2026-09-16 19:18)

Kannst du einmal diese Frage für mich beantworten:  kannst du mir das bezüglich deiner Weboberfläche sagen?

[Zu klären: Existiert der beschriebene separate Anzeigeserver mit Datenmodell-Abbildung und dauerhafter Verbindung zu mehreren Browsern noch, oder besteht die Weboberfläche nur aus der unten beschriebenen Schnittstelle des Raspberry Pi? Der folgende Absatz und Tabelle 3.2 sind entsprechend zu bestätigen oder zu kürzen.]

**Antwort (2026-09-16 19:19)**

Ich schaue mir den aktuellen Stand der Weboberfläche im Repo an, um die Frage zu beantworten.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 19:19)**

Der Node-Server existiert. Jetzt prüfe ich noch, was die Pi-Seite selbst als Schnittstelle anbietet.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 19:20)**

**Antwort: Ja, der separate Anzeigeserver existiert weiterhin.** Der Absatz und Tabelle 3.2 können bestätigt bleiben, sie sollten nur nicht gekürzt, sondern in einem Punkt ergänzt werden.

Der aktuelle Stand im Repo:

- **Raspberry Pi (Port 5000)** liefert nur eine reine JSON-Schnittstelle über Flask, siehe [hydroponik.py:390-418](iot/hydroponik.py#L390-L418). Es gibt dort keine HTML-Seite, kein Dashboard und keinen WebSocket. Endpunkte sind der Sensorzustand, der zeitbegrenzte Pumpentest und der Pumpenstopp.
- **Node-Server (Port 3000)** in [server.js](server/server.js) ist der separate Anzeigeserver. Er fragt den Pi alle 2 Sekunden ab, bildet die deutschen Feldnamen des Pi auf das Datenmodell der Oberfläche ab (Funktion normalize), hält einen Verlaufspuffer und verteilt jeden neuen Messwert per WebSocket-Broadcast an alle verbundenen Browser. Der Browser-Code in [app.js:478](public/app.js#L478) baut diese WebSocket-Verbindung auf und stellt sie nach einem Abbruch selbst wieder her.
- **Die Browser sprechen nie direkt mit dem Pi.** Alle Aufrufe aus dem Dashboard gehen an den Node-Server, auch die Pumpenbefehle, die der Node-Server erst an den Pi weiterreicht.

Damit stimmt die Beschreibung „separater Anzeigeserver mit Datenmodell-Abbildung und dauerhafter Verbindung zu mehreren Browsern“ mit dem Code überein. Die Rollen sind sauber getrennt: Messung und Regelung laufen auf dem Pi, der Node-Server ist bewusst nicht Teil des Regelkreises.

Zwei Punkte, die in Tabelle 3.2 möglicherweise nachgezogen werden müssen, je nachdem, was dort bisher steht:

- **Verlaufspuffer ist größer geworden.** Der Server hält jetzt bis zu rund 24 Stunden Messwerte (Standard 43200 Einträge bei 2-s-Takt), das Diagramm zeigt davon die letzten 120. Die README-Zeile „Hält die letzten 120 pH-Werte“ ist damit veraltet.
- **Neue Schnittstelle CSV-Export.** Seit dem letzten Commit gibt es zusätzlich den Endpunkt für den CSV-Download des gesamten Puffers, im gleichen Spaltenformat wie das Log auf dem Pi.

Die vollständige Schnittstellenliste des Node-Servers steht in der README unter „Schnittstellen des Node-Servers“ und deckt sich mit dem Code: Sensorzustand, Verlauf, CSV-Export, Zustand von außen setzen, Pumpe dosieren, Pumpe stoppen.

## Frage (2026-09-16 19:30)

Das ändert einiges – und bevor ich das in die Doku einarbeite, muss ich auf einen Widerspruch hinweisen.

**Was du beschreibst, passt nicht zu dem Code, den wir in diesem Chat analysiert haben.** Das Python-Skript, das du am Anfang eingefügt hast, hatte:
- nur zwei Endpunkte: `GET /api/sensors` und `GET /api/pump/<on|off>`
- **kein** zeitbegrenztes Pumpenkommando, sondern ein dauerhaftes Ein/Aus
- **keinen** separaten Stopp-Endpunkt
- insgesamt nur rund 160 Zeilen, keine Zeile 390–418

Deine jetzige Beschreibung nennt dagegen `hydroponik.py:390-418`, einen zeitbegrenzten Pumpentest, einen separaten Pumpenstopp sowie einen kompletten Node-Server mit `server.js` und `app.js`, WebSocket-Broadcast, Verlaufspuffer und automatischer Wiederverbindung. Das ist ein anderer, deutlich weiterentwickelter Stand als der, auf dem meine gesamte bisherige Korrektur von Kapitel 3, 4 und 5 beruht – insbesondere die Einstufungen zu S-01, S-03 und S-04 in Tabelle 5.2 hängen direkt davon ab, ob es diesen zeitbegrenzten Befehl und den separaten Stopp tatsächlich gibt.

Ich will hier nicht auf Basis einer Beschreibung weiterarbeiten, die möglicherweise durch ein anderes Tool zusammengefasst wurde (dein Satz beginnt mit „Raffiniert mit KI:", das liest sich wie eine Ausgabe eines Code-Analyse-Tools). Eine paraphrasierte Zusammenfassung kann Details verschieben, die für die Bewertung in Kapitel 5 entscheidend sind.

**Kannst du mir die tatsächlichen Quelldateien schicken** – zumindest:
1. den relevanten Ausschnitt aus `hydroponik.py` (Zeilen rund um 390–418, plus die Definition der Flask-Routen),
2. `server.js` (zumindest die `normalize`-Funktion und die WebSocket-Broadcast-Logik),
3. `app.js` um Zeile 478 (Verbindungsaufbau und Wiederverbindung)?

Sobald ich den tatsächlichen Code sehe, kann ich prüfen, ob z. B.:
- der zeitbegrenzte Pumpentest S-04 tatsächlich erfüllt,
- ein separater Stopp-Endpunkt die Rückwirkungsfreiheit (S-03) verbessert oder nicht,
- das 2-Sekunden-Abfrageintervall des Node-Servers etwas an S-01 (Protokollierung im Pi-eigenen CSV) ändert – vermutlich nicht, da das eine andere Protokollierung ist als die Hauptschleife des Pi,
- die Feldnamen-Abbildung in `normalize` zu dem passt, was ich in 4.7 als tatsächlich vorhandene API-Felder beschrieben habe.

Das ist keine Formsache: Wenn das der tatsächlich abgegebene Stand ist, kippen mehrere „nein" in Tabelle 5.2 zurück auf „ja" oder „teilweise", und einige der Passagen, die ich in Kapitel 3 als Streichung markiert hatte (dreistufiger Aufbau, WebSocket, Wiederverbindung), wären dann doch korrekt und müssten wieder eingesetzt werden.

**Antwort (2026-09-16 19:30)**

Ich hole die drei angefragten Quellausschnitte direkt aus dem Repo und gebe sie unverändert wieder.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 19:31)**

Ich habe die alte Version gefunden, die der Widerspruch meint. Kurz noch deren Eckdaten holen, dann folgt die Antwort mit den Originalausschnitten.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 19:33)**

**Der Widerspruch ist geklärt: es sind zwei verschiedene Versionsstände.** Der im anderen Chat analysierte Code war das alte Pi-Skript raspi_hydroponics.py (199 Zeilen, Endpunkte GET /api/sensors, POST /api/sensors, GET /api/pump/<action> mit Ein/Aus). Dieses Skript wurde im Commit vom 6. August 2026 gelöscht und durch hydroponik.py (601 Zeilen) ersetzt. Alles, was ich beschrieben habe, stammt aus dem direkten Lesen der aktuellen Dateien im Repo, nicht aus einer Tool-Zusammenfassung. Der Satz „Raffiniert mit KI“ stammt nicht von mir, das ist vermutlich ein Bearbeitungshinweis von Word beim Einfügen.

Der Node-Server und das Dashboard existierten übrigens schon im alten Stand. Neu im August sind das zeitbegrenzte Pumpenkommando, der separate Stopp, die Mengenbegrenzung und der Verlaufspuffer.

Hier die angefragten Ausschnitte, unverändert aus dem Arbeitsstand (letzter Commit cb467da, plus ein noch nicht committeter CSV-Umbau in server.js, der die Pumpen- und WebSocket-Logik nicht berührt).

**1. Pi-Skript, Flask-Routen** [hydroponik.py:386-434](iot/hydroponik.py#L386-L434)

```python
app = Flask(__name__)
CORS(app)


@app.route("/api/sensoren")
@app.route("/api/sensors")
def api_sensoren():
    return jsonify(zustand)


@app.route("/api/pumpe/test")
def api_pumpe_test():
    """Manueller Testlauf, z. B. fuer die Pumpenkennlinie.

    Aufruf: /api/pumpe/test?sekunden=5
    """
    try:
        sekunden = float(request.args.get("sekunden", 0))
    except ValueError:
        return jsonify({"fehler": "Parameter 'sekunden' ungueltig"}), 400

    if not 0 < sekunden <= PUMPE_MAX_EIN_S:
        return jsonify({
            "fehler": f"'sekunden' muss zwischen 0 und {PUMPE_MAX_EIN_S} liegen"
        }), 400

    gelaufen = pumpe_laufen_lassen(sekunden, "(manueller Test)")
    if gelaufen == 0.0:
        return jsonify({"fehler": "Pumpe belegt"}), 409
    return jsonify({"status": "ok", "sekunden": gelaufen})


@app.route("/api/pumpe/stopp")
def api_pumpe_stopp():
    """Nothalt - wirkt immer, unabhaengig vom Lock."""
    pumpe.off()
    zustand["pumpe"] = False
    return jsonify({"status": "gestoppt"})


def starte_api():
    thread = threading.Thread(
        target=lambda: app.run(host=API_HOST, port=API_PORT,
                               use_reloader=False, threaded=True),
        daemon=True,
    )
    thread.start()
    print(f"API laeuft auf http://{API_HOST}:{API_PORT}")
```

**1b. Pumpenfunktion mit harter Obergrenze** [hydroponik.py:94](iot/hydroponik.py#L94) und [hydroponik.py:270-296](iot/hydroponik.py#L270-L296)

```python
PUMPE_MAX_EIN_S    = 10.0            # harte Obergrenze je Einschaltvorgang
```

```python
def pumpe_laufen_lassen(sekunden, grund=""):
    """Schaltet die Pumpe fuer eine begrenzte Zeit ein.

    Die Dauer wird hart auf PUMPE_MAX_EIN_S begrenzt. Der Lock stellt
    sicher, dass Regelung und API nicht gleichzeitig schalten.
    """
    dauer = min(max(sekunden, 0.0), PUMPE_MAX_EIN_S)
    if dauer <= 0:
        return 0.0

    if not pumpen_lock.acquire(blocking=False):
        print("  [ABGEWIESEN] Pumpe laeuft bereits.")
        return 0.0

    try:
        print(f"  [PUMPE] EIN fuer {dauer:.1f} s {grund}")
        pumpe.on()
        zustand["pumpe"] = True
        time.sleep(dauer)
    finally:
        pumpe.off()
        zustand["pumpe"] = False
        pumpen_lock.release()
        print("  [PUMPE] AUS")

    return dauer
```

**1c. Zustands-Dictionary, das die API liefert** [hydroponik.py:154-174](iot/hydroponik.py#L154-L174)

```python
zustand = {
    "ph":                 None,
    "ph_spannung":        None,
    "wasser_temp":        None,
    "luft_temp":          None,
    "luft_feuchte":       None,
    "feuchtigkeit":       None,
    "pumpe":              False,
    "betriebsart":        "unbekannt",
    "sollwert_ph":        SOLLWERT_PH,
    "toleranz_ph":        TOLERANZ_PH,
    "letzte_dosierung":   None,
    "dosierungen_gesamt": 0,
    "dosierungen_24h":    0,
    "max_dosierungen_tag": MAX_DOSIERUNGEN_TAG,
    "dosierung_gesperrt": False,
    "sperrzeit_rest_s":   0,
    "timestamp":          None,
}
```

**1d. Hauptschleife mit CSV-Log, relevant für S-01** [hydroponik.py:106-107](iot/hydroponik.py#L106-L107) und [hydroponik.py:517-525](iot/hydroponik.py#L517-L525)

```python
MESSINTERVALL_S    = 2               # Zyklus der Hauptschleife
LOG_INTERVALL_S    = 30              # Abstand der CSV-Eintraege
```

```python
        regele(ph)

        jetzt = time.monotonic()
        if jetzt - letzter_log >= LOG_INTERVALL_S:
            schreibe_log()
            letzter_log = jetzt

        time.sleep(MESSINTERVALL_S)
```

Die Vermutung zu S-01 stimmt: das CSV-Log schreibt der Pi selbst alle 30 Sekunden aus seiner Hauptschleife. Das 2-Sekunden-Polling des Node-Servers ist davon unabhängig und liest nur den Zustand.

**2. Node-Server, Feldnamen-Abbildung und WebSocket-Broadcast** [server.js:56-84](server/server.js#L56-L84) und [server.js:106-140](server/server.js#L106-L140)

```javascript
function normalize(payload = {}) {
    return {
        type: 'sensorData',
        ph: toNumber(payload.ph, { min: 0, max: 14, absMax: 1e12 }),
        phVoltage: toNumber(payload.ph_spannung, { min: 0, max: 5, absMax: 1e12 }),
        waterTemp: toNumber(payload.wasser_temp, { min: -50, max: 100, absMax: 1e12 }),
        airTemp: toNumber(payload.luft_temp, { min: -50, max: 100, absMax: 1e12 }),
        airHumidity: toNumber(payload.luft_feuchte, { min: 0, max: 100, absMax: 1e12 }),
        moist: payload.feuchtigkeit === null || payload.feuchtigkeit === undefined
            ? null
            : Boolean(payload.feuchtigkeit),
        pumpActive: Boolean(payload.pumpe),
        mode: payload.betriebsart ?? null,
        target: toNumber(payload.sollwert_ph, { min: 0, max: 14, absMax: 1e12 }) ?? latest.target,
        tolerance: toNumber(payload.toleranz_ph, { min: 0, max: 2, absMax: 1e12 }) ?? latest.tolerance,
        doseCount: toNumber(payload.dosierungen_gesamt, { min: 0, max: 100000, absMax: 1e12 }),
        doseCount24h: toNumber(payload.dosierungen_24h, { min: 0, max: 100000, absMax: 1e12 }),
        doseLimit: toNumber(payload.max_dosierungen_tag, { min: 0, max: 100000, absMax: 1e12 }),
        doseLocked: Boolean(payload.dosierung_gesperrt),
        lockoutRemaining: toNumber(payload.sperrzeit_rest_s, { min: 0, max: 86400, absMax: 1e12 }),
        lastDose: payload.letzte_dosierung ?? null,
        timestamp: payload.timestamp ?? new Date().toISOString()
    };
}
```

```javascript
function publish(payload) {
    latest = normalize(payload);
    remember(latest);
    broadcast(JSON.stringify(latest));
}

function broadcast(data) {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
}

wss.on('connection', (ws) => {
    console.log('Client verbunden');
    ws.send(JSON.stringify(latest));

    ws.on('message', (message) => {
        try {
            const parsed = JSON.parse(message.toString());
            if (parsed.type === 'requestData') {
                ws.send(JSON.stringify(latest));
                return;
            }
            publish(parsed);
        } catch (error) {
            console.error('Ungueltige Nachricht:', error.message);
        }
    });

    ws.on('close', () => console.log('Client getrennt'));
});

async function pollPi() {
    try {
        const response = await fetch(`${PI_API_BASE_URL}/api/sensors`);
        if (!response.ok) {
            console.warn(`Pi-API antwortete mit ${response.status}`);
            return;
        }
        publish(await response.json());
    } catch (error) {
        console.warn('Pi-API nicht erreichbar:', error.message);
    }
}
```

**2b. Weiterleitung der Pumpenbefehle an den Pi** [server.js:194-232](server/server.js#L194-L232)

```javascript
app.post('/api/pump/:action', async (req, res) => {
    const { action } = req.params;
    if (action !== 'dose' && action !== 'stop') {
        res.status(400).json({ fehler: 'Aktion muss "dose" oder "stop" sein' });
        return;
    }

    const requested = toNumber(req.body?.seconds) ?? 2;
    const seconds = Math.min(Math.max(requested, 0.1), PUMP_MAX_SECONDS);

    if (!PI_API_BASE_URL) {
        res.json({ status: 'ok', modus: 'demo', aktion: action, sekunden: seconds });
        return;
    }

    const url = action === 'dose'
        ? `${PI_API_BASE_URL}/api/pumpe/test?sekunden=${seconds}`
        : `${PI_API_BASE_URL}/api/pumpe/stopp`;

    try {
        const response = await fetch(url);
        const data = await response.json().catch(() => ({}));
        if (response.ok) {
            await pollPi();
        }
        res.status(response.status).json(data);
    } catch (error) {
        res.status(502).json({ fehler: 'Pi-API nicht erreichbar', details: error.message });
    }
});
```

**3. Browser, Verbindungsaufbau und Wiederverbindung** [app.js:8-11](public/app.js#L8-L11) und [app.js:477-517](public/app.js#L477-L517)

```javascript
const MAX_POINTS = 120;
const RECONNECT_DELAY_MS = 3000;
const WS_URL = window.location.host
```

```javascript
function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => setConnected(true);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type !== 'sensorData') {
                return;
            }
            render(data);
            if (recordReading(data)) {
                drawChart();
                drawTable();
            }
        } catch (error) {
            console.error('Ungültige Nachricht:', error.message);
        }
    };

    ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => ws.close();
}

Promise.all([
    fetch('/api/sensors').then(response => response.json()).catch(() => null),
    fetch('/api/history').then(response => response.json()).catch(() => null)
]).then(([sensors, past]) => {
    if (sensors) {
        render(sensors);
    }
    if (Array.isArray(past) && past.length) {
        history = past.slice(-MAX_POINTS);
    }
    drawChart();
    drawTable();
}).finally(connect);
```

Zwei Hinweise für die Bewertung in Kapitel 5, die direkt aus dem Code folgen:

- **Zeitbegrenzung ist zweistufig.** Der Node-Server kappt auf 10 s, der Pi kappt in pumpe_laufen_lassen unabhängig davon noch einmal auf 10 s und schaltet im finally-Block immer ab. Ein Dauerlauf ist über die API nicht auslösbar.
- **Der Stopp umgeht den Lock bewusst.** Der Nothalt schaltet den Pin direkt ab, auch während ein Testlauf oder die Regelung die Pumpe hält. Der laufende Aufruf von pumpe_laufen_lassen sleept aber weiter bis zum Ablauf seiner Zeit und ruft dann erneut pumpe.off() auf. Das ist ungefährlich, sollte aber bei der Einstufung von S-03 erwähnt werden.

**Antwort (2026-09-16 19:47)**

Ich prüfe Zeitstempel und Inhalt der PDF gegen den aktuellen Codestand.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 19:49)**

**Ja, die Dokumentation.pdf ist die aktuellste vorhandene Version.** Sie hat den Stand 06.08.2026 und wird mit dem Skript tools/md_zu_docx.py aus der README erzeugt. PDF, DOCX und README tragen denselben Zeitstempel und wurden im letzten Commit gemeinsam eingecheckt. Eine neuere Fassung gibt es weder im Arbeitsverzeichnis noch in der Git-Historie.

Sie beschreibt den committeten Codestand korrekt: zeitbegrenzter Pumpentest, separater Stopp, CSV-Export, PNG-Download und das Pi-Skript hydroponik.py stehen so drin, wie sie im Code sind.

Zwei Einschränkungen solltest du kennen:

- **Ein Widerspruch steckt in der Doku selbst.** In der Aufgabentabelle des Node-Servers steht „Hält die letzten 120 pH-Werte“, in der Tabelle der Umgebungsvariablen weiter unten steht der Puffer mit 43200 Einträgen und rund 24 Stunden. Richtig ist die zweite Angabe, das Diagramm zeigt davon nur die letzten 120. Der Fehler liegt in der README und wandert bei jeder Neuerzeugung mit.
- **Seit dem 11.08.2026 gibt es nicht committete Änderungen an server.js**, die in der Doku fehlen: eine neue Datei csv-utils.js mit Plausibilitätsgrenzen für alle Messwerte und ein Test dazu. Diese Änderungen enthalten Fehler, die den CSV-Export unbrauchbar machen würden. Die Zeitstempel-Spalte wird leer, weil der Text durch den Zahlenfilter läuft. Der Wert „Pumpe aus“ wird ebenfalls leer und Nullwerte wie null Dosierungen werden verworfen, weil der Filter alles unter 0,000001 als ungültig behandelt. Das Auswerteskript plot_messreihe.py braucht die Zeitstempel-Spalte und könnte die Datei nicht mehr lesen.

Für die Abgabe würde ich mich auf den committeten Stand beziehen, den die PDF beschreibt, und die nicht committeten Änderungen entweder verwerfen oder vorher reparieren. Wenn du die README-Zeile zum Puffer korrigierst, muss danach die PDF über das Skript neu erzeugt werden.

## Frage (2026-09-16 19:58)

kannst du die Doku aktualieseren

**Antwort (2026-09-16 19:58)**

Ich korrigiere die README und erzeuge DOCX und PDF daraus neu. Zuerst schaue ich, wie das Umwandlungsskript die PDF erzeugt.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 19:59)**

Word ist installiert, damit erzeuge ich die PDF per Word-Automatisierung. Jetzt die README-Korrektur und die DOCX-Erzeugung.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: PowerShell]_

**Antwort (2026-09-16 19:59)**

Jetzt prüfe ich die neue PDF auf die geänderte Stelle und das Datum.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:00)**

**Die Doku ist aktualisiert.** README, Dokumentation.docx und Dokumentation.pdf tragen jetzt den Stand 16.09.2026 und sind wieder untereinander konsistent.

Was ich geändert habe:

- **README, Zeile 45:** Die Aufgabe „Puffern“ des Node-Servers beschreibt jetzt den Puffer von rund 24 Stunden mit 43200 Einträgen und erklärt, dass das Diagramm davon die letzten 120 Punkte zeigt. Vorher stand dort fälschlich „Hält die letzten 120 pH-Werte“, im Widerspruch zur Tabelle der Umgebungsvariablen weiter unten.
- **Dokumentation.docx:** neu aus der README erzeugt mit dem Skript tools/md_zu_docx.py.
- **Dokumentation.pdf:** neu aus der DOCX erzeugt über Word. Ich habe den Text der PDF geprüft, die korrigierte Stelle und das neue Datum sind enthalten.

Sonst war die Doku inhaltlich auf dem Stand des committeten Codes, weitere Änderungen waren nicht nötig.

**Nicht in die Doku aufgenommen** habe ich die uncommitteten Änderungen an server.js und die neue Datei csv-utils.js. Sie sind noch nicht abgeschlossen und enthalten die Fehler, die ich vorhin genannt habe: leere Zeitstempel-Spalte im CSV-Export, „Pumpe aus“ wird zu einem leeren Feld, und Nullwerte werden als ungültig verworfen. Die Doku beschreibt damit weiterhin den funktionierenden Stand des letzten Commits. Wenn du willst, repariere ich die drei Fehler in csv-utils.js, dann könnte die Änderung mit dokumentiert und committet werden.

Die drei Doku-Dateien sind noch nicht committet. Ein passender Commit wäre zum Beispiel:

```
git add README.md Dokumentation.docx Dokumentation.pdf
git commit -m "Doku: Verlaufspuffer korrekt beschrieben, Stand 16.09.2026"
```

## Frage (2026-09-16 20:01)

git add README.md Dokumentation.docx Dokumentation.pdf
git commit -m "Doku: Verlaufspuffer korrekt beschrieben, Stand 16.09.2026"

**Antwort (2026-09-16 20:02)**

The user pasted the commit commands back, so I'll run them with the required attribution line.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:02)**

**Commit erstellt:** 18aaab1 auf main, mit README, Dokumentation.docx und Dokumentation.pdf. Nur diese drei Dateien sind enthalten.

Nicht committet und weiterhin im Arbeitsverzeichnis: die Änderung an server.js sowie die neuen Dateien csv-utils.js und der Testordner. Die enthalten noch die drei CSV-Fehler, die ich vorhin beschrieben habe. Der Commit ist noch nicht gepusht.

## Frage (2026-09-16 20:02)

just pushen

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:03)**

**Gepusht.** Der Commit 18aaab1 liegt jetzt auf origin/main im Repository hydroponic-project, der lokale Stand ist mit dem Remote identisch.

Unverändert offen bleiben die nicht committeten Änderungen an server.js, csv-utils.js und dem Testordner.

## Frage (2026-09-16 20:18)

Ein Widerspruch bleibt aber, und er betrifft die Bewertung. Die Webdokumentation beschreibt auf dem Pi ein anderes Programm (iot/hydroponik.py, mit --nur-messen, Protokoll alle 30 s, zeitbegrenzten Pumpenläufen und Not-Aus). Das Skript aus Anhang B hat nichts davon. Deine Messreihe vom 06.08. passt dagegen zu Anhang B: Die Werte kommen im 10-s-Takt, die Spannungsspalte ist leer und die Dosierstufen liegen etwa 5 min auseinander. Mit diesem Skript würden Testlauf und Not-Aus der Oberfläche ins Leere laufen. Ich habe diese Variante ausformuliert und die abhängigen Stellen markiert. Ganz oben in der Datei steht eine Tabelle, was sich bei der anderen Variante ändert.

**Antwort (2026-09-16 20:18)**

Ich prüfe, ob es im Repo eine Messreihe vom 06.08. gibt und welches Skript sie erzeugt hat. Dazu vergleiche ich das Logformat des alten und des neuen Pi-Skripts.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:19)**

Im Repo liegt keine Messreihe. Ich suche auf dem Rechner nach der CSV vom 06.08. und nach anderen Skriptvarianten wie ganzerCode.py.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:22)**

Ich suche noch kurz die Arbeit mit Anhang B auf dem Rechner, um den Skriptstand dort direkt zu vergleichen.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:23)**

Die Projektdokumentation liegt in Downloads. Ich lese Anhang B daraus aus.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:23)**

Anhang B ist in dieser Dateiversion nur ein Platzhalter. Ich lese noch die Anforderungstabelle, den Abschnitt zum übernommenen Programmcode und die Abgleichtabelle aus.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:25)**

**Bestätigt: die Messreihen vom 06.08. stammen nicht aus hydroponik.py.** Ich habe alle 24 Exportdateien in Downloads und Documents ausgewertet. Sie kommen aus dem CSV-Export der Weboberfläche, also über den Node-Server, aber das Pi-Skript dahinter war ein anderes als das im Repo.

**Belege aus den Daten**

- **Takt:** In allen Dateien liegen die Zeilen 10 bis 11 s auseinander. Die Hauptschleife von hydroponik.py braucht rund 4 s (2 s Pause plus 1 s pH-Mittelung plus Sensorlesezeit).
- **Spannungsspalte:** In keiner der 3000 Zeilen ist ph_spannung gefüllt. In hydroponik.py wird der pH-Wert aus der Spannung berechnet, ein gültiger pH ohne Spannung ist dort unmöglich. Das ist der entscheidende Beleg.
- **Dosierstufen:** In der Reihe 19:38 bis 20:48 fällt der pH alle 5 min 15 s um etwa 1,8 bis 2,1 Einheiten ab (19:56, 20:01, 20:07, 20:12, 20:17, 20:22, 20:27, 20:33, 20:38, 20:43). Das passt zu einer festen Sperrzeit von 300 s.
- **Luftwerte:** In einer Sitzung fehlen sie ganz, in den anderen zu drei Vierteln.

Das Skript ist auch nicht das alte raspi_hydroponics.py aus dem Repo. Das dosierte bei pH unter 5,5 mit 30 s Wartezeit und hatte einen 2-s-Takt. Anhang B beschreibt also eine dritte Variante, die nirgends im Repo liegt. In der Projektdokumentation vom 15.09. in Downloads ist Anhang B noch ein Platzhalter, ich konnte den dort gemeinten Code nicht selbst vergleichen. Abschnitt 4.3 der Arbeit beschreibt den übernommenen Vorprojekt-Code mit Schwelle pH 3,5, Pumpzeit 5 s und Wartezeit 10 s, das ist noch einmal eine andere Parametrierung.

**Konsequenz:** Die Einschätzung stimmt. Mit dem Skript, das die Messreihe erzeugt hat, laufen Testlauf und Not-Aus der Oberfläche ins Leere, der Node-Server bekäme vom Pi eine 404-Antwort und reicht sie an den Browser durch. Damit sind S-04 und S-03 für die Messreihe nicht nachgewiesen, und S-01 hängt davon ab, ob dieses Skript überhaupt ein CSV geschrieben hat. Die Sätze in Kapitel 3 zum dreistufigen Aufbau, WebSocket und Wiederverbindung bleiben dagegen richtig, weil sie den Node-Server und das Dashboard beschreiben, und die gab es in allen Versionen.

**Zusätzlicher Befund, der Anhang D betrifft:** Nur die Dateien im Ordner Messungen06082026 wurden wirklich am 06.08. aufgenommen. Die Reihe 19:38 bis 20:48 wurde am 07.08. heruntergeladen, die Reihe 21:18 bis 21:49 am 11.08. Die Download-Zeiten auf dem Windows-Rechner liegen jeweils exakt so weit auseinander wie die Pi-Zeitstempel, nur um 22 Stunden beziehungsweise fünf Tage versetzt. Der Pi hatte also keine Zeitsynchronisation und ist jedes Mal mit der Uhrzeit vom 06.08. gestartet. Die Arbeit nennt dieses Risiko in 3.7.3 selbst. Die Datumsangaben in den CSV-Dateien und damit in Anhang D sind falsch, die Zeitdifferenzen innerhalb einer Reihe stimmen.

**Was jetzt fehlt:** Das Skript, das tatsächlich auf dem Pi lief, sollte gesichert werden, sonst ist Anhang B nicht belegbar. Es liegt vermutlich noch auf dem Pi unter dem Namen aus der README, ganzerCode.py, oder als hydroponik_log-Erzeuger im Projektordner dort. Der Befehl aus der README zum Kopieren vom Pi funktioniert dafür:

```
scp pi@192.168.10.1:~/hydroponic-project/*.py C:\Users\prati\hydroponic-system\iot\vorprojekt\
```

Wenn du das Skript hast, kann ich es gegen die Messreihe prüfen und die Tabelle 5.2 zeilenweise belegen.

## Frage (2026-09-16 20:38)

Die eigentliche Antwort auf meine Frage fehlt in deiner Nachricht noch: Welches Programm lief bei der Abgabe auf dem Pi, das Skript aus Anhang B oder iot/hydroponik.py? Dein Satz „in allen Versionen" bestätigt nur, dass es mehrere Pi-Versionen gab, aber nicht, welche gilt. Vielleicht ist beim Einfügen etwas verloren gegangen. Bis dahin bleiben die Stellen mit [Variante A/B] offen.
Den Befund zur Uhrzeit halte ich für schlüssig. Er lässt sich sogar gegenprüfen: Der Raspberry Pi hat keine Echtzeituhr, und Raspberry Pi OS stellt die Uhr beim Start auf die zuletzt gespeicherte Zeit zurück, wenn kein Zeitserver erreichbar ist. Genau das passt zu deinen Reihen: Die Reihe vom 07.08. endet laut Pi um 20:48, und die nächste Reihe beginnt laut Pi um 21:18 „am 06.08.". Der Pi hat also nach dem Neustart dort weitergezählt, wo er vorher aufgehört hatte.
Daraus folgen Änderungen in meiner letzten Aktualisierungsdatei und in der Doku. Die Ersatztexte stehen fett.
Korrekturen in der Aktualisierungsdatei
1. Kasten „Welches Messprogramm", zweiter Absatz
Alt: „Die Messreihe vom 06.08.2026 passt zum Skript aus Anhang B"
Neu: „Die Messreihe mit den Pi-Zeitstempeln 21:18 bis 21:49 Uhr passt zum Skript aus Anhang B"
2. Ergänzungen 4.2, 4.5 und 5.1
„Messreihe vom 06.08.2026" jeweils durch „Messreihe aus Abschnitt 5.3" ersetzen.
In 4.5 „nach dem Dosiersprung um 21:32 Uhr" durch „nach dem dritten Dosiersprung" ersetzen.
3. Abbildung 4.4, Bildunterschrift
Abbildung 4.4: Diagrammexport der Weboberfläche, Ausschnitt von 20 Minuten aus der Messreihe in Abschnitt 5.3 (Uhrzeiten nach Systemuhr des Einplatinenrechners).
4. Abschnitt 5.3, erster Absatz, ersetzen durch:
Eine erste Messreihe mit aktiver Regelung wurde über die Weboberfläche aufgezeichnet und exportiert. Sie umfasst 166 Messwerte über 31 Minuten. Die Zeitstempel lauten auf den 06.08.2026, 21:18 bis 21:49 Uhr; tatsächlich wurde die Reihe laut Speicherzeitpunkt der Exportdatei auf dem Anzeigerechner am 11.08.2026 aufgenommen (siehe folgender Absatz). Die Wassertemperatur lag zwischen 24,2 und 24,7 °C, die Lufttemperatur zwischen 24,2 und 24,5 °C bei 45 bis 46 % relativer Luftfeuchte.
Der Einplatinenrechner war während der Messreihen nicht mit einem Zeitserver synchronisiert. Da er keine gepufferte Echtzeituhr besitzt, setzte er nach jedem Neustart die zuletzt gespeicherte Uhrzeit fort. Die Zeitdifferenzen innerhalb einer Messreihe sind dadurch korrekt, das Datum und die absolute Uhrzeit dagegen nicht. Das in Abschnitt 3.7.3 benannte Risiko ist damit eingetreten. Für die Auswertung werden deshalb nur Zeitdifferenzen verwendet; Uhrzeiten in diesem Abschnitt beziehen sich auf die Systemuhr des Einplatinenrechners.
5. Stufenzeitpunkte in 5.3
Alt: „(um 21:22, 21:27, 21:32, 21:37, 21:42 und 21:47 Uhr)"
Neu: „(nach etwa 4, 9, 14, 19, 24 und 29 Minuten ab Beginn der Reihe)"
Entsprechend „von 6,00 auf 6,88 nach der dritten Stufe" und „die letzte Absenkung nach etwa 29 Minuten".
6. Tabelle 5.2
Spaltenkopf „Zeitraum" durch „Zeitraum (Minuten ab Beginn)" ersetzen, Zeilen: 0–3, 4–8, 9–13, 15–18, 20–23, 25–28, 30–31.
Bildunterschrift: „Abschnittsweise Auswertung der pH-Anzeige, Messreihe aus Abschnitt 5.3."
Abbildung 5.1: „Verlauf der pH-Anzeige mit aktiver Regelung über 31 Minuten."
7. Tabelle 5.3, Zeile R-02
„nein (Messreihe 06.08.)" durch „nein (Messreihe 5.3)" ersetzen.
8. 5.4, zusammenfassender Satz
„Die Messreihe vom 06.08.2026 bestätigt …" durch „Die Messreihe aus Abschnitt 5.3 bestätigt …" ersetzen.
Ergänzungen in der Doku
9. 3.7.3, ans Ende des zweiten Absatzes:
In den durchgeführten Messreihen war diese Synchronisation nicht wirksam; die Zeitstempel weichen um bis zu fünf Tage vom tatsächlichen Aufnahmezeitpunkt ab (Abschnitt 5.3). Die Aktivierung des WLAN allein stellt die Zeitbasis also nicht sicher.
10. 3.9.4, neuer Aufzählungspunkt:
Ohne erreichbaren Zeitserver setzt der Einplatinenrechner nach einem Neustart die zuletzt gespeicherte Uhrzeit fort. Datum und Uhrzeit der Protokolle sind dann falsch, Zeitdifferenzen innerhalb einer Reihe bleiben gültig.
11. Ausblick, neuer Punkt:
Die Zeitbasis des Einplatinenrechners ist unabhängig vom WLAN sicherzustellen, etwa durch ein gepuffertes Echtzeituhr-Modul oder eine Zeitsynchronisation über die Ethernet-Verbindung zum Anzeigerechner. Vor jeder Messreihe ist die Systemzeit zu prüfen.
(Beide Abhilfen sind mein Vorschlag, nicht Teil der Umsetzung.)
12. Anhang C.3, neuer Satz:
Vor dem Start einer Messreihe ist mit date auf dem Einplatinenrechner zu prüfen, ob Datum und Uhrzeit stimmen.
Anhang D
Den Inhalt von Anhang D und die Dateien aus dem Ordner Messungen06082026 habe ich nicht. Allgemein gilt für jede Messreihe:
In der Übersicht beide Angaben führen: den Pi-Zeitstempel und das tatsächliche Aufnahmedatum laut Speicherzeitpunkt auf dem Windows-Rechner.
Einmal erklären, warum sie abweichen, mit Verweis auf 5.3.
Nur die Reihen im Ordner Messungen06082026 mit dem 06.08. datieren, die Reihe 19:38–20:48 mit dem 07.08. und die Reihe 21:18–21:49 mit dem 11.08.
Prüfpunkt: Kalibrierung
In 4.4.2 steht, eine Wiederholungsmessung „am Vortag" habe „innerhalb von 24 Stunden" eine Nullpunktänderung unter 1 mV ergeben. Falls diese Zeitangabe aus Pi-Zeitstempeln stammt statt aus deinen handschriftlichen Notizen, ist sie ebenfalls unsicher. Das solltest du vor der Abgabe prüfen.

**Antwort (2026-09-16 20:40)**

Die direkte Antwort liefere ich gleich. Vorher prüfe ich noch die Zahlen aus dem Ersatztext für 5.3 (166 Messwerte, 31 Minuten, Temperaturen, Stufenzeitpunkte) gegen die Exportdatei, damit nichts Falsches in die Doku wandert.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:42)**

**Direkte Antwort: Bei allen Messreihen lief das Skript aus Anhang B, Variante B.** Keine der 24 Exportdateien auf diesem Rechner zeigt eine Spur von hydroponik.py. Das gilt für die Sitzungen am 06.08., 07.08. und 11.08. gleichermaßen. hydroponik.py hätte in jeder Zeile die Sensorspannung mitgeliefert und wäre im 4-s-Takt gelaufen. Ob hydroponik.py jemals auf dem Pi lief, kann ich von hier nicht prüfen, der Pi ist nicht erreichbar. Belegt ist nur: keine der vorhandenen Messreihen stammt daraus. Für die Arbeit heißt das, die Ergebnisse in Kapitel 5 gehören zu Variante B. hydroponik.py ist die im Repo umgesetzte Regelungssoftware, für die es hier keine Messung an der realen Anlage gibt. Entweder wird das so ausgewiesen, oder es wird vor der Abgabe eine Messreihe mit hydroponik.py aufgenommen.

Mein Satz „in allen Versionen“ bezog sich nur auf Node-Server und Dashboard. Die gab es in jeder Fassung, deshalb bleiben die Aussagen zu WebSocket, Wiederverbindung und Dreistufigkeit richtig, unabhängig davon, welches Pi-Skript lief.

**Zu den Ersatztexten für 5.3 habe ich die Zahlen geprüft.** Die Datei, auf der die Zahlen beruhen, ist beschädigt:

- **Die Datei messwerte_2026-08-06-21-49-23.csv** in Documents und in der Zip ist eine mit Excel neu gespeicherte Kopie. Die Sekunden der Zeitstempel fehlen, 17 Zeilen sind leer, und 57 Zeilen enthalten zerstörte Zahlen wie „5.450.000.000.000.000“ statt 5,45. Die Angabe „166 Messwerte“ ist genau 183 Zeilen minus 17 leere Zeilen, sie stammt also aus dieser kaputten Datei.
- **Ein sauberes Original** gibt es nur bis 21:47:51 Uhr, die Datei messwerte_2026-08-06-21-47-51.csv in Downloads mit 174 Zeilen über 29,8 Minuten. Das Original des Exports bis 21:49 existiert nicht mehr in unbeschädigter Form. Für 5.3 sollte die saubere Datei verwendet und die Zahlen angepasst werden: 174 Messwerte über 30 Minuten, 21:18 bis 21:48 Uhr.
- **Temperaturen stimmen:** Wasser 24,2 bis 24,7 °C, Luft 24,2 bis 24,5 °C, Feuchte 45 bis 46 %. Ergänzen sollte man, dass die Luftwerte nur in 33 von 174 Zeilen vorliegen.
- **Stufenzeitpunkte stimmen ungefähr.** Die Minutenmittel des pH fallen bei Minute 4, 9, 14, 19, 24 und 29 ab. Die ersten drei Stufen sind deutlich (0,4 bis 0,9 pH), die letzten drei liegen mit 0,2 bis 0,4 pH nur knapp über dem Rauschen von etwa ±0,3. Die Formulierung „nach etwa 4, 9, 14, 19, 24 und 29 Minuten“ ist damit vertretbar.
- **Die Pumpe ist in keiner Zeile aktiv,** die Dosierungen sind nur indirekt über die pH-Sprünge erkennbar. Das sollte in 5.3 stehen.

Die Zip enthält außerdem sechs PNG-Diagrammexporte vom 11.08. mit Pi-Zeitstempeln 21:18 bis 21:49. Die passen als Abbildung 4.4 zum Bildunterschrift-Vorschlag.

**Zum Prüfpunkt Kalibrierung:** Auf diesem Rechner liegen keine Kalibrierdaten, ich kann die Zeitangabe „innerhalb von 24 Stunden“ in 4.4.2 nicht prüfen. Wenn sie aus Pi-Zeitstempeln stammt, gilt derselbe Vorbehalt wie für 5.3.

Die Korrekturen 1 bis 12 zur Uhrzeit sind aus meiner Sicht schlüssig. Anhang D sollte zusätzlich vermerken, dass die Excel-Kopie nicht für die Auswertung taugt und die Originalexporte aus Downloads zu verwenden sind.

Wenn du mir das Skript aus Anhang B als Datei gibst oder es vom Pi kopierst, vergleiche ich es direkt mit der Messreihe, damit Takt, Sperrzeit und fehlende Spannungsspalte auch aus dem Code belegt sind.

**Antwort (2026-09-16 20:43)**

Damit kann ich den Vergleich mit den Messreihen direkt am Code machen. Ich lese ganzerCode.py.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:44)**

Der Code erklärt alle Auffälligkeiten der Messreihen. Ich prüfe noch, ob die Dosierzeitpunkte im Export exakt zum Ablauf der Hauptschleife passen.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-16 20:45)**

**Bestätigt: ganzerCode.py ist das Skript, das alle Messreihen erzeugt hat.** Jede Auffälligkeit der Exporte folgt direkt aus dem Code:

- **10-s-Takt:** Die Hauptschleife misst 30-mal den pH mit 10 s Pause (PH_MESSZYKLEN, PH_MESSPAUSE) und aktualisiert nach jeder Messung den API-Zustand. Die Exporte zeigen zwischen zwei Dosierungen exakt 30 Zeilen.
- **Dosierabstand 5,3 min:** 30 Messungen mal 10 s sind 300 s, dazu Pumpenlauf, 5 s Stabilisierung und Sensorlesezeiten. Die Lücken im Export von 18 bis 25 s markieren genau die Dosierzeitpunkte, alle im Abstand von 5,3 min.
- **Leere Spannungsspalte:** Der API-Zustand enthält kein Spannungsfeld. Die Spannung wird nur auf die Konsole gedruckt.
- **Pumpe nie aktiv im Export:** Der Pumpenstatus wird nur beim Aktualisieren des Zustands gelesen, und während des Pumpenlaufs wird nicht aktualisiert.
- **Lückenhafte Luftwerte:** Der DHT11 wird einmal je 5-min-Durchlauf gelesen. Schlägt das fehl, fehlen die Werte für alle 30 Zeilen des Durchlaufs.

**Folgen für Tabelle 5.2 und Kapitel 3, jetzt aus dem Code belegt:**

- **S-01 (CSV, Intervall ≤ 30 s): nein.** Das Skript schreibt eine CSV-Zeile je Durchlauf, also alle 5 min, und darin nur die letzte der 30 pH-Messungen. Die feinen 10-s-Reihen existieren nur, weil der Node-Server den Zustand abgefragt hat. Anhang D stammt damit aus dem Verlaufspuffer der Weboberfläche, nicht aus dem Pi-Protokoll.
- **S-04 (Zeitbegrenzung ≤ 10 s): nein.** Der Endpunkt /api/pump/on schaltet dauerhaft ein, es gibt keine Zeitbegrenzung und keinen Lock. Nur die Regelung selbst begrenzt auf 2 bis 5 s.
- **S-03 (Rückwirkungsfreiheit): teilweise.** Testlauf und Not-Aus des Dashboards laufen ins Leere, weil der Node-Server /api/pumpe/test und /api/pumpe/stopp aufruft, die dieses Skript nicht kennt. Ein direkter Aufruf von /api/pump/on schaltet die Pumpe dagegen unbegrenzt ein, bis die Regelung sie nach einer Dosierung zufällig wieder ausschaltet.
- **Netzanbindung 3.7.3:** Die API bindet auf alle Schnittstellen, also auch auf das WLAN. Der Satz „damit ist die Pumpen-Schnittstelle von außen nicht erreichbar“ gilt für dieses Skript nicht.

**Korrektur am Ersatztext für 5.3:** In der Reihe 21:18 bis 21:48 gab es nur vier Dosierungen, nach 3,2, 8,6, 13,9 und 19,2 min. Bei 24 und 29 min wurde nicht dosiert, weil die Dosierentscheidung allein von der letzten der 30 Messungen abhängt und die dort unter 6,0 lag. Die Absenkungen bei 24 und 29 min sind Drift oder Rauschen, keine Stufen. Der Effekt der Dosierungen ist in dieser Reihe zudem nicht als Sprung sichtbar, der pH ändert sich direkt danach um +0,40, −0,29, +0,22 und +0,02. Klare Sprünge von 1,1 bis 2,1 pH zeigt nur die Reihe vom 07.08. (19:38 bis 20:48), dort bei zehn Dosierungen. Vielleicht ist diese Reihe für 5.3 die aussagekräftigere.

**Abschnitt 4.3 passt nicht zu diesem Skript.** Dort steht Schwelle pH 3,5, feste Pumpzeit 5 s, Wartezeit 10 s. In ganzerCode.py sind es Schwelle 6,0, Pumpzeit 2 bis 5 s proportional zur Abweichung, 5 s Stabilisierung und der 30er-Messzyklus. Die Kennlinienherleitung in 4.3 stimmt dagegen: VREF 4,95, Offset 365, Mittelung der mittleren 6 von 10 Werten und die additive Konstante K = 8,23.

Die Datei liegt bisher nur in Downloads. Ich würde sie als iot/vorprojekt/ganzerCode.py ins Repo legen und in der README als das bei den Messreihen verwendete Programm nennen, damit Anhang B belegbar ist. Sag Bescheid, dann übernehme ich das mit Commit.

## Frage (2026-09-18 06:51)

Microsoft Windows [Version 10.0.26200.9457]
(c) Microsoft Corporation. All rights reserved.

C:\Users\prati>cd C:\Users\prati\hydroponic-system

C:\Users\prati\hydroponic-system>npm install

up to date, audited 70 packages in 4s

14 packages are looking for funding
  run `npm fund` for details

4 vulnerabilities (2 moderate, 2 high)

To address all issues, run:
  npm audit fix

Run `npm audit` for details.

C:\Users\prati\hydroponic-system> Wie sollte ich dann powershell als Admin laufen lassen

**Antwort (2026-09-18 06:52)**

Du bist gerade in der Eingabeaufforderung (cmd), nicht in PowerShell. Administratorrechte brauchst du nur einmalig für die feste IP-Adresse am Adapter. Der normale Start über start-pi.ps1 läuft ohne Adminrechte.

**PowerShell als Administrator öffnen**, eine der drei Möglichkeiten:

1. Windows-Taste + X drücken, dann „Terminal (Administrator)“ wählen.
2. Im Startmenü „PowerShell“ eintippen, Rechtsklick auf „Windows PowerShell“, „Als Administrator ausführen“.
3. Direkt aus deinem cmd-Fenster heraus:

```
powershell -Command "Start-Process powershell -Verb RunAs"
```

Es erscheint die Abfrage der Benutzerkontensteuerung, die du mit „Ja“ bestätigst. Das neue Fenster zeigt im Titel „Administrator“.

**Dort dann einmalig** die Adresse setzen, wie in Abschnitt 3 der README:

```powershell
Get-NetAdapter
Set-NetIPInterface -InterfaceAlias "Ethernet 2" -Dhcp Disabled
New-NetIPAddress  -InterfaceAlias "Ethernet 2" -IPAddress 192.168.10.2 -PrefixLength 24
```

Der Name „Ethernet 2“ muss genau der Spalte „Name“ aus der ersten Ausgabe entsprechen. Wenn der USB-Adapter bei dir anders heißt, den Namen in den beiden folgenden Befehlen ersetzen.

**Danach das Admin-Fenster schließen** und im normalen Fenster starten. Dafür in cmd erst PowerShell öffnen, da start-pi.ps1 ein PowerShell-Skript ist:

```
powershell
.\start-pi.ps1
```

Falls PowerShell die Skriptausführung blockiert, vorher im selben Fenster:

```powershell
Set-ExecutionPolicy -Scope Process -Bypass
```

Das Skript prüft dann selbst, ob die Adresse gesetzt ist und der Pi erreichbar ist, und startet den Server.

## Frage (2026-09-18 06:53)

Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

PS C:\WINDOWS\system32> Get-NetAdapter

Name                      InterfaceDescription                    ifIndex Status       MacAddress             LinkSpeed
----                      --------------------                    ------- ------       ----------             ---------
Norton VPN Wintun         Norton VPN Wintun Adapter                    23 Disconnected                         100 Gbps
WiFi                      MediaTek Wi-Fi 6E MT7902 Wireless LA...      21 Up           F8-54-F6-45-7C-D2     433.3 Mbps
Norton VPN OpenVPN Dat... Norton VPN OpenVPN Data Channel Offload      14 Up                                   100 Gbps
Bluetooth Network Conn... Bluetooth Device (Personal Area Netw...       6 Disconnected F8-54-F6-45-7C-D3         3 Mbps
Ethernet 2                Realtek USB GbE Family Controller             5 Disconnected 00-13-3B-FD-B4-20          0 bps


PS C:\WINDOWS\system32> Set-NetIPInterface -InterfaceAlias "Ethernet 2" -Dhcp Disabled
PS C:\WINDOWS\system32> New-NetIPAddress  -InterfaceAlias "Ethernet 2" -IPAddress 192.168.10.2 -PrefixLength 24
New-NetIPAddress : Instance MSFT_NetIPAddress already exists
At line:1 char:1
+ New-NetIPAddress  -InterfaceAlias "Ethernet 2" -IPAddress 192.168.10. ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (MSFT_NetIPAddress:ROOT/StandardCimv2/MSFT_NetIPAddress) [New-NetIPAddr
   ess], CimException
    + FullyQualifiedErrorId : Windows System Error 87,New-NetIPAddress

PS C:\WINDOWS\system32>

**Antwort (2026-09-18 06:53)**

Die Fehlermeldung ist unkritisch: die Adresse 192.168.10.2 ist auf „Ethernet 2“ bereits gesetzt, es gibt nichts mehr zu tun. Ich prüfe das kurz von hier aus.

_[Werkzeugaufruf: PowerShell]_

**Antwort (2026-09-18 06:53)**

**Die Windows-Seite ist fertig.** Die Meldung „already exists“ bedeutet nur, dass 192.168.10.2/24 auf „Ethernet 2“ schon eingetragen war, vermutlich aus einer früheren Einrichtung. Die Adresse ist manuell und mit der richtigen Präfixlänge gesetzt. Du kannst das Admin-Fenster schließen.

Zwei Dinge aus der Ausgabe:

- **„Ethernet 2“ ist „Disconnected“.** Das Kabel steckt nicht oder der Pi ist aus. Deshalb steht die Adresse noch auf „Tentative“. Sobald die Verbindung steht, wird sie aktiv.
- **Es liegt zusätzlich 192.168.50.1/24 auf dem Adapter.** Das stört die Verbindung zum Pi nicht. Wenn du sie nicht mehr brauchst, kannst du sie im Admin-Fenster entfernen:

```powershell
Remove-NetIPAddress -InterfaceAlias "Ethernet 2" -IPAddress 192.168.50.1 -Confirm:$false
```

**Weiter geht es so:** Kabel zwischen Rechner und Pi stecken, Pi einschalten, etwa eine Minute warten, dann in einem normalen PowerShell-Fenster im Projektordner:

```powershell
cd C:\Users\prati\hydroponic-system
.\start-pi.ps1
```

Das Skript prüft die Adresse und die Erreichbarkeit des Pi und startet dann den Server. Das Dashboard ist danach unter http://localhost:3000 erreichbar.

Falls das Skript „Pi nicht erreichbar“ meldet, obwohl das Kabel steckt: Norton VPN ist bei dir aktiv. Manche VPN-Clients blockieren Verkehr ins lokale Netz. Dann das VPN kurz trennen und den Test wiederholen. Ansonsten hilft die Tabelle in Abschnitt 3 der README.

Auf dem Pi muss dabei das Messprogramm laufen. Denk daran, dass der Node-Server nur zu hydroponik.py vollständig passt. Mit ganzerCode.py zeigt das Dashboard die Werte an, aber Testlauf und Not-Aus funktionieren nicht.

## Frage (2026-09-18 06:57)

PS C:\WINDOWS\system32> Remove-NetIPAddress -InterfaceAlias "Ethernet 2" -IPAddress 192.168.50.1 -Confirm:$false
>>
PS C:\WINDOWS\system32> Test-NetConnection 192.168.10.1 -Port 5000
WARNING: TCP connect to (192.168.10.1 : 5000) failed
WARNING: Ping to 192.168.10.1 failed with status: TimedOut

**Antwort (2026-09-18 06:57)**

Ich prüfe, ob das Kabel jetzt erkannt wird und über welchen Adapter die Pakete laufen.

_[Werkzeugaufruf: PowerShell]_

**Antwort (2026-09-18 06:58)**

**Die Ursache ist die Kabelverbindung, nicht die Konfiguration.** „Ethernet 2“ meldet weiterhin „Disconnected“ mit 0 bps. Windows sieht also kein Gerät am anderen Ende des Kabels. Solange das so ist, kann kein Ping ankommen, egal was auf dem Pi eingestellt ist.

Der Reihe nach prüfen:

1. **Ist der Pi eingeschaltet?** Rote LED leuchtet dauerhaft, grüne blinkt beim Booten. Nach dem Einschalten etwa eine Minute warten.
2. **Steckt das Kabel an beiden Enden fest?** Am Pi und am USB-Adapter muss es einrasten. An der Ethernet-Buchse des Pi leuchten bei Verbindung die beiden kleinen LEDs.
3. **Ist der USB-Adapter richtig eingesteckt?** Er wird erkannt, sonst stünde er nicht in der Liste. Trotzdem einmal ab- und wieder anstecken, danach die feste Adresse mit dem Befehl aus dem Startskript prüfen, sie geht bei USB-Adaptern gelegentlich verloren.
4. **Anderes Kabel probieren**, falls die LEDs am Pi dunkel bleiben.

Sobald der Link steht, zeigt dieser Befehl „Up“ und eine Geschwindigkeit:

```powershell
Get-NetAdapter -Name "Ethernet 2"
```

Erst dann lohnt sich der Test erneut:

```powershell
Test-NetConnection 192.168.10.1 -Port 5000
```

Schlägt danach nur der Port fehl, der Ping aber klappt, läuft auf dem Pi kein Messprogramm. Schlägt der Ping trotz „Up“ fehl, fehlt auf dem Pi die Adresse 192.168.10.1/24, siehe Abschnitt 3 der README.

## Frage (2026-09-18 06:59)

PS C:\WINDOWS\system32> Test-NetConnection 192.168.10.1 -Port 5000
WARNING: TCP connect to (192.168.10.1 : 5000) failed


ComputerName           : 192.168.10.1
RemoteAddress          : 192.168.10.1
RemotePort             : 5000
InterfaceAlias         : Ethernet 2
SourceAddress          : 192.168.10.2
PingSucceeded          : True
PingReplyDetails (RTT) : 1 ms
TcpTestSucceeded       : False



PS C:\WINDOWS\system32>

**Antwort (2026-09-18 06:59)**

**Die Verbindung steht jetzt.** Ping klappt über „Ethernet 2“ von 192.168.10.2 zu 192.168.10.1 mit 1 ms. Nur Port 5000 antwortet nicht, das heißt: auf dem Pi läuft kein Messprogramm.

Auf dem Pi per SSH anmelden und das Programm starten. Über das Kabel geht das jetzt direkt:

```powershell
ssh pi@192.168.10.1
```

Dort dann, je nachdem welches Programm du verwenden willst:

```bash
cd ~/hydroponic-project
python3 iot/hydroponik.py --nur-messen      # neue Software, Pumpe gesperrt
```

oder das alte Skript, mit dem die Messreihen entstanden sind:

```bash
python3 ganzerCode.py
```

Wenn im Terminal „API laeuft auf http://0.0.0.0:5000“ erscheint, in einem zweiten PowerShell-Fenster auf dem Rechner:

```powershell
cd C:\Users\prati\hydroponic-system
.\start-pi.ps1
```

Danach ist das Dashboard unter http://localhost:3000 erreichbar.

Zwei Hinweise:

- **Falls der Dienst eingerichtet ist**, könnte er nur nicht gestartet sein. Prüfen mit `systemctl status hydroponik`, starten mit `sudo systemctl start hydroponik`. Läuft er angeblich, aber Port 5000 bleibt zu, zeigt `journalctl -u hydroponik -n 30` den Fehler.
- **Uhrzeit vor einer Messreihe prüfen**, das war der Befund von gestern. Auf dem Pi `date` eingeben. Stimmt Datum oder Uhrzeit nicht, ist das WLAN aus oder kein Zeitserver erreichbar. Zur Not lässt sich die Zeit vom Rechner setzen, hier für den Moment:

```bash
sudo date -s "2026-09-18 HH:MM:SS"
```

Die eigentliche Uhrzeit trägst du selbst ein.

## Frage (2026-09-18 07:01)

PS C:\WINDOWS\system32> Test-NetConnection 192.168.10.1 -Port 5000


ComputerName     : 192.168.10.1
RemoteAddress    : 192.168.10.1
RemotePort       : 5000
InterfaceAlias   : Ethernet 2
SourceAddress    : 192.168.10.2
TcpTestSucceeded : True



PS C:\WINDOWS\system32> PS C:\WINDOWS\system32> Test-NetConnection 192.168.10.1 -Port 5000
Get-Process : A positional parameter cannot be found that accepts argument 'Test-NetConnection'.
At line:1 char:1
+ PS C:\WINDOWS\system32> Test-NetConnection 192.168.10.1 -Port 5000
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Get-Process], ParameterBindingException
    + FullyQualifiedErrorId : PositionalParameterNotFound,Microsoft.PowerShell.Commands.GetProcessCommand

PS C:\WINDOWS\system32> WARNING: TCP connect to (192.168.10.1 : 5000) failed
At line:1 char:39
+ WARNING: TCP connect to (192.168.10.1 : 5000) failed
+                                       ~
Unexpected token ':' in expression or statement.
At line:1 char:38
+ WARNING: TCP connect to (192.168.10.1 : 5000) failed
+                                      ~
Missing closing ')' in expression.
At line:1 char:45
+ WARNING: TCP connect to (192.168.10.1 : 5000) failed
+                                             ~
Unexpected token ')' in expression or statement.
    + CategoryInfo          : ParserError: (:) [], ParentContainsErrorRecordException
    + FullyQualifiedErrorId : UnexpectedToken

PS C:\WINDOWS\system32>
PS C:\WINDOWS\system32>
PS C:\WINDOWS\system32> ComputerName           : 192.168.10.1
ComputerName : The term 'ComputerName' is not recognized as the name of a cmdlet, function, script file, or operable
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ ComputerName           : 192.168.10.1
+ ~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (ComputerName:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32> RemoteAddress          : 192.168.10.1
RemoteAddress : The term 'RemoteAddress' is not recognized as the name of a cmdlet, function, script file, or operable
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ RemoteAddress          : 192.168.10.1
+ ~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (RemoteAddress:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32> RemotePort             : 5000
RemotePort : The term 'RemotePort' is not recognized as the name of a cmdlet, function, script file, or operable
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ RemotePort             : 5000
+ ~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (RemotePort:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32> InterfaceAlias         : Ethernet 2
InterfaceAlias : The term 'InterfaceAlias' is not recognized as the name of a cmdlet, function, script file, or
operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try
again.
At line:1 char:1
+ InterfaceAlias         : Ethernet 2
+ ~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (InterfaceAlias:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32> SourceAddress          : 192.168.10.2
SourceAddress : The term 'SourceAddress' is not recognized as the name of a cmdlet, function, script file, or operable
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ SourceAddress          : 192.168.10.2
+ ~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (SourceAddress:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32> PingSucceeded          : True
PingSucceeded : The term 'PingSucceeded' is not recognized as the name of a cmdlet, function, script file, or operable
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ PingSucceeded          : True
+ ~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (PingSucceeded:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32> PingReplyDetails (RTT) : 1 ms
RTT : The term 'RTT' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the
spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:19
+ PingReplyDetails (RTT) : 1 ms
+                   ~~~
    + CategoryInfo          : ObjectNotFound: (RTT:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32> TcpTestSucceeded       : False
TcpTestSucceeded : The term 'TcpTestSucceeded' is not recognized as the name of a cmdlet, function, script file, or
operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try
again.
At line:1 char:1
+ TcpTestSucceeded       : False
+ ~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (TcpTestSucceeded:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\WINDOWS\system32>
PS C:\WINDOWS\system32>
PS C:\WINDOWS\system32>
PS C:\WINDOWS\system32> PS C:\WINDOWS\system32>

**Antwort (2026-09-18 07:01)**

**Alles in Ordnung: der erste Test war erfolgreich.** Er zeigt „TcpTestSucceeded : True“. Der Pi ist erreichbar und das Messprogramm läuft auf Port 5000.

Die vielen Fehlermeldungen darunter sind harmlos. Du hast versehentlich die alte Ausgabe des vorigen Tests in das Fenster eingefügt, und PowerShell hat versucht, jede Zeile davon als Befehl auszuführen. Das hat nichts verändert.

Jetzt in einem normalen PowerShell-Fenster den Server starten:

```powershell
cd C:\Users\prati\hydroponic-system
.\start-pi.ps1
```

Wenn im Terminal diese Zeile erscheint, ist alles verbunden:

```
Pi-API: http://192.168.10.1:5000 (alle 2000 ms)
```

Dann im Browser http://localhost:3000 öffnen. In der Pumpen-Karte muss die Betriebsart „messbetrieb“ oder „regelung“ stehen. Steht dort nichts oder „--“, läuft auf dem Pi ganzerCode.py statt hydroponik.py, denn das alte Skript liefert kein Betriebsart-Feld.

## Frage (2026-09-18 07:03)

Microsoft Windows [Version 10.0.26200.9457]
(c) Microsoft Corporation. All rights reserved.

C:\Users\prati>cd C:\Users\prati\hydroponic-system

C:\Users\prati\hydroponic-system>npm install

up to date, audited 70 packages in 4s

14 packages are looking for funding
  run `npm fund` for details

4 vulnerabilities (2 moderate, 2 high)

To address all issues, run:
  npm audit fix

Run `npm audit` for details.

C:\Users\prati\hydroponic-system>powershell -Command "Start-Process powershell -Verb RunAs"

C:\Users\prati\hydroponic-system>.\start-pi.ps1

C:\Users\prati\hydroponic-system>.\start-pi.ps1

C:\Users\prati\hydroponic-system>npm install

up to date, audited 70 packages in 4s

14 packages are looking for funding
  run `npm fund` for details

4 vulnerabilities (2 moderate, 2 high)

To address all issues, run:
  npm audit fix

Run `npm audit` for details.

C:\Users\prati\hydroponic-system>npm start

> hydroponic-system@1.0.0 start
> node server/server.js

Server laeuft auf http://localhost:3000
Kein PI_API_BASE_URL gesetzt - Demobetrieb, Daten per WebSocket erwartet

**Antwort (2026-09-18 07:03)**

**Der Server läuft im Demobetrieb statt am Pi.** Grund: du bist noch in der Eingabeaufforderung (cmd). Dort öffnet `.\start-pi.ps1` das Skript nur im Editor oder tut nichts, statt es auszuführen, und `npm start` ohne die Variable PI_API_BASE_URL startet den Demobetrieb.

So klappt es, im selben cmd-Fenster:

1. Den laufenden Server mit Strg+C beenden.
2. Dann:

```
powershell
.\start-pi.ps1
```

Die erste Zeile wechselt in PowerShell, die zweite führt das Skript aus. Es meldet „Pi erreichbar.“ und startet den Server. Die Erfolgskontrolle ist diese Zeile:

```
Pi-API: http://192.168.10.1:5000 (alle 2000 ms)
```

Falls PowerShell meldet, dass die Skriptausführung deaktiviert ist:

```powershell
Set-ExecutionPolicy -Scope Process -Bypass
.\start-pi.ps1
```

Alternativ ohne Skript, ebenfalls in PowerShell:

```powershell
$env:PI_API_BASE_URL = "http://192.168.10.1:5000"
npm start
```

Danach http://localhost:3000 im Browser öffnen.

## Frage (2026-09-18 07:05)

Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

 Test-NetConnection - 192.168.10.1:5000
    Attempting TCP connect

    Waiting for response

+ .\start-pi.ps1
+ ~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (.\start-pi.ps1:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\Users\prati> cd C:\Users\prati\hydroponic-system
PS C:\Users\prati\hydroponic-system> .\start-pi.ps1
Pruefe Pi-API unter http://192.168.10.1:5000 ...
Pi erreichbar.

> hydroponic-system@1.0.0 start
> node server/server.js


PS C:\Users\prati> .\start-pi.ps1
.\start-pi.ps1 : The term '.\start-pi.ps1' is not recognized as the name of a cmdlet, function, script file, or
operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try
again.
At line:1 char:1
    at listenInCluster (node:net:1996:12)
    at Server.listen (node:net:2101:7)
    at Object.<anonymous> (C:\Users\prati\hydroponic-system\server\server.js:253:8)
    at Module._compile (node:internal/modules/cjs/loader:1730:14)
    at Object..js (node:internal/modules/cjs/loader:1895:10)
    at Module.load (node:internal/modules/cjs/loader:1465:32)
    at Function._load (node:internal/modules/cjs/loader:1282:12)
    at TracingChannel.traceSync (node:diagnostics_channel:322:14)
    at wrapModuleLoad (node:internal/modules/cjs/loader:235:24)
Emitted 'error' event on WebSocketServer instance at:
    at Server.emit (node:events:518:28)
    at emitErrorNT (node:net:1975:8)
    at process.processTicksAndRejections (node:internal/process/task_queues:90:21) {
  code: 'EADDRINUSE',
  errno: -4091,
  syscall: 'listen',
  address: '::',
  port: 3000
}

Node.js v22.15.0
PS C:\Users\prati\hydroponic-system>

**Antwort (2026-09-18 07:05)**

Das Skript hat funktioniert, der Pi ist erreichbar. Der Start scheitert nur, weil Port 3000 noch vom Demobetrieb-Server aus dem cmd-Fenster belegt ist. Ich prüfe, welcher Prozess das ist.

_[Werkzeugaufruf: PowerShell]_

**Antwort (2026-09-18 07:05)**

Das ist der Demobetrieb-Server aus dem cmd-Fenster. Ich beende ihn.

_[Werkzeugaufruf: PowerShell]_

**Antwort (2026-09-18 07:05)**

**Port 3000 ist wieder frei.** Der alte Demobetrieb-Server aus dem cmd-Fenster ist beendet.

Jetzt in deinem PowerShell-Fenster, das schon im Projektordner steht, einfach noch einmal:

```powershell
.\start-pi.ps1
```

Diesmal sollte nach „Pi erreichbar.“ diese Zeile kommen:

```
Server laeuft auf http://localhost:3000
Pi-API: http://192.168.10.1:5000 (alle 2000 ms)
```

Dann http://localhost:3000 im Browser öffnen. Die Kopfzeile muss „Verbunden“ zeigen und in der Pumpen-Karte die Betriebsart „messbetrieb“ oder „regelung“.

Der Grund für die Fehlermeldung „start-pi.ps1 not recognized“ zwischendurch: dieser Aufruf kam aus dem Ordner C:\Users\prati, wo das Skript nicht liegt. Das Skript muss immer aus dem Projektordner heraus gestartet werden.

## Frage (2026-09-18 07:13)

Das ist die Neue .py code, das auf dem Raspberry Pi läuft: Test 17.09.2026

"""
Kalibrierung der pH-Messkette — eigenständiges Skript, getrennt von
hydroponik.py, damit eine neue Kalibrierung (z. B. nach dem Wässern der
Elektrode, Punkt t) den Regelungscode nicht verändert.

Verfahren (Abschnitt 4.4.1 der Dokumentation):
  - Zweipunktkalibrierung mit den Puffern pH 4,01 und 7,00 -> Steilheit
    und Nullpunkt (Gleichung 4.5/4.6). Der Sollwert 5,8 liegt zwischen
    diesen beiden Stützstellen, es wird also interpoliert, nicht
    extrapoliert.
  - Puffer pH 10,01 dient NUR der Verifikation (Gleichung 4.7), fließt
    nicht in Steilheit/Nullpunkt ein — oberhalb von pH 7 verfälscht der
    Alkalifehler der Glaselektrode sonst die Steilheitsberechnung.

Neu gegenüber der bisherigen Kalibrierung: Die Temperatur wird mit dem
DS18B20 direkt in der jeweiligen Pufferlösung gemessen (Sensor beim
Kalibrieren mit in den Becher halten), statt pauschal Raumtemperatur
anzunehmen (bisherige Einschränkung, siehe Abschnitt 4.4).

Ergebnis wird nach kalibrierung.json geschrieben und von hydroponik.py
beim Start eingelesen.
"""

import json
import os
import statistics
import threading
import time
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

SKRIPT_VERZEICHNIS = os.path.dirname(os.path.abspath(__file__))

W1_DEVICE_PATH   = "/sys/bus/w1/devices/"
KALIBRIER_DATEI  = os.path.join(SKRIPT_VERZEICHNIS, "kalibrierung.json")
ADC_MAX          = 32767   # Vollausschlag ADS1115 bei gain=1 -> 4,096 V
S_THEOR_25C      = 59.16   # mV/pH, Nernst-Steilheit bei 25 °C (Gleichung 2.3)
M06_GRENZE_PROZENT = 85.0  # Brauchbarkeitsgrenze aus M-06

# Messabstand während des Einpendelns. Es wird nicht mehr automatisch anhand
# einer Schwankungsbreite gestoppt, sondern erst, wenn per Enter bestätigt
# wird, dass der angezeigte Wert stabil aussieht.
MESSABSTAND_S = 15

i2c     = busio.I2C(board.SCL, board.SDA)
ads     = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan = AnalogIn(ads, 0)


def read_water_temp():
    """Identisch zu hydroponik.py — hier bewusst dupliziert, damit dieses
    Skript unabhängig läuft und nicht versehentlich die Hauptschleife von
    hydroponik.py mit importiert."""
    try:
        device_folder = [d for d in os.listdir(W1_DEVICE_PATH) if d.startswith("28-")][0]
        device_file   = f"{W1_DEVICE_PATH}{device_folder}/w1_slave"
        with open(device_file, "r") as f:
            lines = f.readlines()
        if "YES" not in lines[0]:
            return None
        return float(lines[1].split("t=")[-1]) / 1000.0
    except Exception:
        return None


def einzelmessung_mv() -> float:
    """Eine gefilterte Spannungsmessung: 10 Rohwerte, sortiert, Mittelwert
    der mittleren 6 — dieselbe Filterung wie in read_ph() (hydroponik.py)."""
    buf = []
    for _ in range(10):
        buf.append(ph_chan.value)
        time.sleep(0.01)
    buf.sort()
    avg_value = sum(buf[2:8]) / 6
    return avg_value * 4.096 / ADC_MAX * 1000


def messe_puffer(bezeichnung: str) -> tuple[float, float]:
    """Fragt den Puffer ab und misst fortlaufend alle MESSABSTAND_S Sekunden.
    Jede Zwischenmessung wird mit Zeitstempel, Spannung, Temperatur und
    Differenz zur vorherigen Messung ausgegeben, damit das Einpendeln am
    Bildschirm sichtbar ist. Es wird so lange weitergemessen, bis die
    Bedienperson per Enter bestätigt, dass der zuletzt angezeigte Wert
    stabil ist — es gibt keinen automatischen Abbruch nach einer festen
    Anzahl Messungen. Gibt (spannung_mv, temperatur_c) der zuletzt vor der
    Bestätigung angezeigten Messung zurück."""
    input(f"\nElektrode UND Temperatursensor in Puffer {bezeichnung} geben, "
          f"dann Enter drücken, um mit der Messung zu beginnen ...")

    bestaetigt = threading.Event()

    def warte_auf_enter():
        input("  (Enter drücken, sobald der Wert stabil aussieht — die "
              "Messung läuft bis dahin weiter)\n")
        bestaetigt.set()

    threading.Thread(target=warte_auf_enter, daemon=True).start()

    letzte_spannung = None
    letzte_temperatur = None
    vorherige_spannung = None
    start = time.time()

    while True:
        u = einzelmessung_mv()
        t = read_water_temp()

        vergangen = time.time() - start
        zeile = f"  t={vergangen:5.0f} s   U={u:8.1f} mV"
        if t is not None:
            zeile += f"   T={t:5.1f} °C"
        if vorherige_spannung is not None:
            zeile += f"   Δ zur letzten Messung: {u - vorherige_spannung:+.1f} mV"
        print(zeile)

        letzte_spannung, letzte_temperatur = u, t
        vorherige_spannung = u

        # Bis zu MESSABSTAND_S Sekunden auf die Bestätigung warten; kommt sie
        # in dieser Zeit, sofort mit der zuletzt gedruckten Messung abbrechen.
        if bestaetigt.wait(timeout=MESSABSTAND_S):
            print(f"  -> übernommen: {letzte_spannung:.1f} mV"
                  + (f", {letzte_temperatur:.1f} °C" if letzte_temperatur is not None else ""))
            return letzte_spannung, letzte_temperatur


def nernst_steilheit_theorie(temperatur_c: float) -> float:
    """Theoretische Steilheit bei gegebener Temperatur, aus dem bekannten
    Wert 59,16 mV/pH bei 25 °C nach Gleichung 2.3 (Steilheit prop. zu T)."""
    return S_THEOR_25C * (273.15 + temperatur_c) / (273.15 + 25.0)


def main():
    print("=== Kalibrierung der pH-Messkette (2-Punkt: pH 4,01 / 7,00) ===")

    u_ph4, t_ph4 = messe_puffer("pH 4,01")
    u_ph7, t_ph7 = messe_puffer("pH 7,00")

    steilheit = (u_ph4 - u_ph7) / (7.00 - 4.01)   # Gleichung 4.5
    u0        = u_ph7                              # Gleichung 4.6, Nullpunkt bei pH 7,00

    if t_ph4 is not None and t_ph7 is not None:
        t_kal = statistics.mean([t_ph4, t_ph7])
    else:
        t_kal = t_ph4 or t_ph7
        print("WARNUNG: Temperatur nur an einem Puffer verfügbar — "
              "Prüfe den DS18B20-Anschluss.")

    if t_kal is None:
        print("FEHLER: Keine Temperaturmessung möglich. Ohne Kalibriertemperatur "
              "kann die Temperaturkompensation (Gleichung 3.2) nicht arbeiten.")
        t_kal = float(input("Ersatzweise Temperatur manuell eingeben (°C): "))

    steilheit_theorie = nernst_steilheit_theorie(t_kal)
    steilheit_prozent = abs(steilheit) / steilheit_theorie * 100

    print(f"\nSteilheit S  = {steilheit:.1f} mV/pH  "
          f"({steilheit_prozent:.1f} % der theoretischen Steilheit bei {t_kal:.1f} °C)")
    print(f"Nullpunkt U0 = {u0:.1f} mV (bei pH 7,00)")

    if steilheit_prozent < M06_GRENZE_PROZENT:
        print(f"ACHTUNG: {steilheit_prozent:.1f} % liegt unter der Brauchbarkeitsgrenze "
              f"von {M06_GRENZE_PROZENT:.0f} % (M-06). Elektrode wässern (Punkt t) "
              f"und erneut kalibrieren, bevor der Regelbetrieb gestartet wird.")

    # --- Verifikation mit pH 10,01 (fließt NICHT in Steilheit/Nullpunkt ein) ---
    u_ph10, t_ph10 = messe_puffer("pH 10,01 (nur Verifikation)")
    steilheit_bei_t10 = steilheit * (273.15 + t_ph10) / (273.15 + t_kal) if t_ph10 else steilheit
    ph_berechnet_10 = 7 + (u0 - u_ph10) / steilheit_bei_t10
    abweichung_10 = ph_berechnet_10 - 10.01
    print(f"\nVerifikation pH 10,01: berechnet {ph_berechnet_10:.2f} "
          f"(Abweichung {abweichung_10:+.2f} pH — Alkalifehler, siehe Abschnitt 4.4.3)")

    ergebnis = {
        "u0_mv": round(u0, 1),
        "steilheit_mv_pro_ph": round(steilheit, 2),
        "t_kal_c": round(t_kal, 1),
        "steilheit_prozent_theorie": round(steilheit_prozent, 1),
        "zeitstempel": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rohdaten": {
            "ph4_mv": round(u_ph4, 1), "ph4_temp_c": round(t_ph4, 1) if t_ph4 else None,
            "ph7_mv": round(u_ph7, 1), "ph7_temp_c": round(t_ph7, 1) if t_ph7 else None,
            "ph10_mv": round(u_ph10, 1), "ph10_temp_c": round(t_ph10, 1) if t_ph10 else None,
        },
        "verifikation_ph10": {
            "berechnet": round(ph_berechnet_10, 2),
            "abweichung": round(abweichung_10, 2),
        },
    }

    with open(KALIBRIER_DATEI, "w") as f:
        json.dump(ergebnis, f, indent=2, ensure_ascii=False)

    print(f"\nGespeichert in {KALIBRIER_DATEI}. hydroponik.py verwendet diese Datei "
          f"automatisch beim nächsten Start.")


if __name__ == "__main__":
    main()

"""
Hydroponik pH-Regelung — überarbeitete Fassung.

Gegenüber der Vorversion umgesetzt (Bezeichner wie in der Projektdokumentation,
Kapitel 3/4):

  a) Kalibrierte Umrechnung (Abschnitt 4.4) statt Herstellerformel + K=8,23;
     Werte werden aus kalibrierung.json geladen (siehe kalibrieren.py),
     damit eine neue Kalibrierung dieses Skript nicht verändert
  c) Regelentscheidung auf Mittelwert der Messfenster-Werte statt Einzelwert
  e) Zeitbegrenzte, mit dem Node-Server kompatible Pumpen-Endpunkte
     (/api/pumpe/test, /api/pumpe/stopp); alter /api/pump/<action> entfernt
  f) Plausibilitätsprüfung (3,0–9,5 pH) und try/except um die ADC-Abfrage,
     damit ein I2C-Fehler nicht das ganze Programm beendet (R-07, S-02)
  h) Flask bindet nur noch auf die Ethernet-Adresse des Einplatinenrechners
  k) Totband ±0,2 pH (PH_TOLERANZ) statt scharfer Schwelle
  n) Kontrollmessung nach 5 s entfällt; die Wirkung wird stattdessen zu
     Beginn des nächsten Messfensters bewertet (~5 min später statt 5 s,
     oberhalb der Elektroden-Ansprechzeit von <2 min)
  o) Temperaturkompensation der Steilheit (Gleichung 3.2)
  p) Log-Intervall ≤ 30 s (jetzt: jede Einzelmessung, alle 10 s)
  q) Pumpenzustand wird vor dem Logging korrekt erfasst
  r) Dosierzeitpunkt und -menge werden protokolliert (dosierungen_log.csv)

  Zusätzlich ergänzt, weil vom Dashboard bereits erwartet (siehe server.js):
  Dosierzähler pro Stunde/Tag, Sperrzeit-Anzeige, Ausfallalarm nach
  wirkungslosen Dosierungen (R-05, R-06, aus [stated] Sicherheitsgrenzen).

Bewusst NICHT umgesetzt, weil sie Messungen statt Codeänderungen brauchen:
  b) Ursache des Messrauschens (Abschnitt 5.1)
  g/j/m) Sperrzeit und Dosiermenge aus Sprungantwort (Abschnitt 4.5) —
         SPERRZEIT_S unten ist ein Platzhalter
  s) Wägeversuch mit Wiederholungen — FOERDERRATE_ML_S ist eine grobe,
     einfach gemessene Schätzung, keine belastbare Kennlinie
  u) Regelgüte im Dauerbetrieb

=== ANNAHMEN, die noch zu bestätigen sind (Zeilen mit "ANNAHME:") ===
  1) SPERRZEIT_S = 600 s (10 min) als Platzhalter bis Abschnitt 4.5 vorliegt.
  2) KEIN_EFFEKT_SCHWELLE = 0.1 pH als Schwelle für "wirkungslose" Dosierung —
     liegt unterhalb des bekannten Messrauschens (0,16–0,31 pH) und ist damit
     selbst noch unsicher; siehe Abschnitt 5.1.
  3) Manuelle Testdosierungen über /api/pumpe/test zählen auf dasselbe
     Tageslimit (MAX_ML_PRO_TAG) wie automatische Dosierungen, aber NICHT auf
     die stündliche Dosenzahl und die Sperrzeit der Regelung.
  4) max_dosierungen_tag im API-Feld ist aus der Stundengrenze abgeleitet
     (MAX_DOSEN_PRO_STUNDE * 24) und keine eigenständig festgelegte Zahl.
"""

import time
import os
import json
import csv
import signal
import sys
import threading
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
from gpiozero import DigitalInputDevice, DigitalOutputDevice
from flask import Flask, jsonify, request
from flask_cors import CORS

# ============================
#   PIN-ZUWEISUNGEN
# ============================
DHT_PIN        = board.D17
FEUCHTE_PIN    = 27
PUMP_PIN       = 5
W1_DEVICE_PATH = "/sys/bus/w1/devices/"
LOG_FILE       = "hydroponik_log.csv"
DOSIER_LOG_FILE = "dosierungen_log.csv"

# Auf welcher Adresse der Einplatinenrechner die API bereitstellt (Punkt h).
# 192.168.10.1 = feste Ethernet-Adresse zum Anzeigerechner (Abschnitt 3.7.2).
# WICHTIG: Der Node-Server muss PI_API_BASE_URL=http://192.168.10.1:5000
# gesetzt haben, sonst ist der Pi über das bisherige WLAN nicht mehr erreichbar.
API_HOST = "192.168.10.1"
API_PORT = 5000

# ============================
#   SENSOR & AKTOR SETUP
# ============================
dht            = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
feuchte_sensor = DigitalInputDevice(FEUCHTE_PIN, pull_up=False)
pumpe          = DigitalOutputDevice(PUMP_PIN)
pumpe_lock     = threading.Lock()  # schützt gegen gleichzeitigen Zugriff
                                    # von Hauptschleife und Flask-Thread

# ============================
#   ADS1115 (pH-Sensor)
# ============================
i2c      = busio.I2C(board.SCL, board.SDA)
ads      = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan  = AnalogIn(ads, 0)
ADC_MAX  = 32767      # Vollausschlag ADS1115 bei gain=1 -> 4,096 V

# ============================
#   KALIBRIERUNG (Abschnitt 4.4) — Punkt a)
# ============================
# Werte kommen aus kalibrierung.json (siehe kalibrieren.py), nicht mehr fest
# im Code. So löst eine neue Kalibrierung (z. B. nach dem Wässern der
# Elektrode, Punkt t) nie eine Änderung an diesem Skript aus.
KALIBRIER_DATEI = "kalibrierung.json"


def lade_kalibrierung() -> dict:
    if not os.path.isfile(KALIBRIER_DATEI):
        raise RuntimeError(
            f"Keine Kalibrierung gefunden ({KALIBRIER_DATEI}). "
            f"Bitte zuerst kalibrieren.py ausführen."
        )
    with open(KALIBRIER_DATEI, "r") as f:
        daten = json.load(f)
    for feld in ("u0_mv", "steilheit_mv_pro_ph", "t_kal_c"):
        if feld not in daten:
            raise RuntimeError(f"{KALIBRIER_DATEI} ist unvollständig (Feld '{feld}' fehlt).")
    print(f"Kalibrierung geladen (vom {daten.get('zeitstempel', 'unbekannt')}): "
          f"U0={daten['u0_mv']} mV, S={daten['steilheit_mv_pro_ph']} mV/pH, "
          f"T_kal={daten['t_kal_c']} °C, "
          f"{daten.get('steilheit_prozent_theorie', '?')}% der theor. Steilheit")
    return daten


_kalibrierung = lade_kalibrierung()
U0_KAL        = _kalibrierung["u0_mv"]
STEILHEIT_KAL = _kalibrierung["steilheit_mv_pro_ph"]
T_KAL         = _kalibrierung["t_kal_c"]

# ============================
#   pH-REGELUNG
# ============================
PH_SOLL       = 5.8     # realer Zielwert, R-01 (vorher: Anzeige 6,0 unkalibriert)
PH_TOLERANZ   = 0.2     # Totband, R-02 — Punkt k). Dosiert wird nur, wenn
                         # ph_mittel > PH_SOLL + PH_TOLERANZ (einseitig, da nur
                         # pH-Minus verfügbar ist)
PH_PLAUSIBEL_MIN = 3.0  # Punkt f)
PH_PLAUSIBEL_MAX = 9.5
PH_MAX_ABW    = 2.0     # ab dieser Abweichung wird maximal lange gepumpt
PH_MESSZYKLEN = 30      # pH-Messungen pro Durchlauf der Hauptschleife
PH_MESSPAUSE  = 10      # Sekunden zwischen zwei pH-Messungen
PUMP_MIN_S    = 2       # kürzeste Pumpdauer (provisorisch, siehe Docstring g/j/m)
PUMP_MAX_S    = 5       # längste Pumpdauer (provisorisch)

# ============================
#   SICHERHEITSGRENZEN (bereits festgelegte Werte übernommen)
# ============================
PUMPE_MAX_EIN_S     = 10    # harte Obergrenze je Einschaltvorgang (S-04);
                             # Name bewusst wie im Kommentar von server.js
FOERDERRATE_ML_S    = 1.7   # ml/s, aus Einzelmessung (Abschnitt 5.2, Punkt s offen)
MAX_ML_PRO_DOSIS    = 20    # R-04
MAX_DOSEN_PRO_STUNDE = 6    # R-05 (Ersatz, bis Sperrzeit aus 4.5 feststeht)
MAX_ML_PRO_TAG      = 150   # R-06
SPERRZEIT_S         = 600   # ANNAHME 1: Platzhalter für R-05, siehe Docstring
KEIN_EFFEKT_SCHWELLE = 0.1  # ANNAHME 2: siehe Docstring
KEIN_EFFEKT_ALARM_NACH = 3  # Anzahl wirkungsloser Dosierungen in Folge

# ============================
#   GLOBALER ZUSTAND
# ============================
sensor_data = {
    "luft_temp":    None,
    "luft_feuchte": None,
    "wasser_temp":  None,
    "ph":           None,
    "ph_spannung":  None,
    "feuchtigkeit": None,
    "pumpe":        False,
    "betriebsart":  "automatik",
    "sollwert_ph":  PH_SOLL,
    "toleranz_ph":  PH_TOLERANZ,
    "dosierungen_gesamt":   0,
    "dosierungen_24h":      0,
    "max_dosierungen_tag":  MAX_DOSEN_PRO_STUNDE * 24,  # ANNAHME 4
    "dosierung_gesperrt":   False,
    "sperrzeit_rest_s":     0.0,
    "letzte_dosierung":     None,
    "timestamp":    None
}

# Dosierhistorie im Speicher: [{"zeit": float(epoch), "sekunden": float,
#   "ml": float, "ph_vor": float, "ausgewertet": bool, "quelle": str}, ...]
dosen_liste = []
regelzustand = {
    "gesperrt": False,
    "wirkungslos_counter": 0,
}


def dosen_in_letzten(sekunden: float) -> list:
    grenze = time.time() - sekunden
    return [d for d in dosen_liste if d["zeit"] >= grenze]


def ml_in_letzten(sekunden: float) -> float:
    return sum(d["ml"] for d in dosen_in_letzten(sekunden))


def status_snapshot() -> dict:
    """Berechnet die Zähler-/Sperrzeit-Felder für /api/sensors neu."""
    jetzt = time.time()
    letzte = dosen_liste[-1] if dosen_liste else None
    sperrzeit_rest = 0.0
    if letzte is not None:
        sperrzeit_rest = max(0.0, SPERRZEIT_S - (jetzt - letzte["zeit"]))
    return {
        "dosierungen_gesamt":  len(dosen_liste),
        "dosierungen_24h":     len(dosen_in_letzten(86400)),
        "dosierung_gesperrt":  regelzustand["gesperrt"],
        "sperrzeit_rest_s":    round(sperrzeit_rest, 1),
        "letzte_dosierung": (
            {
                "zeit": datetime.fromtimestamp(letzte["zeit"]).strftime("%Y-%m-%d %H:%M:%S"),
                "sekunden": letzte["sekunden"],
                "ml": round(letzte["ml"], 2),
            }
            if letzte is not None else None
        ),
    }


def update_sensor_data(luft_temp, luft_feuchte, w_temp, ph, ph_spannung, feucht):
    """Globalen Zustand an einer einzigen Stelle aktualisieren (Punkt q):
    pumpe.is_active wird HIER gelesen, also im selben Moment wie der Rest —
    nicht erst nach einem späteren pumpe.off()."""
    sensor_data.update({
        "luft_temp":    luft_temp,
        "luft_feuchte": luft_feuchte,
        "wasser_temp":  w_temp,
        "ph":           ph,
        "ph_spannung":  ph_spannung,
        "feuchtigkeit": feucht,
        "pumpe":        pumpe.is_active,
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    sensor_data.update(status_snapshot())


# ============================
#   FLASK API
# ============================
app = Flask(__name__)
CORS(app)


@app.route("/api/sensors")
def get_sensors():
    return jsonify(sensor_data)


def _dosierung_ausfuehren(sekunden: float, quelle: str) -> dict:
    """Führt eine zeitbegrenzte Dosierung aus (Punkt e) und protokolliert sie
    (Punkt r). Wird sowohl von der Regelung als auch von /api/pumpe/test
    genutzt, damit es nur eine Stelle gibt, die tatsächlich pumpe.on() ruft."""
    sekunden = min(max(sekunden, 0.0), PUMPE_MAX_EIN_S)
    ml = sekunden * FOERDERRATE_ML_S
    if ml > MAX_ML_PRO_DOSIS:
        ml = MAX_ML_PRO_DOSIS
        sekunden = ml / FOERDERRATE_ML_S

    ph_vor = sensor_data.get("ph")
    with pumpe_lock:
        pumpe.on()
        time.sleep(sekunden)
        pumpe.off()

    eintrag = {
        "zeit": time.time(),
        "sekunden": round(sekunden, 2),
        "ml": round(ml, 2),
        "ph_vor": ph_vor,
        "ausgewertet": False,
        "quelle": quelle,
    }
    dosen_liste.append(eintrag)
    log_dosierung(eintrag)
    return eintrag


@app.route("/api/pumpe/test")
def pumpe_test():
    """Vom Node-Server aufgerufen als GET /api/pumpe/test?sekunden=N.
    Antwortet laut Vorgabe erst NACH Ablauf der Dosierzeit (blockierend)."""
    try:
        sekunden = float(request.args.get("sekunden", 2))
    except (TypeError, ValueError):
        return jsonify({"fehler": "Parameter 'sekunden' ist keine Zahl"}), 400

    # ANNAHME 3: manuelle Tests zählen auf das Tageslimit, nicht auf
    # Stundenzahl/Sperrzeit der automatischen Regelung.
    if regelzustand["gesperrt"]:
        return jsonify({"fehler": "Dosierung gesperrt (Ausfallalarm, siehe Log)"}), 423
    if ml_in_letzten(86400) >= MAX_ML_PRO_TAG:
        return jsonify({"fehler": f"Tageslimit von {MAX_ML_PRO_TAG} ml erreicht"}), 423

    eintrag = _dosierung_ausfuehren(sekunden, quelle="manuell")
    sensor_data.update(status_snapshot())
    return jsonify({"status": "ok", **eintrag})


@app.route("/api/pumpe/stopp")
def pumpe_stopp():
    """Vom Node-Server aufgerufen als GET /api/pumpe/stopp (Not-Aus)."""
    with pumpe_lock:
        pumpe.off()
    return jsonify({"status": "ok", "pumpe": pumpe.is_active})


# Flask in eigenem Thread starten (blockiert nicht die Hauptschleife)
flask_thread = threading.Thread(
    target=lambda: app.run(host=API_HOST, port=API_PORT, use_reloader=False, threaded=True),
    daemon=True,
)
flask_thread.start()


# ============================
#   LOGGING
# ============================
def log_data(data: dict):
    """Schreibt eine Messzeile. Wird jetzt pro Einzelmessung (alle 10 s)
    aufgerufen statt einmal pro 5-Minuten-Fenster — Punkt p), erfüllt S-01
    (Intervall ≤ 30 s)."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def log_dosierung(eintrag: dict):
    """Eigenes Protokoll für Dosierzeitpunkt und -menge — Punkt r). Ohne diese
    Angaben lässt sich die Wirkung einer Dosierung nicht auswerten (Abschnitt
    5.3 / Sprungantwort in 4.5)."""
    file_exists = os.path.isfile(DOSIER_LOG_FILE)
    zeile = {
        "timestamp": datetime.fromtimestamp(eintrag["zeit"]).strftime("%Y-%m-%d %H:%M:%S"),
        "sekunden":  eintrag["sekunden"],
        "ml":        eintrag["ml"],
        "ph_vor":    eintrag["ph_vor"],
        "quelle":    eintrag["quelle"],
    }
    with open(DOSIER_LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=zeile.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(zeile)


# ============================
#   DS18B20 (Wassertemperatur)
# ============================
def read_water_temp():
    try:
        device_folder = [d for d in os.listdir(W1_DEVICE_PATH) if d.startswith("28-")][0]
        device_file   = f"{W1_DEVICE_PATH}{device_folder}/w1_slave"
        with open(device_file, "r") as f:
            lines = f.readlines()
        if "YES" not in lines[0]:
            return None
        return float(lines[1].split("t=")[-1]) / 1000.0
    except Exception:
        return None


# ============================
#   pH-MESSUNG — Punkte a), f), o)
# ============================
def read_ph(wasser_temp=None):
    """Liest den pH-Wert kalibriert (Abschnitt 4.4) mit Temperaturkompensation
    der Steilheit (Gleichung 3.2). Filterung wie bisher: 10 Einzelwerte
    sortiert, Mittelwert der mittleren 6 gegen Ausreißer.

    Gibt (ph, spannung_mv) zurück, oder (None, None) bei einem I2C-Fehler
    bzw. (None, spannung_mv) wenn der Wert außerhalb des Plausibilitäts-
    bereichs liegt (Punkt f) — die Hauptschleife läuft in beiden Fällen
    weiter, es wird nur diese eine Messung verworfen (R-07, S-02)."""
    try:
        buf = []
        for _ in range(10):
            buf.append(ph_chan.value)
            time.sleep(0.01)
    except OSError as e:
        print(f"pH-Sensor: I2C-Fehler beim Lesen ({e})")
        return None, None

    buf.sort()
    avg_value = sum(buf[2:8]) / 6
    spannung_mv = avg_value * 4.096 / ADC_MAX * 1000  # ADS1115, gain=1, Vollausschlag 4,096 V

    steilheit = STEILHEIT_KAL
    if wasser_temp is not None:
        steilheit = STEILHEIT_KAL * (273.15 + wasser_temp) / (273.15 + T_KAL)  # Gleichung 3.2

    ph = 7 + (U0_KAL - spannung_mv) / steilheit
    ph = round(ph, 2)
    spannung_mv = round(spannung_mv, 1)

    if not (PH_PLAUSIBEL_MIN <= ph <= PH_PLAUSIBEL_MAX):
        print(f"pH-Wert {ph} außerhalb des Plausibilitätsbereichs "
              f"({PH_PLAUSIBEL_MIN}–{PH_PLAUSIBEL_MAX}) — Messung verworfen")
        return None, spannung_mv

    return ph, spannung_mv


def berechne_pumpdauer(ph_wert: float) -> float:
    """Pumpdauer in Sekunden (PUMP_MIN_S..PUMP_MAX_S), abhängig vom Abstand
    zum Sollwert. Provisorisch (siehe Docstring g/j/m) — sobald die
    Streckenverstärkung K_S aus der Sprungantrede (Abschnitt 4.5) vorliegt,
    ersetzt die dokumentierte Formel V = (ph_ist - PH_SOLL) / K_S * 0,5
    diese lineare Interpolation."""
    abweichung = abs(ph_wert - PH_SOLL)
    anteil     = min(abweichung / PH_MAX_ABW, 1.0)
    return PUMP_MIN_S + anteil * (PUMP_MAX_S - PUMP_MIN_S)


def bewerte_letzte_dosierung(ph_mittel_aktuell: float):
    """Vergleicht den pH-Mittelwert des aktuellen Fensters mit dem Wert vor
    der letzten (noch nicht bewerteten) Dosierung — Ersatz für die bisherige,
    zu frühe 5-s-Kontrollmessung (Punkt n). Löst nach
    KEIN_EFFEKT_ALARM_NACH wirkungslosen Dosierungen in Folge eine Sperre
    aus (R-05/R-06-Absicherung)."""
    if not dosen_liste:
        return
    letzte = dosen_liste[-1]
    if letzte["ausgewertet"] or letzte["ph_vor"] is None:
        return

    wirkung = letzte["ph_vor"] - ph_mittel_aktuell
    letzte["ausgewertet"] = True

    if wirkung < KEIN_EFFEKT_SCHWELLE:
        regelzustand["wirkungslos_counter"] += 1
        print(f"Dosierung ohne erkennbare Wirkung ({wirkung:+.2f} pH), "
              f"Zähler: {regelzustand['wirkungslos_counter']}/{KEIN_EFFEKT_ALARM_NACH}")
    else:
        regelzustand["wirkungslos_counter"] = 0

    if regelzustand["wirkungslos_counter"] >= KEIN_EFFEKT_ALARM_NACH:
        regelzustand["gesperrt"] = True
        print("ALARM: Dosierung gesperrt — mehrere Dosierungen in Folge ohne "
              "erkennbare Wirkung. Manuelle Prüfung erforderlich "
              "(Neustart des Programms hebt die Sperre auf).")


def darf_automatisch_dosieren() -> bool:
    if regelzustand["gesperrt"]:
        return False
    letzte = dosen_liste[-1] if dosen_liste else None
    if letzte is not None and (time.time() - letzte["zeit"]) < SPERRZEIT_S:
        return False
    if len(dosen_in_letzten(3600)) >= MAX_DOSEN_PRO_STUNDE:
        return False
    if ml_in_letzten(86400) >= MAX_ML_PRO_TAG:
        return False
    return True


# ============================
#   SAUBERES BEENDEN
# ============================
def cleanup(sig, frame):
    print("\nSystem wird beendet – Aktoren werden ausgeschaltet...")
    with pumpe_lock:
        pumpe.off()
    dht.exit()
    sys.exit(0)


signal.signal(signal.SIGINT,  cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ============================
#   HAUPTSCHLEIFE
# ============================
print("Hydroponik-System gestartet...")
print(f"API läuft auf http://{API_HOST}:{API_PORT}\n")

while True:
    print("\n==============================")

    # --- Lufttemperatur & Luftfeuchte (DHT11) ---
    luft_temp    = None
    luft_feuchte = None
    try:
        luft_temp    = dht.temperature
        luft_feuchte = dht.humidity
        if luft_temp is not None and luft_feuchte is not None:
            print(f"Lufttemperatur:  {luft_temp:.1f} °C")
            print(f"Luftfeuchte:     {luft_feuchte:.1f} %")
        else:
            print("DHT11: keine Daten")
    except Exception as e:
        print(f"DHT11 Fehler: {e}")
        dht.exit()
        time.sleep(1)
        dht = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)

    # --- Bodenfeuchtesensor ---
    feucht = feuchte_sensor.value
    print("Feuchtigkeit: erkannt" if feucht else "Feuchtigkeit: trocken")

    # --- Wassertemperatur (DS18B20) ---
    w_temp = read_water_temp()
    if w_temp is not None:
        print(f"Wassertemperatur: {w_temp:.2f} °C")
    else:
        print("Wassertemperatur: Fehler beim Lesen")

    # --- pH-Messfenster: PH_MESSZYKLEN Einzelmessungen, jede sofort
    #     geloggt (Punkt p) und aktualisiert; Entscheidung anschließend
    #     auf dem Mittelwert (Punkt c) ---
    ph_werte = []
    for _ in range(PH_MESSZYKLEN):
        ph_wert, ph_spannung = read_ph(w_temp)
        if ph_wert is not None:
            ph_werte.append(ph_wert)
            print(f"pH-Wert: {ph_wert:.2f}  (U = {ph_spannung:.1f} mV)")
        else:
            print("pH-Wert: ungültig/verworfen")

        update_sensor_data(luft_temp, luft_feuchte, w_temp, ph_wert, ph_spannung, feucht)
        log_data(sensor_data)  # Punkt p): Log-Intervall jetzt PH_MESSPAUSE (10 s)
        time.sleep(PH_MESSPAUSE)

    if not ph_werte:
        print("Kein gültiger pH-Wert in diesem Messfenster — keine Regelentscheidung möglich.")
        time.sleep(2)
        continue

    ph_mittel = sum(ph_werte) / len(ph_werte)
    print(f"pH-Mittelwert des Fensters: {ph_mittel:.2f} (n={len(ph_werte)}/{PH_MESSZYKLEN})")

    # --- Wirkung der letzten Dosierung bewerten (ersetzt die alte 5-s-Kontrollmessung) ---
    bewerte_letzte_dosierung(ph_mittel)

    # --- pH-Regelung: Totband (Punkt k) + Sicherheitsgrenzen ---
    if ph_mittel > PH_SOLL + PH_TOLERANZ:
        if darf_automatisch_dosieren():
            sekunden = berechne_pumpdauer(ph_mittel)
            print(f"pH zu hoch (Mittel {ph_mittel:.2f}) → Pumpe EIN für {sekunden:.1f} s (pH-Minus)")
            eintrag = _dosierung_ausfuehren(sekunden, quelle="automatik")
            print(f"Dosierung: {eintrag['sekunden']} s ≈ {eintrag['ml']} ml")
        else:
            grund = "gesperrt (Ausfallalarm)" if regelzustand["gesperrt"] else \
                    "Sperrzeit/Stunden- oder Tageslimit noch aktiv"
            print(f"pH zu hoch, aber keine Dosierung: {grund}")

    time.sleep(2)

**Antwort (2026-09-18 07:14)**

Das ist die überarbeitete Fassung von ganzerCode.py. Ich prüfe sie gegen den Node-Server, das Dashboard und das Auswerteskript im Repo, damit klar ist, ob alles zusammenpasst.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 07:15)**

**Die neue Fassung passt strukturell zum Node-Server, aber drei Felder brechen das Dashboard, und der Not-Aus hat einen Konstruktionsfehler.** Im Einzelnen:

**Was jetzt stimmt und die Bewertung in Tabelle 5.2 trägt**

- S-01: jede Einzelmessung wird alle 10 s ins CSV geschrieben, dazu ein eigenes Dosierprotokoll.
- S-04: nur zeitbegrenzte Läufe, hart auf 10 s gekappt, kein Dauer-Ein mehr.
- S-03: Endpunkte /api/pumpe/test und /api/pumpe/stopp entsprechen dem, was server.js aufruft. Testlauf und Not-Aus des Dashboards erreichen den Pi jetzt.
- Netzanbindung 3.7.3: die API bindet nur noch auf 192.168.10.1, der Satz „von außen nicht erreichbar“ gilt damit.

**Was mit dem Dashboard nicht zusammenpasst**

1. **Sensorspannung in mV statt V.** Die gesamte Kette erwartet Volt: das Dashboard zeigt den Wert mit vier Nachkommastellen und der Einheit V, das Auswerteskript rechnet für die Kennlinie mit 1000 mal und prüft auf 50 bis 59 mV/pH, der Simulator liefert Volt. Mit dem committeten Server erscheint im Dashboard „1523.4000 V“, mit der uncommitteten Fassung ein „--“, weil sie auf 0 bis 5 V begrenzt. Fix im Pi-Skript: den Wert in read_ph durch 1000 teilen und auf vier Stellen runden.
2. **letzte_dosierung ist ein Objekt.** Das Dashboard setzt den Wert direkt als Text ein, ein Objekt erscheint als „[object Object]“. Das Repo-Skript sendet dort einen Zeitstempel-String. Fix: nur den Zeitstring senden, Sekunden und ml sind im Dosierprotokoll.
3. **Betriebsart „automatik“.** Kein Fehler, das Dashboard zeigt den String an. README und Anhang C.2 sagen aber „messbetrieb“ oder „regelung“. Einen der beiden Texte angleichen.

**Sicherheitsproblem im Not-Aus.** Der Stopp holt sich denselben Lock wie die laufende Dosierung. Während die Pumpe läuft, hält _dosierung_ausfuehren den Lock bis zum Ende des Laufs. Der Not-Aus wartet also, bis die Dosierung ohnehin fertig ist, und schaltet dann eine bereits ausgeschaltete Pumpe aus. Er ist damit wirkungslos, genau in dem Moment, für den er da ist. Das Repo-Skript umgeht den Lock im Stopp bewusst. Fix: in pumpe_stopp den Lock weglassen und direkt pumpe.off() rufen. Der laufende Dosiervorgang schaltet danach noch einmal aus, das ist unschädlich. Wer S-03 in der Arbeit mit dem Not-Aus begründet, muss das vorher beheben.

**Weitere Punkte**

- **Alte Logdatei vorher wegräumen.** Das CSV-Schreiben hängt Zeilen an eine bestehende Datei an, ohne die Kopfzeile zu prüfen. Liegt noch das 7-spaltige hydroponik_log.csv von ganzerCode.py im Ordner, entstehen 17-spaltige Zeilen unter einem 7-spaltigen Kopf. Vor dem ersten Start umbenennen.
- **Pumpe bleibt im Export unsichtbar.** Während des Laufs wird der Zustand nicht aktualisiert, der Node-Server sieht also weiterhin nie „pumpe: true“. Punkt q im Docstring behebt das nicht. Dosierungen sind nur über dosierungen_log.csv belegbar, das sollte in 5.3 stehen.
- **API-Bindung beim Start.** Ist 192.168.10.1 beim Start noch nicht auf eth0 gesetzt, stirbt nur der Flask-Thread, die Hauptschleife läuft ohne API weiter. Der Fehler ist dann nur in der Konsole sichtbar. Als Dienst braucht das ein After=network-online.target.
- **Uhrzeit.** Unverändert offen. Vor jeder Messreihe date prüfen, sonst gilt der Befund von 5.3 auch für neue Reihen.

**Versionsfrage für die Arbeit.** Es gibt jetzt drei Programme: ganzerCode.py (alle Messreihen bis 11.08.), das 601-Zeilen-hydroponik.py im Repo (nie an der Anlage gemessen) und diese neue Fassung (Pi, ab 17.09.). Das Repo enthält die Fassung nicht, die tatsächlich läuft. Ich würde die neue Fassung samt kalibrieren.py ins Repo übernehmen und das bisherige hydroponik.py ersetzen oder klar als verworfen kennzeichnen. Anhang B muss die Fassung enthalten, mit der die Ergebnisse in Kapitel 5 entstanden sind, und 4.3 muss zu ganzerCode.py passen.

Wenn du die beiden Dateien als Dateien im Repo haben willst, lege ich sie unter iot/ ab, baue die vier Fixes ein und committe das. Sag dazu kurz, ob das alte hydroponik.py ersetzt oder daneben behalten werden soll.

## Frage (2026-09-18 07:18)

Mach das was sinnvoll ist

**Antwort (2026-09-18 07:19)**

Ich übernehme die beiden Skripte ins Repo, baue die Fixes ein und passe README und Dienstdatei an. Zuerst schaue ich, was im Repo auf die alten Aufrufparameter verweist.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 07:19)**

Jetzt lege ich die Dateien an: Archiv für die beiden alten Fassungen, das neue Pi-Skript mit den Fixes, kalibrieren.py, und die Reparatur der CSV-Hilfsfunktionen.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 07:22)**

Der Heredoc ist an der Größe der Datei gescheitert. Ich schreibe die drei Dateien direkt mit dem Write-Werkzeug.

_[Werkzeugaufruf: Write]_

_[Werkzeugaufruf: Write]_

_[Werkzeugaufruf: Write]_

_[Werkzeugaufruf: Write]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 07:25)**

Jetzt passe ich die README an das neue Pi-Programm an. Ich schaue mir dafür den betroffenen Abschnitt 4 genau an.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 07:26)**

Der Python-Aufruf ist an den Backslashes in den Windows-Pfaden gescheitert, die README wurde noch nicht verändert. Ich wiederhole die Änderung mit Raw-Strings.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 07:27)**

README ist angepasst. Jetzt erzeuge ich DOCX und PDF neu und committe anschließend alles.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: PowerShell]_

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 07:28)**

**Erledigt und gepusht: Commit 786b86b auf main.** Das Repo enthält jetzt das Programm, das tatsächlich auf dem Pi läuft, mit den besprochenen Korrekturen.

Was ich gemacht habe:

- **iot/hydroponik.py ersetzt** durch deine Fassung vom 17.09. mit fünf Fixes: Sensorspannung in Volt, letzte Dosierung als Zeitstempel, Not-Aus ohne Lock, Kalibrier- und Logdateien liegen neben dem Skript, und die API versucht das Binden alle 5 s erneut, falls die Adresse beim Start fehlt. Dazu die Betriebsart --nur-messen, damit Dienstdatei und README wieder stimmen. Alte Logs mit fremder Kopfzeile werden beim Start umbenannt statt fortgeschrieben.
- **iot/kalibrieren.py** übernommen, fast unverändert. Nur zwei Stellen, die bei einer Temperatur von exakt 0 °C falsch abgezweigt hätten, sind auf None-Prüfungen umgestellt.
- **iot/archiv/** angelegt mit ganzerCode.py, dem 601-Zeilen-Entwurf vom August und einer README, die beide einordnet. Damit ist Anhang B belegbar.
- **CSV-Export repariert.** Zeitstempel, Wahrheitswerte und Nullwerte bleiben erhalten, vier Tests laufen mit `npm test` durch.
- **README, DOCX und PDF** neu mit Stand 18.09.2026: Beschreibung des Pi-Programms, Kalibrierablauf, Uhrzeitprüfung vor jeder Messreihe, Warnung vor Excel, sechs neue Zeilen in der Fehlersuche.

Was du auf dem Pi noch tun musst:

1. Die neuen Dateien kopieren, dann einmal kalibrieren, sonst startet das Messprogramm nicht:

```powershell
scp C:\Users\prati\hydroponic-system\iot\hydroponik.py C:\Users\prati\hydroponic-system\iot\kalibrieren.py pi@192.168.10.1:~/hydroponic-project/iot/
```

2. Auf dem Pi `date` prüfen, dann `python3 iot/kalibrieren.py`, dann `python3 iot/hydroponik.py --nur-messen`.

Ein Punkt bleibt bewusst offen: die Änderungen sind nur per Syntaxprüfung getestet, die Sensorbibliotheken gibt es auf dem Windows-Rechner nicht. Der erste Lauf auf dem Pi ist der eigentliche Test. Wenn dabei etwas im Terminal auffällt, schick mir die Ausgabe.

## Frage (2026-09-18 08:15)

Kannst du mir Test aus 17.09.2026 im Leyman's term erläutern? Auf englisch

**Antwort (2026-09-18 08:15)**

Ich schaue kurz, ob es vom 17.09. auch Messdaten gibt, damit die Erklärung nicht nur den Code, sondern auch das Ergebnis abdeckt.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 08:16)**

There are no measurement files from 17 September on this computer, so what follows explains the program you ran that day, not a result set.

**What the "test of 17.09.2026" is**

It was the first run of the rewritten control program on the Raspberry Pi. Until 11 August, the Pi ran the old program you inherited from the previous project. The new program keeps the same basic rhythm but fixes the things that made the old one unreliable. Think of it as the difference between a thermostat someone guessed the settings for, and one that has been properly calibrated and given safety limits.

**What the program does, step by step**

1. **It measures.** Every 10 seconds it reads the pH probe. It takes ten quick readings, throws away the two highest and two lowest, and averages the middle six. That removes electrical noise. It also reads the water temperature, the air temperature and humidity, and whether the float switch is wet.
2. **It converts voltage into pH using a real calibration.** A pH probe only produces a small voltage. The old program used a formula copied from the sensor maker, plus a fudge factor of 8.23 that someone had tuned by eye. The new program instead uses two numbers you measured yourself with buffer solutions of known pH, stored in a small file. That is what the second script, kalibrieren.py, produces. Without that file the program refuses to start, on purpose.
3. **It corrects for temperature.** A probe reacts slightly differently when the water is warmer or colder. The program adjusts for this automatically.
4. **It decides once every five minutes.** After 30 readings it averages them. If the average pH is above 6.0 (target 5.8 plus a tolerance of 0.2), it runs the pump for 2 to 5 seconds, longer when the pH is further off. Only pH-Minus liquid is available, so the program can only push the value down, never up.
5. **It has safety limits.** No pump run may exceed 10 seconds. It waits at least 10 minutes between two doses, allows at most 6 doses per hour and 150 ml per day. If three doses in a row show no effect, it locks itself and waits for a human. All of these numbers are placeholders to be confirmed by your experiments.
6. **It writes everything down.** Every single reading goes into a CSV log, every 10 seconds. Every dose goes into a second log with time, duration and amount.
7. **It talks to the web dashboard.** It offers a small web address on the Ethernet cable only. The dashboard reads the current values from it, and can trigger a short test run of the pump or an emergency stop.

**What the old program got wrong, in plain words**

- It measured with a formula that did not fit the hardware, so the displayed pH could be off by around half a unit.
- It only wrote one log line every five minutes, and only the last of 30 readings.
- Its pump command was a plain on/off switch with no time limit. If the network dropped while the pump was on, it would have kept pumping.
- Its dosing threshold and timing had nothing to do with the target of pH 5.8.

**What the 17 September run showed**

Since no data from that day is on this PC, I cannot say how the plant behaved. What the run proved is that the new program starts, reads the sensors, and speaks the new web interface. The corrections I added yesterday came from comparing that version with the dashboard code: voltage in the wrong unit, one field the dashboard could not display, and an emergency stop that would have waited for the dose to finish before acting.

**One caution for the write-up.** The measurement series in your thesis were all recorded with the old program. The new program has not yet produced a measurement series that is saved anywhere here. If the thesis is to show the new controller working, one recorded run with it is still missing.

## Frage (2026-09-18 14:07)

Bestimmt meine Kalibrierung K_s oder Regelstrecke? Ich frage weil: Das ist entscheidend, weil ohne Dünger die gemessene Pufferwirkung (und damit K_S) nicht der realen Nährlösung entspricht, sondern nur der von reinem Wasser — und die ist deutlich geringer. Der Versuch würde zwar technisch funktionieren, aber ein K_S liefern, das ihr später im echten Betrieb nicht verwenden könntet.

**Antwort (2026-09-18 14:07)**

Kurz nachgesehen, was deine Dokumentation zu K_S und Abschnitt 4.5 festlegt, damit ich deine Notation treffe.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 14:09)**

**Die Regelstrecke bestimmt K_S, nicht die Kalibrierung.** Das sind zwei getrennte Versuche mit zwei getrennten Größen, die beide „Verstärkung" oder „Steilheit" heißen und deshalb leicht verwechselt werden.

- **Kalibrierung** (Abschnitt 4.4, kalibrieren.py): bestimmt die *Messkette*. Steilheit in Millivolt je pH und Nullpunkt. Das ist eine Eigenschaft der Elektrode, nicht der Lösung. Sie gehört zwingend in die Pufferlösungen, denn nur dort ist der pH-Wert per Definition bekannt. In Nährlösung zu kalibrieren wäre sogar falsch, weil du den wahren Wert dort nicht kennst.
- **Streckenidentifikation** (Abschnitt 4.5): bestimmt, wie die *Lösung* auf eine Dosis reagiert. K_S in pH je Milliliter, dazu Totzeit und Ausgleichszeit. Das ist eine Eigenschaft der Flüssigkeit im Kreislauf.

Die Kalibrierung ist Voraussetzung, nicht Ersatz. Ohne richtige Steilheit der Messkette wäre die gemessene pH-Änderung um denselben Faktor verfälscht und K_S damit ebenfalls.

**Dein Einwand ist richtig, und deine eigene Arbeit sagt es bereits.** Abschnitt 3.8 nennt als zweite Streckeneigenschaft, dass die Verstärkung wegen der Pufferwirkung nicht konstant ist. Die Versuchsbeschreibung in 4.5 fordert deshalb mindestens drei verschiedene Ausgangswerte. Dieselbe Begründung schließt reines Wasser als Versuchsmedium aus. Ohne Dünger fehlen Phosphate und Carbonate, die Pufferwirkung ist klein, die pH-Änderung je Milliliter entsprechend groß.

**Die Fehlerrichtung ist die sichere, aber der Versuch wäre trotzdem wertlos.** Ein zu groß gemessenes K_S steht im Nenner der Dosierformel und führt zu einer zu kleinen Dosis:

```
gemessen in Wasser     K_S = 2,0 pH/ml   ->  V = 0,5 / 2,0 * 0,5 = 0,13 ml
real in Nährlösung     K_S = 0,2 pH/ml   ->  V = 0,5 / 0,2 * 0,5 = 1,25 ml
```

Die Anlage würde also rund zehnfach unterdosieren. Überschwingen droht nicht, aber der Regler wirkt scheinbar gar nicht. In deinem Code läuft das direkt in den Ausfallalarm: drei Dosierungen in Folge unter der Wirkungsschwelle sperren die Dosierung. Für R-04 und R-06 wären die Zahlen unbrauchbar.

**Was aus einem Wasserversuch trotzdem übertragbar wäre:** Totzeit und Ausgleichszeit. Die kommen aus Umlaufzeit, Durchmischung und Ansprechzeit der Elektrode und hängen kaum vom Dünger ab. Wenn du also aus Termingründen vorab etwas messen willst, nimm daraus nur die Zeitkennwerte für R-05 und bestimme K_S später neu.

**Für den eigentlichen Versuch** also Nährlösung in Betriebskonzentration, laufende Umwälzung, mindestens drei Ausgangswerte. Wichtig dabei: K_S hängt am Gesamtvolumen. Ein halb so großes Reservoir verdoppelt die pH-Änderung je Milliliter. Notiere die Dosis deshalb normiert in Milliliter je Liter, so wie es dein Titrationsformat in Abschnitt 5 schon vorsieht. Dann bleibt das Ergebnis übertragbar, auch wenn der Füllstand später ein anderer ist.

## Frage (2026-09-18 14:13)

Jetziger Code: Test Rauschen 17.09.26

"""
Sprungantwort der pH-Regelstrecke — Punkt j) / Abschnitt 4.5.

Eigenständiges Skript, getrennt von hydroponik.py (nicht gleichzeitig
ausführen — gemeinsamer Zugriff auf ADS1115 und die Pumpe an GPIO 5).
Läuft komplett lokal auf dem Pi, keine Netzwerk-/API-Aufrufe nötig.

Protokolliert den pH-Wert im 2-s-Takt (statt der 10 s aus hydroponik.py —
laut Abschnitt 4.5 für das Einschwingverhalten erforderlich), löst dann
eine definierte Dosierung aus und misst danach weiter. Am Ende wird eine
erste automatische Schätzung von T_u, T_g und K_S ausgegeben.

Verwendet dieselbe Kalibrierung (kalibrierung.json) wie hydroponik.py.
"""

import csv
import json
import os
import signal
import statistics
import sys
import time
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import DigitalOutputDevice

SKRIPT_VERZEICHNIS = os.path.dirname(os.path.abspath(__file__))
KALIBRIER_DATEI = os.path.join(SKRIPT_VERZEICHNIS, "kalibrierung.json")
LOG_DATEI = os.path.join(SKRIPT_VERZEICHNIS, "sprungantwort_log.csv")

PUMP_PIN = 5
ADC_MAX = 32767
MESSABSTAND_S = 2.0          # Abschnitt 4.5: 2-s-Auflösung gefordert
FOERDERRATE_ML_S = 1.7       # Abschnitt 5.2, Einzelmessung ohne Wiederholung

W1_DEVICE_PATH = "/sys/bus/w1/devices/"

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan = AnalogIn(ads, 0)
pumpe = DigitalOutputDevice(PUMP_PIN)


def lade_kalibrierung() -> dict:
    if not os.path.isfile(KALIBRIER_DATEI):
        raise RuntimeError(f"Keine Kalibrierung gefunden ({KALIBRIER_DATEI}).")
    with open(KALIBRIER_DATEI, "r") as f:
        daten = json.load(f)
    print(f"Kalibrierung geladen: U0={daten['u0_mv']} mV, "
          f"S={daten['steilheit_mv_pro_ph']} mV/pH, T_kal={daten['t_kal_c']} °C")
    return daten


kal = lade_kalibrierung()
U0_KAL = kal["u0_mv"]
STEILHEIT_KAL = kal["steilheit_mv_pro_ph"]
T_KAL = kal["t_kal_c"]


def read_water_temp():
    try:
        device_folder = [d for d in os.listdir(W1_DEVICE_PATH) if d.startswith("28-")][0]
        device_file = f"{W1_DEVICE_PATH}{device_folder}/w1_slave"
        with open(device_file, "r") as f:
            lines = f.readlines()
        if "YES" not in lines[0]:
            return None
        return float(lines[1].split("t=")[-1]) / 1000.0
    except Exception:
        return None


def read_ph(wasser_temp=None):
    """Wie in hydroponik.py: 10 Werte, sortiert, Mittelwert der mittleren 6,
    kalibrierte Umrechnung mit Temperaturkompensation."""
    buf = []
    for _ in range(10):
        buf.append(ph_chan.value)
        time.sleep(0.01)
    buf.sort()
    avg_value = sum(buf[2:8]) / 6
    spannung_mv = avg_value * 4.096 / ADC_MAX * 1000

    steilheit = STEILHEIT_KAL
    if wasser_temp is not None:
        steilheit = STEILHEIT_KAL * (273.15 + wasser_temp) / (273.15 + T_KAL)

    ph = 7 + (U0_KAL - spannung_mv) / steilheit
    return round(ph, 3), round(spannung_mv, 1)


def cleanup(sig=None, frame=None):
    pumpe.off()
    print("\nPumpe sicher ausgeschaltet. Beendet.")
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

start_gesamt = [None]


def messen_und_loggen(writer, f, dauer_s, phase, dosierung_info=None):
    """Misst für dauer_s Sekunden im 2-s-Takt, gibt Liste von (t, ph) zurück."""
    ergebnisse = []
    start = time.time()
    while time.time() - start < dauer_s:
        zyklus_start = time.time()
        w_temp = read_water_temp()
        ph, spannung = read_ph(w_temp)
        t = time.time() - start_gesamt[0]

        zeile = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "t_s": round(t, 1),
            "phase": phase,
            "ph": ph,
            "spannung_mv": spannung,
            "wasser_temp": w_temp,
            "dosierung": dosierung_info or "",
        }
        writer.writerow(zeile)
        f.flush()
        ergebnisse.append((t, ph))
        print(f"t={t:7.1f} s  [{phase:10s}]  pH={ph:.3f}"
              + (f"   ({dosierung_info})" if dosierung_info else ""))

        rest = MESSABSTAND_S - (time.time() - zyklus_start)
        if rest > 0:
            time.sleep(rest)
    return ergebnisse


def dosieren(sekunden: float):
    print(f"\n>>> Dosierung: Pumpe EIN für {sekunden:.1f} s "
          f"(≈ {sekunden * FOERDERRATE_ML_S:.1f} ml) <<<\n")
    try:
        pumpe.on()
        time.sleep(sekunden)
    finally:
        pumpe.off()


def schaetze_kennwerte(baseline, verlauf, dosierte_ml):
    """Grobe automatische Schätzung von T_u, T_g, K_S nach der
    Zwei-Punkt-Methode (Abschnitt 2.5.2). Dient als erster Anhaltspunkt,
    ersetzt keine sorgfältige manuelle Auswertung."""
    ph_start = statistics.mean(p for _, p in baseline[-6:])  # letzte ~12 s vor Dosierung
    letzte_werte = verlauf[-6:]
    ph_ende = statistics.mean(p for _, p in letzte_werte)

    delta = ph_start - ph_ende
    if delta <= 0:
        print("\nWARNUNG: Kein abfallender Verlauf erkennbar — Auswertung übersprungen.")
        return

    vorherige = verlauf[-12:-6] if len(verlauf) >= 12 else verlauf[:6]
    ph_ende_vorher = statistics.mean(p for _, p in vorherige) if vorherige else ph_ende
    if abs(ph_ende - ph_ende_vorher) > 0.03:
        print(f"\nHINWEIS: Der Verlauf war am Ende der Messzeit noch nicht "
              f"eingeschwungen (Änderung über die letzten 12 s: "
              f"{ph_ende - ph_ende_vorher:+.3f} pH). Beobachtungszeit ggf. "
              f"verlängern und Skript mit längerer Nachlaufzeit wiederholen.")

    ziel_28 = ph_start - 0.28 * delta
    ziel_63 = ph_start - 0.63 * delta
    t28 = next((t for t, p in verlauf if p <= ziel_28), None)
    t63 = next((t for t, p in verlauf if p <= ziel_63), None)

    print("\n=== Automatische Schätzung (Zwei-Punkt-Methode) ===")
    print(f"pH vor Dosierung:  {ph_start:.3f}")
    print(f"pH am Ende:        {ph_ende:.3f}")
    print(f"Gesamthub Δ pH:    {delta:.3f}")

    if t28 is None or t63 is None:
        print("t28 und/oder t63 wurden innerhalb der Messzeit nicht erreicht — "
              "Beobachtungszeit verlängern und wiederholen.")
        return

    T = 1.5 * (t63 - t28)
    Tu = t63 - T
    Ks = delta / dosierte_ml if dosierte_ml else None

    print(f"t28 = {t28:.1f} s, t63 = {t63:.1f} s")
    print(f"T  (Ausgleichszeit) ≈ {T:.1f} s ({T/60:.1f} min)")
    print(f"Tu (Verzugszeit)    ≈ {Tu:.1f} s ({Tu/60:.1f} min)")
    if Ks is not None:
        print(f"Ks (Streckenverstärkung) ≈ {Ks:.4f} pH/ml")
    print("\nDiese Werte sind eine erste Orientierung. Für Abschnitt 4.5 bitte "
          "den Verlauf zusätzlich in sprungantwort_log.csv per Auge prüfen "
          "(Ausreißer, Rauschen um t28/t63) und den Versuch bei mindestens "
          "zwei weiteren Ausgangswerten wiederholen.")


def main():
    start_gesamt[0] = time.time()

    print("=== Sprungantwort-Versuch ===\n")

    entlueften = input("Schlauch vorher entlüften/anspülen? (j/n): ").strip().lower()
    if entlueften == "j":
        sekunden = float(input("  Wie viele Sekunden anspülen (z. B. 3)? "))
        print("  Anspülen ...")
        dosieren(sekunden)
        input("  Fertig. Bitte kurz warten, bis Tropfen abgeschlossen sind, "
              "dann Enter drücken, um mit dem eigentlichen Versuch zu beginnen.")

    baseline_dauer = float(input("\nBaseline-Dauer in Sekunden vor der Dosierung "
                                  "(Vorschlag 120): ") or 120)
    dosis_s = float(input("Dosierdauer für den Testimpuls in Sekunden "
                           "(max. 10, Vorschlag 10): ") or 10)
    dosis_s = min(dosis_s, 10.0)
    beobachtung_min = float(input("Beobachtungszeit NACH der Dosierung in Minuten "
                                   "(Vorschlag 30): ") or 30)

    datei_existiert = os.path.isfile(LOG_DATEI)
    f = open(LOG_DATEI, "a", newline="")
    writer = csv.DictWriter(f, fieldnames=[
        "timestamp", "t_s", "phase", "ph", "spannung_mv", "wasser_temp", "dosierung"
    ])
    if not datei_existiert:
        writer.writeheader()

    print(f"\n--- Baseline ({baseline_dauer:.0f} s) ---")
    baseline = messen_und_loggen(writer, f, baseline_dauer, "baseline")

    dosierte_ml = round(dosis_s * FOERDERRATE_ML_S, 2)
    dosis_info = f"{dosis_s:.1f}s / {dosierte_ml:.1f}ml"
    dosieren(dosis_s)

    print(f"\n--- Beobachtung ({beobachtung_min:.0f} min) ---")
    verlauf = messen_und_loggen(writer, f, beobachtung_min * 60, "nach_dosis",
                                 dosierung_info=dosis_info)

    f.close()
    print(f"\nProtokoll gespeichert in {LOG_DATEI}.")

    schaetze_kennwerte(baseline, verlauf, dosierte_ml)


if __name__ == "__main__":
    main() Kalibrierungscode: Test 17.09.2026

"""
Kalibrierung der pH-Messkette — eigenständiges Skript, getrennt von
hydroponik.py, damit eine neue Kalibrierung (z. B. nach dem Wässern der
Elektrode, Punkt t) den Regelungscode nicht verändert.

Verfahren (Abschnitt 4.4.1 der Dokumentation):
  - Zweipunktkalibrierung mit den Puffern pH 4,01 und 7,00 -> Steilheit
    und Nullpunkt (Gleichung 4.5/4.6). Der Sollwert 5,8 liegt zwischen
    diesen beiden Stützstellen, es wird also interpoliert, nicht
    extrapoliert.
  - Puffer pH 10,01 dient NUR der Verifikation (Gleichung 4.7), fließt
    nicht in Steilheit/Nullpunkt ein — oberhalb von pH 7 verfälscht der
    Alkalifehler der Glaselektrode sonst die Steilheitsberechnung.

Neu gegenüber der bisherigen Kalibrierung: Die Temperatur wird mit dem
DS18B20 direkt in der jeweiligen Pufferlösung gemessen (Sensor beim
Kalibrieren mit in den Becher halten), statt pauschal Raumtemperatur
anzunehmen (bisherige Einschränkung, siehe Abschnitt 4.4).

Ergebnis wird nach kalibrierung.json geschrieben und von hydroponik.py
beim Start eingelesen.
"""

import json
import os
import statistics
import threading
import time
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

SKRIPT_VERZEICHNIS = os.path.dirname(os.path.abspath(__file__))

W1_DEVICE_PATH   = "/sys/bus/w1/devices/"
KALIBRIER_DATEI  = os.path.join(SKRIPT_VERZEICHNIS, "kalibrierung.json")
ADC_MAX          = 32767   # Vollausschlag ADS1115 bei gain=1 -> 4,096 V
S_THEOR_25C      = 59.16   # mV/pH, Nernst-Steilheit bei 25 °C (Gleichung 2.3)
M06_GRENZE_PROZENT = 85.0  # Brauchbarkeitsgrenze aus M-06

# Messabstand während des Einpendelns. Es wird nicht mehr automatisch anhand
# einer Schwankungsbreite gestoppt, sondern erst, wenn per Enter bestätigt
# wird, dass der angezeigte Wert stabil aussieht.
MESSABSTAND_S = 15

i2c     = busio.I2C(board.SCL, board.SDA)
ads     = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan = AnalogIn(ads, 0)


def read_water_temp():
    """Identisch zu hydroponik.py — hier bewusst dupliziert, damit dieses
    Skript unabhängig läuft und nicht versehentlich die Hauptschleife von
    hydroponik.py mit importiert."""
    try:
        device_folder = [d for d in os.listdir(W1_DEVICE_PATH) if d.startswith("28-")][0]
        device_file   = f"{W1_DEVICE_PATH}{device_folder}/w1_slave"
        with open(device_file, "r") as f:
            lines = f.readlines()
        if "YES" not in lines[0]:
            return None
        return float(lines[1].split("t=")[-1]) / 1000.0
    except Exception:
        return None


def einzelmessung_mv() -> float:
    """Eine gefilterte Spannungsmessung: 10 Rohwerte, sortiert, Mittelwert
    der mittleren 6 — dieselbe Filterung wie in read_ph() (hydroponik.py)."""
    buf = []
    for _ in range(10):
        buf.append(ph_chan.value)
        time.sleep(0.01)
    buf.sort()
    avg_value = sum(buf[2:8]) / 6
    return avg_value * 4.096 / ADC_MAX * 1000


def messe_puffer(bezeichnung: str) -> tuple[float, float]:
    """Fragt den Puffer ab und misst fortlaufend alle MESSABSTAND_S Sekunden.
    Jede Zwischenmessung wird mit Zeitstempel, Spannung, Temperatur und
    Differenz zur vorherigen Messung ausgegeben, damit das Einpendeln am
    Bildschirm sichtbar ist. Es wird so lange weitergemessen, bis die
    Bedienperson per Enter bestätigt, dass der zuletzt angezeigte Wert
    stabil ist — es gibt keinen automatischen Abbruch nach einer festen
    Anzahl Messungen. Gibt (spannung_mv, temperatur_c) der zuletzt vor der
    Bestätigung angezeigten Messung zurück."""
    input(f"\nElektrode UND Temperatursensor in Puffer {bezeichnung} geben, "
          f"dann Enter drücken, um mit der Messung zu beginnen ...")

    bestaetigt = threading.Event()

    def warte_auf_enter():
        input("  (Enter drücken, sobald der Wert stabil aussieht — die "
              "Messung läuft bis dahin weiter)\n")
        bestaetigt.set()

    threading.Thread(target=warte_auf_enter, daemon=True).start()

    letzte_spannung = None
    letzte_temperatur = None
    vorherige_spannung = None
    start = time.time()

    while True:
        u = einzelmessung_mv()
        t = read_water_temp()

        vergangen = time.time() - start
        zeile = f"  t={vergangen:5.0f} s   U={u:8.1f} mV"
        if t is not None:
            zeile += f"   T={t:5.1f} °C"
        if vorherige_spannung is not None:
            zeile += f"   Δ zur letzten Messung: {u - vorherige_spannung:+.1f} mV"
        print(zeile)

        letzte_spannung, letzte_temperatur = u, t
        vorherige_spannung = u

        # Bis zu MESSABSTAND_S Sekunden auf die Bestätigung warten; kommt sie
        # in dieser Zeit, sofort mit der zuletzt gedruckten Messung abbrechen.
        if bestaetigt.wait(timeout=MESSABSTAND_S):
            print(f"  -> übernommen: {letzte_spannung:.1f} mV"
                  + (f", {letzte_temperatur:.1f} °C" if letzte_temperatur is not None else ""))
            return letzte_spannung, letzte_temperatur


def nernst_steilheit_theorie(temperatur_c: float) -> float:
    """Theoretische Steilheit bei gegebener Temperatur, aus dem bekannten
    Wert 59,16 mV/pH bei 25 °C nach Gleichung 2.3 (Steilheit prop. zu T)."""
    return S_THEOR_25C * (273.15 + temperatur_c) / (273.15 + 25.0)


def main():
    print("=== Kalibrierung der pH-Messkette (2-Punkt: pH 4,01 / 7,00) ===")

    u_ph4, t_ph4 = messe_puffer("pH 4,01")
    u_ph7, t_ph7 = messe_puffer("pH 7,00")

    steilheit = (u_ph4 - u_ph7) / (7.00 - 4.01)   # Gleichung 4.5
    u0        = u_ph7                              # Gleichung 4.6, Nullpunkt bei pH 7,00

    if t_ph4 is not None and t_ph7 is not None:
        t_kal = statistics.mean([t_ph4, t_ph7])
    else:
        t_kal = t_ph4 or t_ph7
        print("WARNUNG: Temperatur nur an einem Puffer verfügbar — "
              "Prüfe den DS18B20-Anschluss.")

    if t_kal is None:
        print("FEHLER: Keine Temperaturmessung möglich. Ohne Kalibriertemperatur "
              "kann die Temperaturkompensation (Gleichung 3.2) nicht arbeiten.")
        t_kal = float(input("Ersatzweise Temperatur manuell eingeben (°C): "))

    steilheit_theorie = nernst_steilheit_theorie(t_kal)
    steilheit_prozent = abs(steilheit) / steilheit_theorie * 100

    print(f"\nSteilheit S  = {steilheit:.1f} mV/pH  "
          f"({steilheit_prozent:.1f} % der theoretischen Steilheit bei {t_kal:.1f} °C)")
    print(f"Nullpunkt U0 = {u0:.1f} mV (bei pH 7,00)")

    if steilheit_prozent < M06_GRENZE_PROZENT:
        print(f"ACHTUNG: {steilheit_prozent:.1f} % liegt unter der Brauchbarkeitsgrenze "
              f"von {M06_GRENZE_PROZENT:.0f} % (M-06). Elektrode wässern (Punkt t) "
              f"und erneut kalibrieren, bevor der Regelbetrieb gestartet wird.")

    # --- Verifikation mit pH 10,01 (fließt NICHT in Steilheit/Nullpunkt ein) ---
    u_ph10, t_ph10 = messe_puffer("pH 10,01 (nur Verifikation)")
    steilheit_bei_t10 = steilheit * (273.15 + t_ph10) / (273.15 + t_kal) if t_ph10 else steilheit
    ph_berechnet_10 = 7 + (u0 - u_ph10) / steilheit_bei_t10
    abweichung_10 = ph_berechnet_10 - 10.01
    print(f"\nVerifikation pH 10,01: berechnet {ph_berechnet_10:.2f} "
          f"(Abweichung {abweichung_10:+.2f} pH — Alkalifehler, siehe Abschnitt 4.4.3)")

    ergebnis = {
        "u0_mv": round(u0, 1),
        "steilheit_mv_pro_ph": round(steilheit, 2),
        "t_kal_c": round(t_kal, 1),
        "steilheit_prozent_theorie": round(steilheit_prozent, 1),
        "zeitstempel": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rohdaten": {
            "ph4_mv": round(u_ph4, 1), "ph4_temp_c": round(t_ph4, 1) if t_ph4 else None,
            "ph7_mv": round(u_ph7, 1), "ph7_temp_c": round(t_ph7, 1) if t_ph7 else None,
            "ph10_mv": round(u_ph10, 1), "ph10_temp_c": round(t_ph10, 1) if t_ph10 else None,
        },
        "verifikation_ph10": {
            "berechnet": round(ph_berechnet_10, 2),
            "abweichung": round(abweichung_10, 2),
        },
    }

    with open(KALIBRIER_DATEI, "w") as f:
        json.dump(ergebnis, f, indent=2, ensure_ascii=False)

    print(f"\nGespeichert in {KALIBRIER_DATEI}. hydroponik.py verwendet diese Datei "
          f"automatisch beim nächsten Start.")


if __name__ == "__main__":
    main()

"""
Hydroponik pH-Regelung — überarbeitete Fassung.

Gegenüber der Vorversion umgesetzt (Bezeichner wie in der Projektdokumentation,
Kapitel 3/4):

  a) Kalibrierte Umrechnung (Abschnitt 4.4) statt Herstellerformel + K=8,23;
     Werte werden aus kalibrierung.json geladen (siehe kalibrieren.py),
     damit eine neue Kalibrierung dieses Skript nicht verändert
  c) Regelentscheidung auf Mittelwert der Messfenster-Werte statt Einzelwert
  e) Zeitbegrenzte, mit dem Node-Server kompatible Pumpen-Endpunkte
     (/api/pumpe/test, /api/pumpe/stopp); alter /api/pump/<action> entfernt
  f) Plausibilitätsprüfung (3,0–9,5 pH) und try/except um die ADC-Abfrage,
     damit ein I2C-Fehler nicht das ganze Programm beendet (R-07, S-02)
  h) Flask bindet nur noch auf die Ethernet-Adresse des Einplatinenrechners
  k) Totband ±0,2 pH (PH_TOLERANZ) statt scharfer Schwelle
  n) Kontrollmessung nach 5 s entfällt; die Wirkung wird stattdessen zu
     Beginn des nächsten Messfensters bewertet (~5 min später statt 5 s,
     oberhalb der Elektroden-Ansprechzeit von <2 min)
  o) Temperaturkompensation der Steilheit (Gleichung 3.2)
  p) Log-Intervall ≤ 30 s (jetzt: jede Einzelmessung, alle 10 s)
  q) Pumpenzustand wird vor dem Logging korrekt erfasst
  r) Dosierzeitpunkt und -menge werden protokolliert (dosierungen_log.csv)

  Zusätzlich ergänzt, weil vom Dashboard bereits erwartet (siehe server.js):
  Dosierzähler pro Stunde/Tag, Sperrzeit-Anzeige, Ausfallalarm nach
  wirkungslosen Dosierungen (R-05, R-06, aus [stated] Sicherheitsgrenzen).

Bewusst NICHT umgesetzt, weil sie Messungen statt Codeänderungen brauchen:
  b) Ursache des Messrauschens (Abschnitt 5.1)
  g/j/m) Sperrzeit und Dosiermenge aus Sprungantwort (Abschnitt 4.5) —
         SPERRZEIT_S unten ist ein Platzhalter
  s) Wägeversuch mit Wiederholungen — FOERDERRATE_ML_S ist eine grobe,
     einfach gemessene Schätzung, keine belastbare Kennlinie
  u) Regelgüte im Dauerbetrieb

=== ANNAHMEN, die noch zu bestätigen sind (Zeilen mit "ANNAHME:") ===
  1) SPERRZEIT_S = 600 s (10 min) als Platzhalter bis Abschnitt 4.5 vorliegt.
  2) KEIN_EFFEKT_SCHWELLE = 0.1 pH als Schwelle für "wirkungslose" Dosierung —
     liegt unterhalb des bekannten Messrauschens (0,16–0,31 pH) und ist damit
     selbst noch unsicher; siehe Abschnitt 5.1.
  3) Manuelle Testdosierungen über /api/pumpe/test zählen auf dasselbe
     Tageslimit (MAX_ML_PRO_TAG) wie automatische Dosierungen, aber NICHT auf
     die stündliche Dosenzahl und die Sperrzeit der Regelung.
  4) max_dosierungen_tag im API-Feld ist aus der Stundengrenze abgeleitet
     (MAX_DOSEN_PRO_STUNDE * 24) und keine eigenständig festgelegte Zahl.
"""

import time
import os
import json
import csv
import signal
import sys
import threading
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
from gpiozero import DigitalInputDevice, DigitalOutputDevice
from flask import Flask, jsonify, request
from flask_cors import CORS

# ============================
#   PIN-ZUWEISUNGEN
# ============================
DHT_PIN        = board.D17
FEUCHTE_PIN    = 27
PUMP_PIN       = 5
W1_DEVICE_PATH = "/sys/bus/w1/devices/"
LOG_FILE       = "hydroponik_log.csv"
DOSIER_LOG_FILE = "dosierungen_log.csv"

# Auf welcher Adresse der Einplatinenrechner die API bereitstellt (Punkt h).
# 192.168.10.1 = feste Ethernet-Adresse zum Anzeigerechner (Abschnitt 3.7.2).
# WICHTIG: Der Node-Server muss PI_API_BASE_URL=http://192.168.10.1:5000
# gesetzt haben, sonst ist der Pi über das bisherige WLAN nicht mehr erreichbar.
API_HOST = "192.168.10.1"
API_PORT = 5000

# ============================
#   SENSOR & AKTOR SETUP
# ============================
dht            = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
feuchte_sensor = DigitalInputDevice(FEUCHTE_PIN, pull_up=False)
pumpe          = DigitalOutputDevice(PUMP_PIN)
pumpe_lock     = threading.Lock()  # schützt gegen gleichzeitigen Zugriff
                                    # von Hauptschleife und Flask-Thread

# ============================
#   ADS1115 (pH-Sensor)
# ============================
i2c      = busio.I2C(board.SCL, board.SDA)
ads      = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan  = AnalogIn(ads, 0)
ADC_MAX  = 32767      # Vollausschlag ADS1115 bei gain=1 -> 4,096 V

# ============================
#   KALIBRIERUNG (Abschnitt 4.4) — Punkt a)
# ============================
# Werte kommen aus kalibrierung.json (siehe kalibrieren.py), nicht mehr fest
# im Code. So löst eine neue Kalibrierung (z. B. nach dem Wässern der
# Elektrode, Punkt t) nie eine Änderung an diesem Skript aus.
KALIBRIER_DATEI = "kalibrierung.json"


def lade_kalibrierung() -> dict:
    if not os.path.isfile(KALIBRIER_DATEI):
        raise RuntimeError(
            f"Keine Kalibrierung gefunden ({KALIBRIER_DATEI}). "
            f"Bitte zuerst kalibrieren.py ausführen."
        )
    with open(KALIBRIER_DATEI, "r") as f:
        daten = json.load(f)
    for feld in ("u0_mv", "steilheit_mv_pro_ph", "t_kal_c"):
        if feld not in daten:
            raise RuntimeError(f"{KALIBRIER_DATEI} ist unvollständig (Feld '{feld}' fehlt).")
    print(f"Kalibrierung geladen (vom {daten.get('zeitstempel', 'unbekannt')}): "
          f"U0={daten['u0_mv']} mV, S={daten['steilheit_mv_pro_ph']} mV/pH, "
          f"T_kal={daten['t_kal_c']} °C, "
          f"{daten.get('steilheit_prozent_theorie', '?')}% der theor. Steilheit")
    return daten


_kalibrierung = lade_kalibrierung()
U0_KAL        = _kalibrierung["u0_mv"]
STEILHEIT_KAL = _kalibrierung["steilheit_mv_pro_ph"]
T_KAL         = _kalibrierung["t_kal_c"]

# ============================
#   pH-REGELUNG
# ============================
PH_SOLL       = 5.8     # realer Zielwert, R-01 (vorher: Anzeige 6,0 unkalibriert)
PH_TOLERANZ   = 0.2     # Totband, R-02 — Punkt k). Dosiert wird nur, wenn
                         # ph_mittel > PH_SOLL + PH_TOLERANZ (einseitig, da nur
                         # pH-Minus verfügbar ist)
PH_PLAUSIBEL_MIN = 3.0  # Punkt f)
PH_PLAUSIBEL_MAX = 9.5
PH_MAX_ABW    = 2.0     # ab dieser Abweichung wird maximal lange gepumpt
PH_MESSZYKLEN = 30      # pH-Messungen pro Durchlauf der Hauptschleife
PH_MESSPAUSE  = 10      # Sekunden zwischen zwei pH-Messungen
PUMP_MIN_S    = 2       # kürzeste Pumpdauer (provisorisch, siehe Docstring g/j/m)
PUMP_MAX_S    = 5       # längste Pumpdauer (provisorisch)

# ============================
#   SICHERHEITSGRENZEN (bereits festgelegte Werte übernommen)
# ============================
PUMPE_MAX_EIN_S     = 10    # harte Obergrenze je Einschaltvorgang (S-04);
                             # Name bewusst wie im Kommentar von server.js
FOERDERRATE_ML_S    = 1.7   # ml/s, aus Einzelmessung (Abschnitt 5.2, Punkt s offen)
MAX_ML_PRO_DOSIS    = 20    # R-04
MAX_DOSEN_PRO_STUNDE = 6    # R-05 (Ersatz, bis Sperrzeit aus 4.5 feststeht)
MAX_ML_PRO_TAG      = 150   # R-06
SPERRZEIT_S         = 600   # ANNAHME 1: Platzhalter für R-05, siehe Docstring
KEIN_EFFEKT_SCHWELLE = 0.1  # ANNAHME 2: siehe Docstring
KEIN_EFFEKT_ALARM_NACH = 3  # Anzahl wirkungsloser Dosierungen in Folge

# ============================
#   GLOBALER ZUSTAND
# ============================
sensor_data = {
    "luft_temp":    None,
    "luft_feuchte": None,
    "wasser_temp":  None,
    "ph":           None,
    "ph_spannung":  None,
    "feuchtigkeit": None,
    "pumpe":        False,
    "betriebsart":  "automatik",
    "sollwert_ph":  PH_SOLL,
    "toleranz_ph":  PH_TOLERANZ,
    "dosierungen_gesamt":   0,
    "dosierungen_24h":      0,
    "max_dosierungen_tag":  MAX_DOSEN_PRO_STUNDE * 24,  # ANNAHME 4
    "dosierung_gesperrt":   False,
    "sperrzeit_rest_s":     0.0,
    "letzte_dosierung":     None,
    "timestamp":    None
}

# Dosierhistorie im Speicher: [{"zeit": float(epoch), "sekunden": float,
#   "ml": float, "ph_vor": float, "ausgewertet": bool, "quelle": str}, ...]
dosen_liste = []
regelzustand = {
    "gesperrt": False,
    "wirkungslos_counter": 0,
}


def dosen_in_letzten(sekunden: float) -> list:
    grenze = time.time() - sekunden
    return [d for d in dosen_liste if d["zeit"] >= grenze]


def ml_in_letzten(sekunden: float) -> float:
    return sum(d["ml"] for d in dosen_in_letzten(sekunden))


def status_snapshot() -> dict:
    """Berechnet die Zähler-/Sperrzeit-Felder für /api/sensors neu."""
    jetzt = time.time()
    letzte = dosen_liste[-1] if dosen_liste else None
    sperrzeit_rest = 0.0
    if letzte is not None:
        sperrzeit_rest = max(0.0, SPERRZEIT_S - (jetzt - letzte["zeit"]))
    return {
        "dosierungen_gesamt":  len(dosen_liste),
        "dosierungen_24h":     len(dosen_in_letzten(86400)),
        "dosierung_gesperrt":  regelzustand["gesperrt"],
        "sperrzeit_rest_s":    round(sperrzeit_rest, 1),
        "letzte_dosierung": (
            {
                "zeit": datetime.fromtimestamp(letzte["zeit"]).strftime("%Y-%m-%d %H:%M:%S"),
                "sekunden": letzte["sekunden"],
                "ml": round(letzte["ml"], 2),
            }
            if letzte is not None else None
        ),
    }


def update_sensor_data(luft_temp, luft_feuchte, w_temp, ph, ph_spannung, feucht):
    """Globalen Zustand an einer einzigen Stelle aktualisieren (Punkt q):
    pumpe.is_active wird HIER gelesen, also im selben Moment wie der Rest —
    nicht erst nach einem späteren pumpe.off()."""
    sensor_data.update({
        "luft_temp":    luft_temp,
        "luft_feuchte": luft_feuchte,
        "wasser_temp":  w_temp,
        "ph":           ph,
        "ph_spannung":  ph_spannung,
        "feuchtigkeit": feucht,
        "pumpe":        pumpe.is_active,
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    sensor_data.update(status_snapshot())


# ============================
#   FLASK API
# ============================
app = Flask(__name__)
CORS(app)


@app.route("/api/sensors")
def get_sensors():
    return jsonify(sensor_data)


def _dosierung_ausfuehren(sekunden: float, quelle: str) -> dict:
    """Führt eine zeitbegrenzte Dosierung aus (Punkt e) und protokolliert sie
    (Punkt r). Wird sowohl von der Regelung als auch von /api/pumpe/test
    genutzt, damit es nur eine Stelle gibt, die tatsächlich pumpe.on() ruft."""
    sekunden = min(max(sekunden, 0.0), PUMPE_MAX_EIN_S)
    ml = sekunden * FOERDERRATE_ML_S
    if ml > MAX_ML_PRO_DOSIS:
        ml = MAX_ML_PRO_DOSIS
        sekunden = ml / FOERDERRATE_ML_S

    ph_vor = sensor_data.get("ph")
    with pumpe_lock:
        pumpe.on()
        time.sleep(sekunden)
        pumpe.off()

    eintrag = {
        "zeit": time.time(),
        "sekunden": round(sekunden, 2),
        "ml": round(ml, 2),
        "ph_vor": ph_vor,
        "ausgewertet": False,
        "quelle": quelle,
    }
    dosen_liste.append(eintrag)
    log_dosierung(eintrag)
    return eintrag


@app.route("/api/pumpe/test")
def pumpe_test():
    """Vom Node-Server aufgerufen als GET /api/pumpe/test?sekunden=N.
    Antwortet laut Vorgabe erst NACH Ablauf der Dosierzeit (blockierend)."""
    try:
        sekunden = float(request.args.get("sekunden", 2))
    except (TypeError, ValueError):
        return jsonify({"fehler": "Parameter 'sekunden' ist keine Zahl"}), 400

    # ANNAHME 3: manuelle Tests zählen auf das Tageslimit, nicht auf
    # Stundenzahl/Sperrzeit der automatischen Regelung.
    if regelzustand["gesperrt"]:
        return jsonify({"fehler": "Dosierung gesperrt (Ausfallalarm, siehe Log)"}), 423
    if ml_in_letzten(86400) >= MAX_ML_PRO_TAG:
        return jsonify({"fehler": f"Tageslimit von {MAX_ML_PRO_TAG} ml erreicht"}), 423

    eintrag = _dosierung_ausfuehren(sekunden, quelle="manuell")
    sensor_data.update(status_snapshot())
    return jsonify({"status": "ok", **eintrag})


@app.route("/api/pumpe/stopp")
def pumpe_stopp():
    """Vom Node-Server aufgerufen als GET /api/pumpe/stopp (Not-Aus)."""
    with pumpe_lock:
        pumpe.off()
    return jsonify({"status": "ok", "pumpe": pumpe.is_active})


# Flask in eigenem Thread starten (blockiert nicht die Hauptschleife)
flask_thread = threading.Thread(
    target=lambda: app.run(host=API_HOST, port=API_PORT, use_reloader=False, threaded=True),
    daemon=True,
)
flask_thread.start()


# ============================
#   LOGGING
# ============================
def log_data(data: dict):
    """Schreibt eine Messzeile. Wird jetzt pro Einzelmessung (alle 10 s)
    aufgerufen statt einmal pro 5-Minuten-Fenster — Punkt p), erfüllt S-01
    (Intervall ≤ 30 s)."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def log_dosierung(eintrag: dict):
    """Eigenes Protokoll für Dosierzeitpunkt und -menge — Punkt r). Ohne diese
    Angaben lässt sich die Wirkung einer Dosierung nicht auswerten (Abschnitt
    5.3 / Sprungantwort in 4.5)."""
    file_exists = os.path.isfile(DOSIER_LOG_FILE)
    zeile = {
        "timestamp": datetime.fromtimestamp(eintrag["zeit"]).strftime("%Y-%m-%d %H:%M:%S"),
        "sekunden":  eintrag["sekunden"],
        "ml":        eintrag["ml"],
        "ph_vor":    eintrag["ph_vor"],
        "quelle":    eintrag["quelle"],
    }
    with open(DOSIER_LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=zeile.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(zeile)


# ============================
#   DS18B20 (Wassertemperatur)
# ============================
def read_water_temp():
    try:
        device_folder = [d for d in os.listdir(W1_DEVICE_PATH) if d.startswith("28-")][0]
        device_file   = f"{W1_DEVICE_PATH}{device_folder}/w1_slave"
        with open(device_file, "r") as f:
            lines = f.readlines()
        if "YES" not in lines[0]:
            return None
        return float(lines[1].split("t=")[-1]) / 1000.0
    except Exception:
        return None


# ============================
#   pH-MESSUNG — Punkte a), f), o)
# ============================
def read_ph(wasser_temp=None):
    """Liest den pH-Wert kalibriert (Abschnitt 4.4) mit Temperaturkompensation
    der Steilheit (Gleichung 3.2). Filterung wie bisher: 10 Einzelwerte
    sortiert, Mittelwert der mittleren 6 gegen Ausreißer.

    Gibt (ph, spannung_mv) zurück, oder (None, None) bei einem I2C-Fehler
    bzw. (None, spannung_mv) wenn der Wert außerhalb des Plausibilitäts-
    bereichs liegt (Punkt f) — die Hauptschleife läuft in beiden Fällen
    weiter, es wird nur diese eine Messung verworfen (R-07, S-02)."""
    try:
        buf = []
        for _ in range(10):
            buf.append(ph_chan.value)
            time.sleep(0.01)
    except OSError as e:
        print(f"pH-Sensor: I2C-Fehler beim Lesen ({e})")
        return None, None

    buf.sort()
    avg_value = sum(buf[2:8]) / 6
    spannung_mv = avg_value * 4.096 / ADC_MAX * 1000  # ADS1115, gain=1, Vollausschlag 4,096 V

    steilheit = STEILHEIT_KAL
    if wasser_temp is not None:
        steilheit = STEILHEIT_KAL * (273.15 + wasser_temp) / (273.15 + T_KAL)  # Gleichung 3.2

    ph = 7 + (U0_KAL - spannung_mv) / steilheit
    ph = round(ph, 2)
    spannung_mv = round(spannung_mv, 1)

    if not (PH_PLAUSIBEL_MIN <= ph <= PH_PLAUSIBEL_MAX):
        print(f"pH-Wert {ph} außerhalb des Plausibilitätsbereichs "
              f"({PH_PLAUSIBEL_MIN}–{PH_PLAUSIBEL_MAX}) — Messung verworfen")
        return None, spannung_mv

    return ph, spannung_mv


def berechne_pumpdauer(ph_wert: float) -> float:
    """Pumpdauer in Sekunden (PUMP_MIN_S..PUMP_MAX_S), abhängig vom Abstand
    zum Sollwert. Provisorisch (siehe Docstring g/j/m) — sobald die
    Streckenverstärkung K_S aus der Sprungantrede (Abschnitt 4.5) vorliegt,
    ersetzt die dokumentierte Formel V = (ph_ist - PH_SOLL) / K_S * 0,5
    diese lineare Interpolation."""
    abweichung = abs(ph_wert - PH_SOLL)
    anteil     = min(abweichung / PH_MAX_ABW, 1.0)
    return PUMP_MIN_S + anteil * (PUMP_MAX_S - PUMP_MIN_S)


def bewerte_letzte_dosierung(ph_mittel_aktuell: float):
    """Vergleicht den pH-Mittelwert des aktuellen Fensters mit dem Wert vor
    der letzten (noch nicht bewerteten) Dosierung — Ersatz für die bisherige,
    zu frühe 5-s-Kontrollmessung (Punkt n). Löst nach
    KEIN_EFFEKT_ALARM_NACH wirkungslosen Dosierungen in Folge eine Sperre
    aus (R-05/R-06-Absicherung)."""
    if not dosen_liste:
        return
    letzte = dosen_liste[-1]
    if letzte["ausgewertet"] or letzte["ph_vor"] is None:
        return

    wirkung = letzte["ph_vor"] - ph_mittel_aktuell
    letzte["ausgewertet"] = True

    if wirkung < KEIN_EFFEKT_SCHWELLE:
        regelzustand["wirkungslos_counter"] += 1
        print(f"Dosierung ohne erkennbare Wirkung ({wirkung:+.2f} pH), "
              f"Zähler: {regelzustand['wirkungslos_counter']}/{KEIN_EFFEKT_ALARM_NACH}")
    else:
        regelzustand["wirkungslos_counter"] = 0

    if regelzustand["wirkungslos_counter"] >= KEIN_EFFEKT_ALARM_NACH:
        regelzustand["gesperrt"] = True
        print("ALARM: Dosierung gesperrt — mehrere Dosierungen in Folge ohne "
              "erkennbare Wirkung. Manuelle Prüfung erforderlich "
              "(Neustart des Programms hebt die Sperre auf).")


def darf_automatisch_dosieren() -> bool:
    if regelzustand["gesperrt"]:
        return False
    letzte = dosen_liste[-1] if dosen_liste else None
    if letzte is not None and (time.time() - letzte["zeit"]) < SPERRZEIT_S:
        return False
    if len(dosen_in_letzten(3600)) >= MAX_DOSEN_PRO_STUNDE:
        return False
    if ml_in_letzten(86400) >= MAX_ML_PRO_TAG:
        return False
    return True


# ============================
#   SAUBERES BEENDEN
# ============================
def cleanup(sig, frame):
    print("\nSystem wird beendet – Aktoren werden ausgeschaltet...")
    with pumpe_lock:
        pumpe.off()
    dht.exit()
    sys.exit(0)


signal.signal(signal.SIGINT,  cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ============================
#   HAUPTSCHLEIFE
# ============================
print("Hydroponik-System gestartet...")
print(f"API läuft auf http://{API_HOST}:{API_PORT}\n")

while True:
    print("\n==============================")

    # --- Lufttemperatur & Luftfeuchte (DHT11) ---
    luft_temp    = None
    luft_feuchte = None
    try:
        luft_temp    = dht.temperature
        luft_feuchte = dht.humidity
        if luft_temp is not None and luft_feuchte is not None:
            print(f"Lufttemperatur:  {luft_temp:.1f} °C")
            print(f"Luftfeuchte:     {luft_feuchte:.1f} %")
        else:
            print("DHT11: keine Daten")
    except Exception as e:
        print(f"DHT11 Fehler: {e}")
        dht.exit()
        time.sleep(1)
        dht = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)

    # --- Bodenfeuchtesensor ---
    feucht = feuchte_sensor.value
    print("Feuchtigkeit: erkannt" if feucht else "Feuchtigkeit: trocken")

    # --- Wassertemperatur (DS18B20) ---
    w_temp = read_water_temp()
    if w_temp is not None:
        print(f"Wassertemperatur: {w_temp:.2f} °C")
    else:
        print("Wassertemperatur: Fehler beim Lesen")

    # --- pH-Messfenster: PH_MESSZYKLEN Einzelmessungen, jede sofort
    #     geloggt (Punkt p) und aktualisiert; Entscheidung anschließend
    #     auf dem Mittelwert (Punkt c) ---
    ph_werte = []
    for _ in range(PH_MESSZYKLEN):
        ph_wert, ph_spannung = read_ph(w_temp)
        if ph_wert is not None:
            ph_werte.append(ph_wert)
            print(f"pH-Wert: {ph_wert:.2f}  (U = {ph_spannung:.1f} mV)")
        else:
            print("pH-Wert: ungültig/verworfen")

        update_sensor_data(luft_temp, luft_feuchte, w_temp, ph_wert, ph_spannung, feucht)
        log_data(sensor_data)  # Punkt p): Log-Intervall jetzt PH_MESSPAUSE (10 s)
        time.sleep(PH_MESSPAUSE)

    if not ph_werte:
        print("Kein gültiger pH-Wert in diesem Messfenster — keine Regelentscheidung möglich.")
        time.sleep(2)
        continue

    ph_mittel = sum(ph_werte) / len(ph_werte)
    print(f"pH-Mittelwert des Fensters: {ph_mittel:.2f} (n={len(ph_werte)}/{PH_MESSZYKLEN})")

    # --- Wirkung der letzten Dosierung bewerten (ersetzt die alte 5-s-Kontrollmessung) ---
    bewerte_letzte_dosierung(ph_mittel)

    # --- pH-Regelung: Totband (Punkt k) + Sicherheitsgrenzen ---
    if ph_mittel > PH_SOLL + PH_TOLERANZ:
        if darf_automatisch_dosieren():
            sekunden = berechne_pumpdauer(ph_mittel)
            print(f"pH zu hoch (Mittel {ph_mittel:.2f}) → Pumpe EIN für {sekunden:.1f} s (pH-Minus)")
            eintrag = _dosierung_ausfuehren(sekunden, quelle="automatik")
            print(f"Dosierung: {eintrag['sekunden']} s ≈ {eintrag['ml']} ml")
        else:
            grund = "gesperrt (Ausfallalarm)" if regelzustand["gesperrt"] else \
                    "Sperrzeit/Stunden- oder Tageslimit noch aktiv"
            print(f"pH zu hoch, aber keine Dosierung: {grund}")

    time.sleep(2) . Wie sollte dieses K_s einbezogen werden
, wenn ich mein NPK reinmischen würde? Wie sollte mein Programmcode ändern? Wie höre/lausche ich dazu bei meiner Webanwendunbg?

**Antwort (2026-09-18 14:15)**

Kurz den Repo-Stand geprüft, damit ich auf die richtige Fassung verweise.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 14:17)**

Drei Antworten, aber zuerst der Punkt, der über alles andere entscheidet: **das Skript berechnet die Verzugszeit falsch, und bei eurem Rauschen trifft es t28 und t63 zu früh.** Wenn ihr so misst, ist K_S zwar brauchbar, T_u und damit die Sperrzeit nach R-05 aber nicht.

- **Verzugszeit ist um die gesamte Vorlaufzeit verschoben.** Die Zeitachse zählt ab Skriptstart, nicht ab Dosierende. In der Auswertung ist `T = 1.5*(t63-t28)` als Differenz korrekt, `Tu = t63 - T` dagegen enthält Baseline, Anspülen und deine Tippzeit an den Eingabeaufforderungen. Bei 120 s Baseline kommt T_u also um mehr als zwei Minuten zu groß heraus, und weil die Tippzeit mitläuft, ist der Fehler nicht einmal konstant. Merke dir die Zeit am Ende von `dosieren()` und rechne alles relativ dazu.
- **Die Schwellensuche nimmt den ersten Treffer.** Bei einem Hub von etwa einer halben pH-Einheit liegt die 28-Prozent-Marke bei 0,14 pH, also mitten im Rauschen von 0,16 bis 0,31 pH. Ein einzelner Ausreißer nach unten setzt t28 sofort. Vor der Suche über fünf bis zehn Werte gleitend mitteln.
- **Der Startwert stützt sich auf zwölf Sekunden.** Nimm die letzten 60 s der Baseline, nicht die letzten sechs Messwerte.
- **Prüfe nach dem ersten Lauf, ob der Hub überhaupt auswertbar ist.** Zehn Sekunden Pumpe sind rund 17 ml. In gepufferter Nährlösung kann das eine Änderung unterhalb des Rauschens erzeugen. Der Hub sollte das Rauschen um mindestens das Dreifache übersteigen, sonst braucht ihr eine größere Dosis.

## 1  K_S in der Nährlösung

**K_S kommt aus der Sprungantwort, gemessen in der fertig angesetzten Lösung mit NPK in Betriebskonzentration und laufender Umwälzung.** Der Dünger ist der Puffer, vor allem über die Phosphate. Genau deshalb ist der Wert aus Wasser nicht übertragbar, wie du selbst festgestellt hast.

Drei Dinge musst du dabei mitführen:

- **K_S hängt vom Ausgangswert ab.** Das ist die Nichtlinearität, die deine Arbeit in Abschnitt 3.8 als zweite Streckeneigenschaft nennt und die der Versuchsplan in 4.5 mit mindestens drei Ausgangswerten abdeckt. Notiere alle Messpunkte, nimm als Auslegungswert aber den größten K_S im Arbeitsbereich.
- **Die sichere Richtung ist der größte Wert.** K_S steht im Nenner der Dosierformel. Ein zu groß angesetztes K_S liefert eine zu kleine Dosis, also langsame Annäherung ohne Überschwingen. Ein zu klein angesetztes K_S überdosiert, und das ist mit reiner pH-Minus-Lösung nicht rückgängig zu machen. Prüfe dazu den vorletzten Satz in Abschnitt 3.8 deiner Arbeit, er beschreibt die Richtungen meiner Rechnung nach vertauscht.
- **K_S hängt am Füllvolumen.** Halbes Volumen bedeutet doppelte pH-Änderung je Milliliter. Schreibe das Volumen mit in die Ergebnisdatei und rechne bei anderem Füllstand um:

```
K_S(V) = K_S(V0) · V0 / V
```

Nach jeder Änderung der Düngerkonzentration und nach größerem Nachfüllen gilt der alte Wert nicht mehr.

## 2  Änderungen am Programmcode

Der saubere Weg ist derselbe, den du bei der Kalibrierung schon gewählt hast: eine eigene Datei neben dem Skript, damit ein wiederholter Versuch den Regelungscode nicht anfasst. Also `strecke.json` mit K_S, Volumen, T_u, T_g, den Einzelmesspunkten und einem Zeitstempel, geschrieben vom Sprungantwort-Skript und gelesen beim Start.

Damit ändern sich vier Stellen in [hydroponik.py](iot/hydroponik.py):

- **Dosiermenge statt linearer Interpolation.** Die Formel aus dem Docstring wird echt:

```python
V_ml = (ph_ist - PH_SOLL) / K_S * SICHERHEITSFAKTOR
V_ml = min(V_ml, MAX_ML_PRO_DOSIS)
t_s  = min(V_ml / FOERDERRATE_ML_S, PUMPE_MAX_EIN_S)
```

- **Kleine Dosen nicht aufrunden.** Liegt die berechnete Zeit unter der kürzesten sinnvollen Pumpzeit, darf nicht auf zwei Sekunden hochgesetzt werden. Das wäre eine Überdosierung durch Rundung. In dem Fall lieber gar nicht dosieren und den nächsten Zyklus abwarten, das Totband deckt den Bereich ohnehin ab.
- **Sperrzeit aus der Messung.** R-05 verlangt mindestens Totzeit plus das Dreifache der Ausgleichszeit. Damit entfällt der Platzhalter von 600 Sekunden.
- **Wirkungsschwelle aus dem erwarteten Effekt.** Erwartet wird eine Änderung von `V_ml · K_S`. Ein Bruchteil davon ist die sinnvolle Schwelle, nach unten begrenzt durch das Rauschen.

An der Stelle steckt noch ein zweiter Fehler in der Fassung, die du eingefügt hast. Der Vergleichswert `ph_vor` ist ein einzelner Messwert aus dem Zustandsdictionary, verglichen wird er aber mit dem Mittel aus dreißig Messungen. Das Rauschen des Einzelwerts schlägt voll durch und kann den Ausfallalarm auslösen, obwohl die Dosierung gewirkt hat. Nimm als `ph_vor` den Fenstermittelwert vor der Dosierung. Dasselbe gilt für den Wert, der im Dosierprotokoll landet und später in die Auswertung eingeht.

Ein Hinweis zur Fassung: du hast oben den Stand vom 17.09. eingefügt. Im Repo liegt die korrigierte Fassung mit Spannung in Volt, entsperrtem Not-Aus und Betriebsart. Kopiere die auf den Pi, nicht die eingefügte.

## 3  Mitlesen in der Weboberfläche

Im Moment gar nicht, und das ist kein Einstellungsproblem. Das Sprungantwort-Skript stellt keine Schnittstelle bereit, und es darf nicht gleichzeitig mit dem Messprogramm laufen, weil beide denselben Analog-Digital-Umsetzer und denselben Pumpenausgang benutzen. Während des Versuchs zeigt das Dashboard also nichts Aktuelles.

Der günstigste Weg führt über den Push-Endpunkt, den der Node-Server schon hat. Er nimmt einen Zustand per POST entgegen und verteilt ihn sofort an alle Browser, ohne dass am Server etwas geändert werden muss. Ergänze in `messen_und_loggen` nach dem Schreiben der CSV-Zeile:

```python
import requests
try:
    requests.post("http://192.168.10.2:3000/api/sensors", timeout=1, json={
        "ph": ph,
        "ph_spannung": round(spannung / 1000.0, 4),   # Volt, nicht Millivolt
        "wasser_temp": w_temp,
        "pumpe": False,
        "betriebsart": "sprungantwort",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
except Exception:
    pass                      # Anzeige darf den Versuch nie aufhalten
```

Vier Dinge dazu:

- **Die Spannung muss in Volt gehen.** Der Server verwirft Werte über fünf, in Millivolt bliebe die Anzeige leer.
- **Starte den Node-Server ohne die Pi-Adresse**, also schlicht mit `npm start`. Dann fragt er nichts ab und überschreibt deine gesendeten Werte nicht.
- **Das Diagramm zeigt nur die letzten 120 Punkte**, im Zwei-Sekunden-Takt also vier Minuten. Für die Live-Beobachtung reicht das, für das Bild in Abschnitt 4.5 nicht. Nimm dafür die CSV und das Auswerteskript, oder erhöhe die Punktzahl im Dashboard.
- **Der Pumpenlauf wird nicht sichtbar**, weil während der Dosierung nichts gesendet wird. Wenn du den Moment im Diagramm brauchst, sende einmal vor und nach dem Lauf einen Zustand mit gesetztem Pumpenflag.

Wenn du willst, baue ich das ein: Sprungantwort-Skript ins Repo mit korrigierter Zeitachse und Glättung, `strecke.json` als Schnittstelle, und die vier Änderungen in der Regelung mit Rückfall auf das bisherige Verhalten, solange die Datei noch fehlt.

## Frage (2026-09-18 14:39)

So we have in our uh, NPK dose. Uh, various uh, uh, lifespan uh, do doses for example first root first true leaves growing pre-flowering flowering ripening cleaning so what should we use for to uh, dose our uh, solution

**Antwort (2026-09-18 14:40)**

Let me check what crop and nutrient details your documentation already commits to, so the recommendation fits it.

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 14:41)**

Your documentation answers most of this already, and it narrows the question a lot: the crop is basil and parsley, and the circulating volume is 18.4 litres.

**Use the vegetative dose, the one your chart calls "growing".** Basil and parsley are leaf crops. You harvest foliage and you want to prevent bolting, because a basil plant that flowers produces bitter leaves. The pre-flowering, flowering and ripening columns of your fertilizer chart are written for fruiting crops such as tomatoes or peppers. For your system they never apply in normal operation. So the realistic sequence is the first two stages while the seedlings establish, then the growing dose for the entire rest of the culture.

For basil and parsley in a recirculating system the usual target conductivity is roughly 1.0 to 1.6 millisiemens per centimetre, at a pH of 5.5 to 6.5. Your setpoint of 5.8 sits well inside that. You have no conductivity meter, which your own outlook section already lists as the obvious next extension, so in practice you follow the dilution printed on the bottle and record it. At 18.4 litres, a chart that says two millilitres per litre means 37 millilitres into the reservoir.

**For the project, that single operating point is what you identify and tune for.** Mix the growing-stage solution at full strength, let it circulate, and run the step response in that. Record alongside K_S the fertilizer, the dilution, the fill volume and the date, because K_S is only valid for that state. Your Grenzen der Methodik section already says this in so many words: the buffering changes with the standing time of the solution and when you top up with tap water, so the measured values describe one condition and not the whole culture period. Keep that sentence, it is exactly right, and it is what lets you defend identifying at one point.

**One clarification, because it is easy to misread.** The requirement in section 4.5 to repeat the experiment at a minimum of three different starting values means three different starting pH values within the same nutrient solution. It does not mean three different growth stages. The point is to capture the curvature of the buffering, not to characterise the whole fertilizer chart.

**The flush stage is where this becomes a safety question.** During cleaning you run plain water, which has a fraction of the buffering of the nutrient solution. The same dose then moves the pH several times as far. An illustrative case with a controller tuned for nutrient solution:

```
tuned for      K_S = 0,15 pH/ml   ->  dose for a 0,5 pH error ≈ 1,7 ml
actual flush   K_S = 1,5 pH/ml    ->  actual effect ≈ 2,5 pH
```

A drop from 6,0 to 3,5 would pass your plausibility check, which only rejects below 3,0, and it is not reversible because you only carry pH-Minus. Two things follow. Run the flush in measurement mode only, never with automatic dosing. And add the mirror image of the alarm you already have: your code locks dosing after three doses that did too little, but nothing reacts when a dose does far too much. Compare the measured effect against the expected `V_ml · K_S` and lock the dosing if it exceeds it by more than roughly a factor of two. That guard protects the one direction you cannot undo, and it also catches the case where somebody refilled the reservoir without telling the controller.

If you want, I can add that overshoot lock and the K_S file loader to the control script now, with the existing behaviour kept as fallback until the step response gives you real numbers.

## Frage (2026-09-18 14:51)

How do I calculate this: V_ml · K_S ?

**Antwort (2026-09-18 14:51)**

It is a multiplication, and the units are what make it read correctly:

```
V_ml   [ml]        dosed volume
K_S    [pH/ml]     process gain from the step response
V_ml · K_S = [ml · pH/ml] = [pH]    expected drop in pH
```

So the product is simply the pH change that dose should produce. A worked example, with a gain that is illustrative because you have not measured yours yet:

```
pump time        3,0 s
delivery rate    1,7 ml/s        ->  V_ml = 3,0 · 1,7   = 5,1 ml
gain             0,15 pH/ml      ->  expected = 5,1 · 0,15 = 0,77 pH
```

Both inputs already exist in your code. The volume is computed in the dosing function as pump seconds times the delivery rate, and it is written into the dosing log. The gain comes out of the step response script as the total pH drop divided by the millilitres dosed.

**One correction you need on top: the gain depends on the fill level.** You measure it at 18.4 litres. In a smaller volume the same millilitre moves the pH further. Store the gain normalised by volume, the same way your titration file already normalises millilitres per litre, and divide by the current volume when you use it:

```
K_S_spez = K_S · V_ref = 0,15 · 18,4 = 2,76 pH·l/ml
at 15 l:  K_S = 2,76 / 15 = 0,184 pH/ml
same 5,1 ml dose -> expected = 0,94 pH
```

**A useful shortcut, and its limit.** When the controller computes the dose itself with the formula from your docstring, the expected effect collapses to half the control deviation, because the gain cancels:

```
V = e / K_S · 0,5     ->     V · K_S = 0,5 · e
```

That holds only as long as nothing clamps the dose. As soon as the maximum millilitres per dose or the ten second pump limit cuts in, or when somebody triggers a manual test run from the dashboard where there is no deviation to refer to, the shortcut is wrong. So compute it as volume times gain in all cases. That form is correct either way.

**In the alarm, use it on both sides.** Your current threshold of a tenth of a pH unit is a fixed number that sits below your measurement noise, which the docstring admits. Replace it with a fraction of the expected effect, and add the missing upper bound:

```python
erwartet = ml * (K_S_SPEZ / volumen_l)
wirkung  = ph_vor_mittel - ph_mittel_aktuell

if erwartet < 3 * RAUSCHEN_PH:
    return                      # Dosis zu klein, nicht auswertbar
if wirkung > 2.0 * erwartet:
    sperren("Überdosierung: Wirkung deutlich über Erwartung")
if wirkung < 0.3 * erwartet:
    wirkungslos_counter += 1
```

The first check matters more than it looks. If the expected drop is smaller than your noise, neither branch can be decided, and evaluating anyway would produce alarms out of pure scatter.

## Frage (2026-09-18 15:02)

What is e?

**Antwort (2026-09-18 15:02)**

`e` is the control deviation, the amount by which the measured pH sits above your setpoint.

```
e = ph_mittel - PH_SOLL
```

In your main loop `ph_mittel` is the average of the 30 readings in the window, and `PH_SOLL` is 5.8. Dosing only starts once that difference exceeds the dead band of 0.2, so `e` is never smaller than that when a dose is actually triggered.

Worked through with the same illustrative gain:

```
measured window mean   6,30
setpoint               5,80
e                      0,50 pH

V = e / K_S · 0,5 = 0,50 / 0,15 · 0,5 = 1,67 ml
expected effect   = 1,67 · 0,15        = 0,25 pH   (= 0,5 · e)
```

That last line is the shortcut from before: half the deviation, with the gain cancelling out.

One thing to pin down before you write it up. Control textbooks define the deviation as setpoint minus actual value, so their `e` would be negative here. Your dosing formula uses the opposite order, because it needs a positive volume when the pH is too high. Both are fine, but state which convention you use where you introduce the formula, otherwise the sign looks wrong to a reader who checks it against your section on control loop terminology. The cleanest fix is to call it the excess above the setpoint and write it out as `ph_ist - PH_SOLL` rather than using the bare letter.

## Frage (2026-09-18 15:23)

k_s ergibt sich aus der Sprungangtwort nach gabe von ph- oder npk oder weiterem ph- nach npk durchmischung?

**Antwort (2026-09-18 15:24)**

**Die dritte Variante ist richtig: pH-Minus, gegeben in die fertig gemischte Nährlösung mit NPK.**

Der Grund steckt in der Definition. K_S ist die Änderung der Regelgröße je Änderung der Stellgröße, und deine Stellgröße ist ausschließlich die Menge pH-Minus aus der Dosierpumpe. Der Dünger ist keine Stellgröße, sondern Teil der Strecke. Er legt fest, wie stark die Lösung puffert, und damit den Zustand, in dem du misst. Ein Sprung mit NPK würde etwas ganz anderes bestimmen, nämlich wie stark der Dünger selbst den pH-Wert verschiebt. Das ist für die Auslegung des Reglers ohne Nutzen, weil die Regelung nie Dünger dosiert.

Die Reihenfolge am Versuchstag:

1. **NPK in der Wachstumsdosierung einmischen**, bei 18,4 Litern also die Literangabe des Herstellers mal 18,4.
2. **Umwälzen lassen, bis die Lösung homogen und der pH-Wert stabil ist.** Frisch angesetzter Dünger löst sich weiter und tauscht Kohlendioxid mit der Luft aus. Rechne mit einer halben Stunde, eher mehr, und prüfe an der Anzeige, dass der Wert nicht mehr wandert.
3. **Falls nötig von Hand grob auf den oberen Rand des Arbeitsbereichs bringen**, etwa 6,5. Diese erste Korrektur ist nicht der Versuch, sondern die Vorbereitung.
4. **Erst dann Baseline, eine definierte Dosis pH-Minus, beobachten.**

**Der wichtigste Prüfpunkt vor der Dosierung ist eine flache Baseline.** Wenn der pH-Wert schon von allein driftet, weil sich der Dünger noch löst, zählst du diese Drift als Wirkung der Dosis und K_S kommt zu groß heraus. Zwei Minuten Baseline reichen dafür nicht. Nimm zehn bis fünfzehn Minuten und sieh dir an, ob die Linie liegt.

**Für die drei geforderten Ausgangswerte brauchst du keine drei Ansätze.** Du kannst sie in derselben Lösung hintereinander messen, weil jede Dosis dich auf einen neuen Ausgangswert bringt:

```
Start 6,5  ->  Dosis  ->  einschwingen lassen  ->  Punkt 1
dann 6,2   ->  Dosis  ->  einschwingen lassen  ->  Punkt 2
dann 6,0   ->  Dosis  ->  einschwingen lassen  ->  Punkt 3
```

Warte zwischen den Dosen mindestens so lange, wie der erste Versuch als Ausgleichszeit ergeben hat, sonst überlagern sich die Antworten. Plane die Schritte so, dass du den Arbeitsbereich um 5,8 abdeckst und nicht darunter landest, denn zurück nach oben kommst du nur mit frischer Lösung.

**Ein kostenloser Gegencheck:** Wenn du die Menge notierst, die du in Schritt 3 von Hand brauchst, und den pH-Wert davor und danach, hast du daraus eine mittlere Streckenverstärkung über diesen Bereich. Die ersetzt die Sprungantwort nicht, weil sie keine Zeitkennwerte liefert, aber sie sagt dir noch vor dem eigentlichen Versuch, ob deine geplante Dosis überhaupt eine messbare Änderung erzeugt.

## Frage (2026-09-18 15:29)

Ich habe heute morgen PH- reingetan und die kalibierung durchgeführt. AnfangsPHWert war 8,2 und ist nach Stabilisierung auf 7,6 runtergekommen. Muss ich nochmal PH- reintun und auf 6,5 runterziehen?

**Antwort (2026-09-18 15:29)**

**Das hängt davon ab, ob der Dünger schon drin ist. Wenn nicht: jetzt kein weiteres pH-Minus.**

Ein Wert von 8,2 ist typisch für reines Leitungswasser mit Hydrogencarbonat. Eine fertig angesetzte Nährlösung liegt meist von allein bei 5,5 bis 6,5, weil die Düngerkomponenten sauer sind. Dein Ausgangswert spricht also dafür, dass noch kein NPK im Reservoir ist.

Die Reihenfolge ist in der Hydroponik immer dieselbe: erst Dünger, dann pH. Der Grund ist genau das, worüber wir gestern gesprochen haben. Der Dünger verschiebt den pH-Wert selbst, und er verändert die Pufferwirkung vollständig. Wenn du das Wasser jetzt mühsam auf 6,5 ziehst und danach NPK einmischst, springt der Wert wieder weg und du stellst ein zweites Mal ein. Die Säure dafür ist verschenkt, und schlimmer: der eingestellte Zustand hat mit dem späteren Betriebszustand nichts zu tun.

Ist der Dünger dagegen schon eingemischt, dann ja. Dann ist 6,5 genau der richtige Startpunkt, von dem aus du die Sprungantwort nach unten durch den Arbeitsbereich fährst.

**Wenn du herunterziehst, dann in kleinen Schritten und mit Protokoll.** Von 7,6 auf 6,5 sind 1,1 Einheiten, deutlich mehr als der Schritt von heute Morgen. Nimm die Menge, die du für 8,2 auf 7,6 gebraucht hast, als Maßstab und dosiere in Teilmengen davon. Zwischen den Schritten umwälzen lassen und warten, bis der Wert wirklich steht. Unter 5,8 kommst du ohne frischen Ansatz nicht mehr zurück.

Der Aufwand lohnt doppelt, wenn du jeden Schritt notierst:

```
zugegebene Menge kumuliert [ml] -> auf 18,4 l normiert [ml/l] -> pH danach
```

Das ist bereits die Titrationskurve, die deine Arbeit im Auswerteskript vorsieht. Du bekommst sie nebenbei, ohne einen eigenen Versuch.

**Bevor du den Zahlen vertraust, sieh dir die Ausgabe der Kalibrierung an.** Entscheidend ist die Steilheit in Prozent des theoretischen Werts. Liegt sie unter 85 Prozent, ist die Anforderung M-06 verletzt, und die Elektrode gehört gewässert und neu kalibriert, bevor du Versuche fährst. Beim letzten dokumentierten Stand waren es 80,3 Prozent. Steht in der Datei jetzt ein besserer Wert, ist das ein Ergebnis für Kapitel 4 und gehört festgehalten.

Eine Einordnung noch zu den 7,6: Deine Kalibrierung stützt sich auf die Puffer 4,01 und 7,00. Im Bereich um 5,8, wo du regelst, ist sie damit belastbar. Bei 8 liegst du außerhalb der Stützstellen und zusätzlich im Bereich des Alkalifehlers. Den genauen Wert dort würde ich nicht überbewerten, die Richtung stimmt aber.

## Frage (2026-09-18 15:32)

Sollte ich nun jetzt neues Wasser nehmen für diesen Versuch?

**Antwort (2026-09-18 15:33)**

**Nein, das Wasser kannst du behalten.** Die Säure von heute Morgen hat der Pufferwirkung kaum etwas genommen.

Der Grund liegt im Carbonatsystem. Zwischen 8,2 und 7,6 liegt fast der gesamte gelöste Kohlenstoff weiterhin als Hydrogencarbonat vor. Umgewandelt wird in diesem Bereich nur ein kleiner Teil, grob geschätzt wenige Prozent der gesamten Säurekapazität. Der große Verbrauch kommt erst auf dem Weg von 7 nach 6, wo der Übergang zu gelöstem Kohlendioxid stattfindet. Dein Reservoir verhält sich also praktisch noch wie frisches Leitungswasser.

Zwei Dinge sprechen sogar dafür, es zu behalten. Das Wasser steht seit heute Morgen, das beim Ansäuern frei gewordene Kohlendioxid ist weitgehend entwichen und der Wert hat sich eingependelt. Frisches Wasser bräuchte diese Zeit erneut. Und du hast bereits einen Messpunkt: die Menge, die 8,2 auf 7,6 gebracht hat. Den wirfst du mit dem Wasser weg.

Neu ansetzen würde ich nur, wenn es alte Nährlösung ist, wenn sich etwas darin abgesetzt hat oder es trüb riecht, oder wenn du nicht mehr weißt, was alles hineingekommen ist.

**Der Ablauf von hier aus:**

1. **NPK einmischen**, Wachstumsdosierung mal 18,4 Liter.
2. **Mindestens eine halbe Stunde umwälzen**, bis die Lösung homogen ist und der Wert nicht mehr wandert.
3. **Erst dann ablesen, wo du gelandet bist.** Wahrscheinlich fällt der pH-Wert durch den Dünger allein deutlich, viele Nährstoffkonzentrate sind sauer. Es kann gut sein, dass du danach schon im Bereich um 6 bist.
4. **Nur nachsteuern, wenn du noch über 6,5 liegst**, und dann in kleinen, notierten Schritten. Nicht tiefer ziehen als nötig, unter 5,8 kommst du ohne frischen Ansatz nicht zurück.
5. **Baseline von zehn bis fünfzehn Minuten**, prüfen ob die Linie flach liegt, dann die Dosis.

Schritt 3 ist der, den man gern überspringt. Wenn du vor dem Einmischen schon auf 6,5 ziehst und der Dünger danach noch einmal um eine halbe Einheit drückt, bist du unter dem Sollwert und musst neu ansetzen.

**Eine Frage noch zum Versuchsaufbau:** Sind die Basilikum- und Petersilienpflanzen gerade im System? Die Wurzeln geben je nach Nährstoffaufnahme selbst Säure oder Lauge ab, und das läuft dir während der halben Stunde Beobachtungszeit als Störgröße mit. Für die saubere Identifikation ist es besser, ohne Pflanzen zu messen. Geht das nicht, notiere es, denn es gehört als Einschränkung zur Auswertung in Abschnitt 4.5.

## Frage (2026-09-18 16:34)

die Basilikum- und Petersilienpflanzen sind nicht gerade im System.

**Antwort (2026-09-18 16:35)**

Gut, das ist der saubere Fall für die Identifikation.

**Für die Gültigkeit des Ergebnisses ist das kein Nachteil.** K_S ist eine Eigenschaft der Lösungschemie, also der Pufferwirkung aus Düngerphosphat und Hydrogencarbonat. Die Wurzeln verändern die Pufferwirkung kurzfristig nicht, sie wirken als Störgröße auf den pH-Wert selbst, indem sie je nach Nitrat- oder Ammoniumaufnahme Säure oder Lauge abgeben. Dein Messwert ist damit die richtige Auslegungsgrundlage. Die eigentliche Einschränkung bleibt die, die deine Arbeit schon nennt: über die Standzeit zehrt die Pflanze Phosphat aus der Lösung, die Pufferwirkung nimmt ab und K_S steigt. Das ist eine Frage der Kulturdauer, nicht der Anwesenheit der Pflanzen während der Messung.

**Der praktische Gewinn ist größer, als er zunächst aussieht: du darfst jetzt kräftig dosieren.** Genau daran wäre der Versuch sonst gescheitert. Bei einem Rauschen von 0,16 bis 0,31 pH und einer Auflösung von zwei Sekunden ohne Mittelung über dreißig Werte muss ein Sprung deutlich aus dem Rauschen herausragen, sonst liegen t28 und t63 im Zufall. Mit Glättung über fünf Werte solltest du je Sprung mindestens eine halbe pH-Einheit anstreben.

Ohne Pflanzen kostet ein Unterschwinger nichts als einen neuen Ansatz. Plane also ruhig von etwa 7,0 nach unten in drei Stufen bis rund 5,5. Das deckt den Arbeitsbereich um 5,8 ab und gibt dir die drei Ausgangswerte aus Abschnitt 4.5 in einer Sitzung.

Zwei Dinge bleiben trotzdem: Der Versuch gehört in das volle Reservoir mit laufender Umwälzung, nicht in ein Becherglas, weil die Totzeit aus Umlaufzeit und Durchmischung entsteht. Und halte im Protokoll fest, dass ohne Bepflanzung gemessen wurde.

## Frage (2026-09-18 16:51)

Was machen wir mit dem PH werte, das wir am Ende kriegen nach Schritt 5

**Antwort (2026-09-18 16:52)**

Der Endwert ist die wichtigste Zahl des ganzen Versuchs. Aus ihm folgt K_S.

```
ph_start  Mittel der Baseline vor der Dosis
ph_ende   Mittel des eingeschwungenen Werts danach
Δ         = ph_start − ph_ende
K_S       = Δ / V_ml                    [pH/ml]
K_S_spez  = K_S · 18,4                  [pH·l/ml], damit volumenunabhängig
```

Zusätzlich setzt der Endwert den Maßstab für die Zeitkennwerte: t28 und t63 sind 28 und 63 Prozent von Δ. Steht Δ falsch, stehen auch Verzugszeit und Ausgleichszeit falsch, und damit die Sperrzeit nach R-05.

**Die eine Falle dabei: den Endwert zu früh ablesen.** Wenn der Verlauf noch fällt und du schon mittelst, kommt Δ zu klein heraus. Dann wird K_S zu klein, und weil K_S im Nenner der Dosierformel steht, dosiert der Regler später zu viel. Das ist genau die Richtung, die du mit reiner pH-Minus-Lösung nicht zurückholen kannst. Im Zweifel also länger warten.

Die Einschwingprüfung im Skript vergleicht dafür nur zwölf Sekunden gegen zwölf Sekunden. Bei deinem Rauschen sagt das nichts aus. Beurteile über mehrere Minuten, ob die Linie wirklich liegt, und nimm für ph_ende das Mittel der letzten paar Minuten, nicht der letzten sechs Werte.

**Danach ist der Endwert zugleich der Startwert des nächsten Sprungs.** So bekommst du die drei geforderten Ausgangswerte. Lass zwischen zwei Dosen mindestens das Dreifache der Ausgleichszeit vergehen, die der erste Versuch ergeben hat, sonst überlagern sich die Antworten. Am Ende hast du drei Wertepaare aus Ausgangs-pH und zugehörigem K_S. Das ist genau die Tabelle 4.5 deiner Arbeit, und daraus liest du ab, wie stark die Verstärkung über den Arbeitsbereich schwankt.

**Für die Lösung selbst gibt es nach dem dritten Sprung zwei sinnvolle Wege.** Entweder du verwirfst sie. Oder, besser, du benutzt sie gleich für den Störungsversuch, den deine Arbeit in Kapitel 5 ohnehin verlangt: eine definierte Menge Leitungswasser nachfüllen, den Anstieg durch das Hydrogencarbonat beobachten und dann die Regelung ausregeln lassen. Das prüft R-02 und R-03 in einem Zug.

Nur eines dabei beachten: Das Nachfüllen erhöht das Volumen und bringt frische Pufferwirkung mit. K_S aus der Identifikation gilt danach nicht mehr unverändert, du musst mit dem neuen Füllstand umrechnen. Notiere deshalb die nachgefüllte Menge.

## Frage (2026-09-18 18:16)

Wie berechnet man T_t in s und T_g in S?

**Antwort (2026-09-18 18:17)**

Beide Zeiten zählen ab dem **Ende der Dosierung**, nicht ab Skriptstart. Lege diesen Zeitpunkt als Nullpunkt fest, dann stimmen die folgenden Formeln.

Vorab brauchst du die beiden Randwerte und den Hub:

```
ph_start  Mittel der Baseline           z. B. 6,50
ph_ende   Mittel im eingeschwungenen Zustand   5,90
Δ         = ph_start − ph_ende               = 0,60
```

**Verfahren A, Wendetangente.** Das ist das, was deine Arbeit in Abschnitt 2.6.2 beschreibt. Du musst dafür nichts zeichnen, es gibt eine direkte Rechnung:

```
T_g = Δ / |größte Steigung|
T_t = Zeitpunkt, an dem die Tangente den Startwert schneidet
```

Die größte Steigung bestimmst du aus der geglätteten Kurve, etwa durch eine Ausgleichsgerade über ein gleitendes Fenster von dreißig bis sechzig Sekunden. Nimm den größten Betrag, den du findest. Ohne Glättung ist das sinnlos, weil das Maximum einer verrauschten Ableitung reines Rauschen ist.

**Verfahren B, Zwei-Punkt-Methode.** Das rechnet dein Skript, und es ist objektiver, weil keine Tangente nach Augenmaß gelegt wird:

```
ziel_28 = ph_start − 0,283 · Δ      = 6,33
ziel_63 = ph_start − 0,632 · Δ      = 6,12

t28 = Zeit, zu der die geglättete Kurve ziel_28 erreicht    z. B. 200 s
t63 = Zeit, zu der die geglättete Kurve ziel_63 erreicht         320 s

T_g = 1,5 · (t63 − t28) = 1,5 · 120   = 180 s
T_t = t63 − T_g         = 320 − 180   = 140 s
```

Die beiden Verfahren liefern für eine Strecke erster Ordnung mit Totzeit dasselbe Ergebnis. Bei deiner Strecke, die aus Transportweg plus Durchmischung besteht, wird die Tangentenmethode eine etwas größere Verzugszeit ergeben als die Zwei-Punkt-Methode. Nimm eines von beiden durchgängig und schreibe in die Auswertung, welches.

Zur Benennung: Was dein Skript als Ausgleichszeit ausgibt, ist streng genommen die Zeitkonstante des angepassten Modells, und was es Verzugszeit nennt, ist dessen Totzeit. Für deine Zwecke ist das dasselbe, aber gleiche die Bezeichnungen an die Arbeit an, sonst fragt der Prüfer.

**Der wichtigste Gegencheck ist physikalisch.** Deine Totzeit setzt sich laut Abschnitt 2.6.2 aus Umlaufzeit, Durchmischung und Ansprechzeit der Elektrode zusammen. Die Umlaufzeit kannst du ausrechnen, sobald du die Fördermenge der Umwälzpumpe ausgelitert hast, was in Tabelle 4.1 ohnehin noch offen ist:

```
Umlaufzeit = 18,4 l / Fördermenge in l/s
```

Kommt deine Auswertung auf eine Totzeit deutlich unter der Umlaufzeit, stimmt etwas nicht, meist die Zeitachse oder eine zu früh getroffene Schwelle im Rauschen. Kommt sie weit darüber, hat die Elektrode länger gebraucht als erwartet, und das gehört als eigener Befund in den Text.

**Für R-05 rechnest du damit die Sperrzeit:**

```
Sperrzeit ≥ T_t + 3 · T_g = 140 + 540 = 680 s ≈ 11 min
```

Dein derzeitiger Platzhalter von 600 Sekunden läge damit sogar in der richtigen Größenordnung. Die Zahlen oben sind aber erfunden, sie zeigen nur den Rechenweg.

## Frage (2026-09-18 18:19)

Wie berechne ich die Größte Steigung für Tg?

**Antwort (2026-09-18 18:20)**

Nicht aus der Differenz zweier benachbarter Messwerte. Bei deinem Rauschen ist die so berechnete Steigung um ein Vielfaches größer als das echte Signal. Du brauchst eine Ausgleichsgerade über ein gleitendes Fenster.

```python
import numpy as np

def groesste_steigung(t, ph, fenster_s=60.0, dt=2.0):
    """Steilste Stelle der Sprungantwort per gleitender Ausgleichsgerade.
    Gibt (t_wende, ph_wende, steigung) zurueck; steigung ist negativ."""
    n = max(5, int(fenster_s / dt))
    t, ph = np.asarray(t, float), np.asarray(ph, float)
    kandidaten = []
    for i in range(len(ph) - n + 1):
        tt, pp = t[i:i+n], ph[i:i+n]
        m = np.polyfit(tt, pp, 1)[0]
        kandidaten.append((tt.mean(), pp.mean(), m))   # Gerade geht durch den Schwerpunkt
    return min(kandidaten, key=lambda k: k[2])         # steilster Abfall = kleinstes m
```

Damit folgen beide Kennwerte ohne Zeichnung:

```
T_g = Δ / |m|
T_t = t_wende + (ph_start − ph_wende) / m
```

**Die Fenstergröße ist der eigentliche Knackpunkt, und bei dir ist sie eng.** Zu kurz, und die Steigung ertrinkt im Rauschen. Zu lang, und du mittelst den Übergang weg, den du gerade vermessen willst. Der Fehler der Steigung aus einer Ausgleichsgeraden lässt sich vorher ausrechnen:

```
σ_m = σ / ( Δt · √( N(N²−1)/12 ) )
```

Mit deinem Rauschen von etwa 0,3 pH und einem Messabstand von 2 s:

| Fenster | Punkte | Fehler der Steigung |
| --- | --- | --- |
| 30 s | 15 | 0,009 pH/s |
| 60 s | 31 | 0,003 pH/s |
| 120 s | 61 | 0,0011 pH/s |

Dem gegenüber steht die Steigung, die du erwartest, nämlich ungefähr Δ geteilt durch T_g:

```
Hub 0,6 pH bei T_g ≈ 180 s  ->  0,0033 pH/s
Hub 1,5 pH bei T_g ≈ 180 s  ->  0,0083 pH/s
```

Lies die beiden Blöcke zusammen. Bei einem Hub von 0,6 pH ist der Fehler selbst im 120-Sekunden-Fenster noch ein Drittel des Signals, und ein Fenster von 120 s verschmiert einen Übergang von 180 s bereits deutlich. Bei einem Hub von 1,5 pH und einem Fenster von 60 s liegt der Fehler dagegen bei gut einem Drittel der Steigung, was brauchbar ist.

Daraus die Faustregel: **Fenster höchstens ein Drittel von T_g, und der Sprung groß genug, dass Δ/T_g mehrere Male über σ_m liegt.** Weil du ohne Pflanzen misst, kannst du den Sprung entsprechend groß wählen. Das ist derselbe Grund wie gestern, nur diesmal von der Steigung her gerechnet.

**Eine ehrliche Einordnung dazu.** Die Wendetangente ist das Verfahren, das deine Arbeit in Abschnitt 2.6.2 beschreibt, aber sie ist von allen das rauschempfindlichste, weil sie über eine Ableitung geht. Die Zwei-Punkt-Methode braucht nur Durchgangszeiten des geglätteten Verlaufs, und Durchgangszeiten sind gegenüber Rauschen erheblich gutmütiger als Steigungen.

Mein Vorschlag für die Auswertung: nimm die Zahlen der Zwei-Punkt-Methode als Ergebnis in Tabelle 4.5, rechne die Wendetangente zusätzlich und führe sie als Gegenprobe mit. Weichen beide stark voneinander ab, sagt dir das, dass die Strecke nicht gut durch ein Verzögerungsglied erster Ordnung mit Totzeit beschrieben wird. Das ist selbst ein Befund und gehört in den Text, nicht weggerechnet.

Vorher glätten und danach differenzieren bringt übrigens kaum etwas zusätzlich, weil beides dieselbe Mittelung ist. Die Grenze aus der Tabelle bleibt bestehen.

## Frage (2026-09-18 18:28)

Wie wäre es wenn ich die Logdatei mit PH werten von Anfang von Dosierung bis zum Ende von Dosierung dir zur Verfügung stelle?

**Antwort (2026-09-18 18:28)**

Sehr gern, das ist der bessere Weg. Die Schätzung im Skript hat die Zeitachsen- und Rauschprobleme, über die wir gesprochen haben. Mit den Rohdaten rechne ich beide Verfahren sauber durch und schreibe dir eine ordentliche Auswertung ins Repo.

**Ich brauche dafür allerdings mehr als die Zeitspanne, in der die Pumpe läuft.** Die paar Sekunden Pumpenlauf enthalten noch gar keine Reaktion, die kommt erst danach. Nötig ist die ganze Sitzung:

```
Baseline vor der Dosierung      10–15 min
Dosierung selbst                die paar Sekunden
Beobachtung danach              bis der Wert wirklich steht, 30 min und mehr
```

Genau das schreibt `sprungantwort_log.csv` schon mit. Die Spalte `phase` trennt Baseline und Nachlauf, und in `dosierung` steht die Menge. Damit kann ich den Dosierzeitpunkt aus dem Phasenwechsel rekonstruieren, der Fehler in der Spalte `t_s` stört mich also nicht. Schick einfach die vollständige Datei.

**Wichtig: nicht mit Excel öffnen und speichern.** Das ist der Fehler, der deine Reihe vom August zerstört hat, Sekunden weg und Dezimalzahlen zu Milliardenwerten. Kopier die Datei unverändert vom Pi:

```powershell
scp pi@192.168.10.1:~/hydroponic-project/iot/sprungantwort_log.csv C:\Users\prati\hydroponic-system\
```

Leg sie irgendwo ab und nenn mir den Namen, den Rest mache ich.

**Dazu vier Angaben, die nicht in der Datei stehen:**

- Dosierte Menge, also Pumpensekunden und die Förderrate, mit der du gerechnet hast
- Füllvolumen des Reservoirs zum Versuchszeitpunkt, ob wirklich die 18,4 Liter
- Ob NPK drin war und in welcher Verdünnung
- Ob die Umwälzpumpe durchgehend lief

Und schick mir bitte `kalibrierung.json` mit. Daraus sehe ich die Steilheit in Prozent, und die sagt mir, wie viel von deinem Rauschen auf die Elektrode zurückgeht. Bei achtzig Prozent der theoretischen Steilheit liefert dieselbe Spannungsschwankung rund ein Viertel mehr pH-Rauschen als bei einer gesunden Elektrode. Das gehört in die Bewertung, nicht nur in Kapitel 4.

**Was du zurückbekommst:**

- Ein Auswerteskript im Repo, das glättet, beide Verfahren rechnet und den Verlauf mit eingezeichneter Tangente plottet
- T_t, T_g und K_S, letzteres auf das Volumen normiert
- Den Gegencheck gegen die Umlaufzeit, sobald du die Fördermenge der Umwälzpumpe hast
- Eine klare Aussage, ob der Sprung groß genug gegenüber dem Rauschen war

Ein Hinweis noch zur Uhrzeit: Wenn der Pi nicht zeitsynchron war, steht ein falsches Datum in der Datei. Für diese Auswertung zählen nur Differenzen, das stört also nicht. Sag mir trotzdem, an welchem Tag du gemessen hast, damit ich es im Protokoll richtig einordne.

Und schick die Datei auch dann, wenn der Verlauf unbrauchbar aussieht. Aus einem misslungenen Lauf lässt sich meist genau ablesen, was beim nächsten anders sein muss.

## Frage (2026-09-18 18:33)

Ich kann nur PH werten und dazugehörige Spannungen und Dosier Menge und Füllvolumen, NPK Volumen zur Verfügung stellen

**Antwort (2026-09-18 18:34)**

Das reicht, mit einer Ergänzung.

**Das Einzige, was ich zwingend zusätzlich brauche, ist die Stelle im Verlauf, an der dosiert wurde.** Ohne sie kann ich den Nullpunkt der Zeitachse nicht setzen, und damit fallen T_t und T_g weg. Am einfachsten gibst du die Werte in zwei Blöcken: alles vor der Dosierung, dann alles danach. Oder du sagst mir schlicht, nach dem wievielten Wert die Pumpe lief.

**Die Zeitachse rekonstruiere ich aus dem Messabstand.** Das Skript misst alle zwei Sekunden und zieht die Rechenzeit vom Schlafintervall ab, der Abstand ist also gleichmäßig. Damit ist der Zeitpunkt des n-ten Wertes einfach n mal zwei Sekunden.

Noch genauer wird es, wenn du mir zwei Uhrzeiten nennst, nämlich wann die Messung begann und wann sie endete. Daraus ergibt sich der wahre mittlere Abstand:

```
Abstand = (Ende − Anfang) / (Anzahl der Werte − 1)
```

Das sind zwei Zahlen statt einer ganzen Spalte, und sie nehmen die Unsicherheit aus den absoluten Zeiten. Ohne sie rechne ich mit glatt zwei Sekunden, dann tragen T_t und T_g einen systematischen Fehler in der Größe der Abweichung des echten Takts.

**Die Spannungen sind wertvoller, als du vermutlich denkst.** Aus den Paaren von pH-Wert und Spannung kann ich die verwendete Kalibriergerade zurückrechnen, weil der Zusammenhang linear ist. Ich bekomme daraus die Steilheit in Millivolt je pH und den Nullpunkt, und damit auch die Prozentangabe zur Anforderung M-06. Die Datei `kalibrierung.json` brauche ich dann gar nicht. Voraussetzung ist nur, dass die Wassertemperatur während des Laufs halbwegs konstant war, weil die Kompensation sonst die Steilheit unterwegs verschiebt. Ein einzelner Temperaturwert vom Versuchstag genügt mir dafür.

**Format ist mir gleich.** Zwei Spalten, pro Zeile eine Messung, in der richtigen Reihenfolge und ohne Lücken. Ob Komma, Semikolon oder Leerzeichen dazwischen steht, ist egal. Bei rund tausend Werten ist eine Datei bequemer als ein Einfügen in den Chat, leg sie einfach in den Projektordner und nenn mir den Namen.

Wichtig ist nur: nichts umsortieren, nichts herausnehmen, auch keine Ausreißer. Die Lücken und Sprünge sind Teil der Information, und das Aussortieren übernimmt die Glättung in der Auswertung.

Damit liefere ich dir K_S vollständig, normiert auf dein Füllvolumen, sowie T_t und T_g nach beiden Verfahren, mit einem Hinweis, wie belastbar die Zeiten angesichts des rekonstruierten Takts sind.

## Frage (2026-09-18 18:35)

die Stelle im Verlauf, an der dosiert wurde bedeutet anfangsPHWert oder?

**Antwort (2026-09-18 18:35)**

Nein, das sind zwei verschiedene Dinge.

Der Anfangs-pH-Wert ist eine **Höhe**, also ein Wert auf der pH-Achse. Die Stelle der Dosierung ist ein **Zeitpunkt**, also eine Position auf der Zeitachse. Ich brauche die Position.

Den Anfangswert rechne ich mir selbst aus, nämlich als Mittel der Messwerte vor der Dosierung. Den musst du mir nicht nennen.

**Warum ich die Position nicht aus der Kurve ablesen kann:** Genau der Abstand zwischen der Dosierung und der ersten sichtbaren Reaktion ist die Totzeit. Würde ich den Dosierzeitpunkt dort ansetzen, wo die Kurve zu knicken beginnt, hätte ich stillschweigend angenommen, die Totzeit sei null. Damit wäre die Zahl, die ich bestimmen soll, schon vorweggenommen.

```
Wert 450                  Pumpe lief hier
Wert 520                  Kurve beginnt sichtbar zu fallen
Differenz 70 Werte x 2 s = 140 s  =  T_t
```

Ohne die 450 bekomme ich die 140 Sekunden nicht.

**Am einfachsten gibst du mir die Werte in zwei Blöcken:**

```
Block 1: alle Messwerte vor der Dosierung
Block 2: alle Messwerte nach der Dosierung
```

Dann liegt die Grenze von selbst richtig und du musst gar nichts zählen. Alternativ reicht ein Satz wie „die Pumpe lief nach dem 450. Wert" oder eine Uhrzeit der Dosierung zusammen mit der Uhrzeit des ersten Messwerts.

**Falls du es nachträglich nicht mehr rekonstruieren kannst, ist nicht alles verloren.** K_S hängt nur von der Gesamthöhe des Sprungs und der dosierten Menge ab, das bekomme ich ohne die Position. Auch T_g ist eine Zeitdifferenz und braucht keinen Nullpunkt. Nur T_t fällt dann weg. Für die Sperrzeit nach R-05 wäre das verschmerzbar, weil die Ausgleichszeit dort dreifach eingeht und den Wert ohnehin dominiert. Sauberer ist es natürlich mit der Position.

## Frage (2026-09-18 18:40)

Wie teile ich dieses Gespräch mit meinem Kommiliton

**Antwort (2026-09-18 18:40)**

Ich schaue kurz nach, wo die Mitschrift dieses Gesprächs liegt und was zum Export bereitsteht.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

**Antwort (2026-09-18 18:41)**

Der Gesprächsverlauf liegt als Maschinenformat vor. Ich wandle ihn in etwas Lesbares um.

_[Werkzeugaufruf: Bash]_

_[Werkzeugaufruf: Bash]_

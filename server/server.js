const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const path = require('path');
const cors = require('cors');
const { formatCsvValue, sanitizeNumericValue } = require('./csv-utils');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = process.env.PORT || 3000;
const PI_API_BASE_URL = process.env.PI_API_BASE_URL;
const PI_SENSOR_POLL_INTERVAL_MS = Number(process.env.PI_SENSOR_POLL_INTERVAL_MS || 2000);

// Dosiermenge fuer den manuellen Testlauf ueber die Weboberflaeche.
// Die harte Obergrenze setzt zusaetzlich der Pi (PUMPE_MAX_EIN_S in hydroponik.py).
const PUMP_MAX_SECONDS = Number(process.env.PUMP_MAX_SECONDS || 10);

// Fallback, solange die Pi-API Sollwert und Toleranz nicht selbst mitliefert.
const PH_TARGET = Number(process.env.PH_TARGET || 5.8);
const PH_TOLERANCE = Number(process.env.PH_TOLERANCE || 0.2);

// Verlauf fuer Diagramm und CSV-Export. 43200 Eintraege entsprechen bei
// 2-s-Takt rund 24 Stunden; das Diagramm zeigt davon die letzten 120.
const HISTORY_LIMIT = Number(process.env.HISTORY_LIMIT || 43200);
const history = [];

let latest = {
    type: 'sensorData',
    ph: null,
    phVoltage: null,
    waterTemp: null,
    pumpActive: false,
    mode: null,
    target: PH_TARGET,
    tolerance: PH_TOLERANCE,
    doseCount: null,
    doseCount24h: null,
    doseLimit: null,
    doseLocked: false,
    lockoutRemaining: null,
    lastDose: null,
    timestamp: null
};

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

function toNumber(value, options = {}) {
    return sanitizeNumericValue(value, options);
}

/**
 * Uebersetzt den "sensor_data"-Dictionary aus hydroponik.py in die Feldnamen
 * der Weboberflaeche. Ungueltige Messungen bleiben null und werden als "--"
 * angezeigt - es wird bewusst kein alter Wert weitergefuehrt.
 */
function normalize(payload = {}) {
    return {
        type: 'sensorData',
        ph: toNumber(payload.ph, { min: 0, max: 14, absMax: 1e12 }),
        phVoltage: toNumber(payload.ph_spannung, { min: 0, max: 5, absMax: 1e12 }),
        waterTemp: toNumber(payload.wasser_temp, { min: -50, max: 100, absMax: 1e12 }),
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

function remember(reading) {
    if (reading.ph === null) {
        return;
    }
    const previous = history[history.length - 1];
    if (previous && previous.timestamp === reading.timestamp) {
        return;
    }
    history.push({
        timestamp: reading.timestamp,
        ph: reading.ph,
        phVoltage: reading.phVoltage,
        waterTemp: reading.waterTemp,
        pumpActive: reading.pumpActive
    });
    if (history.length > HISTORY_LIMIT) {
        history.shift();
    }
}

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

// ------------------------------------------------------------------
//   WebSocket: Push an alle Browser
// ------------------------------------------------------------------
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
            // Messwerte vom Pi oder vom Simulator.
            publish(parsed);
        } catch (error) {
            console.error('Ungueltige Nachricht:', error.message);
        }
    });

    ws.on('close', () => console.log('Client getrennt'));
});

// ------------------------------------------------------------------
//   Pi-Abfrage
// ------------------------------------------------------------------
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

// ------------------------------------------------------------------
//   REST
// ------------------------------------------------------------------
app.get('/api/sensors', (req, res) => res.json(latest));

app.post('/api/sensors', (req, res) => {
    publish(req.body);
    res.json({ status: 'ok' });
});

// Fuer das Diagramm reichen die letzten Punkte; der volle Puffer waere
// bei 24 h Laufzeit mehrere Megabyte je Seitenaufruf.
app.get('/api/history', (req, res) => {
    const limit = Math.max(1, Number(req.query.limit) || 120);
    res.json(history.slice(-limit));
});

/**
 * CSV-Export des gesamten Verlaufspuffers.
 *
 * Die Spaltennamen entsprechen dem Log des Pi (hydroponik_log.csv),
 * damit tools/plot_messreihe.py die Datei direkt einlesen kann.
 */
app.get('/api/export.csv', (req, res) => {
    const kopf = 'timestamp,ph,ph_spannung,wasser_temp,pumpe';
    const zeilen = history.map(punkt =>
        [punkt.timestamp, punkt.ph, punkt.phVoltage, punkt.waterTemp, punkt.pumpActive]
            .map(formatCsvValue)
            .join(','));

    const stempel = (history[history.length - 1]?.timestamp || '')
        .replace(/[: ]/g, '-') || 'leer';
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition',
        `attachment; filename="messwerte_${stempel}.csv"`);
    res.send([kopf, ...zeilen].join('\n') + '\n');
});

/**
 * Peristaltikpumpe (pH-Minus).
 *
 *   POST /api/pump/dose  { "seconds": 2 }  ->  Pi: GET /api/pumpe/test?sekunden=2
 *   POST /api/pump/stop                    ->  Pi: GET /api/pumpe/stopp
 *
 * Ein dauerhaftes Einschalten gibt es bewusst nicht: hydroponik.py kennt nur
 * zeitbegrenzte Laeufe, damit die Pumpe bei einem Verbindungsabbruch stoppt.
 * Hinweis: /api/pumpe/test antwortet erst NACH Ablauf der Dosierzeit.
 */
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

// ------------------------------------------------------------------
//   Start
// ------------------------------------------------------------------
if (PI_API_BASE_URL) {
    pollPi();
    setInterval(pollPi, PI_SENSOR_POLL_INTERVAL_MS);
}

server.listen(PORT, () => {
    console.log(`Server laeuft auf http://localhost:${PORT}`);
    console.log(PI_API_BASE_URL
        ? `Pi-API: ${PI_API_BASE_URL} (alle ${PI_SENSOR_POLL_INTERVAL_MS} ms)`
        : 'Kein PI_API_BASE_URL gesetzt - Demobetrieb, Daten per WebSocket erwartet');
});

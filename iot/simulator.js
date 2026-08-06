/**
 * Simulator fuer den Betrieb ohne Raspberry Pi.
 *
 * Sendet dasselbe Datenformat, das hydroponik.py ueber GET /api/sensors
 * liefert. Damit laesst sich die Weboberflaeche ohne Hardware testen.
 *
 * Start:  npm run simulate
 */
const WebSocket = require('ws');

const WS_URL = process.env.SIM_WS_URL || 'ws://localhost:3000';
const INTERVAL_MS = Number(process.env.SIM_INTERVAL_MS || 2000);

const SOLLWERT_PH = 5.8;
const TOLERANZ_PH = 0.2;
const SPERRZEIT_S = 30;          // im Simulator verkuerzt, auf dem Pi 300 s
// Zum Ausprobieren der Mengenbegrenzung klein setzen: SIM_DOSE_LIMIT=3 npm run simulate
const MAX_DOSIERUNGEN = Number(process.env.SIM_DOSE_LIMIT || 20);

let ph = 6.35;
let dosierungen = 0;
let sperrzeitRest = 0;
let pumpeLaeuft = false;
let letzteDosierung = null;

function zeitstempel() {
    const pad = (wert) => String(wert).padStart(2, '0');
    const jetzt = new Date();
    return `${jetzt.getFullYear()}-${pad(jetzt.getMonth() + 1)}-${pad(jetzt.getDate())} ` +
        `${pad(jetzt.getHours())}:${pad(jetzt.getMinutes())}:${pad(jetzt.getSeconds())}`;
}

// Vereinfachtes Modell: der pH-Wert driftet nach oben, eine Dosierung
// pH-Minus senkt ihn, danach laeuft die Sperrzeit.
function simuliereRegelung() {
    ph += 0.01 + Math.random() * 0.025;

    if (sperrzeitRest > 0) {
        sperrzeitRest = Math.max(0, sperrzeitRest - INTERVAL_MS / 1000);
        return;
    }

    // Mengenbegrenzung: ab hier wird nicht mehr korrigiert, der pH steigt weiter.
    if (dosierungen >= MAX_DOSIERUNGEN) {
        return;
    }

    if (ph > SOLLWERT_PH + TOLERANZ_PH) {
        ph -= 0.5 + Math.random() * 0.2;
        dosierungen += 1;
        letzteDosierung = zeitstempel();
        sperrzeitRest = SPERRZEIT_S;
        pumpeLaeuft = true;
        setTimeout(() => { pumpeLaeuft = false; }, 1500);
    }
}

const ws = new WebSocket(WS_URL);

ws.on('open', () => {
    console.log(`Simulator verbunden mit ${WS_URL}`);

    setInterval(() => {
        simuliereRegelung();

        ws.send(JSON.stringify({
            ph: Number(ph.toFixed(2)),
            ph_spannung: Number(((7 - ph) / 17.85 + 2.15).toFixed(4)),
            wasser_temp: Number((21 + Math.random() * 1.5).toFixed(2)),
            luft_temp: Number((22 + Math.random() * 2).toFixed(1)),
            luft_feuchte: Number((55 + Math.random() * 8).toFixed(1)),
            feuchtigkeit: true,
            pumpe: pumpeLaeuft,
            betriebsart: 'regelung (simuliert)',
            sollwert_ph: SOLLWERT_PH,
            toleranz_ph: TOLERANZ_PH,
            letzte_dosierung: letzteDosierung,
            dosierungen_gesamt: dosierungen,
            dosierungen_24h: dosierungen,
            max_dosierungen_tag: MAX_DOSIERUNGEN,
            dosierung_gesperrt: dosierungen >= MAX_DOSIERUNGEN,
            sperrzeit_rest_s: Math.round(sperrzeitRest),
            timestamp: zeitstempel()
        }));
    }, INTERVAL_MS);
});

ws.on('error', (error) => {
    console.error('Simulator: Verbindung fehlgeschlagen -', error.message);
});

// ==================================================================
//   Hydroponik - pH-Anzeige
//   Zeigt die Messwerte des Raspberry Pi live an und steuert die
//   Peristaltikpumpe (pH-Minus) ueber die REST-Schnittstelle.
// ==================================================================

const SVG_NS = 'http://www.w3.org/2000/svg';
const MAX_POINTS = 120;
const RECONNECT_DELAY_MS = 3000;

const WS_URL = window.location.host
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
    : 'ws://localhost:3000';

/** @type {{timestamp: string, ph: number, phVoltage: number|null}[]} */
let history = [];
let current = null;
let focusIndex = null;
let ws = null;

const $ = (id) => document.getElementById(id);

const chart = $('chart');
const chartEmpty = $('chart-empty');
const tooltip = $('tooltip');
const tableView = $('table-view');
const tableBody = $('table-body');
const tableToggle = $('table-toggle');
const pumpSeconds = $('pump-seconds');
const pumpDose = $('pump-dose');
const pumpStop = $('pump-stop');
const pumpFeedback = $('pump-feedback');

// ==================================================================
//   Formatierung
// ==================================================================

function num(value, digits, unit = '') {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) {
        return '--';
    }
    return `${Number(value).toFixed(digits)}${unit}`;
}

function clockOf(timestamp) {
    // Der Pi liefert "YYYY-MM-DD HH:MM:SS"; der Simulator ebenso.
    const match = String(timestamp || '').match(/(\d{2}):(\d{2}):(\d{2})/);
    return match ? match[0] : '--';
}

function setText(id, text) {
    const element = $(id);
    if (element) {
        element.textContent = text;
    }
}

function setPill(element, variant, icon, text) {
    element.className = `pill pill-${variant}`;
    element.innerHTML = '';
    const iconSpan = document.createElement('span');
    iconSpan.className = 'pill-icon';
    iconSpan.setAttribute('aria-hidden', 'true');
    iconSpan.textContent = icon;
    element.append(iconSpan, document.createTextNode(text));
}

// ==================================================================
//   Anzeige der Messwerte
// ==================================================================

function render(data) {
    current = data;

    setText('ph-value', num(data.ph, 2));
    setText('ph-voltage', `Sensorspannung ${num(data.phVoltage, 4, ' V')}`);
    setText('last-update', `Letzte Messung: ${data.timestamp || '--'}`);

    // Zielbereich
    const target = Number(data.target);
    const tolerance = Number(data.tolerance);
    const hasBand = Number.isFinite(target) && Number.isFinite(tolerance);
    setText('target-text', hasBand
        ? `Zielbereich ${(target - tolerance).toFixed(2)} – ${(target + tolerance).toFixed(2)}`
        : 'Zielbereich --');

    // Zustand: Farbe immer zusammen mit Symbol und Text.
    const state = $('ph-state');
    if (data.ph === null || data.ph === undefined) {
        setPill(state, 'critical', '✕', 'Messwert ungültig');
    } else if (!hasBand) {
        setPill(state, 'neutral', '●', 'Kein Zielbereich');
    } else if (data.ph > target + tolerance) {
        setPill(state, 'warning', '▲', 'Über Zielbereich');
    } else if (data.ph < target - tolerance) {
        setPill(state, 'warning', '▼', 'Unter Zielbereich');
    } else {
        setPill(state, 'good', '✓', 'Im Zielbereich');
    }

    // Pumpe und Regelung
    setText('mode', data.mode || '--');
    setText('pump-state', data.pumpActive ? 'läuft' : 'aus');
    setText('dose-count', data.doseCount === null ? '--' : String(data.doseCount));
    setText('dose-24h', data.doseCount24h === null
        ? '--'
        : `${data.doseCount24h}${data.doseLimit !== null ? ` / ${data.doseLimit}` : ''}`);

    // Ausgeloeste Mengenbegrenzung heisst: es wird nicht mehr geregelt.
    // Das muss sichtbar sein, nicht nur im Log des Pi stehen.
    $('dose-lock').hidden = !data.doseLocked;
    $('dose-lock-note').hidden = !data.doseLocked;
    setText('lockout', data.lockoutRemaining === null ? '--' : `${Math.round(data.lockoutRemaining)} s`);
    setText('last-dose', data.lastDose || '--');

    // Begleitmesswerte
    setText('water-temp', num(data.waterTemp, 1, ' °C'));
    setText('air-temp', num(data.airTemp, 1, ' °C'));
    setText('air-humidity', num(data.airHumidity, 0, ' %'));
    setText('moisture', data.moist === null || data.moist === undefined
        ? '--'
        : (data.moist ? 'nass' : 'trocken'));
}

function recordReading(data) {
    if (data.ph === null || data.ph === undefined) {
        return false;
    }
    const previous = history[history.length - 1];
    if (previous && previous.timestamp === data.timestamp) {
        return false;
    }
    history.push({ timestamp: data.timestamp, ph: data.ph, phVoltage: data.phVoltage });
    if (history.length > MAX_POINTS) {
        history.shift();
        if (focusIndex !== null) {
            focusIndex = Math.max(0, focusIndex - 1);
        }
    }
    return true;
}

// ==================================================================
//   Diagramm - pH-Verlauf
//   Eine Serie, daher keine Legende: die Ueberschrift benennt sie.
//   Die x-Achse ist indexbasiert, die Messungen kommen im festen
//   Intervall (MESSINTERVALL_S auf dem Pi).
// ==================================================================

const PADDING = { top: 16, right: 60, bottom: 30, left: 46 };

function svgEl(name, attrs = {}, className = '') {
    const element = document.createElementNS(SVG_NS, name);
    for (const [key, value] of Object.entries(attrs)) {
        element.setAttribute(key, value);
    }
    if (className) {
        element.setAttribute('class', className);
    }
    return element;
}

function yDomain() {
    const values = history.map(point => point.ph);
    const target = Number(current?.target);
    const tolerance = Number(current?.tolerance);

    if (Number.isFinite(target) && Number.isFinite(tolerance)) {
        values.push(target - tolerance, target + tolerance);
    }
    if (!values.length) {
        return [5, 7];
    }

    let min = Math.min(...values);
    let max = Math.max(...values);
    const padding = Math.max((max - min) * 0.25, 0.15);
    min -= padding;
    max += padding;
    return [min, max];
}

function drawChart() {
    const width = chart.clientWidth;
    const height = chart.clientHeight;
    if (!width || !height) {
        return;
    }

    chart.setAttribute('viewBox', `0 0 ${width} ${height}`);
    chart.replaceChildren();

    chartEmpty.hidden = history.length > 0;
    if (history.length === 0) {
        return;
    }

    const plotWidth = width - PADDING.left - PADDING.right;
    const plotHeight = height - PADDING.top - PADDING.bottom;
    const [minY, maxY] = yDomain();

    const xOf = (index) => history.length === 1
        ? PADDING.left + plotWidth / 2
        : PADDING.left + (index / (history.length - 1)) * plotWidth;
    const yOf = (value) => PADDING.top + plotHeight - ((value - minY) / (maxY - minY)) * plotHeight;

    // --- Zielbereich als zurueckhaltende Flaeche, mit Textbeschriftung ---
    const target = Number(current?.target);
    const tolerance = Number(current?.tolerance);
    if (Number.isFinite(target) && Number.isFinite(tolerance)) {
        const top = yOf(target + tolerance);
        const bottom = yOf(target - tolerance);
        chart.append(svgEl('rect', {
            x: PADDING.left, y: top, width: plotWidth, height: Math.max(bottom - top, 1)
        }, 'chart-band'));
        const bandLabel = svgEl('text', { x: PADDING.left + 8, y: top - 5 }, 'chart-band-label');
        bandLabel.textContent =
            `Zielbereich ${(target - tolerance).toFixed(2)}–${(target + tolerance).toFixed(2)}`;
        chart.append(bandLabel);
    }

    // --- Gitternetz und y-Achse: durchgezogene Haarlinien, zurueckhaltend ---
    const TICKS = 4;
    for (let i = 0; i <= TICKS; i++) {
        const value = minY + (i / TICKS) * (maxY - minY);
        const y = yOf(value);
        chart.append(svgEl('line', {
            x1: PADDING.left, y1: y, x2: PADDING.left + plotWidth, y2: y
        }, 'chart-grid'));
        const tick = svgEl('text', { x: PADDING.left - 10, y: y + 4 }, 'chart-tick');
        tick.textContent = value.toFixed(1);
        chart.append(tick);
    }

    // --- x-Achse: erster, mittlerer und letzter Zeitstempel ---
    const axisY = PADDING.top + plotHeight;
    chart.append(svgEl('line', {
        x1: PADDING.left, y1: axisY, x2: PADDING.left + plotWidth, y2: axisY
    }, 'chart-axis'));

    const labelIndexes = history.length > 2
        ? [0, Math.floor((history.length - 1) / 2), history.length - 1]
        : [0, history.length - 1];
    new Set(labelIndexes).forEach((index) => {
        const label = svgEl('text', { x: xOf(index), y: axisY + 18 }, 'chart-time');
        label.textContent = clockOf(history[index].timestamp);
        chart.append(label);
    });

    // --- Datenlinie: 2px, runde Enden ---
    const path = history.map((point, index) =>
        `${index === 0 ? 'M' : 'L'}${xOf(index).toFixed(1)},${yOf(point.ph).toFixed(1)}`).join(' ');
    chart.append(svgEl('path', { d: path }, 'chart-line'));

    // --- Endpunkt mit Ring in Flaechenfarbe, direkt beschriftet ---
    const lastIndex = history.length - 1;
    const last = history[lastIndex];
    chart.append(svgEl('circle', { cx: xOf(lastIndex), cy: yOf(last.ph), r: 4 }, 'chart-dot'));
    const endLabel = svgEl('text', {
        x: Math.min(xOf(lastIndex) + 12, width - 6), y: yOf(last.ph) + 4
    }, 'chart-end-label');
    endLabel.textContent = last.ph.toFixed(2);
    chart.append(endLabel);

    // --- Fadenkreuz fuer Hover und Tastatur ---
    if (focusIndex !== null && history[focusIndex]) {
        const point = history[focusIndex];
        const x = xOf(focusIndex);
        chart.append(svgEl('line', {
            x1: x, y1: PADDING.top, x2: x, y2: axisY
        }, 'chart-crosshair'));
        chart.append(svgEl('circle', { cx: x, cy: yOf(point.ph), r: 4 }, 'chart-dot'));
        showTooltip(point, x, yOf(point.ph));
    } else {
        tooltip.hidden = true;
    }

    // --- Trefferflaeche fuer den Zeiger, deutlich groesser als die Punkte ---
    const hit = svgEl('rect', {
        x: PADDING.left, y: PADDING.top, width: plotWidth, height: plotHeight, fill: 'transparent'
    });
    hit.addEventListener('pointermove', (event) => {
        const box = chart.getBoundingClientRect();
        const relative = (event.clientX - box.left - PADDING.left) / plotWidth;
        const index = Math.round(relative * (history.length - 1));
        const clamped = Math.min(Math.max(index, 0), history.length - 1);
        if (clamped !== focusIndex) {
            focusIndex = clamped;
            drawChart();
        }
    });
    hit.addEventListener('pointerleave', () => {
        focusIndex = null;
        drawChart();
    });
    chart.append(hit);
}

function showTooltip(point, x, y) {
    tooltip.hidden = false;
    tooltip.innerHTML = '';

    const time = document.createElement('div');
    time.className = 'tooltip-time';
    time.textContent = clockOf(point.timestamp);

    const value = document.createElement('div');
    value.className = 'tooltip-value';
    value.textContent = `pH ${point.ph.toFixed(2)}`;

    tooltip.append(time, value);

    if (point.phVoltage !== null && point.phVoltage !== undefined) {
        const voltage = document.createElement('div');
        voltage.className = 'tooltip-time';
        voltage.textContent = `${point.phVoltage.toFixed(4)} V`;
        tooltip.append(voltage);
    }

    // an den Kartenraendern einklappen, damit der Kasten nicht ueberlaeuft
    const half = tooltip.offsetWidth / 2;
    const maxX = chart.clientWidth - half - 4;
    tooltip.style.left = `${Math.min(Math.max(x, half + 4), maxX)}px`;
    tooltip.style.top = `${y - 12}px`;
}

// Tastaturbedienung: gleiche Information wie beim Hover.
chart.setAttribute('tabindex', '0');
chart.addEventListener('keydown', (event) => {
    if (!history.length) {
        return;
    }
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        const start = focusIndex === null ? history.length - 1 : focusIndex;
        const step = event.key === 'ArrowLeft' ? -1 : 1;
        focusIndex = Math.min(Math.max(start + step, 0), history.length - 1);
        drawChart();
    } else if (event.key === 'Escape') {
        focusIndex = null;
        drawChart();
    }
});
chart.addEventListener('blur', () => {
    focusIndex = null;
    drawChart();
});

new ResizeObserver(() => drawChart()).observe(chart);

// ==================================================================
//   Tabellenansicht - jeder Wert auch ohne Zeiger erreichbar
// ==================================================================

function drawTable() {
    if (tableView.hidden) {
        return;
    }
    tableBody.replaceChildren();
    [...history].reverse().forEach((point) => {
        const row = document.createElement('tr');
        [clockOf(point.timestamp), point.ph.toFixed(2), num(point.phVoltage, 4, ' V')]
            .forEach((text) => {
                const cell = document.createElement('td');
                cell.textContent = text;
                row.append(cell);
            });
        tableBody.append(row);
    });
}

// ==================================================================
//   Export: CSV vom Server, Diagramm als PNG
// ==================================================================

document.getElementById('csv-export').addEventListener('click', () => {
    // Content-Disposition des Servers loest den Download aus,
    // die Seite bleibt dabei stehen.
    window.location.href = '/api/export.csv';
});

/**
 * Rastert das SVG-Diagramm in ein PNG.
 *
 * Die Farben und Linienstaerken stehen im Stylesheet, nicht im SVG -
 * beim Serialisieren gingen sie verloren und das Bild waere leer.
 * Deshalb werden die berechneten Stile vorher elementweise auf einen
 * Klon uebertragen.
 */
async function erzeugeDiagrammPng() {
    const klon = chart.cloneNode(true);
    const originale = chart.querySelectorAll('*');
    const kopien = klon.querySelectorAll('*');
    const EIGENSCHAFTEN = [
        'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin',
        'opacity', 'font-family', 'font-size', 'font-weight', 'text-anchor',
        'paint-order', 'font-variant-numeric'
    ];
    originale.forEach((element, index) => {
        const stil = getComputedStyle(element);
        let css = '';
        for (const eigenschaft of EIGENSCHAFTEN) {
            const wert = stil.getPropertyValue(eigenschaft);
            if (wert) {
                css += `${eigenschaft}:${wert};`;
            }
        }
        kopien[index].setAttribute('style', css);
    });

    const breite = chart.clientWidth;
    const hoehe = chart.clientHeight;
    klon.setAttribute('xmlns', SVG_NS);
    klon.setAttribute('width', breite);
    klon.setAttribute('height', hoehe);

    // Hintergrund in Flaechenfarbe, sonst wird das PNG transparent.
    const flaeche = getComputedStyle(document.documentElement)
        .getPropertyValue('--surface').trim() || '#ffffff';
    const hintergrund = document.createElementNS(SVG_NS, 'rect');
    hintergrund.setAttribute('width', '100%');
    hintergrund.setAttribute('height', '100%');
    hintergrund.setAttribute('fill', flaeche);
    klon.insertBefore(hintergrund, klon.firstChild);

    const svgText = new XMLSerializer().serializeToString(klon);
    const url = URL.createObjectURL(new Blob([svgText], { type: 'image/svg+xml' }));
    try {
        const bild = new Image();
        await new Promise((geladen, fehler) => {
            bild.onload = geladen;
            bild.onerror = fehler;
            bild.src = url;
        });
        // doppelte Aufloesung, damit das PNG im Dokument scharf bleibt
        const leinwand = document.createElement('canvas');
        leinwand.width = breite * 2;
        leinwand.height = hoehe * 2;
        leinwand.getContext('2d').drawImage(bild, 0, 0, leinwand.width, leinwand.height);
        return leinwand.toDataURL('image/png');
    } finally {
        URL.revokeObjectURL(url);
    }
}

document.getElementById('png-export').addEventListener('click', async () => {
    if (!history.length) {
        return;                          // leeres Diagramm, nichts zu speichern
    }
    focusIndex = null;                   // Fadenkreuz nicht mit exportieren
    drawChart();

    const dataUrl = await erzeugeDiagrammPng();
    const link = document.createElement('a');
    const stempel = (current?.timestamp || 'export').replace(/[: ]/g, '-');
    link.href = dataUrl;
    link.download = `ph-verlauf_${stempel}.png`;
    link.click();
});

tableToggle.addEventListener('click', () => {
    tableView.hidden = !tableView.hidden;
    tableToggle.setAttribute('aria-expanded', String(!tableView.hidden));
    tableToggle.textContent = tableView.hidden ? 'Tabelle anzeigen' : 'Tabelle ausblenden';
    drawTable();
});

// ==================================================================
//   Verbindung
// ==================================================================

function setConnected(connected) {
    setPill($('connection'), connected ? 'online' : 'offline', '●',
        connected ? 'Verbunden' : 'Getrennt');
}

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

// Letzten Stand und Verlauf vom Server holen, damit nach einem Reload
// sofort Werte und Zielbereich stehen, statt auf die erste Messung zu warten.
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

// ==================================================================
//   Pumpensteuerung
//   Die Grenzen setzt der Pi durch; hier nur Bedienung und Rueckmeldung.
// ==================================================================

function feedback(message, isError = false) {
    pumpFeedback.textContent = message;
    pumpFeedback.classList.toggle('error', isError);
    pumpFeedback.classList.toggle('ok', !isError);
}

async function pumpRequest(action, seconds) {
    pumpDose.disabled = true;
    pumpStop.disabled = true;
    try {
        const response = await fetch(`/api/pump/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(seconds ? { seconds } : {})
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            feedback(data.fehler || data.error || `Fehler ${response.status}`, true);
            return;
        }
        feedback(action === 'dose'
            ? `Dosierung ausgeführt (${data.sekunden ?? seconds} s)`
            : 'Pumpe gestoppt');
    } catch (error) {
        feedback(`Server nicht erreichbar: ${error.message}`, true);
    } finally {
        pumpDose.disabled = false;
        pumpStop.disabled = false;
    }
}

pumpDose.addEventListener('click', () => {
    const seconds = Number(pumpSeconds.value);
    if (!Number.isFinite(seconds) || seconds <= 0) {
        feedback('Bitte eine Dosierzeit größer 0 angeben.', true);
        return;
    }
    feedback(`Pumpe läuft für ${seconds} s …`);
    pumpRequest('dose', seconds);
});

pumpStop.addEventListener('click', () => {
    feedback('Not-Aus gesendet …');
    pumpRequest('stop');
});

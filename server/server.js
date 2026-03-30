const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });
const PI_API_BASE_URL = process.env.PI_API_BASE_URL;

let latestSensorData = {
    type: 'sensorData',
    temperature: null,
    ph: null,
    waterLevel: null,
    nitrogen: null,
    phosphorus: null,
    potassium: null,
    lightsOn: false,
    timestamp: null
};

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '../public')));

function toNumber(value) {
    if (value === null || value === undefined || value === '') {
        return null;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
}

function normalizeSensorData(payload = {}) {
    const isPiShape = Object.prototype.hasOwnProperty.call(payload, 'luft_temp') ||
        Object.prototype.hasOwnProperty.call(payload, 'wasser_temp') ||
        Object.prototype.hasOwnProperty.call(payload, 'luft_feuchte');

    if (isPiShape) {
        return {
            ...latestSensorData,
            type: 'sensorData',
            // UI zeigt aktuell "Water Temp", daher priorisieren wir wasser_temp.
            temperature: toNumber(payload.wasser_temp ?? payload.luft_temp),
            ph: toNumber(payload.ph),
            // Wenn kein Tank-Fuellstand vorhanden ist, bleibt der letzte bekannte Wert erhalten.
            waterLevel: toNumber(payload.water_level ?? payload.waterLevel ?? latestSensorData.waterLevel),
            timestamp: payload.timestamp ?? new Date().toISOString()
        };
    }

    return {
        ...latestSensorData,
        ...payload,
        type: 'sensorData',
        temperature: toNumber(payload.temperature ?? latestSensorData.temperature),
        ph: toNumber(payload.ph ?? latestSensorData.ph),
        waterLevel: toNumber(payload.waterLevel ?? latestSensorData.waterLevel),
        nitrogen: toNumber(payload.nitrogen ?? latestSensorData.nitrogen),
        phosphorus: toNumber(payload.phosphorus ?? latestSensorData.phosphorus),
        potassium: toNumber(payload.potassium ?? latestSensorData.potassium),
        lightsOn: Boolean(payload.lightsOn ?? latestSensorData.lightsOn),
        timestamp: payload.timestamp ?? new Date().toISOString()
    };
}

// WebSocket Server for real-time communication
wss.on('connection', (ws) => {
    console.log('New client connected');
    ws.send(JSON.stringify(latestSensorData));
    
    ws.on('message', (message) => {
        const rawMessage = message.toString();
        console.log('Received:', rawMessage);

        try {
            const parsed = JSON.parse(rawMessage);

            if (parsed.type === 'requestData') {
                ws.send(JSON.stringify(latestSensorData));
                return;
            }

            if (parsed.type === 'sensorData' || parsed.wasser_temp !== undefined || parsed.luft_temp !== undefined) {
                latestSensorData = normalizeSensorData(parsed);
                broadcastToClients(JSON.stringify(latestSensorData));
                return;
            }

            broadcastToClients(rawMessage);
        } catch (error) {
            console.error('Invalid JSON message:', error.message);
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

function broadcastToClients(data) {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
}

// REST API Endpoints
app.post('/api/sensor-data', (req, res) => {
    latestSensorData = normalizeSensorData(req.body);
    broadcastToClients(JSON.stringify(latestSensorData));
    res.status(200).json({ status: 'ok' });
});

app.get('/api/sensors', (req, res) => {
    res.json(latestSensorData);
});

app.post('/api/sensors', (req, res) => {
    latestSensorData = normalizeSensorData(req.body);
    broadcastToClients(JSON.stringify(latestSensorData));
    res.status(200).json({ status: 'ok' });
});

app.post('/api/pump/:action', async (req, res) => {
    const { action } = req.params;
    if (action !== 'on' && action !== 'off') {
        res.status(400).json({ error: 'Invalid action' });
        return;
    }

    if (PI_API_BASE_URL) {
        try {
            const response = await fetch(`${PI_API_BASE_URL}/api/pump/${action}`);
            const data = await response.json();
            res.status(response.status).json(data);
            return;
        } catch (error) {
            res.status(502).json({ error: 'Pi API unreachable', details: error.message });
            return;
        }
    }

    broadcastToClients(JSON.stringify({ type: 'pumpControl', action }));
    res.json({ status: 'ok', mode: 'ws-only', action });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`WebSocket server listening on ws://localhost:${PORT}`);
});
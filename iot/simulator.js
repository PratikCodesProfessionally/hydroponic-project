const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:3000');

ws.on('open', () => {
    setInterval(() => {
        const sensorData = {
            type: 'sensorData',
            temperature: (Math.random() * 10 + 20).toFixed(1),
            ph: (Math.random() * 3 + 5.5).toFixed(1),
            waterLevel: (Math.random() * 100).toFixed(0),
            nitrogen: (Math.random() * 80 + 120).toFixed(0),
            phosphorus: (Math.random() * 40 + 40).toFixed(0),
            potassium: (Math.random() * 100 + 140).toFixed(0),
            lightsOn: Math.random() > 0.5,
            timestamp: new Date().toISOString()
        };
        ws.send(JSON.stringify(sensorData));
    }, 2000);
});
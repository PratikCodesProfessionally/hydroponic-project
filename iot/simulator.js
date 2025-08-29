const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:3000');

ws.on('open', () => {
    setInterval(() => {
        const sensorData = {
            temperature: (Math.random() * 10 + 20).toFixed(1),
            ph: (Math.random() * 3 + 5.5).toFixed(1),
            waterLevel: Math.random() * 100,
            ec: (Math.random() * 2 + 1.5).toFixed(1)
        };
        ws.send(JSON.stringify(sensorData));
    }, 2000);
});
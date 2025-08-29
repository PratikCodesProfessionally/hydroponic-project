const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '../public')));

// WebSocket Server for real-time communication
wss.on('connection', (ws) => {
    console.log('New client connected');
    
    ws.on('message', (message) => {
        console.log('Received:', message.toString());
        // Handle IoT device messages here
        broadcastToClients(message.toString());
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
    const sensorData = req.body;
    broadcastToClients(JSON.stringify(sensorData));
    res.status(200).send('Data received');
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`WebSocket server listening on ws://localhost:${PORT}`);
});
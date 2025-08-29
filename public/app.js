// WebSocket Connection
const ws = new WebSocket(`ws://${window.location.hostname}:3000`);

// DOM Elements
const connectionStatus = document.getElementById('connection-status');
const nValue = document.getElementById('n-value');
const pValue = document.getElementById('p-value');
const kValue = document.getElementById('k-value');
const nSlider = document.getElementById('n-slider');
const pSlider = document.getElementById('p-slider');
const kSlider = document.getElementById('k-slider');
const lightToggle = document.getElementById('light-toggle');
const lightStatus = document.getElementById('light-status');

// Connection Handling
ws.onopen = () => {
    connectionStatus.textContent = "Connected";
    connectionStatus.classList.replace('offline', 'online');
};

ws.onclose = () => {
    connectionStatus.textContent = "Disconnected";
    connectionStatus.classList.replace('online', 'offline');
};

// Message Handling
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update sensor readings
    if (data.type === 'sensorData') {
        document.getElementById('temperature').textContent = `${data.temperature}°C`;
        document.getElementById('ph-level').textContent = data.ph;
        document.getElementById('water-level').textContent = `${data.waterLevel}%`;
        
        // Update NPK values
        nValue.textContent = `${data.nitrogen} ppm`;
        pValue.textContent = `${data.phosphorus} ppm`;
        kValue.textContent = `${data.potassium} ppm`;
        
        // Update light status
        lightToggle.checked = data.lightsOn;
        lightStatus.textContent = data.lightsOn ? "ON" : "OFF";
    }
};

// Control Event Listeners
nSlider.addEventListener('input', (e) => {
    ws.send(JSON.stringify({
        type: 'nutrientControl',
        nutrient: 'nitrogen',
        value: e.target.value
    }));
});

pSlider.addEventListener('input', (e) => {
    ws.send(JSON.stringify({
        type: 'nutrientControl',
        nutrient: 'phosphorus',
        value: e.target.value
    }));
});

kSlider.addEventListener('input', (e) => {
    ws.send(JSON.stringify({
        type: 'nutrientControl',
        nutrient: 'potassium',
        value: e.target.value
    }));
});

document.getElementById('n-dose').addEventListener('click', () => {
    ws.send(JSON.stringify({
        type: 'nutrientDose',
        nutrient: 'nitrogen',
        amount: 5
    }));
});

document.getElementById('p-dose').addEventListener('click', () => {
    ws.send(JSON.stringify({
        type: 'nutrientDose',
        nutrient: 'phosphorus',
        amount: 3
    }));
});

document.getElementById('k-dose').addEventListener('click', () => {
    ws.send(JSON.stringify({
        type: 'nutrientDose',
        nutrient: 'potassium',
        amount: 7
    }));
});

lightToggle.addEventListener('change', (e) => {
    ws.send(JSON.stringify({
        type: 'lightControl',
        state: e.target.checked
    }));
    lightStatus.textContent = e.target.checked ? "ON" : "OFF";
});

// Simulate data for demo (remove in production)
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'requestData'
        }));
    }
}, 2000);
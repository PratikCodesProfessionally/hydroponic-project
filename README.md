# hydroponic-project
Bachelorproject

## Raspberry Pi

Der Pi-Teil liegt in [iot/raspi_hydroponics.py](iot/raspi_hydroponics.py).

Starten mit:

```bash
PI_API_BASE_URL=http://192.168.1.23:5000 python3 iot/raspi_hydroponics.py
```

Der Node-Server liest die Sensordaten dann über `GET /api/sensors` von der Pi-API ein.

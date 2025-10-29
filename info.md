
## SolaX Cloud (Multi)

Diese Integration pollt mehrere SolaX-Geräte (Cloud V2 API) parallel über einen gemeinsamen **tokenId**.
- UI-Setup via **Config Flow**
- Geräteverwaltung (wifiSn, Anzeigename, Batterie-kWh) in den **Optionen**
- Sensoren: AC Power, Feed-in Power, Battery Power, Battery SoC, Battery Temperature, Battery Cycles + Battery ETA (Text & Minuten)
- Polling-Intervall einstellbar

### Installation
- **HACS → Integrations → Custom repositories**: `https://github.com/empx92/HASS-Solax-API-Call`
- Kategorie: *Integration*
- Installieren, **HA Neustart**
- Einstellungen → Geräte & Dienste → **Integration hinzufügen** → *SolaX Cloud (Multi)*

### Hinweise
- API: `POST /api/v2/dataAccess/realtimeInfo/get` (Header `tokenId`, Body `{"wifiSn":"..."}`) der SolaX Cloud.

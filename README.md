
# SolaX Cloud (Multi) — Home Assistant Custom Integration

> by **empx92**

Pollt **mehrere** SolaX-Geräte (Cloud V2 API) parallel mit **einem tokenId** und je **eigener wifiSn**.
Erstellt Sensors je Gerät: `AC Power`, `Feed-in Power`, `Battery Power`, `Battery SoC`, `Battery Temperature`, `Battery Cycles` + `Battery ETA` (Text & Minuten).

**API**: `POST /api/v2/dataAccess/realtimeInfo/get` (Header `tokenId`, Body `{"wifiSn":"..."}`) der SolaX Cloud.

## Installation

### über HACS (empfohlen)
1. HACS → **Integrations** → **Custom repositories** → URL dieses Repos hinzufügen, Kategorie: *Integration*.
2. Integration installieren → HA neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → *SolaX Cloud (Multi)*.
4. `tokenId` eingeben.
5. In den **Optionen** Geräte hinzufügen (`wifiSn`, Anzeigename, Batterie-kWh, Intervall).

### manuell
Ordner `custom_components/solax_cloud_multi/` nach `/config/` kopieren → HA Neustart → Integration hinzufügen.

## Lovelace
Unter `lovelace/solax_dashboard.yaml` liegt eine fertige Ansicht (benötigt die HACS-Card **auto-entities**).

## Hinweise
- `Battery ETA` nutzt einfache Energie-Bilanz (ohne Effizienz/Begrenzungen).
- Ein gemeinsamer Token für alle Geräte; pro Gerät abweichende `wifiSn`.
- Polling-Intervall in Optionen (Standard 15 s).

---

MIT © 2025 empx92

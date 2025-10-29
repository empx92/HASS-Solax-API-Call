# HASS-Solax-API-Call
# SolaX Cloud (Multi) — Home Assistant Custom Integration

Pollt **mehrere** SolaX-Geräte (Cloud V2 API) parallel mit **einem tokenId** und je **eigener wifiSn**.
Erstellt Sensors je Gerät: `AC Power`, `Feed-in Power`, `Battery Power`, `Battery SoC`, `Battery Temperature`, `Battery Cycles` + `Battery ETA` (Text & Minuten).

**API**: `POST /api/v2/dataAccess/realtimeInfo/get` mit Header `tokenId` & JSON `{"wifiSn":"..."}`.

## Installation

### über HACS (empfohlen)
1. HACS → **Integrations** → **Custom repositories** → URL deines Repos hinzufügen, Kategorie: *Integration*.
2. Integration installieren → HA neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → *SolaX Cloud (Multi)*.
4. `tokenId` eingeben.
5. In den **Optionen** Geräte hinzufügen (`wifiSn`, Anzeigename, Batterie-kWh, Intervall).

### manuell
Ordner `custom_components/solax_cloud_multi/` in deinen `/config/` kopieren → HA Neustart → Integration hinzufügen.

## Lovelace
Unter `lovelace/solax_dashboard.yaml` liegt eine fertige Ansicht; Anleitung siehe unten.

## Hinweise
- `Battery ETA` nutzt einfache Energie = kWh × SoC / Leistung (keine Verluste/Begrenzungen).
- Polling-Intervall in den Optionen (Standard 15 s).
- Ein gemeinsamer Token für alle Geräte; pro Gerät abweichende `wifiSn`.

## Support
PRs willkommen 🙂

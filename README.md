<p align="center">
  <img src="https://raw.githubusercontent.com/pentafive/clublog-ha-bridge/main/images/logo.png" alt="ClubLog HA Bridge" width="400">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/pentafive/clublog-ha-bridge/releases"><img src="https://img.shields.io/github/v/release/pentafive/clublog-ha-bridge" alt="GitHub Release"></a>
  <a href="https://github.com/pentafive/clublog-ha-bridge/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pentafive/clublog-ha-bridge" alt="License"></a>
  <a href="https://github.com/pentafive/clublog-ha-bridge/actions/workflows/hacs-validation.yml"><img src="https://github.com/pentafive/clublog-ha-bridge/actions/workflows/hacs-validation.yml/badge.svg" alt="HACS Validation"></a>
</p>

Home Assistant integration for [ClubLog](https://clublog.org), the amateur radio community's premier DX logging and analysis platform. Track your DXCC progress across bands and modes, monitor propagation conditions, follow active DXpeditions, and automatically generate "still needed" watchlists that feed into [pskr-ha-bridge](https://github.com/pentafive/pskr-ha-bridge) and [wspr-ha-bridge](https://github.com/pentafive/wspr-ha-bridge) for real-time spot alerting.

> Data provided by [ClubLog](https://clublog.org). ClubLog is created and maintained by [Michael Wells, G7VJR](https://clublog.org). If you find ClubLog valuable, please consider [supporting the project](https://clublog.org/donate.php).

> **Disclaimer:** This project is independently developed and is not affiliated with, endorsed by, or connected to ClubLog or its maintainer. "ClubLog" is a service created by Michael Wells (G7VJR).

## Features

- **DXCC Progress Tracking** — Worked, confirmed, and verified entity counts
- **Most Wanted Rankings** — Global most wanted DXCC entity list with top 10 in attributes
- **Active Expeditions** — Track current DXpeditions with QSO counts
- **Callsign Monitor** — Activity summary (total QSOs, expedition status, OQRS, last upload)
- **Livestreams** — Active ClubLog livestreams with callsigns and URLs
- **Band Activity** — Propagation data based on actual logged QSOs
- **API Health** — Connectivity binary sensor with per-endpoint error tracking

## Installation

### Option A: HACS Integration (Recommended)

1. Install [HACS](https://hacs.xyz/) if not already installed
2. Add this repository as a custom repository in HACS
3. Install "ClubLog HA Bridge"
4. Restart Home Assistant
5. Go to Settings > Devices & Services > Add Integration > ClubLog

### Option B: Docker/MQTT Bridge

```bash
git clone https://github.com/pentafive/clublog-ha-bridge.git
cd clublog-ha-bridge
cp .env.example .env
# Edit .env with your ClubLog credentials and MQTT broker
docker compose up -d
```

## Configuration

### Required Credentials

| Setting | Description |
|---------|-------------|
| **Callsign** | Your amateur radio callsign |
| **API Key** | ClubLog API key ([request here](https://clublog.org/need_api.php)) |
| **Email** | Email associated with your ClubLog account |
| **Application Password** | Generated in ClubLog Settings > Application Passwords (not your main login password) |

### Polling Intervals

| Endpoint | Default | Notes |
|----------|---------|-------|
| DXCC Matrix | 60 min | Server caches for 60 minutes |
| Watch/Monitor | 10 min | Callsign activity summary |
| Most Wanted | Weekly | Updated infrequently (per G7VJR) |
| Activity Data | Daily | Updated only a few times per year |
| Expeditions | 60 min | Active DXpedition list |
| Livestreams | 10 min | Active livestream list |

All intervals include ±10% jitter to avoid synchronized polling bursts.

## Sensors

### DXCC Progress

| Sensor | Description |
|--------|-------------|
| `sensor.clublog_dxcc_worked` | Total DXCC entities worked |
| `sensor.clublog_dxcc_confirmed` | Total DXCC entities confirmed |
| `sensor.clublog_dxcc_verified` | Total DXCC entities verified (LoTW) |

### Expeditions & Livestreams

| Sensor | Description |
|--------|-------------|
| `sensor.clublog_active_expeditions` | Count of active DXpeditions (details in attributes) |
| `sensor.clublog_active_livestreams` | Count of active livestreams (details in attributes) |
| `sensor.clublog_most_wanted_count` | Total most wanted entities (top 10 in attributes) |

### Callsign Monitor

| Sensor | Description |
|--------|-------------|
| `sensor.clublog_watch_total_qsos` | Total QSOs uploaded to ClubLog |
| `sensor.clublog_watch_is_expedition` | Whether callsign is flagged as expedition |
| `sensor.clublog_watch_has_oqrs` | Whether OQRS is enabled |
| `sensor.clublog_watch_last_upload` | Timestamp of last log upload |

### Band Activity

| Sensor | Description |
|--------|-------------|
| `sensor.clublog_band_activity` | Number of active bands (per-band totals in attributes) |

### Diagnostics

| Sensor | Description |
|--------|-------------|
| `binary_sensor.clublog_api_status` | API connectivity (on = at least one endpoint succeeded recently) |
| `sensor.clublog_api_consecutive_errors` | Total consecutive API errors (disabled by default) |

## Related Projects

| Project | Description |
|---------|-------------|
| [pskr-ha-bridge](https://github.com/pentafive/pskr-ha-bridge) | PSKReporter spots > Home Assistant |
| [wspr-ha-bridge](https://github.com/pentafive/wspr-ha-bridge) | WSPR propagation data > Home Assistant |
| [8311-ha-bridge](https://github.com/pentafive/8311-ha-bridge) | AT&T ONT monitoring > Home Assistant |
| [web888-ha-bridge](https://github.com/pentafive/web888-ha-bridge) | KiwiSDR Web-888 > Home Assistant |
| [ntopng-ha-bridge](https://github.com/pentafive/ntopng-ha-bridge) | ntopng network monitoring > Home Assistant |

## Disclaimer

This project is independently developed and is not affiliated with, endorsed by, or connected to [ClubLog](https://clublog.org) or its maintainer. All ClubLog data is provided by the ClubLog API and remains the property of ClubLog. If you find ClubLog valuable, please consider [supporting the project](https://clublog.org/donate.php).

## License

MIT License - see [LICENSE](LICENSE) for details.

# ClubLog HA Bridge

Home Assistant integration for [ClubLog](https://clublog.org), the amateur radio community's premier DX logging and analysis platform. Track your DXCC progress across bands and modes, monitor propagation conditions, follow active DXpeditions, and automatically generate "still needed" watchlists that feed into [pskr-ha-bridge](https://github.com/pentafive/pskr-ha-bridge) and [wspr-ha-bridge](https://github.com/pentafive/wspr-ha-bridge) for real-time spot alerting.

## Features

- **DXCC Progress Tracking** — Worked, confirmed, and verified entity counts by band and mode
- **Most Wanted Rankings** — Global most wanted DXCC entity list
- **Active Expeditions** — Track current DXpeditions with QSO counts
- **Callsign Monitor** — Activity summary (QSOs, spots, skimmer) for your callsign
- **Band Activity** — Propagation data based on actual logged QSOs
- **Wanted List Generation** — Compute "still needed" DXCC/band combos for pskr and wspr bridges

## Installation

### Option A: HACS Integration (Recommended)

1. Install [HACS](https://hacs.xyz/) if not already installed
2. Add this repository as a custom repository in HACS
3. Install "ClubLog HA Bridge"
4. Restart Home Assistant
5. Go to Settings → Devices & Services → Add Integration → ClubLog

### Option B: Docker/MQTT Bridge

```bash
# Clone the repository
git clone https://github.com/pentafive/clublog-ha-bridge.git
cd clublog-ha-bridge

# Configure
cp .env.example .env
# Edit .env with your ClubLog credentials and MQTT broker

# Run
docker compose up -d
```

## Configuration

### Required Credentials

| Setting | Description |
|---------|-------------|
| **Callsign** | Your amateur radio callsign |
| **API Key** | ClubLog API key ([request here](https://clublog.org/need_api.php)) |
| **Email** | Email associated with your ClubLog account |
| **Application Password** | Generated in ClubLog Settings (not your main password) |

### Polling Intervals

| Endpoint | Default | Description |
|----------|---------|-------------|
| DXCC Matrix | 60 min | Your worked/confirmed/verified status (API caches for 60 min) |
| Watch/Monitor | 10 min | Callsign activity summary |
| Most Wanted | 24 hours | Global most wanted rankings |
| Activity Data | 60 min | Band propagation data |
| Expeditions | 60 min | Active DXpedition list |

## Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.clublog_dxcc_worked` | Total DXCC entities worked |
| `sensor.clublog_dxcc_confirmed` | Total DXCC entities confirmed |
| `sensor.clublog_dxcc_verified` | Total DXCC entities verified (LoTW) |

More sensors will be added as development continues.

## Related Projects

| Project | Description |
|---------|-------------|
| [pskr-ha-bridge](https://github.com/pentafive/pskr-ha-bridge) | PSKReporter spots → Home Assistant |
| [wspr-ha-bridge](https://github.com/pentafive/wspr-ha-bridge) | WSPR propagation data → Home Assistant |
| [8311-ha-bridge](https://github.com/pentafive/8311-ha-bridge) | AT&T ONT monitoring → Home Assistant |

## License

MIT License - see [LICENSE](LICENSE) for details.

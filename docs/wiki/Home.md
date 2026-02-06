<p align="center">
  <img src="https://raw.githubusercontent.com/pentafive/clublog-ha-bridge/main/images/logo.png" alt="ClubLog HA Bridge" width="400">
</p>

# ClubLog HA Bridge

Welcome to the ClubLog HA Bridge wiki!

> Data provided by [ClubLog](https://clublog.org), created and maintained by Michael Wells (G7VJR). This project is independently developed and is not affiliated with ClubLog.

## Quick Links

- [Dashboard Examples](Dashboard-Examples) - Lovelace card configurations
- [Troubleshooting](Troubleshooting) - Common issues and solutions
- [ClubLog Data](ClubLog-Data) - Understanding ClubLog API data

## Getting Started

### Installation

1. **HACS (Recommended)**
   - Add `https://github.com/pentafive/clublog-ha-bridge` as a custom repository
   - Install "ClubLog HA Bridge"
   - Restart Home Assistant
   - Add via Settings > Devices & Services > ClubLog

2. **Docker**
   ```bash
   git clone https://github.com/pentafive/clublog-ha-bridge.git
   cp .env.example .env
   docker compose up -d
   ```

### Required Credentials

You need four pieces of information from ClubLog:

| Credential | Where to Get It |
|------------|----------------|
| **API Key** | [Request here](https://clublog.org/need_api.php) or via ClubLog helpdesk |
| **Email** | Your ClubLog account email |
| **Application Password** | [ClubLog Settings > Application Passwords](https://clublog.org/edituser.php?tab=6) (NOT your login password) |
| **Callsign** | Your amateur radio callsign |

**Important:** Use an Application Password, not your main ClubLog login password. Application Passwords are designed for third-party integrations and can be revoked independently.

## Sensors Overview

### DXCC Progress (3 sensors)

| Sensor | Description |
|--------|-------------|
| DXCC Worked | Total DXCC entities with at least one QSO logged |
| DXCC Confirmed | Total DXCC entities confirmed (QSL received) |
| DXCC Verified | Total DXCC entities verified via LoTW |

### Expeditions & Community (3 sensors)

| Sensor | Description |
|--------|-------------|
| Active Expeditions | Count of active DXpeditions (list in attributes) |
| Active Livestreams | Count of active ClubLog livestreams (list in attributes) |
| Most Wanted Entities | Total DXCC entities in the most wanted list (top 10 in attributes) |

### Callsign Monitor (4 sensors)

| Sensor | Description |
|--------|-------------|
| Total QSOs | Total QSOs uploaded to your ClubLog account |
| Is Expedition | Whether your callsign is flagged as an expedition |
| Has OQRS | Whether Online QSL Request System is enabled |
| Last Upload | Timestamp of your last log upload |

### Band Activity (1 sensor)

| Sensor | Description |
|--------|-------------|
| Band Activity | Number of active bands with per-band QSO totals in attributes |

### Diagnostics (2 sensors)

| Sensor | Description |
|--------|-------------|
| API Status | Binary sensor — ON when ClubLog API is reachable |
| API Errors | Consecutive API error count with per-endpoint breakdown (disabled by default) |

## Polling Intervals

All intervals include ±10% random jitter to avoid synchronized polling bursts, as recommended by ClubLog's maintainer (G7VJR).

| Endpoint | Default | Rationale |
|----------|---------|-----------|
| DXCC Matrix | 60 min | Server caches responses for 60 minutes |
| Watch/Monitor | 10 min | Callsign activity summary |
| Most Wanted | Weekly | List changes infrequently |
| Activity Data | Daily | Updated only a few times per year |
| Expeditions | 60 min | Active DXpedition list |
| Livestreams | 10 min | Active livestream list |

## What's New in v0.2.0

- **12 sensors + 1 binary sensor** (was 3 sensors)
- **All 6 ClubLog endpoints** polled (was 3)
- **Polling jitter** on all intervals (per G7VJR)
- **User-Agent header** on all API requests (`clublog-ha-bridge/0.2.0`)
- **Device grouping** — all sensors grouped under one "ClubLog" device in HA
- **Rich attributes** — expedition lists, most wanted top 10, per-band activity, livestream URLs
- **Per-endpoint error tracking** — individual endpoint health in binary sensor attributes
- **Connection pooling** — uses HA's shared aiohttp session (HACS mode)
- **Attribution** — "Data provided by ClubLog (clublog.org)" on all entities
- **Docker parity** — Docker bridge publishes same sensors as HACS integration

## Support

- [GitHub Issues](https://github.com/pentafive/clublog-ha-bridge/issues)
- [Buy Me a Coffee](https://buymeacoffee.com/pentafive) — Support development of this and other HA integrations
- [ClubLog](https://clublog.org/)
- [Support ClubLog](https://clublog.org/donate.php) — If you find ClubLog valuable, please consider donating

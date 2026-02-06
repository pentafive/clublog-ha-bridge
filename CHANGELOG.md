# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-02-06

### Fixed
- Initial stagger bug: all endpoints now fetch on first coordinator cycle (was: only matrix fetched, others waited 5 minutes due to stagger vs 300s wake cycle)
- Watch `last_upload` key name: API uses `last_clublog_upload`, not `last_upload` (verified against live API responses)
- Null response guards on all endpoint fetches — prevents crash if API returns empty body

### Changed
- Application Password docs now link directly to `clublog.org/edituser.php?tab=6`
- Config flow app_password description shortened for cleaner UI
- Wiki uses logo image instead of icon for consistency with README

### Added
- Buy Me a Coffee link in README and wiki

## [0.2.0] - 2026-02-05

### Added
- 12 sensors + 1 binary sensor (up from 3 sensors)
- All 6 ClubLog API endpoints: DXCC matrix, watch/monitor, most wanted, expeditions, livestreams, band activity
- Expedition sensor with active DXpedition list in attributes
- Most wanted sensor with top 10 rankings in attributes
- Watch data sensors: total QSOs, expedition status, OQRS status, last upload timestamp
- Livestream sensor with active stream details in attributes
- Band activity sensor with per-band QSO totals in attributes
- API status binary sensor (connectivity, diagnostic category)
- API consecutive errors diagnostic sensor with per-endpoint breakdown
- Device grouping — all sensors appear under one "ClubLog" device in Home Assistant
- Rich attributes (expedition lists, most wanted top 10, per-band data, livestream URLs)
- Attribution on all entities ("Data provided by ClubLog (clublog.org)")
- User-Agent header on all API requests (`clublog-ha-bridge/0.2.0`)
- Polling jitter (±10% on all intervals) per G7VJR recommendation
- Staggered initial endpoint fetches to avoid startup burst
- Per-endpoint error tracking with consecutive error counts
- Connection pooling via `async_get_clientsession` (HACS mode)
- `requests.Session` with connection reuse (Docker mode)
- Wiki documentation: Home, Dashboard Examples, Troubleshooting, ClubLog Data

### Changed
- Coordinator rewritten: single coordinator with per-endpoint interval tracking (was: all endpoints on same timer)
- Most wanted default interval: weekly (was: 24 hours) per G7VJR guidance
- Activity default interval: daily (was: 60 minutes) per G7VJR guidance — data updated only a few times per year
- Application Password emphasis in config flow descriptions and documentation
- Docker bridge publishes all sensors matching HACS integration (was: 3 basic sensors)
- Docker bridge includes device config block on all MQTT discovery messages
- Docker bridge uses `json_attributes_topic` for rich sensor attributes

### Fixed
- `__init__.py` listed `Platform.BINARY_SENSOR` but `binary_sensor.py` didn't exist — HA would error on setup
- Coordinator created new `aiohttp.ClientSession` on every update instead of using HA's shared session

## [0.1.0] - 2026-02-02

### Added
- Initial project scaffold
- Dual-mode architecture: HACS integration + Docker/MQTT bridge
- HACS custom component skeleton (`custom_components/clublog/`)
- Docker bridge skeleton with polling loop placeholder
- ConfigFlow for ClubLog API key, email, Application Password, and callsign
- DataUpdateCoordinator skeleton for polling-based data fetching
- Sensor platform skeleton with proposed sensor definitions
- CI/CD workflows (Ruff linting, hassfest validation, HACS validation)
- Project documentation (README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

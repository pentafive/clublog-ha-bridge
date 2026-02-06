# Roadmap

Future enhancements for clublog-ha-bridge.

## Pre-Publication (before v0.2.0 release)

*Awaiting G7VJR approval on brand assets (sent 2026-02-05)*

- [ ] **Non-affiliation statement** — Clear statement in README that clublog-ha-bridge is an independent community project, not affiliated with or endorsed by ClubLog
- [ ] **ClubLog attribution** — Credit Michael Wells (G7VJR) as ClubLog creator/maintainer
- [ ] **ClubLog site link** — Link to [clublog.org](https://clublog.org) in README and docs
- [ ] **Donate page link** — Link to G7VJR's donate page so users can support ClubLog directly
- [ ] **Brand asset approval** — Confirm G7VJR is happy with icon/logo use of ClubLog globe
- [ ] **Push to Forgejo** — Review and push to git.pentafive.net
- [ ] **Unit tests** — Basic test coverage for API client and sensor definitions
- [ ] **PII scrub** — Final check for IPs, paths, credentials in code and git history

## v0.3.0 — Wanted List Generation

*Core feature: compute "still needed" DXCC/band combos from ClubLog matrix*

- [ ] **Wanted list computation** — Derive needed DXCC/band combos from DXCC matrix data
- [ ] **Wanted list export** — Write file for pskr-ha-bridge and wspr-ha-bridge consumption
- [ ] **Wanted list sensors** — Count of needed entities, progress percentage
- [ ] **Cross-bridge integration** — Document file format and mount paths for pskr/wspr

## v0.4.0 — Livestream & Expedition Alerting

- [ ] **Livestream alerting** — Cross-reference active livestreams with wanted list
- [ ] **Expedition tracking** — Alert when active DXpedition matches a needed entity
- [ ] **HA events** — `clublog_wanted_expedition` and `clublog_livestream` events for automations

## v0.5.0 — Adaptive Polling

- [ ] **Adaptive watch.php refresh** — Faster polling for active expeditions, slower for general callsigns (per G7VJR suggestion)
- [ ] **Rate limit detection** — Back off gracefully on 403, alert user

## v1.0.0 — Stable Release

- [ ] **HACS default registration** — Submit to hacs/default
- [ ] **HA brands submission** — Submit icon/logo to home-assistant/brands
- [ ] **Community posts** — HA Community, QRZ Forums
- [ ] **LinkedIn post** — Portfolio announcement
- [ ] **Full documentation** — Complete wiki, example automations, dashboard templates

## Future Considerations

- [ ] **Dashboard generator** — Web-based YAML generator (like pskr/wspr)
- [ ] **DXCC progress card** — Custom Lovelace card showing band/mode matrix
- [ ] **Multi-callsign support** — Track multiple callsigns (linked calls)
- [ ] **LoTW cross-reference** — Compare ClubLog confirmations with LoTW status

## Completed

### v0.2.0 (2026-02-05)
- [x] All 6 ClubLog API endpoints implemented
- [x] 12 sensors + 1 binary sensor
- [x] Per-endpoint polling with jitter (±10%)
- [x] User-Agent header on all requests
- [x] Application Password enforcement in config flow
- [x] Adjusted intervals per G7VJR guidance (most wanted weekly, activity daily)
- [x] Attribution on all entities
- [x] Wiki documentation
- [x] Brand assets created (icon + logo)

### v0.1.0 (2026-02-02)
- [x] Project scaffolded from pskr-ha-bridge template
- [x] Dual-mode architecture (HACS + Docker)
- [x] CI/CD workflows (Ruff, hassfest, HACS validation)
- [x] Community files (LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT)

---

*Last updated: 2026-02-05*

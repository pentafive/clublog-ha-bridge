# Dashboard Examples

This page provides Home Assistant dashboard examples for the ClubLog integration.

**Quick Links:**
- [DXCC Progress Cards](#dxcc-progress-cards)
- [Expedition & Livestream Cards](#expedition--livestream-cards)
- [Callsign Monitor Cards](#callsign-monitor-cards)
- [Health Monitoring Cards](#health-monitoring-cards)
- [Automations](#automations)
- [Entity Mapping (Docker vs HACS)](#entity-mapping-docker-vs-hacs)

## Required HACS Frontend Cards

For the full dashboard experience, install these cards from HACS:

| Card | Purpose | Install |
|------|---------|---------|
| [mushroom](https://github.com/piitaya/lovelace-mushroom) | Modern entity cards, chips, titles | HACS > Frontend |
| [mini-graph-card](https://github.com/kalkih/mini-graph-card) | Simple trend charts | HACS > Frontend |

**Minimum requirement:** The basic entities card works without custom cards.

---

## DXCC Progress Cards

### Basic Entities Card

```yaml
type: entities
title: ClubLog - DXCC Progress
entities:
  - entity: sensor.clublog_dxcc_worked
    name: Worked
  - entity: sensor.clublog_dxcc_confirmed
    name: Confirmed
  - entity: sensor.clublog_dxcc_verified
    name: Verified (LoTW)
```

### Glance Card

```yaml
type: glance
title: DXCC Progress
entities:
  - entity: sensor.clublog_dxcc_worked
    name: Worked
  - entity: sensor.clublog_dxcc_confirmed
    name: Confirmed
  - entity: sensor.clublog_dxcc_verified
    name: Verified
  - entity: binary_sensor.clublog_api_status
    name: API
```

### Mushroom Cards

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: ClubLog DXCC Progress
    subtitle: Worked / Confirmed / Verified

  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: sensor.clublog_dxcc_worked
        name: Worked
        icon_color: blue
      - type: custom:mushroom-entity-card
        entity: sensor.clublog_dxcc_confirmed
        name: Confirmed
        icon_color: green
      - type: custom:mushroom-entity-card
        entity: sensor.clublog_dxcc_verified
        name: Verified
        icon_color: purple
```

### DXCC Progress Trend

```yaml
type: custom:mini-graph-card
name: DXCC Progress (30 days)
entities:
  - entity: sensor.clublog_dxcc_worked
    name: Worked
    color: "#1E88E5"
  - entity: sensor.clublog_dxcc_confirmed
    name: Confirmed
    color: "#43A047"
  - entity: sensor.clublog_dxcc_verified
    name: Verified
    color: "#8E24AA"
hours_to_show: 720
points_per_hour: 0.04
line_width: 2
show:
  labels: true
  points: false
  legend: true
```

---

## Expedition & Livestream Cards

### Expeditions Overview

```yaml
type: entities
title: DXpeditions & Community
entities:
  - entity: sensor.clublog_active_expeditions
    name: Active Expeditions
  - entity: sensor.clublog_active_livestreams
    name: Active Livestreams
  - entity: sensor.clublog_most_wanted_count
    name: Most Wanted Entities
```

### Mushroom Expedition Chips

```yaml
type: custom:mushroom-chips-card
chips:
  - type: entity
    entity: sensor.clublog_active_expeditions
    name: Expeditions
    icon_color: orange
  - type: entity
    entity: sensor.clublog_active_livestreams
    name: Livestreams
    icon_color: red
  - type: entity
    entity: sensor.clublog_most_wanted_count
    name: Wanted
    icon_color: amber
```

### Expedition Details (Markdown)

Use a Markdown card to display expedition details from attributes:

```yaml
type: markdown
title: Active DXpeditions
content: >
  {% set exps = state_attr('sensor.clublog_active_expeditions', 'expeditions') %}
  {% if exps %}
  | Call | Date | QSOs |
  |------|------|------|
  {% for e in exps[:10] %}
  | {{ e.call }} | {{ e.date }} | {{ e.qso_count }} |
  {% endfor %}
  {% else %}
  No active expeditions.
  {% endif %}
```

---

## Callsign Monitor Cards

### Watch Data

```yaml
type: entities
title: ClubLog - Callsign Monitor
entities:
  - entity: sensor.clublog_watch_total_qsos
    name: Total QSOs
  - entity: sensor.clublog_watch_last_upload
    name: Last Upload
  - entity: sensor.clublog_watch_is_expedition
    name: Expedition Status
  - entity: sensor.clublog_watch_has_oqrs
    name: OQRS Enabled
```

### Band Activity

```yaml
type: entities
title: Band Activity
entities:
  - entity: sensor.clublog_band_activity
    name: Active Bands
```

The band activity sensor includes per-band QSO totals in its attributes. To display individual bands, use a Markdown card:

```yaml
type: markdown
title: Band Activity Breakdown
content: >
  {% set attrs = states.sensor.clublog_band_activity.attributes %}
  {% for key, value in attrs.items() if key.startswith('band_') %}
  - **{{ key | replace('band_', '') }}**: {{ value }} QSOs
  {% endfor %}
```

---

## Health Monitoring Cards

### Diagnostic Panel

```yaml
type: entities
title: ClubLog Health
show_header_toggle: false
entities:
  - entity: binary_sensor.clublog_api_status
    name: API Connectivity
  - entity: sensor.clublog_api_consecutive_errors
    name: API Errors
```

### Conditional Alert Card

```yaml
type: conditional
conditions:
  - entity: binary_sensor.clublog_api_status
    state: "off"
card:
  type: markdown
  content: |
    ## ClubLog API Unreachable
    No endpoint has succeeded in the last 2 hours.
    Check your credentials and network connectivity.
    Review `sensor.clublog_api_consecutive_errors` attributes for per-endpoint details.
```

---

## Automations

### Alert on API Failure

```yaml
automation:
  - alias: "ClubLog API Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.clublog_api_status
        to: "off"
        for:
          minutes: 30
    action:
      - service: notify.mobile_app
        data:
          title: "ClubLog Alert"
          message: "ClubLog API has been unreachable for 30 minutes"
```

### DXCC Milestone Alert

```yaml
automation:
  - alias: "DXCC Milestone"
    trigger:
      - platform: numeric_state
        entity_id: sensor.clublog_dxcc_confirmed
        above: 100
    action:
      - service: notify.mobile_app
        data:
          title: "DXCC Milestone!"
          message: "You now have {{ states('sensor.clublog_dxcc_confirmed') }} DXCC entities confirmed!"
```

### New Expedition Alert

```yaml
automation:
  - alias: "New Expedition Detected"
    trigger:
      - platform: numeric_state
        entity_id: sensor.clublog_active_expeditions
        above: 0
    action:
      - service: logbook.log
        data:
          name: "DXpedition"
          message: "{{ states('sensor.clublog_active_expeditions') }} active expedition(s)"
```

---

## Entity Mapping (Docker vs HACS)

Entity IDs differ between deployment methods due to how Home Assistant generates them.

### Docker Mode Entity IDs

Docker uses MQTT discovery with explicit `object_id`, producing predictable entity IDs:

| Sensor | Docker Entity ID |
|--------|-----------------|
| DXCC Worked | `sensor.clublog_dxcc_worked_total` |
| DXCC Confirmed | `sensor.clublog_dxcc_confirmed_total` |
| DXCC Verified | `sensor.clublog_dxcc_verified_total` |
| Active Expeditions | `sensor.clublog_active_expeditions` |
| Most Wanted | `sensor.clublog_most_wanted_count` |
| Total QSOs | `sensor.clublog_watch_total_qsos` |
| Is Expedition | `sensor.clublog_watch_is_expedition` |
| Has OQRS | `sensor.clublog_watch_has_oqrs` |
| Last Upload | `sensor.clublog_watch_last_upload` |
| Livestreams | `sensor.clublog_active_livestreams` |
| Band Activity | `sensor.clublog_band_activity` |
| API Errors | `sensor.clublog_api_consecutive_errors` |
| API Status | `binary_sensor.clublog_api_status` |

### HACS Mode Entity IDs

HACS uses `has_entity_name = True` with a device, so HA generates entity IDs from the device name and entity name. The format is typically:

`sensor.clublog_CALLSIGN_SENSOR_NAME`

For example, with callsign KD5QLM: `sensor.clublog_kd5qlm_dxcc_worked`

**Check your actual entity IDs** in Settings > Devices & Services > ClubLog after setup.

**Tip:** The dashboard YAML examples above use short names like `sensor.clublog_dxcc_worked`. Replace these with your actual entity IDs from the Entities list. Docker users should use the Docker entity IDs from the table above.

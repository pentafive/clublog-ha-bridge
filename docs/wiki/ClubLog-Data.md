# ClubLog Data

## What is ClubLog?

[ClubLog](https://clublog.org) is the amateur radio community's premier DX logging and analysis platform. Created and maintained by Michael Wells (G7VJR), it provides DXCC progress tracking, most wanted rankings, expedition monitoring, and QSO analysis tools used by thousands of amateur radio operators worldwide.

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Logging    │────▶│   ClubLog    │────▶│   ClubLog API   │
│   Software   │     │   Server     │     │  (JSON/REST)    │
│  (ADIF/LoTW) │     └──────────────┘     └────────┬────────┘
└─────────────┘                                    │
                                                   ▼
                                          ┌────────────────┐
                                          │ Home Assistant  │
                                          │  (This Bridge)  │
                                          └────────────────┘
```

1. **Log Uploads** — Operators upload QSO logs (ADIF files) to ClubLog
2. **Server Processing** — ClubLog computes DXCC status, rankings, activity data
3. **API Endpoints** — JSON REST API exposes computed data
4. **This Integration** — Polls API endpoints and creates HA sensors

## API Endpoints Used

This integration polls 6 ClubLog API endpoints:

### DXCC Matrix (`json_dxccchart.php`)

**Auth:** API key + email + Application Password
**Poll interval:** 60 minutes (server caches for 60 min)

Returns your DXCC progress as a matrix of entities and bands with status values:

| Status | Meaning |
|--------|---------|
| 1 | Confirmed (QSL received) |
| 2 | Worked (QSO logged but not confirmed) |
| 3 | Verified (confirmed via LoTW) |
| Missing | Not worked on that band |

The integration computes totals: how many unique DXCC entities you've worked, confirmed, and verified across all bands.

**Features:**
- Filterable by mode (All, CW, Phone, Data)
- Linked callsigns are combined automatically
- Satellite QSOs can be included/excluded

### Watch/Monitor (`watch.php`)

**Auth:** API key
**Poll interval:** 10 minutes

Returns detailed activity data for a callsign:

| Field | Description |
|-------|-------------|
| `clublog_info.total_qsos` | Total QSOs uploaded to ClubLog |
| `clublog_info.last_upload` | Timestamp of last log upload |
| `is_expedition` | Whether callsign is flagged as expedition |
| `has_oqrs` | Whether OQRS (Online QSL Request System) is enabled |
| QSOs by band/mode | 24-hour breakdown |
| Spots/skimmer by band | 24-hour breakdown |
| 7-day QSO totals | Daily counts |

**Important:** The API parameter is `call`, not `callsign`. Using `callsign` returns an empty response.

### Most Wanted (`mostwanted.php`)

**Auth:** None (public endpoint)
**Poll interval:** Weekly

Returns the global most wanted DXCC entity ranking as a dictionary of `{rank: ADIF_entity_code}`. Typically contains ~340 entities.

This list changes infrequently. ClubLog's maintainer (G7VJR) recommends weekly polling.

### Expeditions (`expeditions.php`)

**Auth:** None (public endpoint, undocumented — discovered via `?api=1`)
**Poll interval:** 60 minutes

Returns currently active DXpeditions as an array:

```json
[
  ["CALLSIGN", "2026-01-15", 12345],
  ["CALLSIGN2", "2026-02-01", 6789]
]
```

Each entry: `[callsign, start_date, qso_count]`

### Livestreams (`livestreams.php`)

**Auth:** None (public endpoint, undocumented — discovered via `?api=1`)
**Poll interval:** 10 minutes

Returns active ClubLog livestreams as an array:

```json
[
  ["CALLSIGN", 123, "2026-02-05", "https://clublog.org/livestream/CALLSIGN"]
]
```

Each entry: `[callsign, dxcc_code, date, url]`

### Activity (`activity_json.php`)

**Auth:** API key
**Poll interval:** Daily

Returns band activity data showing hourly QSO distribution by band. Must include `lastyear=1` parameter to avoid server timeout (504).

G7VJR notes this data is only updated a few times per year, so daily polling is more than sufficient.

## Data Freshness

| Data Type | How Often It Changes | Our Poll Rate |
|-----------|---------------------|---------------|
| DXCC Matrix | When you upload logs | 60 min (matches server cache) |
| Watch Data | When QSOs/spots occur | 10 min |
| Most Wanted | Rarely (big contest weekends) | Weekly |
| Activity | A few times per year | Daily |
| Expeditions | When DXpeditions start/end | 60 min |
| Livestreams | When streams start/stop | 10 min |

## DXCC Explained

DXCC (DX Century Club) is amateur radio's most prestigious operating award. It requires confirmed contacts with at least 100 DXCC "entities" (roughly countries/territories).

| Term | Meaning |
|------|---------|
| **Worked** | You made a QSO with a station in that entity |
| **Confirmed** | The contact is confirmed (QSL card or electronic) |
| **Verified** | Confirmed via Logbook of The World (LoTW) — ARRL's electronic system |
| **DXCC Entity** | A country, territory, or special area recognized by the ARRL |
| **Band** | Frequency range (160m, 80m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 6m) |
| **Mode** | Operating mode (CW, Phone/SSB, Data/FT8) |

There are currently ~340 active DXCC entities. Working all of them across multiple bands and modes is the pursuit of dedicated DXers.

## Rate Limiting

ClubLog enforces strict rate limits:

- **403 responses** indicate rate limiting or invalid credentials
- Excessive 403s can trigger an **IP-level firewall block**
- The integration **ceases all requests** on persistent failures
- All intervals include **±10% jitter** to prevent synchronized polling bursts
- The coordinator uses **staggered initial fetches** (5-second offsets) to avoid startup burst

## Cross-Project Integration

ClubLog data powers the "wanted list" concept across related bridges:

```
clublog-ha-bridge (DXCC matrix)
  → compute "still needed" DXCC/band combinations
  → export wanted list
      ↓
pskr-ha-bridge (filters PSKReporter spots for wanted entities)
wspr-ha-bridge (filters WSPR propagation data for wanted entities)
```

This enables automations like: "Alert me when PSKReporter spots a station in a DXCC entity I haven't confirmed on 20m."

## Related Resources

- [ClubLog](https://clublog.org/) — Official website
- [ARRL DXCC](https://www.arrl.org/dxcc) — DXCC award program
- [Logbook of The World](https://lotw.arrl.org/) — Electronic QSL confirmation
- [PSKReporter](https://pskreporter.info/) — Real-time spot reporting

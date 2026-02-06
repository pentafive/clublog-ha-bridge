# Troubleshooting

## Common Issues

### No Sensors Appearing

**Symptoms:** Integration added but no sensors show up in Home Assistant.

**Solutions:**
1. **Restart Home Assistant** — Required after initial HACS installation
2. **Check credentials** — Verify API key, email, and Application Password are correct
3. **Check logs** — Look for ClubLog errors in Home Assistant logs
4. **Wait for first poll** — Endpoints are staggered on startup (5-second intervals between each)

```yaml
# Enable debug logging
logger:
  default: info
  logs:
    custom_components.clublog: debug
```

### 403 Forbidden Error

**Symptoms:** Logs show "ClubLog API returned 403" errors.

**This is serious.** ClubLog uses 403 to indicate rate limiting, and excessive 403 responses can trigger an IP-level firewall block.

**Solutions:**
1. **Stop the integration immediately** — Disable the integration in HA or stop the Docker container
2. **Check credentials** — Invalid API key or Application Password triggers 403
3. **Check rate limits** — Make sure polling intervals are not too aggressive
4. **Wait** — If IP-blocked, wait 24 hours before retrying
5. **Contact G7VJR** — If the issue persists, contact ClubLog support via their helpdesk

**Prevention:**
- Never set DXCC Matrix interval below 3600 seconds (server caches for 60 min)
- Use Application Passwords, not your main login password
- The integration includes jitter on all intervals to avoid synchronized bursts

### API Status Binary Sensor Shows "Off"

**Symptoms:** `binary_sensor.clublog_api_status` is OFF.

The binary sensor turns OFF when no endpoint has succeeded in the last 2 hours.

**Diagnostic Steps:**
1. Check binary sensor attributes for per-endpoint details:
   - `{endpoint}_last_success` — timestamp of last successful fetch
   - `{endpoint}_errors` — consecutive error count
   - `{endpoint}_last_error` — error message
2. Check if ClubLog.org is accessible from your network
3. Check Home Assistant logs for specific error messages

### Application Password vs Login Password

**Symptoms:** Authentication failures despite correct-looking credentials.

ClubLog distinguishes between your **login password** (used to sign in to clublog.org) and **Application Passwords** (used for third-party integrations like this bridge).

**How to create an Application Password:**
1. Log in to [clublog.org](https://clublog.org)
2. Go to **Settings**
3. Find **Application Passwords** section
4. Generate a new Application Password
5. Copy it into the integration configuration

**Why Application Passwords?**
- Can be revoked independently without changing your login
- Don't expose your main password to third-party tools
- Recommended by ClubLog's maintainer (G7VJR)

### Empty Watch Data

**Symptoms:** Watch sensors show no data (Total QSOs = 0, etc.).

**Solutions:**
1. **Verify callsign** — The `watch.php` endpoint uses `call` (not `callsign`) as the parameter. The integration handles this correctly, but verify your callsign is entered exactly as registered on ClubLog.
2. **Check ClubLog account** — Make sure you have QSOs uploaded to your ClubLog account
3. **Wait for poll cycle** — Watch data polls every 10 minutes by default

### Most Wanted / Expeditions Show Zero

**Symptoms:** `sensor.clublog_most_wanted_count` or `sensor.clublog_active_expeditions` shows 0.

**Most Wanted:**
- This endpoint is public (no auth needed) and returns ~340 entities
- If it shows 0, check network connectivity to clublog.org
- Default poll interval is weekly — it may not have fetched yet on first startup

**Expeditions:**
- This shows currently active DXpeditions
- Zero is valid if no expeditions are currently active
- Check attributes for the expedition list

### Activity Data Timeout

**Symptoms:** Band activity sensor fails to update, logs show timeout errors.

The `activity_json.php` endpoint can timeout (504) if called without the `lastyear=1` parameter. The integration always includes this parameter, but if you see timeouts:

1. **Check network** — The response can be large
2. **Increase timeout** — This is an infrequent endpoint (daily default)
3. **G7VJR notes** — This data is only updated a few times per year, so daily polling is sufficient

## HACS Specific Issues

### Integration Not Found After Install

1. Fully restart Home Assistant (not just reload)
2. Clear browser cache
3. Check HACS download completed successfully

### "Custom Repository" Error

1. Verify URL: `https://github.com/pentafive/clublog-ha-bridge`
2. Select "Integration" as category
3. Check GitHub is accessible from your network

## Docker Specific Issues

### Container Exits Immediately

```bash
# Check logs
docker logs clublog-ha-bridge

# Common causes:
# - Missing required env vars (API_KEY, EMAIL, APP_PASSWORD, CALLSIGN, MQTT_BROKER)
# - Invalid MQTT broker address
```

### No MQTT Discovery in Home Assistant

1. **Enable MQTT discovery** — Settings > Devices & Services > MQTT > Configure
2. **Check broker connectivity** — Container must reach HA's MQTT broker
3. **Verify topics** — Check broker for `homeassistant/sensor/clublog/*/config`

### Sensors Not Grouped Under One Device

The Docker bridge includes `device` configuration in all MQTT discovery messages. All sensors should appear under a single "ClubLog (CALLSIGN)" device. If they don't:

1. Delete the old sensors from MQTT (publish empty payload to config topics)
2. Restart the container to re-publish discovery messages

## Debug Logging

### Enable Debug Mode

**HACS Integration:**
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.clublog: debug
    custom_components.clublog.coordinator: debug
```

**Docker:**
```bash
# .env
DEBUG_MODE=True
```

### Key Log Messages

| Message | Meaning |
|---------|---------|
| `Fetched matrix successfully` | DXCC matrix data received |
| `Fetched watch successfully` | Watch/monitor data received |
| `Error fetching {endpoint}` | API call failed (check error details) |
| `All attempted endpoints failed` | All endpoints in this cycle failed |
| `using cached data` | Failed endpoints using previous data |

## Getting Help

1. **Check existing issues**: [GitHub Issues](https://github.com/pentafive/clublog-ha-bridge/issues)
2. **Enable debug logging** and capture relevant logs
3. **Open new issue** with:
   - Home Assistant version
   - Integration version (0.2.0)
   - Deployment method (HACS or Docker)
   - Debug logs (scrub API keys and passwords!)
   - Steps to reproduce

## ClubLog Status

- **Website**: [clublog.org](https://clublog.org/)
- **Helpdesk**: Available via ClubLog website (maintained by G7VJR)
- **API**: No public status page — check website accessibility

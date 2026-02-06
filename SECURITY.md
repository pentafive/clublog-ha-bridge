# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in ClubLog HA Bridge, please report it responsibly:

1. **Do NOT open a public issue**
2. **Email**: pentafive@gmail.com with subject "clublog-ha-bridge Security Issue"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity, typically 1-4 weeks

## Security Considerations

### Credentials

- ClubLog API key, email, and Application Password are stored in environment variables (Docker) or HA config (HACS)
- **Never commit `.env` files** - only `.env.example` with placeholders
- Consider using Docker secrets or a secrets manager in production
- ClubLog auto-deletes API keys found in public repositories

### Network Security

- The bridge connects to ClubLog API (clublog.org) via HTTPS
- The bridge connects to your local MQTT broker (Docker mode only)
- Restrict network access to the bridge container if using Docker

### Rate Limiting

- ClubLog enforces strict rate limits
- Excessive requests result in 403 responses and potential IP firewall blocks
- The bridge respects configured poll intervals and ceases requests on 403
- Do not decrease poll intervals below recommended minimums

### Data Privacy

- Amateur radio callsigns are inherently public information
- ClubLog data includes DXCC progress and QSO statistics
- No personal data beyond callsigns is transmitted or stored beyond what the API provides
- Debug mode may log API responses containing callsign data
- Keep `DEBUG_MODE=False` in production
- Review logs before sharing in issue reports

## Scope

This security policy covers:
- The `clublog-ha-bridge.py` script
- The `custom_components/clublog/` HACS integration
- Docker configuration files
- Example configurations

It does NOT cover:
- ClubLog.org service security
- Home Assistant security
- MQTT broker security

# Pull Request

## Summary
<!-- Short description of the changes. -->

## Changes

- Authentication & session reuse
- API error handling and one-time re-auth on error code
- Stable unique IDs (UnitId-based)
- Sensor state class corrections (totals vs measurements)
- Config flow enhancements (URL normalization, duplicate prevention, error differentiation)
- Added device_info for grouping
- Added constants (DEFAULT_URL, PLATFORMS)
- New translation keys (auth_failed, already_configured, unexpected_response)
- Version bump to 0.0.3

## Rationale

Improves robustness, reduces server load, and clarifies user setup feedback while stabilizing entity identity.

## Backwards Compatibility

Unique ID pattern changed; existing entities may appear as new ones. If migration is desired, maintainers can opt to revert unique ID composition or implement a registry migration.

## Testing

- Manual inspection of API client logic
- Guarded against empty/malformed meter values

## Follow-ups (Optional)

- Token-based login if anti-forgery token enforcement appears
- Options flow (scan interval)
- Diagnostics endpoint
- Entity migration for legacy IDs

## Checklist

- [ ] I have reviewed README changes
- [ ] Translation keys exist for new errors
- [ ] Version updated in manifest.json
- [ ] No secrets in diffs

/cc @sillymoi @AndersMarkoff

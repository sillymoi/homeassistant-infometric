# Changelog

All notable changes to this project will be documented in this file.

## [0.0.3] - 2025-10-28

### Added

- Device grouping via `device_info` for sensors.
- New translation keys: `auth_failed`, `already_configured`, `unexpected_response`.
- Constants: `DEFAULT_URL`, `PLATFORMS`.

### Changed

- Stable unique IDs now based solely on `UnitId`.
- Config flow: URL normalization, duplicate prevention, clearer error mapping.
- Sensor state classes: Monthly average & prognosis set to `MEASUREMENT`.
- Improved API client with session reuse and one-time re-auth on API error code.

### Fixed

- Removed incorrect usage of `resp.ok` in API client; now checks HTTP status.
- Guarded against empty/malformed meter value arrays.
- Clean unload of config entry data.

## [0.0.2]

- Small adaptations to the Infometric API.
- Uplift to Home Assistant 2025.5.3.
- Support for hot and cold water.
- Support of HACS installation.
- Removal of hardcoded meters.

## [0.0.1]

- Initial Release.

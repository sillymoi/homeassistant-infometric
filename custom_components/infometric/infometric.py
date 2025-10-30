"""Lightweight Infometric Panorama API client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Dict
import logging

from aiohttp import ClientSession, ClientError

_LOGGER = logging.getLogger(__name__)


class InfometricException(Exception):
    """Base exception for Infometric client errors."""


@dataclass
class InfometricMeter:
    """Represents a single meter returned by the API."""

    id: str
    name: str
    label: str
    average: float
    prognosis: float
    last_values: List[Dict[str, Any]]


class InfometricClient:
    """Client handling authentication and data retrieval."""

    def __init__(self, url: str, username: str, password: str) -> None:
        # Normalize base URL (strip trailing slash)
        self._base_url = url.rstrip("/")
        self._username = username
        self._password = password
        self._session: ClientSession | None = None
        self._authenticated: bool = False

    async def authenticate(self, session: ClientSession) -> bool:
        """Authenticate against the Panorama site.

        NOTE: This is a simplified form login. It may need enhancement
        with hidden token parsing if the site introduces anti-forgery tokens.
        """
        self._session = session
        login_payload = {
            "UserName": self._username,
            "Password": self._password,
            "RememberMe": "true",
            "commit": "Logga in",
        }
        try:
            resp = await self._session.post(
                url=self._base_url,
                data=login_payload,
            )
        except ClientError as err:
            raise InfometricException(f"Network error during authenticate: {err}") from err
        except Exception as err:  # pragma: no cover - unexpected
            raise InfometricException(f"Unexpected error during authenticate: {err}") from err

        if 200 <= resp.status < 300:
            self._authenticated = True
            _LOGGER.debug("Authenticated to Infometric (status %s)", resp.status)
            return True

        text = await resp.text()
        raise InfometricException(
            f"Authentication failed (status {resp.status}): {text[:120]}"
        )

    async def get_meters(self) -> List[InfometricMeter]:
        """Retrieve and parse meters data.

        If the API returns an auth-related error code, one re-auth attempt
        will be made automatically.
        """
        if not self._session:
            raise InfometricException("Session not initialized. Call authenticate first.")

        try:
            resp = await self._session.post(
                url=f"{self._base_url}/Consumption/GetMeasureTypes"
            )
        except ClientError as err:
            raise InfometricException(f"Network error during get_meters: {err}") from err
        except Exception as err:  # pragma: no cover
            raise InfometricException(f"Unexpected error during get_meters: {err}") from err

        if resp.status != 200:
            body = await resp.text()
            raise InfometricException(
                f"GetMeasureTypes failed (status {resp.status}): {body[:120]}"
            )

        data = await resp.json(content_type=None)

        # Handle potential error structure {"result": false, "message": "5004"}
        if isinstance(data, dict) and data.get("result") is False:
            code = data.get("message")
            _LOGGER.warning(
                "Infometric API returned error code %s; attempting re-auth once", code
            )
            # Try a single re-auth if previously authenticated
            if self._authenticated:
                self._authenticated = False
                await self.authenticate(self._session)
                return await self.get_meters()
            raise InfometricException(f"API returned error code {code}")

        meters: List[InfometricMeter] = []
        for raw in data:
            try:
                last_values_raw = raw.get("LastOKValues") or []
                # Build structured list; guard missing keys
                last_values = [
                    {
                        "series": lv.get("SeriesId"),
                        "time": lv.get("Date"),
                        "value": lv.get("Value"),
                    }
                    for lv in last_values_raw
                ]
                average = raw.get("AverageConsumption") or 0
                prognosis = raw.get("PrognosConsumption") or 0
                meters.append(
                    InfometricMeter(
                        id=str(raw.get("UnitId")),
                        label=str(raw.get("UnitLabel")),
                        name=str(raw.get("Name")),
                        average=float(average) if str(average).strip() else 0.0,
                        prognosis=float(prognosis) if str(prognosis).strip() else 0.0,
                        last_values=last_values,
                    )
                )
            except (ValueError, TypeError) as parse_err:
                _LOGGER.warning(
                    "Skipping malformed meter entry %s: %s", raw, parse_err
                )
        _LOGGER.debug("Parsed %d Infometric meters", len(meters))
        return meters

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import REQUEST_TIMEOUT


class DaikinOneError(Exception):
    """Base error for the Daikin One Local API."""


class DaikinOneConnectionError(DaikinOneError):
    """The thermostat could not be reached."""


class DaikinOneRequestError(DaikinOneError):
    """The thermostat answered with error: true."""


class DaikinOneClient:
    """Talks to one thermostat over HTTP."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"

    async def _request(
        self, method: str, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        form = {k: str(v) for k, v in data.items()} if data else None
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.request(
                    method, f"{self._base}{path}", data=form
                ) as resp:
                    resp.raise_for_status()
                    body = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise DaikinOneConnectionError(f"{method} {path} failed: {err}") from err
        except ValueError as err:
            raise DaikinOneError(f"{method} {path} returned invalid JSON") from err

        if isinstance(body, dict) and body.get("error"):
            raise DaikinOneRequestError(body.get("reason", "unknown error"))
        return body

    async def get_api_info(self) -> dict[str, Any]:
        """GET / : api_ver, type, model, brand, firmware."""
        return await self._request("GET", "/")

    async def get_status(self) -> dict[str, Any]:
        """GET /query/info : mode, setpoints, temperature, humidity, state."""
        return await self._request("GET", "/query/info")

    async def set_control(self, **params: Any) -> None:
        """POST /control : mode, fan, heatSetpoint, coolSetpoint. Omitted keys are unchanged."""
        await self._request("POST", "/control", params)

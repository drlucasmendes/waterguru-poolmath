"""PoolMath API client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_URL, CLIENT_VERSION, ORIGIN


class PoolMathError(Exception):
    """Base PoolMath API error."""


class PoolMathAuthError(PoolMathError):
    """PoolMath authentication failed."""


class PoolMathRequestError(PoolMathError):
    """PoolMath request failed."""


@dataclass(slots=True)
class PoolMathResult:
    """Result of a PoolMath test-log submission."""

    status: int
    log_id: str | None
    response: dict[str, Any]


class PoolMathClient:
    """Minimal asynchronous client for PoolMath's test-log endpoint."""

    def __init__(self, session: ClientSession, authorization: str, pool_id: str) -> None:
        self._session = session
        self._authorization = authorization.strip()
        self._pool_id = pool_id.strip()

    async def async_submit_testlog(
        self,
        *,
        fc: float,
        ph: float,
        water_temp_f: float,
        log_timestamp: str,
    ) -> PoolMathResult:
        """Submit one test log to PoolMath."""
        payload: dict[str, Any] = {
            "type": "testlog",
            "fc": fc,
            "cc": None,
            "cya": None,
            "ch": None,
            "ph": ph,
            "ta": None,
            "salt": None,
            "bor": None,
            "tds": None,
            "csi": None,
            "waterTemp": water_temp_f,
            "waterTempUnits": 0,
            "poolId": self._pool_id,
            "logTimestamp": log_timestamp,
            "weather": None,
            "weatherLogId": None,
            "userId": None,
            "origin": ORIGIN,
            "id": None,
            "_ts": -62135596800,
            "deleted": False,
        }
        headers = {
            "Authorization": self._authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "x-clientversion": CLIENT_VERSION,
        }

        try:
            async with self._session.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=30,
            ) as response:
                if response.status in (401, 403):
                    raise PoolMathAuthError(
                        f"PoolMath rejected the authorization header (HTTP {response.status})"
                    )
                response.raise_for_status()
                try:
                    data = await response.json(content_type=None)
                except (ValueError, TypeError) as err:
                    body = (await response.text())[:500]
                    raise PoolMathRequestError(
                        f"PoolMath returned a non-JSON response: {body}"
                    ) from err
        except PoolMathError:
            raise
        except ClientResponseError as err:
            raise PoolMathRequestError(
                f"PoolMath request failed with HTTP {err.status}"
            ) from err
        except (ClientError, TimeoutError) as err:
            raise PoolMathRequestError(f"Could not reach PoolMath: {err}") from err

        log_data = data.get("log", {}) if isinstance(data, dict) else {}
        return PoolMathResult(
            status=response.status,
            log_id=log_data.get("id"),
            response=data,
        )

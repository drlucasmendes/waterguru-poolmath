"""PoolMath API client."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import (
    API_AUTH_URL,
    API_POOLS_URL,
    API_TESTLOGS_URL,
    CLIENT_VERSION,
    LOGIN_DEVICE_NAME,
    ORIGIN,
)


class PoolMathError(Exception):
    """Base PoolMath API error."""


class PoolMathAuthError(PoolMathError):
    """PoolMath authentication failed."""


class PoolMathRequestError(PoolMathError):
    """PoolMath request failed."""


class PoolMathNoPoolsError(PoolMathError):
    """PoolMath account has no active pools."""


@dataclass(slots=True)
class PoolMathLoginResult:
    """Result of PoolMath email/password authentication."""

    authorization: str
    user_id: str
    default_pool_id: str | None


@dataclass(slots=True)
class PoolMathPool:
    """A PoolMath pool available to the account."""

    pool_id: str
    name: str
    volume: float | None
    volume_unit: int | None

    @property
    def display_name(self) -> str:
        """Return a useful display label."""
        if self.volume is None:
            return self.name
        unit = "gal" if self.volume_unit == 0 else "L"
        return f"{self.name} — {self.volume:g} {unit}"


@dataclass(slots=True)
class PoolMathResult:
    """Result of a PoolMath test-log submission."""

    status: int
    log_id: str | None
    response: dict[str, Any]


class PoolMathClient:
    """Asynchronous client for PoolMath's mobile-app API."""

    def __init__(
        self,
        session: ClientSession,
        authorization: str | None = None,
        pool_id: str | None = None,
    ) -> None:
        self._session = session
        self._authorization = authorization.strip() if authorization else None
        self._pool_id = pool_id.strip() if pool_id else None

    @staticmethod
    def _base_headers() -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "x-clientversion": CLIENT_VERSION,
        }

    @staticmethod
    def _build_basic_authorization(user_id: str, token: str) -> str:
        raw = f"{user_id}:{token}".encode("utf-8")
        encoded = base64.b64encode(raw).decode("ascii")
        return f"Basic {encoded}"

    @staticmethod
    def _select_authorization_token(
        authorizations: list[dict[str, Any]],
    ) -> str:
        usable = [item for item in authorizations if item.get("token")]
        if not usable:
            raise PoolMathAuthError("PoolMath login returned no authorization token")

        named = [
            item for item in usable
            if item.get("name") == LOGIN_DEVICE_NAME
        ]
        candidates = named or usable

        def sort_key(item: dict[str, Any]) -> datetime:
            value = item.get("timestamp")
            if not value:
                return datetime.min
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return datetime.min

        return max(candidates, key=sort_key)["token"]

    async def async_login(
        self,
        *,
        email: str,
        password: str,
    ) -> PoolMathLoginResult:
        """Authenticate with PoolMath and create a Basic authorization value."""
        payload = {
            "provider": "tfp",
            "token": None,
            "user": email.strip(),
            "pwd": password,
            "device": LOGIN_DEVICE_NAME,
        }

        try:
            async with self._session.post(
                API_AUTH_URL,
                headers=self._base_headers(),
                json=payload,
                timeout=30,
            ) as response:
                if response.status in (401, 403):
                    raise PoolMathAuthError("Invalid PoolMath email or password")
                response.raise_for_status()
                data = await response.json(content_type=None)
        except PoolMathError:
            raise
        except ClientResponseError as err:
            raise PoolMathRequestError(
                f"PoolMath login failed with HTTP {err.status}"
            ) from err
        except (ClientError, TimeoutError, ValueError, TypeError) as err:
            raise PoolMathRequestError(f"Could not log in to PoolMath: {err}") from err

        user_id = data.get("userId")
        if not user_id:
            raise PoolMathAuthError("PoolMath login response did not contain userId")

        token = self._select_authorization_token(data.get("authorizations", []))
        authorization = self._build_basic_authorization(user_id, token)
        return PoolMathLoginResult(
            authorization=authorization,
            user_id=user_id,
            default_pool_id=data.get("defPoolId"),
        )

    async def async_get_pools(
        self,
        authorization: str | None = None,
    ) -> list[PoolMathPool]:
        """Return active pools available to the authorization."""
        auth = (authorization or self._authorization or "").strip()
        if not auth:
            raise PoolMathAuthError("PoolMath authorization is missing")

        headers = self._base_headers()
        headers["Authorization"] = auth

        try:
            async with self._session.post(
                API_POOLS_URL,
                headers=headers,
                data=b"",
                timeout=30,
            ) as response:
                if response.status in (401, 403):
                    raise PoolMathAuthError(
                        f"PoolMath rejected the authorization (HTTP {response.status})"
                    )
                response.raise_for_status()
                data = await response.json(content_type=None)
        except PoolMathError:
            raise
        except ClientResponseError as err:
            raise PoolMathRequestError(
                f"PoolMath pool discovery failed with HTTP {err.status}"
            ) from err
        except (ClientError, TimeoutError, ValueError, TypeError) as err:
            raise PoolMathRequestError(
                f"Could not retrieve PoolMath pools: {err}"
            ) from err

        pools: list[PoolMathPool] = []
        for item in data.get("results", []):
            if item.get("deleted"):
                continue
            pool_id = item.get("id")
            name = item.get("name")
            if not pool_id or not name:
                continue
            pools.append(
                PoolMathPool(
                    pool_id=pool_id,
                    name=name,
                    volume=item.get("volume"),
                    volume_unit=item.get("poolVolumeUnit"),
                )
            )

        if not pools:
            raise PoolMathNoPoolsError("No active PoolMath pools were found")
        return pools

    async def async_submit_testlog(
        self,
        *,
        values: dict[str, float],
        log_timestamp: str,
    ) -> PoolMathResult:
        """Submit one test log to PoolMath."""
        if not self._authorization or not self._pool_id:
            raise PoolMathRequestError("PoolMath client is missing authorization or pool ID")

        payload: dict[str, Any] = {
            "type": "testlog",
            "fc": values["fc"],
            "cc": values.get("cc"),
            "cya": values.get("cya"),
            "ch": values.get("ch"),
            "ph": values["ph"],
            "ta": values.get("ta"),
            "salt": values.get("salt"),
            "bor": values.get("bor"),
            "tds": values.get("tds"),
            "csi": values.get("csi"),
            "waterTemp": values["water_temp_f"],
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
        headers = self._base_headers()
        headers["Authorization"] = self._authorization

        try:
            async with self._session.post(
                API_TESTLOGS_URL,
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

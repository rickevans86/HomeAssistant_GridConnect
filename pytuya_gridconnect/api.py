"""Grid Connect cloud API client (Tuya mobile-app "api.json" protocol).

Synchronous, built on :mod:`requests`. The Home Assistant integration wraps calls
in an executor; the CLI uses it directly.

Flow
----
1. ``login_email`` -> ``*.user.email.token.create`` (gets an ephemeral RSA key),
   then ``*.user.email.password.login`` with the RSA-wrapped password. The reply
   is a ``User`` carrying ``sid`` (session) and ``ecode`` (et=3 body key salt).
2. ``homes`` -> ``m.life.home.space.list`` -> the ``gid`` of each home.
3. ``devices`` -> ``thing.m.my.group.device.list`` (per ``gid``) -> every device,
   including its ``localKey`` (for LocalTuya / tinytuya) and current ``dps``.
4. ``get_dps`` / ``set_dps`` -> ``thing.m.device.dp.*`` to read/write datapoints.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import requests

from . import crypto
from .const import (
    APP_KEY,
    APP_VERSION,
    DEFAULT_REGION,
    REGIONS,
    SDK_VERSION,
    TTID,
)


class GridConnectError(Exception):
    """A Grid Connect / Tuya cloud request failed."""


@dataclass
class Device:
    """One device as returned by the device list."""

    dev_id: str
    name: str
    local_key: str
    product_id: str
    category: str
    online: bool
    icon: str | None
    gid: int
    dps: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: dict[str, Any], gid: int) -> "Device":
        return cls(
            dev_id=d.get("devId") or d.get("id") or "",
            name=d.get("name", ""),
            local_key=d.get("localKey", ""),
            product_id=d.get("productId", ""),
            category=d.get("category", ""),
            online=bool(d.get("isOnline", d.get("online", False))),
            icon=d.get("iconUrl") or d.get("icon"),
            gid=gid,
            dps=d.get("dps", {}) or {},
            raw=d,
        )


@dataclass
class _Session:
    sid: str = ""
    ecode: str | None = None
    uid: str = ""


class GridConnectCloud:
    """Client for one Grid Connect account."""

    def __init__(
        self,
        country_code: str = "61",
        region: str = DEFAULT_REGION,
        *,
        lang: str = "en",
        timeout: float = 20.0,
        session: requests.Session | None = None,
    ) -> None:
        self.country_code = country_code
        self.region = region
        self.endpoint = REGIONS[region]
        self.lang = lang
        self.timeout = timeout
        self._http = session or requests.Session()
        self._sess = _Session()
        self._chkey = crypto.channel_key()

    # ---- low-level request -------------------------------------------------

    def _call(
        self,
        api: str,
        version: str,
        post_data: dict[str, Any] | None = None,
        *,
        session_required: bool = True,
        extra_url: dict[str, str] | None = None,
    ) -> Any:
        """Build, sign, send one api.json call and return the decoded ``result``."""
        wire_api = ("smartlife" + api[5:]) if api.startswith("thing") else api
        request_id = str(uuid.uuid4())

        params: dict[str, str] = {
            "a": wire_api,
            "v": version,
            "clientId": APP_KEY,
            "os": "Android",
            "lang": self.lang,
            "ttid": TTID,
            "appVersion": APP_VERSION,
            "sdkVersion": SDK_VERSION,
            "time": str(int(time.time())),
            "requestId": request_id,
            "et": "3",
            "cp": "gzip",
            "chKey": self._chkey,
        }
        if session_required and self._sess.sid:
            params["sid"] = self._sess.sid
        if extra_url:
            params.update(extra_url)

        if post_data is not None:
            plain = json.dumps(post_data, separators=(",", ":"))
            ecode = self._sess.ecode if session_required else None
            body_key = crypto.derive_body_key(request_id, ecode)
            params["postData"] = crypto.encrypt_body(body_key, plain)

        params["sign"] = crypto.sign(params)

        try:
            resp = self._http.post(
                self.endpoint,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            envelope = resp.json()
        except (requests.RequestException, ValueError) as err:
            raise GridConnectError(f"{api}: transport error: {err}") from err

        if not envelope.get("success"):
            code = envelope.get("errorCode") or envelope.get("errorMsg") or envelope
            raise GridConnectError(f"{api}: {code}")

        result = envelope.get("result")
        if isinstance(result, str) and result:
            # et=3 encrypts the reply with the same per-request key.
            ecode = self._sess.ecode if session_required else None
            body_key = crypto.derive_body_key(request_id, ecode)
            try:
                result = json.loads(crypto.decrypt_body(body_key, result))
            except Exception as err:  # noqa: BLE001 - surface any decrypt/JSON failure
                raise GridConnectError(f"{api}: cannot decrypt reply: {err}") from err
        return result

    # ---- auth --------------------------------------------------------------

    def login_email(self, email: str, password: str) -> None:
        """Log in with a Grid Connect email + password; populates the session."""
        token_info = self._call(
            "thing.m.user.email.token.create",
            "1.0",
            {"countryCode": self.country_code, "email": email},
            session_required=False,
        )
        passwd = crypto.encrypt_password(
            password, token_info["publicKey"], token_info["exponent"]
        )
        user = self._call(
            "thing.m.user.email.password.login",
            "3.0",
            {
                "countryCode": self.country_code,
                "email": email,
                "passwd": passwd,
                "token": token_info["token"],
                "ifencrypt": 1,
                "options": '{"group": 1}',
            },
            session_required=False,
        )
        self._sess = _Session(
            sid=user.get("sid", ""),
            ecode=user.get("ecode"),
            uid=user.get("uid", ""),
        )
        if not self._sess.sid:
            raise GridConnectError("login succeeded but no session id returned")

    @property
    def logged_in(self) -> bool:
        return bool(self._sess.sid)

    # ---- devices -----------------------------------------------------------

    def homes(self) -> list[dict[str, Any]]:
        """Return the account's homes (each has a ``gid``)."""
        result = self._call("m.life.home.space.list", "1.0", {}) or []
        return result if isinstance(result, list) else result.get("list", [])

    def devices(self, gid: int | None = None) -> list[Device]:
        """Return every device across all homes, or just one home's ``gid``."""
        gids = [gid] if gid is not None else [h.get("gid") for h in self.homes()]
        out: list[Device] = []
        for g in gids:
            if g is None:
                continue
            result = self._call(
                "thing.m.my.group.device.list",
                "2.1",
                {},
                extra_url={"gid": str(g)},
            ) or []
            for item in result:
                out.append(Device.from_json(item, int(g)))
        return out

    def get_dps(self, dev_id: str) -> dict[str, Any]:
        """Read the live datapoints of one device."""
        result = self._call(
            "thing.m.device.dp.get", "1.0", {"devId": dev_id}
        )
        if isinstance(result, dict):
            return result.get("dps", result)
        return {}

    def set_dps(self, dev_id: str, dps: dict[str, Any]) -> None:
        """Write one or more datapoints, e.g. ``{"1": True}`` to turn a plug on."""
        self._call(
            "thing.m.device.dp.publish",
            "1.0",
            {"devId": dev_id, "dps": json.dumps(dps, separators=(",", ":"))},
        )

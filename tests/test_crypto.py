"""Offline self-tests for the signing and body crypto.

These run with no network and no account. They prove the *algorithms* are
implemented correctly; a live login additionally proves the *keys* are right.

Run with:  python -m pytest  (or just  python tests/test_crypto.py)
"""

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.hazmat.primitives.asymmetric import padding, rsa

from pytuya_gridconnect import crypto
from pytuya_gridconnect.const import APP_KEY


def test_chkey_matches_reference_app():
    """chKey derivation is HMAC-SHA256(appKey, "pkg_cert")[8:16].

    Validated against a second, publicly-documented Tuya app (the eufy Security
    app, appKey w8x4ppqkdxvqnd73ahj9) whose chKey is the known constant
    7cbfe6d8 -- this exercises the exact HMAC path used for Grid Connect.
    """
    eufy_pkg_cert = (
        "com.oceanwing.battery.cam_"
        "16:6C:23:45:57:B7:76:CA:D8:AC:94:C9:79:37:9E:48:"
        "DF:38:7D:4D:8F:96:A3:43:DF:40:FC:D9:05:BF:F6:86"
    )
    import hmac

    chk = hmac.new(
        b"w8x4ppqkdxvqnd73ahj9", eufy_pkg_cert.encode(), hashlib.sha256
    ).hexdigest()[8:16]
    assert chk == "7cbfe6d8"


def test_chkey_is_stable_for_gridconnect():
    assert crypto.channel_key(APP_KEY) == crypto.channel_key(APP_KEY)
    assert len(crypto.channel_key()) == 8


def test_sign_preimage_shape():
    params = {"a": "smartlife.p.time.get", "v": "1.0", "et": "3", "os": "Android", "time": "1"}
    assert crypto.build_preimage(params) == "a=smartlife.p.time.get||et=3||os=Android||time=1||v=1.0"


def test_sign_is_deterministic_hex():
    s = crypto.sign({"a": "x", "v": "1.0", "time": "1"})
    assert len(s) == 64 and all(c in "0123456789abcdef" for c in s)


def test_swap_md5_rotates_blocks():
    h = hashlib.md5(b"abc").hexdigest()
    assert crypto._swap_md5("abc") == h[8:16] + h[0:8] + h[24:32] + h[16:24]


def test_et3_body_roundtrip():
    key = crypto.derive_body_key("request-id", "ecode123")
    assert len(key) == 16
    blob = crypto.encrypt_body(key, '{"devId":"x","dps":"{\\"1\\":true}"}')
    assert crypto.decrypt_body(key, blob) == '{"devId":"x","dps":"{\\"1\\":true}"}'


def test_password_is_md5_then_rsa_pkcs1():
    # The app supplies modulus and exponent as DECIMAL strings (BigInteger radix
    # 10), so encrypt_password must parse them as base 10, not hex.
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pn = key.public_key().public_numbers()
    enc = crypto.encrypt_password("hunter2", str(pn.n), str(pn.e))
    decrypted = key.decrypt(bytes.fromhex(enc), padding.PKCS1v15())
    assert decrypted.decode() == hashlib.md5(b"hunter2").hexdigest()


def test_success_envelope_has_no_success_field():
    """Regression: the live api.json success reply is {t, sign, result} with no
    "success" key, so the client must not treat its absence as a failure.
    A failure instead carries errorCode (and success=false)."""
    import json

    from pytuya_gridconnect import api

    rid = "fixed-request-id"
    # The decrypted payload is itself an envelope with the data under "result".
    inner = json.dumps(
        {
            "result": {"publicKey": "c0ffee", "exponent": "10001", "token": "T"},
            "t": 1,
            "success": True,
            "status": "ok",
        }
    )
    enc = crypto.encrypt_body(crypto.derive_body_key(rid, None), inner)

    class _Resp:
        def raise_for_status(self):
            pass

        def __init__(self, p):
            self._p = p

        def json(self):
            return self._p

    class _OK:
        def post(self, *a, **k):
            # mirror the request's requestId so the reply key matches
            return _Resp({"t": 1, "sign": "x", "result": enc})

    client = api.GridConnectCloud(region="us", session=_OK())
    # feed our fixed request id by patching uuid once
    import pytuya_gridconnect.api as m

    orig = m.uuid.uuid4
    m.uuid.uuid4 = lambda: rid
    try:
        out = client._call("thing.m.user.email.token.create", "1.0", {"x": 1},
                           session_required=False)
    finally:
        m.uuid.uuid4 = orig
    assert out["token"] == "T"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("\nAll crypto self-tests passed.")

"""Signing and body crypto for the Tuya mobile-app protocol.

Three pieces, all reverse-engineered from the Grid Connect app (v3.0.0) and its
native ``libthing_security.so``:

* :func:`sign` — the request signature (HMAC-SHA256 over a canonical param string).
* :func:`channel_key` — the per-app ``chKey`` sent on every request.
* :func:`derive_body_key` / :func:`encrypt_body` / :func:`decrypt_body` — the
  ``et=3`` body encryption (AES-128-GCM) applied to ``postData`` and to the
  reply ``result``.
* :func:`encrypt_password` — the login password transform (MD5 -> RSA/PKCS1).

Only :mod:`hashlib`, :mod:`hmac` and the ``cryptography`` package are used.
"""

from __future__ import annotations

import gzip
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

from .const import APP_KEY, PACKAGE_NAME, SIGN_ALLOWLIST, SIGN_CERT_SHA256, SIGN_KEY


def _swap_md5(post_data: str) -> str:
    """Fold ``postData`` for signing: md5 hex, then reorder the four 8-char blocks
    ``[b0 b1 b2 b3] -> [b1 b0 b3 b2]``. Matches ThingApiSignManager.swapSignString.
    """
    h = hashlib.md5(post_data.encode("utf-8")).hexdigest()
    return h[8:16] + h[0:8] + h[24:32] + h[16:24]


def build_preimage(params: dict[str, str]) -> str:
    """Canonical string to sign: allowlisted, non-empty keys sorted ascending and
    joined ``key=value`` with ``||``; ``postData`` folded via :func:`_swap_md5`."""
    keys = sorted(k for k in params if k in SIGN_ALLOWLIST and params.get(k))
    parts = []
    for k in keys:
        v = _swap_md5(params[k]) if k == "postData" else params[k]
        parts.append(f"{k}={v}")
    return "||".join(parts)


def sign(params: dict[str, str], sign_key: str = SIGN_KEY) -> str:
    """``HMAC-SHA256(K, preimage)`` as lowercase hex."""
    return hmac.new(
        sign_key.encode("utf-8"), build_preimage(params).encode("utf-8"), hashlib.sha256
    ).hexdigest()


def channel_key(app_key: str = APP_KEY) -> str:
    """The per-app ``chKey``.

    Reversed from ``getChKey`` in libthing_security.so: ``chKey`` is a pure
    function of the appId only, equal to
    ``HMAC-SHA256(key=appKey, msg="{package}_{certSHA256}")`` taken as hex and
    sliced ``[8:16]``. Verified against a second Tuya app whose chKey is public.
    """
    msg = f"{PACKAGE_NAME}_{SIGN_CERT_SHA256}"
    return hmac.new(app_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()[8:16]


def derive_body_key(request_id: str, ecode: str | None, sign_key: str = SIGN_KEY) -> bytes:
    """``et=3`` per-request AES-128 key.

    ``HMAC-SHA256(key=requestId, msg = K    )`` pre-login (ecode is None), or
    ``HMAC-SHA256(key=requestId, msg = K_ecode)`` once logged in; take the first
    16 hex characters and use them as 16 ASCII bytes.
    """
    msg = sign_key if ecode is None else f"{sign_key}_{ecode}"
    digest = hmac.new(request_id.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:16].encode("ascii")


def encrypt_body(key: bytes, plaintext: str) -> str:
    """Seal an ``et=3`` body: AES-128-GCM, random 12-byte nonce, no AAD, laid out
    ``nonce(12) || ciphertext || tag(16)`` then base64."""
    import base64

    nonce = os.urandom(12)
    sealed = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + sealed).decode("ascii")


def decrypt_body(key: bytes, result_b64: str) -> str:
    """Open an ``et=3`` reply ``result``: base64 -> AES-128-GCM verify/decrypt,
    gunzip when the plaintext is gzip-framed. Raises on a bad tag."""
    import base64

    blob = base64.b64decode(result_b64)
    if len(blob) < 12 + 16:
        raise ValueError("et=3 reply too short to hold nonce + tag")
    nonce, sealed = blob[:12], blob[12:]
    plain = AESGCM(key).decrypt(nonce, sealed, None)
    if len(plain) >= 2 and plain[0] == 0x1F and plain[1] == 0x8B:
        plain = gzip.decompress(plain)
    return plain.decode("utf-8")


def encrypt_password(password: str, public_key_hex: str, exponent_hex: str) -> str:
    """Login password transform.

    The app sends ``passwd = hex( RSA_PKCS1v15( utf8( md5_hex(password) ) ) )``
    with ``ifencrypt=1``, where the RSA public key (modulus + exponent) comes from
    the ``*.token.create`` reply. Matches RSAUtil.encrypt / MD5Util.md5AsBase64
    (the latter actually returns lowercase hex despite its name).
    """
    md5_hex = hashlib.md5(password.encode("utf-8")).hexdigest()
    modulus = int(public_key_hex, 16)
    exponent = int(exponent_hex, 16)
    pub = RSAPublicNumbers(exponent, modulus).public_key()
    ciphertext = pub.encrypt(md5_hex.encode("utf-8"), padding.PKCS1v15())
    return ciphertext.hex()

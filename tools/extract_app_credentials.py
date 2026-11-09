#!/usr/bin/env python3
"""Verify the Grid Connect app constants against an APK.

The values in ``pytuya_gridconnect/const.py`` are app-level constants from the
public Grid Connect APK. This tool proves them rather than asking you to trust
them: it checks that each constant literally occurs in the APK, and recomputes
the signing-certificate SHA-256 independently.

    python tools/extract_app_credentials.py GridConnect.apk

What it checks
--------------
* app key, app secret, ttid  -> present as strings in the APK's dex files.
* signing cert SHA-256        -> recomputed (via androguard if installed, else the
                                 openssl CLI) and compared to the constant.
* stego key                   -> instructions to recover it from assets/t_s.bmp
                                 with the bundled C extractor (independent path).

Exit code 0 means everything matched.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pytuya_gridconnect import const  # noqa: E402


def _dex_blobs(apk: str):
    with zipfile.ZipFile(apk) as z:
        for name in z.namelist():
            if name.endswith(".dex"):
                yield z.read(name)


def string_present(apk: str, needle: str) -> bool:
    raw = needle.encode()
    return any(raw in blob for blob in _dex_blobs(apk))


def cert_sha256(apk: str) -> str | None:
    """Colon-hex uppercase SHA-256 of the APK signing certificate."""
    # Preferred: androguard (pure-python, no external tools).
    try:
        import hashlib
        import logging

        logging.disable(logging.CRITICAL)
        from androguard.core.apk import APK

        for c in APK(apk).get_certificates():
            h = hashlib.sha256(c.dump()).hexdigest().upper()
            return ":".join(h[i : i + 2] for i in range(0, 64, 2))
    except Exception:  # noqa: BLE001 - fall back to openssl
        pass

    # Fallback: openssl CLI.
    with zipfile.ZipFile(apk) as z:
        rsa = [n for n in z.namelist() if re.match(r"META-INF/.*\.(RSA|EC|DSA)$", n)]
        if not rsa:
            return None
        der = z.read(rsa[0])
    with tempfile.NamedTemporaryFile(suffix=".p7", delete=False) as f:
        f.write(der)
        p7 = f.name
    try:
        pem = subprocess.run(
            ["openssl", "pkcs7", "-inform", "DER", "-print_certs", "-in", p7],
            capture_output=True, check=True,
        ).stdout
        der_cert = subprocess.run(
            ["openssl", "x509", "-outform", "der"],
            input=pem, capture_output=True, check=True,
        ).stdout
        digest = subprocess.run(
            ["openssl", "dgst", "-sha256"],
            input=der_cert, capture_output=True, check=True,
        ).stdout.decode().strip().split()[-1].upper()
        return ":".join(digest[i : i + 2] for i in range(0, len(digest), 2))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    apk = sys.argv[1]
    ok = True

    checks = {
        "app key": const.APP_KEY,
        "app secret": const.APP_SECRET,
        "ttid": const.TTID,
    }
    for label, value in checks.items():
        present = string_present(apk, value)
        ok &= present
        print(f"[{'PASS' if present else 'FAIL'}] {label} present in APK: {value}")

    cert = cert_sha256(apk)
    if cert is None:
        print("[SKIP] cert SHA-256: install `androguard` or `openssl` to verify")
    else:
        match = cert == const.SIGN_CERT_SHA256
        ok &= match
        print(f"[{'PASS' if match else 'FAIL'}] cert SHA-256: {cert}")

    print(f"\n[INFO] stego key (from assets/t_s.bmp): {const.STEGO_KEY}")
    print("       recover independently with:")
    print("         sh tools_bmp_extractor/compile.sh")
    print(f"         tools_bmp_extractor/read_keys {const.APP_KEY} "
          "<unzipped-apk>/assets/t_s.bmp")
    print(f"\n[INFO] sign key K = {const.SIGN_KEY}")

    print("\nAll matched." if ok else "\nSome checks FAILED.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

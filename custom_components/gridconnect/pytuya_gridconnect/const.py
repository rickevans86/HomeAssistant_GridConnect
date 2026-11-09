"""App-level constants for the Grid Connect app, and how they were obtained.

All values below are per-app constants baked into the public Grid Connect APK
(``com.arlec.gridconnect``, versionName 3.0.0 / versionCode 65). They are not
anyone's personal credentials; they identify the *app* to Tuya's cloud, the same
way a browser's user-agent identifies the browser. ``tools/extract_app_credentials.py``
reproduces every one of them from an APK so you never have to trust a magic number.

Provenance
----------
* ``APP_KEY`` / ``APP_SECRET``  -> ``BuildConfig.THING_SMART_APPKEY`` /
  ``THING_SMART_SECRET`` in the decompiled app (classes8.dex).
* ``SIGN_CERT_SHA256``          -> SHA-256 of the APK's signing certificate
  (``openssl x509 ... | sha256sum``), colon-hex uppercase. The native signer
  (libthing_security.so) folds this into the HMAC key.
* ``STEGO_KEY``                 -> the token hidden in ``assets/t_s.bmp``,
  recovered with the matrix/imath extractor keyed by ``APP_KEY``
  (see tools/extract_app_credentials.py --bmp).
* ``SIGN_KEY`` (K)              -> ``"{pkg}_{cert}_{stego}_{secret}"`` — the
  HMAC-SHA256 key used for request signing and et=3 body-key derivation.
  Confirmed by reversing ``libthing_security.so`` command 1 (mbedtls_md_hmac).
* ``chKey`` is NOT a constant here; it is derived per-app at runtime — see
  ``crypto.channel_key``. Derivation verified against a second Tuya app whose
  chKey is publicly documented.
"""

PACKAGE_NAME = "com.arlec.gridconnect"
APP_VERSION = "3.0.0"
SDK_VERSION = "7.8.0"
TTID = "gridconnect"

APP_KEY = "k584ttaqt7f4huakhtgp"
APP_SECRET = "c5t98m3kp7atcnspggcqewp5cqhnfuum"

SIGN_CERT_SHA256 = (
    "D2:2E:4F:CC:03:E0:91:F6:42:55:8A:AC:5A:D9:63:E6:"
    "8D:AD:C0:83:5D:D0:BD:DE:FC:ED:AD:29:5B:46:41:3F"
)
STEGO_KEY = "yg7pds9ap4vd3vj8t8cjy5agvj4jygay"

# K = package_cert_stego_appSecret  (underscore-joined, in this order)
SIGN_KEY = f"{PACKAGE_NAME}_{SIGN_CERT_SHA256}_{STEGO_KEY}_{APP_SECRET}"

# Keys that participate in the request signature. Everything else in the query
# (sdkVersion, bizData, os-info, cp/channel/nd, ...) is deliberately excluded.
SIGN_ALLOWLIST = frozenset({
    "a", "v", "lat", "lon", "lang", "deviceId", "appVersion", "ttid", "isH5",
    "h5Token", "os", "clientId", "postData", "time", "requestId", "et", "n4h5",
    "sid", "chKey", "sp",
})

# Tuya regional data centres (api.json endpoints). An account exists on exactly
# one of these; the right one accepts the login and the others report the account
# as not found. The "az" variants are the Azure-hosted Eastern-US / Western-EU
# clusters, which some accounts (including AU ones) land on.
REGIONS = {
    "us": "https://a1.tuyaus.com/api.json",
    "us-az": "https://a1-ueaz.tuyaus.com/api.json",
    "eu": "https://a1.tuyaeu.com/api.json",
    "eu-az": "https://a1-weaz.tuyaeu.com/api.json",
    "in": "https://a1.tuyain.com/api.json",
    "cn": "https://a1.tuyacn.com/api.json",
}
DEFAULT_REGION = "auto"

# Order to try when auto-probing. AU accounts are most often on these first few.
PROBE_ORDER = ["us", "eu", "in", "us-az", "eu-az", "cn"]

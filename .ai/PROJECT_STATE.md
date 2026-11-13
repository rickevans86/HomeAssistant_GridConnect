# PROJECT_STATE

_Current overview of the project. Summary only — GitHub history is authoritative._

**Last updated:** 2026-11-13 by Claude
**Integration version:** 0.1.2 (`custom_components/gridconnect/manifest.json`)
**Canonical branch:** `main` (GitHub default is still `reverse-engineer-integration`; see Issue #5)

## Goal

A Home Assistant custom integration for Grid Connect (Arlec) smart devices, which
are Tuya-based. It logs in with the user's Grid Connect account over the Tuya
mobile-app (`api.json`) protocol, lists the devices they own, and reads/controls
them. Reverse-engineered from the Grid Connect APK (package `com.arlec.gridconnect`,
v3.0.0).

## Architecture

- **`pytuya_gridconnect/`** — standalone protocol client (source of truth):
  - `crypto.py` — request signing (HMAC-SHA256), per-app `chKey`, `et=3`
    AES-128-GCM body crypto, MD5→RSA/PKCS1 password transform.
  - `api.py` — `GridConnectCloud`: login, device list, dp get/set; nested-envelope
    handling; `login_autoregion()` data-centre probe.
  - `const.py` — app constants (from the public APK) and the data-centre endpoints.
- **`custom_components/gridconnect/`** — the HA integration (config flow, polling
  coordinator, switch/light/sensor platforms). **Vendors a copy** of the client at
  `custom_components/gridconnect/pytuya_gridconnect/` — keep it in sync.
- **`cli.py`**, **`tests/`**, **`tools/`**, **`tools_bmp_extractor/`** — tooling.

## Protocol status (all verified working in code)

- Request signing — HMAC-SHA256 over sorted `||`-joined allowlist, `postData`
  folded via swap-MD5. ✅
- `chKey` — `HMAC-SHA256(appKey, "pkg_cert")[8:16]`, verified against a second
  Tuya app's known value. ✅
- `et=3` body crypto — AES-128-GCM, key `HMAC-SHA256(requestId, K[_ecode])[:16]`,
  `nonce|ct|tag` base64, gzip-aware. ✅
- Response envelopes — outer `{t, sign, result}`; decrypted payload is itself a
  `{result, t, success, status}` envelope that is unwrapped. ✅
- Login — `email.token.create` → RSA key (decimal modulus/exponent, exponent 3)
  → password = `hex(RSA-PKCS1(md5_hex(password)))` → `email.password.login`. ✅
- `deviceId` — stable per-install 44-hex id sent on every request. ✅
- Region — `login_autoregion()` probes all six Tuya data centres and keeps the one
  that accepts the account. ✅ (in code; see Open Questions)

## Current real-world status

- Sign-in reaches `password.login` and the server accepts the app identity and the
  encrypted password format. The owner confirmed the account password is correct
  (fresh logout/login in the Grid Connect app succeeded).
- `us`, `eu`, `cn` returned "incorrect account or password", which for a confirmed
  password means the account lives on a **different data centre**. v0.1.2 added the
  Eastern-US and Azure endpoints (`us-az`, `eu-az`) plus `auto` probing to find it.
- **Awaiting owner confirmation** that `auto` sign-in succeeds, and which data
  centre it selects (logged as "auto-probe selected region …").
- The account currently has **no devices paired**, so the device-list and control
  paths are implemented but not yet exercised end-to-end against real hardware.

## Open questions / unknowns

- Does `auto` sign-in succeed, and on which data centre? (If all six fail, more
  endpoints may be needed.)
- Device-list field names (`devId`, `localKey`, `dps`, `category`, …) are the
  standard Tuya set but unconfirmed against a real Grid Connect device.
- Light colour / colour-temperature datapoints are not yet mapped (on/off +
  brightness only).

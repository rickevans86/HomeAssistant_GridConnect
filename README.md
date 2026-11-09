# Home Assistant — Grid Connect

Control your **Grid Connect** (Arlec) smart plugs, switches and lights from Home
Assistant, without the vendor app and without the official Tuya IoT developer
cloud.

Grid Connect runs on Tuya's platform (app package `com.arlec.gridconnect`). This
project reverse-engineers the exact protocol the Grid Connect app uses to talk to
Tuya's cloud, so Home Assistant can sign in with your normal Grid Connect account,
list the devices you own, read their state, and control them. This is
interoperability with hardware **you own** — the same thing projects like
[tinytuya](https://github.com/jasonacox/tinytuya) and
[LocalTuya](https://github.com/rospogrigio/localtuya) do.

> Nothing here uses anyone's personal credentials. The app-level constants in
> [`pytuya_gridconnect/const.py`](pytuya_gridconnect/const.py) are baked into the
> public APK, and [`tools/extract_app_credentials.py`](tools/extract_app_credentials.py)
> re-derives every one of them from the APK so you never have to trust a magic
> number.

---

## What's in here

| Path | What it is |
|------|------------|
| `pytuya_gridconnect/` | Standalone Python client for the Grid Connect cloud protocol (signing, `et=3` body crypto, login, device list, datapoint read/write). |
| `cli.py` | Command-line tool: log in, list devices + **local keys**, read/write datapoints. |
| `custom_components/gridconnect/` | The Home Assistant integration (UI config flow, switch / light / sensor platforms). |
| `tests/test_crypto.py` | Offline self-tests for the crypto/signing. |
| `tools/extract_app_credentials.py` | Verifies the app constants against an APK. |
| `tools_bmp_extractor/` | C tool to recover the key hidden in `assets/t_s.bmp` (from [nalajcie/tuya-sign-hacking](https://github.com/nalajcie/tuya-sign-hacking)). |

---

## Quick start — try it from the command line first

This confirms your account works before touching Home Assistant, and also prints
the **local keys** you'd need for LocalTuya/tinytuya.

```bash
pip install -r requirements.txt

# Australian account on the default (us) data centre:
python cli.py --email you@example.com --country 61 devices
```

You'll be prompted for your Grid Connect password (or set `GRIDCONNECT_PASSWORD`).
If sign-in fails, your account may live in another Tuya region — try
`--region eu` or `--region in`.

Example output:

```
Kitchen Plug  (online)
  devId     : 0123456789abcdef01234
  localKey  : a1b2c3d4e5f6a7b8
  productId : abcDEF123
  category  : cz
  dps       : {"1": true, "19": 42, "20": 2415}
```

Control a device:

```bash
python cli.py --email you@example.com set <devId> 1 true    # turn on
python cli.py --email you@example.com set <devId> 1 false   # turn off
```

---

## Install the Home Assistant integration

**Via HACS (custom repository):** add `https://github.com/rickevans86/HomeAssistant_GridConnect`
as an *Integration*, install, restart Home Assistant.

**Manually:** copy `custom_components/gridconnect/` into your Home Assistant
`config/custom_components/` folder and restart.

Then: **Settings → Devices & Services → Add Integration → Grid Connect**, and
enter your email, password, country code (Australia = `61`) and region.

Your plugs and switches appear as **switch** entities, lights as **light**
entities, and metered plugs get **power / voltage / current** sensors. Every
other datapoint is exposed as a disabled diagnostic sensor so you can inspect it
and refine the mapping.

> This integration polls the cloud (default every 30 s). For instant, offline,
> LAN-speed control, use the local keys from `cli.py` with LocalTuya — see below.

---

## Two ways to run it, and which to pick

| | This integration (cloud) | LocalTuya, seeded by `cli.py` |
|---|---|---|
| Setup | Easiest — just log in | Needs device id + local key + device IP |
| Speed | ~30 s polling | Instant, push |
| Internet | Required | Works fully offline |
| Best for | Getting going quickly, devices HA can't reach on the LAN | Reliable day-to-day control |

The cloud integration is the fastest way to confirm everything works. Many people
then switch the plugs/lights over to LocalTuya for local control, using the
`devId` and `localKey` that `cli.py devices` prints.

---

## How it works (the reverse-engineering)

The Grid Connect app signs every request to Tuya's `api.json` endpoint. The pieces,
all recovered from the app (v3.0.0) and its native `libthing_security.so`:

* **Signature** — `HMAC-SHA256(K, preimage)`. The preimage is the allowlisted,
  non-empty request params, sorted and joined `key=value` with `||`, with
  `postData` folded through an MD5-and-block-swap. `K` is
  `package_certSHA256_stegoKey_appSecret`.
* **`chKey`** — a per-app constant sent on every request, equal to
  `HMAC-SHA256(appKey, "package_certSHA256")[8:16]`. (Verified against a second
  Tuya app whose `chKey` is publicly documented.)
* **`et=3` body crypto** — `postData` and the reply `result` are AES-128-GCM,
  keyed per-request by `HMAC-SHA256(requestId, K[_ecode])[:16]`, laid out
  `nonce(12) ‖ ciphertext ‖ tag(16)`, base64, gzip-aware.
* **Login** — `*.token.create` returns an ephemeral RSA key; the password is
  sent as `hex(RSA-PKCS1(md5_hex(password)))`. The login reply yields the session
  `sid` and the `ecode` that salts `et=3`.
* **Stego key** — hidden in `assets/t_s.bmp` using Tuya's matrix/`imath` scheme,
  recovered by `tools_bmp_extractor`.

The signing algorithm is proven offline in `tests/test_crypto.py`; the keys are
proven against the APK by `tools/extract_app_credentials.py`.

### Verify the constants yourself

```bash
python tools/extract_app_credentials.py /path/to/GridConnect.apk
```

### Credits

The `et=3` body-crypto and signing layout build on prior community work:
[nalajcie/tuya-sign-hacking](https://github.com/nalajcie/tuya-sign-hacking) and
the Tuya protocol notes in
[tinytuya](https://github.com/jasonacox/tinytuya). This project applies that to
the Grid Connect app specifically and packages it for Home Assistant.

---

## Status & limitations

* **Tested:** signing, `chKey`, `et=3` round-trip and the RSA password path are
  covered by offline self-tests. A live login additionally proves the keys — run
  `cli.py` against your own account to confirm end to end.
* Lights model **on/off + brightness** only; colour/temperature datapoints vary
  per product and aren't shipped as guesses yet.
* Multi-gang switches expose one entity per relay dp.
* If an API returns a `SIGN_INVALID` error, the app version may have rotated its
  keys — re-run the extractor against the current APK.

## Legal

For interoperability with devices you own. Tuya, Grid Connect and Arlec are
trademarks of their respective owners; this project is not affiliated with or
endorsed by any of them.

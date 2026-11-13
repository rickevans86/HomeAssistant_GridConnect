# DECISIONS

_Architectural decisions, newest first. Record the decision, why, and any
alternative rejected. Don't rewrite history — append a new entry if a decision
changes._

## 2026-11-13 — Coordination via `.ai/` files + GitHub Issues
GitHub Issues are the authoritative task tracker; the `.ai/` files are summaries
for fast context. Chosen over a single status doc so task ownership/status is
enforced by a system all three agents and the owner can see. Labels: `ai:chatgpt`,
`ai:claude`, `ai:codex`, `status:in-progress|blocked|review`.

## 2026-11-09 — Vendor the client inside the integration
`custom_components/gridconnect/` ships a **copy** of `pytuya_gridconnect/` rather
than depending on it as an external package. Reason: a HACS/custom integration
must be self-contained under `custom_components/`. Cost: the copy must be re-synced
on every client change (documented in `AGENTS.md`). Alternative rejected:
publishing the client to PyPI and listing it in `manifest.json` `requirements` —
too heavy for this stage.

## 2026-11-09 — Cloud polling first, local control later
The integration controls devices through the Tuya **cloud** `api.json` protocol
(`iot_class: cloud_polling`, ~30 s). Reason: it works immediately after login with
no per-device setup. Local control (LocalTuya/tinytuya) is faster and offline but
needs each device's `localKey` + IP; the CLI already surfaces `localKey` so users
can move to LocalTuya if they want. Not either/or — cloud is the default, local is
an upgrade path.

## 2026-11-09 — Generic datapoint mapping, not per-product schemas
Switches = boolean dps; lights = on/off (+ brightness) for known lighting
categories; numeric dps → metering or diagnostic sensors. Reason: avoids shipping
guessed per-product schemas as authoritative. Colour/colour-temp and exact dp
meanings are deferred until confirmed on real hardware (Issues #2, #3).

## 2026-11-09 — App constants are reproducible, not secret
The Tuya app key/secret/cert/stego key in `pytuya_gridconnect/const.py` come from
the public APK and identify the **app**, not a user. `tools/extract_app_credentials.py`
re-derives them. User credentials (email, password, `sid`, `localKey`) must never
be committed. This is why reverse-engineering the app for interoperability is in
scope.

## 2026-11-13 — Auto data-centre probing for login
Tuya accounts live on exactly one of six data centres and the login error for
"wrong data centre" is indistinguishable from "wrong password". Rather than make
users guess, `login_autoregion()` tries each endpoint and keeps the one that
accepts the account, then persists the discovered region. Safe against lockouts:
wrong data centres don't hold the account, so they don't count failed attempts
against it.

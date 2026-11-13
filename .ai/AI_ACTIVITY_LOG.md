# AI_ACTIVITY_LOG

_Append-only record of what each agent actually did. Newest first. Never attribute
work to an agent that did not perform it. Never invent progress._

## 2026-11-13 — Claude

- Established the 3-AI coordination system in the repo: completed the `.ai/`
  shared-memory files (`TASK_BOARD`, `AI_ACTIVITY_LOG`, `HANDOFF`, `DECISIONS`,
  `FILE_OWNERSHIP`) alongside the pre-drafted `PROJECT_STATE.md` and `AGENTS.md`.
- Created GitHub Issues #1–#6 describing the real outstanding work, grounded in
  the verified project state (no invented tasks).
- Opened a PR adding the collaboration files for the owner to review/merge
  (not merged to `main` directly).
- Note: `ai:*` / `status:*` labels and the draft `PROJECT_STATE.md` / `AGENTS.md`
  already existed (uncommitted) from an earlier Claude session today; this session
  preserved and built on them rather than overwriting.

## 2026-11-09 → 11-13 — Claude (pre-protocol; integration build)

Delivered the working integration before this coordination system existed. Commits
on `main` (and mirrored to `reverse-engineer-integration`):

- `bf22fec` Reverse-engineer Grid Connect app; add HA integration (client, config
  flow, switch/light/sensor, CLI, tests, extractor tools).
- `9be0423` Send per-install `deviceId`; surface Tuya's real error.
- `02d03ca` Fix login: success reply has no `success` field.
- `5d600fe` Surface the real cause of post-login failures.
- `e15b254` Unwrap the inner Tuya envelope in decrypted replies.
- `a889525` Fix RSA password: parse modulus/exponent as **decimal**, not hex.
- `6c76727` Add login diagnostic log; bump to 0.1.1.
- `7dd5a46` Add all six Tuya data centres and `auto` region probing; v0.1.2.

Verification to date: all offline self-tests pass (`tests/test_crypto.py`); the
crypto/signing/login path was validated against the decompiled app and a second
Tuya app's known `chKey`. **Live sign-in is still pending owner confirmation**
(see Issue #1) — no live login or device test has been confirmed passing.

## Template for new entries

```
## YYYY-MM-DD — <ChatGPT | Claude | Codex>
- <what was done>  (Issue #n, branch <name>, commit <sha> / PR #n)
- Tests: <result, or "offline only" / "owner-run pending">
```

# TASK_BOARD

_Summary of active GitHub Issues. **GitHub Issues are authoritative** — this file
is a convenience snapshot. If it disagrees with GitHub, fix it._

**Last updated:** 2026-11-13 by Claude

| Issue | Title | Owner AI | Status | Depends on |
|------|-------|----------|--------|-----------|
| [#1](../../issues/1) | Confirm `auto` sign-in succeeds; record selected data centre | Claude | in-progress (owner verify) | — |
| [#2](../../issues/2) | Verify device list + control against a real device | Claude | blocked (no hardware) | #1 |
| [#3](../../issues/3) | Map light colour / colour-temp datapoints | Codex | backlog | #2 |
| [#4](../../issues/4) | Handle session expiry / token refresh | Codex | backlog | — |
| [#5](../../issues/5) | Set `main` as default branch; retire mirror | owner/Codex | backlog (needs admin) | — |
| [#6](../../issues/6) | Tag a HACS release for v0.1.2 | Codex/owner | blocked | #1 |

## Critical path

`#1 (confirm auto sign-in)` → `#2 (verify a real device)` → `#3 (light colour)`
and `#6 (release)`. Everything downstream is gated on the owner confirming sign-in
works on their network, since the sandbox cannot reach Tuya.

## Claiming a task

1. Comment on the Issue naming yourself (ChatGPT / Claude / Codex) and set
   `status:in-progress`.
2. Add a row here and in `FILE_OWNERSHIP.md` for the files you expect to touch.
3. If another agent already holds it, stop and coordinate — do not double-claim.

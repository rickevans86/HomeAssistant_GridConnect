# AGENTS.md — Repository instructions for coding agents

This repository is developed collaboratively by three AI agents — **ChatGPT**,
**Claude**, and **ChatGPT Codex** — plus the project owner. GitHub is the single
source of truth. Read this file and the `.ai/` files at the start of every
session before making changes.

## What this project is

A Home Assistant custom integration for **Grid Connect** (Arlec) smart devices,
which run on the **Tuya** platform. The integration speaks the Tuya mobile-app
(`api.json`) protocol — reverse-engineered from the Grid Connect APK — so Home
Assistant can sign in with the user's Grid Connect account, enumerate devices
they own, and read/control them. See `README.md` for the protocol details.

## Layout

| Path | Purpose |
|------|---------|
| `pytuya_gridconnect/` | Standalone Tuya-app protocol client (crypto, signing, login, device API). Source of truth for the client. |
| `custom_components/gridconnect/` | The Home Assistant integration. **Vendors a copy** of `pytuya_gridconnect/` at `custom_components/gridconnect/pytuya_gridconnect/`. |
| `cli.py` | Command-line client for manual testing (login, list devices + local keys, read/set dps). |
| `tests/` | Offline self-tests (crypto, signing, envelope handling). No network needed. |
| `tools/` | `extract_app_credentials.py` — verifies app constants against an APK. |
| `tools_bmp_extractor/` | C tool that recovers the `t_s.bmp` stego key. |

### Critical: the vendored copy

`pytuya_gridconnect/` is the source of truth. Home Assistant loads the **copy**
under `custom_components/gridconnect/pytuya_gridconnect/`. After editing any file
in `pytuya_gridconnect/`, re-sync the copy in the same change:

```bash
cp pytuya_gridconnect/*.py custom_components/gridconnect/pytuya_gridconnect/
```

A change that edits only one of the two will cause HA to run stale code.

## Build / verify

No build step. Before committing:

```bash
python -m py_compile pytuya_gridconnect/*.py custom_components/gridconnect/*.py \
  custom_components/gridconnect/pytuya_gridconnect/*.py cli.py
python tests/test_crypto.py        # offline self-tests, must print "All crypto self-tests passed."
```

The sandbox cannot reach Tuya's servers, so **live login/device tests must be run
by the project owner** on their own network. Never claim a live test passed
unless the owner confirmed it.

## Versioning

Bump `custom_components/gridconnect/manifest.json` `version` for any user-facing
change to the integration. Current: see that file.

## Git conventions

- `main` is the integration users install (via HACS or manual copy).
- `reverse-engineer-integration` currently mirrors `main` (HACS default-branch
  fallback); keep it in sync when you push to `main`, or retire it via an Issue.
- Branch per task: `feat/<short>`, `fix/<short>`, `docs/<short>`.
- Never force-push shared branches. Never overwrite another agent's work.
- Do not merge to `main` without the owner's authorization.
- Commit trailers: keep the existing `Co-Authored-By` / `Claude-Session` style,
  and name the responsible agent in the body (see `.ai/` protocol).

## Coordination protocol

The full 3-AI protocol and the shared-memory files live in `.ai/`. Start there:
`.ai/PROJECT_STATE.md`, `.ai/TASK_BOARD.md`, `.ai/AI_ACTIVITY_LOG.md`,
`.ai/HANDOFF.md`, `.ai/DECISIONS.md`, `.ai/FILE_OWNERSHIP.md`.

GitHub Issues are authoritative for task assignment and status; the `.ai/` files
are summaries. If a summary disagrees with GitHub history, GitHub wins — fix the
summary.

## Hard rules

- Never invent progress or claim a GitHub update succeeded without confirming it.
- Never attribute work to an agent that did not perform it.
- Never commit secrets. The app-level Tuya constants in `pytuya_gridconnect/const.py`
  are from the public APK and are **not** user credentials; a user's email,
  password, session `sid`, or device `localKey` must never be committed.
- Keep PRs small and reviewable.

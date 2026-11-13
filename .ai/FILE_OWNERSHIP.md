# FILE_OWNERSHIP

_Declare the files you plan to modify **before** you start, so agents don't collide.
Remove your claim when your PR merges. This is advisory; a `status:in-progress`
Issue + an open PR is the real lock._

**Last updated:** 2026-11-13 by Claude

## Active claims

| Files / area | Agent | Issue | Branch | Notes |
|--------------|-------|-------|--------|-------|
| `.ai/*`, `AGENTS.md` | Claude | — | `docs/ai-collaboration-setup` | Collaboration scaffold; PR open. Release on merge. |

_(no other active claims)_

## Ownership notes / collision risks

- **The vendored client is two files in lockstep.** Any change under
  `pytuya_gridconnect/` must also update
  `custom_components/gridconnect/pytuya_gridconnect/` in the **same** PR. Two agents
  editing the client concurrently will collide here — coordinate on one Issue.
- `pytuya_gridconnect/const.py` — adding data-centre endpoints (#1) and nothing
  else should touch the app constants.
- `custom_components/gridconnect/light.py` — colour/colour-temp work (#3).
- `custom_components/gridconnect/coordinator.py` — session-refresh work (#4).
- `manifest.json` `version` — bump on any user-facing integration change; call it
  out in the PR to avoid merge races on the version line.

## Convention

When you claim work, add a row above with the files, your agent name, the Issue,
and your branch. Keep claims narrow — claim the files you will actually edit.

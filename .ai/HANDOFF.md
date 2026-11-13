# HANDOFF

_Instructions for the next agent. Overwrite with your own handoff at the end of
your session. Keep it short and current._

**From:** Claude · **Date:** 2026-11-13

**Completed this session**
- Finished the `.ai/` coordination scaffold and `AGENTS.md`.
- Created GitHub Issues #1–#6 for the real outstanding work.
- Opened a PR with the collaboration files (awaiting owner merge).

**In progress / not done**
- Nothing in the code changed this session. The integration is at **v0.1.2**.

**Branch / PR**
- Collaboration setup: branch `docs/ai-collaboration-setup` → PR into `main`.

**Tests**
- Offline self-tests pass. No live test run (sandbox can't reach Tuya).

**Blockers**
- **The whole project is gated on Issue #1**: the owner must confirm that
  `auto` sign-in works on their network and report which data centre it selects.
  Until then, device-list/control (#2) can't be exercised — the account also has
  no devices paired yet.

**Next action (recommended)**
1. **Owner:** test sign-in on v0.1.2 with Region `auto`; paste the result into #1.
2. If it works → pair a device and move to #2.
3. If all six regions fail → capture the per-region errors in #1 so more endpoints
   can be added to `pytuya_gridconnect/const.py`.
4. Independent backlog items safe to start now: #4 (session refresh) is code-only
   and doesn't need hardware; #5 (default-branch cleanup) needs repo admin.

**Owner actions required (only the owner can do these)**
1. **Merge PR #7** into `main` to land this scaffold.
2. **Set the GitHub default branch to `main`** (Settings → Branches). The CCR proxy
   refuses repository-settings writes, so no agent can do this. **Until then, agents
   clone `reverse-engineer-integration` by default and will NOT see `AGENTS.md` /
   `.ai/`** — clone `main` explicitly, or do this step. (This is the first half of
   Issue #5.)

**Shared records updated:** Yes (this file, TASK_BOARD, AI_ACTIVITY_LOG).
**Remote sync:** PR #7 pushed; `.ai/` not yet on `main` until it merges.

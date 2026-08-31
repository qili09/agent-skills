# Field Notes — architecture-decision-review

Friction observed during runs that SKILL.md didn't anticipate. Append a dated entry at
the moment of surprise; keep it to what happened and what would have prevented it.
Entries get codified into SKILL.md when a pattern recurs and the user approves, then
removed from here. A clean run adds nothing.

Entry format:

```
## YYYY-MM-DD — <one-line summary> (<decision/ticket ref>)
- What happened:
- What would have prevented it:
- Codify? (leave blank until retro)
```

---

_No open notes. The 2026-08-18 PROJ-18183 run's six findings were codified directly
into SKILL.md (commit 3695025) before this file existed._

## 2026-08-21 — lavish poll does not survive machine sleep
During the PROJ-16600 banking-app pilot-gating review, the `lavish-axi poll` background task died with `SERVER_ERROR` three nights in a row (Aug 18→21): the local lavish server is killed when the laptop sleeps, and each restart requires re-running `lavish-axi <file>` (to restart the server + session) before `poll` works again. For multi-day review windows (stakeholder reviews around meetings), don't rely on a single long-lived poll: expect nightly restarts, and after ~2 silent days treat the stakeholder as quiet per Phase 3 — deliver the artifact as a review-ready draft and invite feedback via chat instead of babysitting the poll.

## 2026-08-21 (addendum) — lavish server crashes are not sleep-related
Correction to the note above: a same-day restart also died with `SERVER_ERROR` within hours, with an empty `~/.lavish-axi/server.log` and no surviving process — the server is crashing on its own on this machine, not just being killed by sleep. When lavish polling fails twice in a row, stop the restart loop entirely: the artifact HTML on disk is the deliverable, and stakeholder feedback should move to chat. Reopen a session only on explicit request.

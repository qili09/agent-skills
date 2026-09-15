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

_No open notes. Codified so far: the 2026-08-18 PROJ-18183 run's six findings (commit
3695025); the PROJ-16600 lavish-crash notes, superseded by the always-launch rule in
Phase 2; and the three 2026-09-09 PROJ-20221 findings — Jira
v3 `search/jql` fallback (Phase 5), `gh api` URL quoting (Phase 1), unconditional lavish
launch (Phase 2), and the literal observed-behaviour pass (Phase 1) (commits 3857805,
d24a536); and the 2026-09-15 PROJ-20223 second-round notes — replay the reviewer's probe
set against the new implementation, and carry untestable forcing facts as
"claimed — unverified here" (Phase 1)._

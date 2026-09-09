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

## 2026-09-09 — RESOLVED: lavish server crashes were transient; never skip launching the report
Two now-removed 2026-08-21 notes (PROJ-16600) reported `lavish-axi poll` dying with
`SERVER_ERROR` and advised stopping restarts and reopening sessions "only on explicit
request." Later runs (e.g. the 2026-08-31 FirstMate calm-mode review) ran full lavish
sessions with long polls and no crashes — the failures were transient on that machine at
that time, not a standing condition. The stale advice caused runs to skip launching the
visual report entirely, which contradicts the user's standing preference and confused
the review flow. Corrected rule (codified in SKILL.md Phase 2): always build AND open
the lavish artifact; a polling/server failure downgrades feedback collection to chat,
never the launch itself.

## 2026-09-09 — Jira Cloud REST v2 `search` is gone; use v3 `search/jql` (PROJ-20221)
- What happened: the mcp-atlassian server stayed wedged ("Failed to configure OAuth session") even after a successful manual token refresh, so I fell back to direct REST. `GET /rest/api/2/search?jql=...` now returns **410 Gone** (Atlassian removed the legacy search endpoint). `GET /rest/api/3/search/jql?jql=...&fields=...` works with the same bearer token; `issue/<key>`, `user?accountId=`, and attachment `content` URLs still work on v2.
- What would have prevented it: the direct-REST bypass in the memory/skill notes should name `search/jql` (v3) as the search endpoint. Also: quote `gh api "...?ref=develop"` URLs — zsh treats the `?` as a glob and errors with "no matches found".
- Codify? (leave blank until retro)

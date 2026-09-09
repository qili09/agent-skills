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
- Codify? RESOLVED 2026-09-09 — codified in SKILL.md: v3 `search/jql` fallback in Phase 5 step 5, `gh api` URL quoting in Phase 1's repo bullet.

## 2026-09-09 — Skipped the lavish artifact because the session was flagged "non-interactive" (PROJ-20221)
- What happened: Phase 2 says build the artifact in lavish "if the lavish skill is available and the session is interactive". The harness flagged this session non-interactive (OAuth notice) and prior notes recorded lavish server crashes, so Phase 1 findings went to chat. The user asked why no lavish session had started — their global CLAUDE.md says to use lavish for anything visual. Once opened, the review ran seven rounds of annotations without a single server crash, and the review itself produced a factual reversal (the redirect is bilingual) that the chat pass had missed.
- What would have prevented it: drop the "session is interactive" qualifier — the user's ability to open a browser is what matters, not the harness flag. Default to opening lavish; fall back to chat only if `lavish-axi` itself fails.
- Codify? RESOLVED 2026-09-09 — codified in SKILL.md Phase 2: the "session is interactive" qualifier is removed; always attempt the launch (past failures and harness non-interactive flags are not reasons to skip), fall back to a standalone document only when lavish is unavailable or `lavish-axi` itself fails.

## 2026-09-09 — Requirements validation needs a literal "observed behaviour" pass before judging the spec (PROJ-20221)
- What happened: the first premise check marked "all paths → one destination" as verified after probing two paths. Building a literal observed-behaviour section on the reviewer's request forced a 23-path probe and found a case-sensitive `/FR` prefix rule to a different (French) destination — a blocking error in the document and in the recommended option's config.
- What would have prevented it: for "is the requirement captured correctly?" reviews, record observed behaviour exhaustively and literally (all record types, path variants, methods, headers, external vantage point) *before* comparing to the document; the document's own claims must not define the probe set.
- Codify? RESOLVED 2026-09-09 — codified in SKILL.md Phase 1 as the "Behavioural claims get a literal observed-behaviour pass" bullet.

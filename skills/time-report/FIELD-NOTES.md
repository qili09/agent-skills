# Field Notes — time-report

Friction observed during runs that SKILL.md didn't anticipate. Append a dated entry at the
moment of surprise; keep it to what happened and what would have prevented it. Entries get
codified into SKILL.md when a pattern recurs and the user approves, then removed from here.
A clean run adds nothing.

Entry format:

```
## YYYY-MM-DD — <one-line summary> (<ticket ref>)
- What happened:
- What would have prevented it:
- Codify? (leave blank until retro)
```

---



## 2026-09-09 — Jira-native worklog leaves Tempo "billing key" empty (first live run)
- What happened: the first real entry synced into Tempo but the user saw the Tempo *billing key* attribute empty. Jira's worklog API has no notion of Tempo work attributes; only Tempo's own REST API (api.tempo.io/4, personal Tempo token) can set them, or the attribute derives from the issue's Tempo Account field.
- What would have prevented it: the sync test should have checked the Tempo entry's attributes, not just its presence. Backend decision needs revisiting: Tempo REST API for posting (with attribute options fetched from Tempo), Jira API kept for read/delete.
- Codify? (leave blank until retro)

<!-- 2026-09-16 `--issue` filter quirk + created-ticket single-entry rule: codified (session_time.py fix, SKILL.md step 3). -->

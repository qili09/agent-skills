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

## 2026-09-16 — `--issue KEY` filters instead of charging the whole session (ticket-creation session)
- What happened: SKILL.md says "with `--issue KEY` the whole session is charged to that key". Running `session_time.py --issue <new-key>` instead returned only that key's own slice (27 s, rounded to 15 m) and dropped the other allocation; the whole-session total had to be taken from the no-flag run. The session also split 21 min of work into two 15 m allocations because the *created* ticket's key first appeared in a user message at the very end — logging both would have double-counted.
- What would have prevented it: either make `--issue` reassign all active time to the given key (matching the doc), or reword step 3 to say the flag filters. Also worth a rule: when one story's slice is under ~1 min and is the ticket the session *created*, fold the whole session into a single entry rather than proposing two.
- Codify? (leave blank until retro)

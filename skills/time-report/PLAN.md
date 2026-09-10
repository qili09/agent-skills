# time-report — plan (approved 2026-09-09)

## Goal
Stop hand-entering Tempo time. Whenever a Claude Code session works on a Jira story, the
time spent is computed from the session transcript and logged as a Jira worklog (which
Tempo Cloud mirrors) after a one-line confirmation.

## Decisions (user, 2026-09-09)
| Decision | Choice | Rejected alternatives |
|---|---|---|
| Automation level | **Stop-hook nudge + one-line confirm** | Fully automatic SessionEnd post (wrong story/duration goes to Jira unseen); manual-only |
| Backend | ~~Jira native worklog API~~ → **Tempo REST v4** with a personal Tempo token (revised 2026-09-09 after the first entry synced into Tempo with an empty *Billing Key*; Jira's API cannot set Tempo work attributes). Jira API kept for list/delete and as a warned fallback | Jira-only (attributes blank) |
| Billing key (Tempo Account attribute, e.g. `_BillingKey_`) | **Infer, show, ask only if unsure** (refined 2026-09-09): existing functionality / keeping it running → `<TEAM>-RUN`; new functionality or improvement → `<TEAM>-BUILD`; stories of another product line → that product's key; genuine RUN-vs-BUILD doubt → ask with the reason. The inferred key is always visible in the confirmation line so it can be overridden in the reply. Historical usage was heavily skewed to RUN (roughly 3:1 over BUILD in the last 200 entries) | Fixed default key; default + per-epic overrides; ask every time (first choice, superseded same day) |
| Duration rule | **Active time**: sum of gaps ≤ 20 min between consecutive messages; round to nearest 15 min; minimum 15 min | Wall-clock span; ask each time |
| Multi-story sessions | **One entry per story** (added 2026-09-09): time is charged to the story the conversation was on at each moment — a user message naming a story switches the current story; time before the first mention goes to the first story. Each story rounds separately with the 15-min floor. Continued sessions propose only the unlogged remainder | Single entry on the dominant story; ask how to split |
| Logging threshold | **Every session that worked on a story is logged**, however short; under 15 min → 15 min. Nudge fires from 1 min of active time (added 2026-09-09 after first run) | Nudge only at ≥ 30 min (initial draft) |
| Plan location | `skills/time-report/PLAN.md` in the agent-skills repo | `~/.claude/plans/`; none |

## Components
- `SKILL.md` — triggers, workflow, guardrails.
- `scripts/session_time.py` — reads a transcript `.jsonl`, extracts Jira keys from *user-authored* text (slash-command args and prose, never tool results or system reminders), ranks them worked-on vs referenced, computes active time, emits a JSON proposal. `--nudge` mode prints a Stop-hook `systemMessage` only when there is unlogged time ≥ 30 min and no nudge in the last 60 min.
- `scripts/post_worklog.py` — posts / lists / deletes Jira worklogs with the mcp-atlassian OAuth token (auto-refresh), appends to `~/.claude/time-report/ledger.jsonl` so a session is never double-logged.
- `hooks/stop-nudge.sh` — Stop hook wrapper: reads `transcript_path` from stdin, calls `session_time.py --nudge`.
- `FIELD-NOTES.md` — learning loop, same convention as architecture-decision-review.

## Evidence gathered before building
- Tempo is installed on the target Jira Cloud site as an ecosystem extension, with
  instance-specific custom fields for Tempo Team and Account.
- The user's historical Tempo entries are returned by Jira's native `/issue/{key}/worklog` API (Tempo → Jira mirroring confirmed). Jira → Tempo direction is what the test entry proves.
- Transcripts live at `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`; each line has `timestamp`, `type`, `sessionId`; user text lives in `message.content` (string or text blocks). The pilot session: 566 timestamped records, 3 h 39 m wall clock, 15 distinct issue keys of which one was actually worked on.
- Jira REST v2 `search` is gone (410); use v3 `search/jql`.

## Verification steps
1. `session_time.py` on the pilot session → the worked-on story ranked primary, plausible active time.
2. Post a 15-min test worklog on that story with description "time-report sync test — delete me"; user confirms it is visible in Tempo; delete it via `post_worklog.py --delete`.
3. Stop hook pipe-test with a synthetic stdin payload; `jq -e` validation of settings.json; live proof in-session.

## Out of scope (for now)
- Splitting one session across several stories automatically (skill proposes the split; user confirms).
- Tempo work attributes (Account/Team) — only if the sync test shows they are mandatory.
- Daily consolidation across sessions (ledger makes it possible later).

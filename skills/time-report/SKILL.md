---
name: time-report
description: Log the time spent on a Jira story during the current Claude Code session as a Jira worklog (mirrored into Tempo Timesheets), computed from the session transcript instead of typed by hand. Use when the user says "log time", "log my time", "time report", "record this in Tempo", "how long did I spend on <KEY>", or when a Stop-hook nudge reports unlogged time — and at the natural end of any session in which a Jira story (e.g. PROJ-12345) was actively worked on, offer to run it. Do NOT use it for editing or reporting on Tempo timesheets in general, for estimating future effort, or for stories that were merely mentioned in passing.
argument-hint: "[ISSUE-KEY] [duration e.g. 1h30m] [description] — all optional; defaults are computed from the session transcript"
---

# time-report

Turn a working session into a Tempo entry autonomously. The transcript is the
timesheet: which story was worked on, for how long, and what was done are all derivable
from it. The skill computes, posts, and reports what it logged (user rule, 2026-09-22 —
no confirmation gate); the script records a ledger entry so the same session is never
logged twice. Ask first only in the genuinely ambiguous cases called out below.

Decisions and evidence behind the design: [PLAN.md](PLAN.md).

## Workflow

1. **Locate the transcript.** `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`. The
   session id is in the scratchpad path given in the environment; the cwd slug is the
   working directory with `/` replaced by `-`. If in doubt, pick the most recently
   modified `.jsonl` in that folder.
2. **Compute the proposal.**
   ```bash
   python3 scripts/session_time.py <transcript.jsonl> [--issue KEY]
   ```
   Output: `allocations[]` — **one per story the session worked on** — each with `issue`,
   `active_seconds`, `rounded_seconds`/`rounded_human`, `started`, `ended`, `already_logged`,
   and `unlogged_*` (the remainder not yet in the ledger). Rules: active time is the sum of
   gaps ≤ 20 min between consecutive records; time is charged to the story the conversation
   was on at that moment (a user message naming a story switches it); each story is rounded
   to 15 min with a 15-min floor. Keys come only from user-authored text (slash-command args
   weigh ×3); assistant output and tool results never nominate a story. Whole-session totals
   (`primary_issue`, `rounded_human`) are also returned for reference.
3. **Reconcile with the arguments.** An explicit `ISSUE-KEY`, duration, or description on
   the command line overrides the computed value (with `--issue KEY` the whole session is
   charged to that key — the script replaces the per-story split with one allocation). A
   session that crossed several stories gets **one entry per story** (user rule, 2026-09-09)
   — never merge them. Drop an allocation only if the user says that story was merely
   mentioned; if the split looks wrong, show it and ask — do not guess.
   **Exception — the ticket the session created** (rule, 2026-09-16): when a story's slice
   is under a minute and its key first appeared because the session *created* that ticket
   (or the user only named it at the end to ask where to log), do not propose two 15-min
   entries for one piece of work. Re-run with `--issue <KEY>` on the story the work belongs
   to — normally the created ticket — and propose a single entry.
4. **Draft the description** in one line, past tense, from what was actually done
   (e.g. “Validated requirements in the redirect solution doc; 13 findings”).
   No Claude/AI attribution, no markdown.
5. **Infer the billing key.** The Tempo *Billing Key* is an
   Account attribute (attribute name and choices in `~/.claude/time-report/config.json`).
   Infer it from what the story and the session were about (user rule, 2026-09-09), using
   the team's RUN/BUILD split:
   - **`<TEAM>-RUN`** — work on *existing* functionality: keeping something running,
     analysis or migration of current behaviour, defects, operations, support, cleanup,
     decommissioning, config or infra changes that do not add capability.
   - **`<TEAM>-BUILD`** — *new* functionality or an *improvement*: new features, new
     integrations, redesigns, enhancements that change what the system does for users.
   - **Another product's key** — only when the story belongs to a product line that has
     its own billing key in the config choices.
   - **Unsure between RUN and BUILD** (e.g. a migration that also adds capability, or a
     story whose description is empty) → ask, with the one-line reason for the doubt.
   **No confirmation gate** (user rule, 2026-09-22 — supersedes the draft-first gate):
   when the story, duration, and billing key are all clear, post immediately without
   asking. Stop and ask only when (a) the billing key is genuinely unsure, (b) the
   per-story split looks wrong (step 3), or (c) the user gave a duration/story that
   contradicts the computed one. If a story is `already_logged` in this session, post
   only its `unlogged_human` remainder (a continued session), or skip it silently when
   the remainder is 0m.
6. **Post via Tempo — once per story** (needed for attributes; the script falls
   back to Jira only if the Tempo token is missing and then warns that the billing key was
   not set). **Date the worklog with the current date/time** (user rule, 2026-09-22): pass
   "now" (UTC ISO) as `<started-iso>`, not the allocation's historical `started` — entries
   land on today's timesheet row where the user looks for them, even when the session's
   work stretched over earlier days. Use `rounded_seconds` (or `unlogged_rounded_seconds`
   for a continued session):
   ```bash
   python3 scripts/post_worklog.py post <ISSUE> <seconds> <now-iso> "<description>" \
       --session <session-id> --attr _BillingKey_=<CHOICE>
   ```
   Afterwards report, per story: duration, date, billing key, description, and the
   returned `tempo_worklog_id` — so the user can veto anything (step 7 undoes). The script
   appends to `~/.claude/time-report/ledger.jsonl`. `post_worklog.py attributes` lists
   Tempo attributes.
   **Then refresh the user's Tempo tab** (user rule, 2026-09-22): after the last post of
   the run, execute
   ```bash
   scripts/refresh_tempo_tabs.sh
   ```
   It reloads open browser tabs whose URL contains `tempo` or `my-work` (Jira Cloud
   serves the Tempo app under `/jira/apps/<uuid>/…/my-work/…`, so the app name never
   appears in the URL) in Chrome/Edge/Safari, so the new entry is visible without a
   manual refresh. Best-effort: it never fails the run — if it warns about Automation
   permission, tell the user to approve the terminal controlling the browser in
   System Settings → Privacy & Security → Automation (one-time). It deliberately does
   not reload plain Jira issue tabs (a reload could discard a comment mid-typing).
7. **Undo / repair.** `post_worklog.py list <ISSUE>`; `post_worklog.py delete <ISSUE> <JIRA_WORKLOG_ID>`;
   `post_worklog.py fix <JIRA_WORKLOG_ID> --attr _BillingKey_=<CHOICE>` sets attributes on an
   existing entry through Tempo.

## Nudge (Stop hook)

`hooks/stop-nudge.sh` reads the hook's `transcript_path` and prints a `systemMessage` when
the session has any unlogged active time on a story (≥ 1 min), at most once per hour per
session. Registered in `~/.claude/settings.json` under `hooks.Stop`. It only reminds; it
never posts. User rule (2026-09-09): every session that touched a story gets logged;
work under 15 minutes is logged as 15 minutes.

## Guardrails

- A worklog is visible to the whole project — post autonomously (user rule, 2026-09-22)
  but always report exactly what was posted immediately afterwards, and undo on any veto;
  the ledger prevents double-posting the same session slice.
- Never log time to a key that appears only in tool output, search results, or sibling
  tickets read for context; the transcript ranking already excludes those sources.
- Time is rounded, not padded: report the raw `active_seconds` if the user asks.
- Tokens: Jira via the mcp-atlassian OAuth file (auto-refresh; if 401 twice the refresh
  token is dead — see the mcp-atlassian OAuth memory note); Tempo via
  `~/.claude/time-report/tempo-token` (personal token, scopes worklogs r/w + work-attributes
  read; `accounts:view` would additionally let `attributes` list every Account). Never paste
  tokens into chat — have the user write the file themselves.
- Jira-created worklogs do sync into Tempo but arrive with **empty work attributes**; that is
  why posting goes through Tempo. If the Tempo path fails, tell the user the billing key
  will need setting by hand before falling back to Jira.

## Learning loop

When a run hits friction this file didn't anticipate, append a dated note to
`FIELD-NOTES.md` immediately. Offer a retro at the end; codify only what the user approves.

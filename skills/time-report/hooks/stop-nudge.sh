#!/usr/bin/env bash
# Stop hook: remind the user when the current session has >= 30 min of unlogged work on a Jira story.
# Reads Claude Code hook JSON on stdin (uses transcript_path). Prints a systemMessage JSON or nothing.
# Never blocks: any failure exits 0 silently.
set -u
input="$(cat)"
transcript="$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("transcript_path",""))' 2>/dev/null)"
[ -n "$transcript" ] && [ -f "$transcript" ] || exit 0
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$here/../scripts/session_time.py" "$transcript" --nudge 2>/dev/null || true
exit 0

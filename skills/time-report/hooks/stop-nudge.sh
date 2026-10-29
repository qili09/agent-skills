#!/usr/bin/env bash
# Stop hook: when the current session has unlogged work on a Jira story (>= 1 min active, no
# ledger entry for it), hand the model a nudge so the time-report skill runs on its own.
#
# Output shape (2026-10-29): hookSpecificOutput.additionalContext — Claude Code appends it to the
# conversation and lets the model act. The earlier systemMessage form was only printed to the
# user's terminal and went unnoticed. Cooldown 120 min per session; stop_hook_active (set by
# Claude Code when the model is already continuing because of a Stop hook) always yields silence,
# so the hook cannot loop. Never blocks: any failure exits 0 silently.
set -u
input="$(cat)"
read -r transcript active < <(printf '%s' "$input" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print(d.get("transcript_path",""), "1" if d.get("stop_hook_active") else "0")' 2>/dev/null) || exit 0
[ -n "${transcript:-}" ] && [ -f "$transcript" ] || exit 0
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
flag=""
[ "${active:-0}" = "1" ] && flag="--stop-hook-active"
python3 "$here/../scripts/session_time.py" "$transcript" --nudge $flag 2>/dev/null || true
exit 0

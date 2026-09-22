#!/bin/bash
# Reload any open Tempo tabs in Chrome, Edge, and Safari so a just-posted
# worklog is visible without a manual refresh.
#
# Matching: a tab is a "Tempo tab" if its URL contains any of the substrings
# given as arguments (default: "tempo" and "my-work"). Jira Cloud serves the
# Tempo app under /jira/apps/<uuid>/…/my-work/…, so the app name never appears
# in the URL — "my-work" is what actually matches the timesheet. Plain Jira
# issue tabs are deliberately NOT matched: reloading them could discard a
# comment the user is mid-typing.
#
# Best-effort by design: browsers that aren't running are skipped, and any
# AppleScript failure (e.g. the macOS Automation permission not yet granted)
# is reported but never fails the caller — a missing refresh must not break
# a successful worklog post. Always exits 0.
#
# Usage: refresh_tempo_tabs.sh [url-substring ...]

MATCHES=("${@:-tempo my-work}")
[ $# -eq 0 ] && MATCHES=(tempo my-work)
TOTAL=0

condition() { # emit AppleScript condition over $URLVAR for all match terms
  local var="$1" out="" m
  for m in "${MATCHES[@]}"; do
    [ -n "$out" ] && out+=" or "
    out+="($var contains \"$m\")"
  done
  echo "$out"
}

reload_chromium() { # $1 = app name (Chrome-family AppleScript dialect)
  local app="$1"
  pgrep -xq "$app" || return 0
  local cond n
  cond=$(condition "URL of t")
  n=$(osascript 2>/dev/null <<EOF
set reloadCount to 0
tell application "$app"
  repeat with w in every window
    repeat with t in every tab of w
      if $cond then
        tell t to reload
        set reloadCount to reloadCount + 1
      end if
    end repeat
  end repeat
end tell
return reloadCount
EOF
  ) || { echo "warn: could not talk to $app (Automation permission?)" >&2; return 0; }
  [ -n "$n" ] && TOTAL=$((TOTAL + n))
}

reload_safari() {
  pgrep -xq "Safari" || return 0
  local cond n
  cond=$(condition "URL of t")
  n=$(osascript 2>/dev/null <<EOF
set reloadCount to 0
tell application "Safari"
  repeat with w in every window
    repeat with t in every tab of w
      if $cond then
        set URL of t to (URL of t)
        set reloadCount to reloadCount + 1
      end if
    end repeat
  end repeat
end tell
return reloadCount
EOF
  ) || { echo "warn: could not talk to Safari (Automation permission?)" >&2; return 0; }
  [ -n "$n" ] && TOTAL=$((TOTAL + n))
}

reload_chromium "Google Chrome"
reload_chromium "Microsoft Edge"
reload_safari

echo "reloaded $TOTAL tab(s) matching: ${MATCHES[*]}"
exit 0

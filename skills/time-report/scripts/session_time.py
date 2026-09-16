#!/usr/bin/env python3
"""Compute time spent per Jira story from a Claude Code session transcript.

Usage:
  session_time.py <transcript.jsonl> [--issue KEY] [--gap-min 20] [--round-min 15] [--json]
  session_time.py <transcript.jsonl> --nudge          # Stop-hook mode: print systemMessage JSON or nothing

Rules (approved 2026-09-09):
  * Jira keys are taken only from user-authored text (slash-command args and prose),
    never from tool results, system reminders, or assistant output.
  * Active time = sum of gaps between consecutive timestamped records that are <= gap-min.
  * Rounded to the nearest round-min, minimum one round-min.
  * Time is charged to the story the conversation was on at each moment (a user message naming
    a story switches the current story); one session across several stories → one allocation each.
"""
import json, os, re, sys, time
from datetime import datetime, timezone

LEDGER = os.path.expanduser("~/.claude/time-report/ledger.jsonl")
NUDGE_STATE = os.path.expanduser("~/.claude/time-report/nudge-state.json")
CONFIG = os.path.expanduser("~/.claude/time-report/config.json")  # optional: {"projects": ["PROJ"]}
KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d{1,6})\b")
# Things that look like Jira keys but never are (hash names, standards, CVEs, model names...)
NOT_PROJECTS = {"SHA", "MD", "UTF", "ISO", "RFC", "TLS", "SSL", "AES", "RSA", "CVE", "HTTP", "HTTPS",
                "GPT", "IEEE", "ANSI", "ASCII", "X", "P", "V", "TCP", "UDP", "IP", "IPV", "AWS", "GCP",
                "ID", "UUID", "COVID", "OAUTH", "HMAC", "PKCS", "ECDSA", "TLSV", "SSLV"}


def allowed_projects():
    try:
        return set(json.load(open(CONFIG)).get("projects") or [])
    except Exception:
        return set()


def is_issue_key(key):
    proj = key.split("-")[0]
    if proj in NOT_PROJECTS:
        return False
    allow = allowed_projects()
    return proj in allow if allow else True
SYSREM_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
CMD_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def user_text(rec):
    """Return user-authored text from a transcript record, or '' if none."""
    if rec.get("type") != "user":
        return ""
    msg = rec.get("message") or {}
    content = msg.get("content")
    parts = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            # tool_result blocks are deliberately ignored
    text = "\n".join(parts)
    text = SYSREM_RE.sub("", text)
    if "[SYSTEM NOTIFICATION" in text or "<task-notification>" in text:
        return ""
    return text


def load(path):
    recs = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("timestamp"):
                recs.append(d)
    recs.sort(key=lambda r: r["timestamp"])
    return recs


def analyse(path, gap_min=20, round_min=15):
    """Attribute active time to the story the conversation was on at each moment.

    A user message that names a story (slash-command args or prose) switches the *current*
    story; time between consecutive records is charged to the current story. Time before
    the first mention goes to the first story mentioned. One session that moves across
    several stories therefore yields several allocations (user rule, 2026-09-09).
    """
    recs = load(path)
    if not recs:
        return {"error": "no timestamped records", "transcript": path}
    session_id = next((r.get("sessionId") for r in recs if r.get("sessionId")), None)
    ts = [parse_ts(r["timestamp"]) for r in recs]
    wall = (ts[-1] - ts[0]).total_seconds()

    # Pass 1: which story is "current" at each record, plus mention counts.
    counts, cmd_keys, current = {}, set(), None
    current_at = []
    for r in recs:
        t = user_text(r)
        if t:
            keys_here = []
            for m in CMD_ARGS_RE.findall(t):
                for k in filter(is_issue_key, KEY_RE.findall(m)):
                    cmd_keys.add(k)
                    counts[k] = counts.get(k, 0) + 3
                    keys_here.append(k)
            for k in filter(is_issue_key, KEY_RE.findall(t)):
                counts[k] = counts.get(k, 0) + 1
                keys_here.append(k)
            if keys_here:
                # switch to the first key named in this message unless the current story is also named
                if current not in keys_here:
                    current = keys_here[0]
        current_at.append(current)
    first_story = next((c for c in current_at if c), None)
    current_at = [c or first_story for c in current_at]

    # Pass 2: charge gaps to the story current at the *start* of each gap.
    active_by = {}
    seen_by = {}
    active = 0.0
    for i in range(len(ts) - 1):
        gap = (ts[i + 1] - ts[i]).total_seconds()
        if 0 <= gap <= gap_min * 60:
            active += gap
            k = current_at[i]
            if k:
                active_by[k] = active_by.get(k, 0.0) + gap
        k = current_at[i]
        if k:
            fs, ls = seen_by.get(k, (ts[i], ts[i]))
            seen_by[k] = (min(fs, ts[i]), max(ls, ts[i + 1]))

    unit = round_min * 60
    def rnd(sec):
        return max(unit, int(round(sec / unit)) * unit)

    allocations = []
    for k, sec in sorted(active_by.items(), key=lambda kv: -kv[1]):
        fs, ls = seen_by[k]
        logged = logged_for(session_id, k)
        logged_sec = sum(int(e.get("seconds", 0)) for e in logged)
        remainder = max(0, int(sec) - logged_sec)
        # remainder rounds to the same 15-min grid; below half a unit it is not worth an entry
        rem_rounded = int(round(remainder / unit)) * unit if logged else rnd(sec)
        allocations.append({
            "issue": k,
            "active_seconds": int(sec),
            "rounded_seconds": rnd(sec),
            "rounded_human": human(rnd(sec)),
            "started": fs.isoformat(),
            "ended": ls.isoformat(),
            "mentions": counts.get(k, 0),
            "from_command_args": k in cmd_keys,
            "already_logged": logged,
            "logged_seconds": logged_sec,
            "unlogged_seconds": remainder,
            "unlogged_rounded_seconds": rem_rounded,
            "unlogged_human": human(rem_rounded) if rem_rounded else "0m",
        })
    primary = allocations[0]["issue"] if allocations else None
    return {
        "transcript": path,
        "session_id": session_id,
        "started": ts[0].isoformat(),
        "ended": ts[-1].isoformat(),
        "records": len(recs),
        "wall_clock_seconds": int(wall),
        "active_seconds": int(active),
        "rounded_seconds": rnd(active),
        "rounded_human": human(rnd(active)),
        "primary_issue": primary,
        "primary_mentions": counts.get(primary, 0) if primary else 0,
        "from_command_args": primary in cmd_keys if primary else False,
        "referenced_issues": [k for k in sorted(counts, key=lambda k: -counts[k]) if k not in active_by],
        "allocations": allocations,
        "already_logged": logged_for(session_id, primary),
    }


def human(sec):
    h, m = divmod(int(sec) // 60, 60)
    return ((f"{h}h " if h else "") + (f"{m}m" if m or not h else "")).strip()


def logged_for(session_id, issue):
    if not (session_id and issue) or not os.path.exists(LEDGER):
        return []
    out = []
    with open(LEDGER) as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("session_id") == session_id and e.get("issue") == issue:
                out.append(e)
    return out


def nudge(path, min_active_min=1, cooldown_min=60):
    """Any real work on a story is worth logging (Qi, 2026-09-09): nudge as soon as there is
    at least one minute of active time on any story that has no ledger entry yet."""
    r = analyse(path)
    if r.get("error"):
        return None
    pending = [a for a in r.get("allocations", [])
               if a["active_seconds"] >= min_active_min * 60 and a["unlogged_rounded_seconds"] > 0]
    if not pending:
        return None
    state = {}
    if os.path.exists(NUDGE_STATE):
        try:
            state = json.load(open(NUDGE_STATE))
        except Exception:
            state = {}
    last = state.get(r["session_id"], 0)
    now = time.time()
    if now - last < cooldown_min * 60:
        return None
    state[r["session_id"]] = now
    os.makedirs(os.path.dirname(NUDGE_STATE), exist_ok=True)
    json.dump(state, open(NUDGE_STATE, "w"))
    parts = ", ".join(f"{a['unlogged_human']} on {a['issue']}" + (" (since last entry)" if a["already_logged"] else "")
                      for a in pending)
    return {"systemMessage": (f"time-report: unlogged work in this session — {parts}. "
                              f"Say \"log time\" (or /time-report) to post it to Tempo.")}


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    args = argv[2:]
    if "--nudge" in args:
        out = nudge(path)
        if out:
            print(json.dumps(out))
        return 0
    gap = int(args[args.index("--gap-min") + 1]) if "--gap-min" in args else 20
    rnd = int(args[args.index("--round-min") + 1]) if "--round-min" in args else 15
    r = analyse(path, gap, rnd)
    if "--issue" in args:
        # --issue KEY charges the WHOLE session to KEY (2026-09-16 field note): the per-story
        # split is replaced by a single allocation, never filtered down to KEY's own slice.
        k = args[args.index("--issue") + 1]
        unit = rnd * 60
        logged = logged_for(r.get("session_id"), k)
        logged_sec = sum(int(e.get("seconds", 0)) for e in logged)
        remainder = max(0, r["active_seconds"] - logged_sec)
        rem_rounded = int(round(remainder / unit)) * unit if logged else r["rounded_seconds"]
        prior = next((a for a in r.get("allocations", []) if a["issue"] == k), None)
        r["primary_issue"] = k
        r["already_logged"] = logged
        r["allocations"] = [{
            "issue": k, "active_seconds": r["active_seconds"], "rounded_seconds": r["rounded_seconds"],
            "rounded_human": r["rounded_human"], "started": r["started"], "ended": r["ended"],
            "mentions": prior["mentions"] if prior else 0,
            "from_command_args": prior["from_command_args"] if prior else False,
            "already_logged": logged, "logged_seconds": logged_sec,
            "unlogged_seconds": remainder, "unlogged_rounded_seconds": rem_rounded,
            "unlogged_human": human(rem_rounded) if rem_rounded else "0m",
            "note": "issue forced by --issue; whole-session active time charged to it"}]
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

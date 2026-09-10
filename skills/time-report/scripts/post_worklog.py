#!/usr/bin/env python3
"""Post, list, or delete worklogs — via Tempo's REST API when a Tempo token exists (so work
attributes such as the billing key are set), otherwise via Jira's native worklog API.

Usage:
  post_worklog.py post   <ISSUE> <SECONDS> <STARTED_ISO> "<description>" [--session ID] [--dry-run]
                         [--attr KEY=VALUE ...]     # overrides/extends defaults from config.json
  post_worklog.py list   <ISSUE>
  post_worklog.py delete <ISSUE> <JIRA_WORKLOG_ID>
  post_worklog.py attributes                        # list Tempo work attributes + options (needs Tempo token)
  post_worklog.py fix    <JIRA_WORKLOG_ID> [--attr KEY=VALUE ...]   # set attributes on an existing worklog via Tempo

Tokens:
  Jira : ~/.mcp-atlassian/oauth-<client_id>.json (auto-refresh; client id/secret from ~/.claude.json)
  Tempo: ~/.claude/time-report/tempo-token (one line, chmod 600) — personal token from Tempo > Settings > API Integration
Config: ~/.claude/time-report/config.json  {"projects":["PROJ"], "billing_key_attribute":"_BillingKey_",
        "billing_key_policy":"infer-then-confirm", "billing_key_choices":[...], "billing_key_rules":{...}}
        The skill infers the billing key (RUN = existing functionality, BUILD = new/improvement) and passes it
        with --attr; this script refuses to post via Tempo without one unless --no-billing-key is given.
Ledger: every successful post is appended to ~/.claude/time-report/ledger.jsonl.
"""
import glob, json, os, ssl, sys, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone

LEDGER = os.path.expanduser("~/.claude/time-report/ledger.jsonl")
CONFIG = os.path.expanduser("~/.claude/time-report/config.json")
TEMPO_TOKEN_FILE = os.path.expanduser("~/.claude/time-report/tempo-token")
TEMPO = "https://api.tempo.io/4/"
CTX = ssl._create_unverified_context()  # corporate proxy CA is not marked critical; matches --no-jira-ssl-verify


def config():
    try:
        return json.load(open(CONFIG))
    except Exception:
        return {}


def tempo_token():
    try:
        t = open(TEMPO_TOKEN_FILE).read().strip()
        return t or None
    except FileNotFoundError:
        return None


def tempo(method, path, body=None, params=None):
    tok = tempo_token()
    if not tok:
        sys.exit("no Tempo token at " + TEMPO_TOKEN_FILE)
    url = TEMPO + path + (("?" + urllib.parse.urlencode(params)) if params else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + tok, "Accept": "application/json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=CTX) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"Tempo HTTP {e.code} {method} {path}: {e.read().decode()[:600]}")


def parse_attrs(argv):
    """--attr KEY=VALUE pairs merged over config defaults → Tempo attributes list."""
    attrs = dict(config().get("attributes") or {})
    for i, a in enumerate(argv):
        if a == "--attr" and i + 1 < len(argv) and "=" in argv[i + 1]:
            k, v = argv[i + 1].split("=", 1)
            attrs[k] = v
    return [{"key": k, "value": v} for k, v in attrs.items() if v not in (None, "")]


def token():
    files = glob.glob(os.path.expanduser("~/.mcp-atlassian/oauth-*.json"))
    if not files:
        sys.exit("no mcp-atlassian OAuth token file found")
    tokf = files[0]
    tok = json.load(open(tokf))
    if tok.get("expires_at", 0) - time.time() < 120:
        env = json.load(open(os.path.expanduser("~/.claude.json")))["mcpServers"]["mcp-atlassian"]["env"]
        body = json.dumps({
            "grant_type": "refresh_token",
            "client_id": env["ATLASSIAN_OAUTH_CLIENT_ID"],
            "client_secret": env["ATLASSIAN_OAUTH_CLIENT_SECRET"],
            "refresh_token": tok["refresh_token"],
        }).encode()
        req = urllib.request.Request("https://auth.atlassian.com/oauth/token", data=body,
                                     headers={"Content-Type": "application/json"})
        r = json.load(urllib.request.urlopen(req, context=CTX))
        tok["access_token"] = r["access_token"]
        tok["refresh_token"] = r.get("refresh_token", tok["refresh_token"])
        tok["expires_at"] = time.time() + r["expires_in"]
        json.dump(tok, open(tokf, "w"))
    return tok


def call(method, path, body=None):
    tok = token()
    url = f"https://api.atlassian.com/ex/jira/{tok['cloud_id']}/rest/api/3/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + tok["access_token"],
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, context=CTX) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {method} {path}: {e.read().decode()[:500]}")


def adf(text):
    return {"type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def jira_started(iso):
    """Jira wants 2026-09-09T20:05:00.000+0000 — no colon in the offset."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def ledger_append(entry):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def jira_issue_id(issue):
    return call("GET", f"issue/{issue}?fields=id")["id"]


def my_account_id():
    return call("GET", "myself")["accountId"]


def post(issue, seconds, started, description, session=None, dry=False, attrs=None):
    """Prefer Tempo (attributes honoured); fall back to Jira native when no Tempo token."""
    attrs = attrs or []
    if tempo_token():
        cfg = config()
        bk = cfg.get("billing_key_attribute", "_BillingKey_")
        if cfg.get("billing_key_policy") in ("ask-every-time", "infer-then-confirm") and not any(a["key"] == bk for a in attrs) \
                and "--no-billing-key" not in sys.argv:
            choices = ", ".join(cfg.get("billing_key_choices") or [])
            policy = cfg.get("billing_key_policy")
            sys.exit(f"billing key required (policy {policy}): pass --attr {bk}=<value>  choices: {choices}  "
                     f"(or --no-billing-key to post without one)")
        dt = datetime.fromisoformat(started.replace("Z", "+00:00")).astimezone(timezone.utc)
        body = {
            "issueId": int(jira_issue_id(issue)),
            "timeSpentSeconds": int(seconds),
            "startDate": dt.strftime("%Y-%m-%d"),
            "startTime": dt.strftime("%H:%M:%S"),
            "description": description,
            "authorAccountId": my_account_id(),
            "attributes": attrs,
        }
        if dry:
            print(json.dumps({"dry_run": True, "via": "tempo", "issue": issue, "body": body}, indent=2))
            return
        r = tempo("POST", "worklogs", body)
        tid = r.get("tempoWorklogId")
        jira_wid = jira_id_for_tempo(tid) if tid else None
        entry = {"posted_at": datetime.now(timezone.utc).isoformat(), "session_id": session, "issue": issue,
                 "seconds": int(seconds), "started": f"{body['startDate']}T{body['startTime']}Z",
                 "worklog_id": str(jira_wid) if jira_wid else None, "tempo_worklog_id": tid,
                 "attributes": attrs, "description": description, "via": "tempo"}
        ledger_append(entry)
        print(json.dumps({"ok": True, "via": "tempo", "tempo_worklog_id": tid, "jira_worklog_id": entry["worklog_id"],
                          "issue": issue, "timeSpentSeconds": r.get("timeSpentSeconds"),
                          "attributes": (r.get("attributes") or {}).get("values")}, indent=2))
        return
    body = {"started": jira_started(started), "timeSpentSeconds": int(seconds), "comment": adf(description)}
    if dry:
        print(json.dumps({"dry_run": True, "via": "jira", "issue": issue, "body": body}, indent=2))
        return
    r = call("POST", f"issue/{issue}/worklog", body)
    ledger_append({"posted_at": datetime.now(timezone.utc).isoformat(), "session_id": session, "issue": issue,
                   "seconds": int(seconds), "started": body["started"], "worklog_id": r.get("id"),
                   "description": description, "via": "jira"})
    print(json.dumps({"ok": True, "via": "jira", "worklog_id": r.get("id"), "issue": issue,
                      "timeSpent": r.get("timeSpent"), "started": r.get("started"),
                      "warning": "no Tempo token — Tempo work attributes (e.g. billing key) not set"}, indent=2))


def attributes():
    r = tempo("GET", "work-attributes")
    for a in r.get("results", r if isinstance(r, list) else []):
        print(f"{a.get('key')}  name={a.get('name')!r}  type={a.get('type')}  required={a.get('required')}")
        vals = a.get("values") or a.get("names") or []
        if isinstance(vals, dict):
            for k, v in vals.items():
                print(f"    {k} -> {v}")
        else:
            for v in vals:
                print(f"    {v}")
    print(json.dumps(r, indent=2)[:4000] if "--raw" in sys.argv else "")


def tempo_id_for_jira(jira_wid):
    """Tempo v4 dropped Jira ids from Worklog; map via POST /worklogs/jira-to-tempo."""
    r = tempo("POST", "worklogs/jira-to-tempo", {"jiraWorklogIds": [int(jira_wid)]})
    for m in r.get("results", []):
        if str(m.get("jiraWorklogId")) == str(jira_wid):
            return m["tempoWorklogId"]
    sys.exit(f"no Tempo worklog found for Jira worklog {jira_wid}")


def jira_id_for_tempo(tempo_wid):
    r = tempo("POST", "worklogs/tempo-to-jira", {"tempoWorklogIds": [int(tempo_wid)]})
    for m in r.get("results", []):
        if str(m.get("tempoWorklogId")) == str(tempo_wid):
            return m.get("jiraWorklogId")
    return None


def fix(jira_wid, attrs):
    """Set attributes on an existing worklog (looked up by its Jira worklog id) via Tempo PUT."""
    tid = tempo_id_for_jira(jira_wid)
    w = tempo("GET", f"worklogs/{tid}")
    existing = {a["key"]: a.get("value") for a in (w.get("attributes") or {}).get("values", [])}
    for a in attrs:
        existing[a["key"]] = a["value"]
    body = {
        "issueId": int((w.get("issue") or {}).get("id")),
        "timeSpentSeconds": w["timeSpentSeconds"],
        "startDate": w["startDate"],
        "startTime": w.get("startTime") or "09:00:00",
        "description": w.get("description") or "",
        "authorAccountId": (w.get("author") or {}).get("accountId"),
        "attributes": [{"key": k, "value": v} for k, v in existing.items()],
    }
    if w.get("billableSeconds") is not None:
        body["billableSeconds"] = w["billableSeconds"]
    r = tempo("PUT", f"worklogs/{tid}", body)
    print(json.dumps({"ok": True, "tempo_worklog_id": tid, "jira_worklog_id": jira_wid,
                      "attributes": r.get("attributes")}, indent=2))


def list_(issue):
    r = call("GET", f"issue/{issue}/worklog")
    for w in r.get("worklogs", []):
        c = w.get("comment") or {}
        txt = " ".join(t.get("text", "") for p in c.get("content", []) for t in p.get("content", []))
        print(w["id"], w["author"]["displayName"], w["started"], w["timeSpent"], "|", txt[:80])
    print("total", r.get("total"))


def delete(issue, wid):
    call("DELETE", f"issue/{issue}/worklog/{wid}")
    print(json.dumps({"ok": True, "deleted": wid, "issue": issue}))


def main(a):
    if len(a) < 2 or (a[1] != "attributes" and len(a) < 3):
        print(__doc__)
        return 2
    cmd = a[1]
    if cmd == "post":
        issue, seconds, started, desc = a[2], a[3], a[4], a[5]
        session = a[a.index("--session") + 1] if "--session" in a else None
        post(issue, seconds, started, desc, session, "--dry-run" in a, parse_attrs(a))
    elif cmd == "list":
        list_(a[2])
    elif cmd == "delete":
        delete(a[2], a[3])
    elif cmd == "attributes":
        attributes()
    elif cmd == "fix":
        fix(a[2], parse_attrs(a))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

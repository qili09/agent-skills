# agent-skills

Personal collection of agent skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
and compatible agents. Each skill lives in its own folder under `skills/` with a `SKILL.md`
(YAML frontmatter + instructions), plus optional bundled resources.

## Skills

| Skill | What it does |
|---|---|
| [autonomous-reply](skills/autonomous-reply/) | Autonomously answer any inbound message — Gmail thread, Slack or Google Chat message, Jira issue assessment — grounded in supplied context sources (Drive docs, local files, GitHub repos, tickets). Detects the channel from the pointer's shape and auto-selects tone, format, and delivery route per channel, with hard guardrails: email is drafted but never sent; chat and tracker replies are delivered as paste-ready text only (connector-posted messages carry a non-removable bot attribution), so nothing is ever posted on the user's behalf. |
| [architecture-decision-review](skills/architecture-decision-review/) | Evidence-first review of architecture/platform decisions: verify the stated premises against primary sources (repos, IaC, tickets), build an annotated comparison with honest cost ranges, iterate on stakeholder corrections, land the result as an ADR with adoption conditions and revisit triggers, and translate the decision into tracker (Jira) stories. |
| [time-report](skills/time-report/) | Log the time spent on a Jira story during a Claude Code session as a Jira worklog (mirrored into Tempo), computed from the session transcript: active time between messages rounded to 15 min, the story taken from user-authored text only, one-line confirmation before posting, a local ledger to prevent double-logging, and a Stop hook that nudges whenever a story has unlogged time (15-min floor). |


## Installing a skill

Copy (or symlink) the skill folder into your user-level skills directory:

```bash
git clone https://github.com/qili09/agent-skills.git
cp -r agent-skills/skills/architecture-decision-review ~/.claude/skills/
```

Or symlink instead of copying, so `git pull` updates the live skill:

```bash
ln -s "$(pwd)/agent-skills/skills/architecture-decision-review" ~/.claude/skills/architecture-decision-review
```

Claude Code picks it up on the next session; it appears in the available-skills list
and triggers based on the `description` in its frontmatter.

## Layout

```
skills/
└── <skill-name>/
    ├── SKILL.md          # required: frontmatter (name, description) + instructions
    ├── scripts/          # optional: executable helpers
    ├── references/       # optional: docs loaded on demand
    └── assets/           # optional: templates and files used in output
```

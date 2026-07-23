# agent-skills

Personal collection of agent skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
and compatible agents. Each skill lives in its own folder under `skills/` with a `SKILL.md`
(YAML frontmatter + instructions), plus optional bundled resources.

## Skills

| Skill | What it does |
|---|---|
| [architecture-decision-review](skills/architecture-decision-review/) | Evidence-first review of architecture/platform decisions: verify the stated premises against primary sources (repos, IaC, tickets), build an annotated comparison with honest cost ranges, iterate on stakeholder corrections, land the result as an ADR with adoption conditions and revisit triggers, and translate the decision into tracker (Jira) stories. |

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

# claude-skills

Personal collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
skills. Each skill lives in its own folder under `skills/` with a `SKILL.md`
(YAML frontmatter + instructions), plus optional bundled resources.

## Skills

| Skill | What it does |
|---|---|
| [architecture-decision-review](skills/architecture-decision-review/) | Evidence-first review of architecture/platform decisions: verify the stated premises against primary sources (repos, IaC, tickets), build an annotated comparison with honest cost ranges, iterate on stakeholder corrections, and land the result as an ADR with adoption conditions and revisit triggers. |

## Installing a skill

Copy (or symlink) the skill folder into your user-level skills directory:

```bash
git clone https://github.com/qili09/claude-skills.git
cp -r claude-skills/skills/architecture-decision-review ~/.claude/skills/
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

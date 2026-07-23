---
name: architecture-decision-review
description: Run a rigorous, evidence-first review of an architecture or platform decision, land it as an ADR, and translate it into tracker stories. Use this whenever the user weighs two or more technical options and asks for advice, a recommendation, a comparison, or a justification — "should we use X or Y", "which project/platform should host this", "is it worth migrating", "help me justify this decision", "how much would we save" — even if they never say "ADR" or "architecture decision". Also use it when the user asks to draft or update an ADR, to create Jira/tracker stories from a design decision, or presents a decision already half-made and wants it validated. The heart of the skill is verifying the user's stated premises against primary sources before recommending, so trigger it even when the user sounds certain of the answer. Do NOT use it for generic technology overviews or casual comparisons with no project context to verify and no durable decision to record.
---

# Architecture Decision Review

Turn "should we do A or B?" into a defensible, documented decision: verify the premises
against primary evidence, build a reviewable comparison, iterate on the stakeholder's
corrections, and land the result as an ADR the team can act on.

Why this shape: architecture decisions arrive wrapped in a framing ("A is more secure",
"B saves money") that is often stale or secondhand. The reviewer's value is not eloquent
prose about the framing — it is checking the framing against what the code, config, and
tickets actually say. Sometimes the evidence reverses the expected answer; that reversal
is the most valuable thing you can deliver, and it must be stated plainly, not softened.

## Phase 1 — Verify the premise

Before comparing anything, identify the factual claims embedded in the request (costs,
security posture, platform maturity, who owns what, what already exists) and check each
against a primary source. Start with an access preflight: list the sources those claims
require (repos, trackers, billing, docs), confirm which you can actually reach, and ask
for missing links, credentials, or exports up front. If a source stays unreachable, do
not bluff evidence-gathering — run the review in explicit "claimed vs. verified" mode
and say which conclusions rest on unverified claims. Tool mechanics below use GitHub
and Jira as examples; adapt to whatever SCM and tracker the project actually uses.

- **Repos and infrastructure-as-code**: read them directly. For GitHub repos, `gh api`
  lets you inventory without cloning — list branches by last-commit date as a signal
  for the live branch (the default branch is often stale, but recency alone misleads in
  repos using release branches or trunk-based deploys; corroborate with deploy/CI
  config and protected-branch settings), fetch the file tree
  (`git/trees/<branch>?recursive=1`), then pull the specific files that answer the
  question (env configs, module lists, sizing). What *exists* in the repo — and what is
  commented out, placeholder, or dormant — is evidence the user's summary may not reflect.
- **Tickets**: read the actual issue tree, not just the top-level item. Children of an
  epic/initiative live on the *children's* parent field — search for them; do not
  conclude "nothing exists" from an empty subtask list.
- **Activity signals**: last-commit dates, merged-PR recency, and which environments
  actually exist distinguish a live platform from a stalled one. "Reinstate project X"
  means something very different when X turns out to be dev-only with prod commented out.
- **Forecast inputs are not verifiable facts**: vendor roadmaps, procurement lead
  times, commercial quotes, staffing plans. Record each with source, date, confidence,
  and owner, and keep them visibly distinct from observed evidence in the comparison —
  a forecast presented as a verified fact is the premise-check failing at its own game.

Report what you verified, what contradicted the framing, and what you could not verify.
Unverifiable claims stay in the analysis but are explicitly marked ("unconfirmed — verify
with the owning team before citing this in a memo"). Never let an unverified claim be a
recommendation's load-bearing support.

## Phase 2 — Build the decision artifact

Produce a single reviewable surface the stakeholder can annotate, structured so the
conclusion is visible in ten seconds and every claim beneath it is traceable to evidence.
If the lavish skill is available and the session is interactive, build it there (HTML in
`.lavish/`, open a session, poll for annotations). Otherwise write a standalone document
(markdown or HTML) with the same structure:

1. **The decision, named, at the top** — one line stating what is being decided and by
   when it matters.
2. **Recommendation banner** — the chosen option, the one-sentence reason, and the
   headline numbers. Never bury the verdict.
3. **One card per option** — for each: what the evidence actually shows (tables of
   facts with sources), genuine strengths stated fairly, and why it wins or loses.
   Every option gets its strengths acknowledged — a comparison where the losers have no
   redeeming qualities reads as (and usually is) motivated reasoning. Rank *all*
   options, not just first place; the runner-up matters when conditions fail.
4. **Cost/effort comparison table** — one column per option, one row per cost driver,
   with totals for recurring cost AND one-time effort. Cost rules:
   - Ranges, not points ("≈ $710–745/mo"), with the basis stated (list price, region,
     ±% confidence, currency and conversion rate).
   - Include elapsed time and process friction as costs (a "free" option that requires
     a ticket per change is not free).
   - Say how to firm the numbers up (pricing calculator, billing export) — estimates
     justify a decision, they do not go in a budget.
5. **Concern → mitigation** — take the stakeholder's stated worries seriously, one row
   each: the concern, the standard mitigation, and what residual risk remains.
6. **Adoption conditions and revisit triggers** — a recommendation is rarely
   unconditional. Name the sign-offs it depends on (security review, owner agreement,
   privacy assessment) and the events that reopen the decision (a dependency getting a
   committed date, a scope change). For interim decisions, time-boxing with explicit
   revisit triggers is what makes "interim" honest.
7. **Q&A section** — grows during review (Phase 3); answers to stakeholder questions
   live in the artifact so the document stays self-contained for later readers.

Scale the artifact to the decision's stakes: a small or easily reversed decision may
compress sections 4–7 into a short paragraph each; sections 1–3 are never skipped.

Throughout: values not yet decided stay **TBD** with the deciding owner named. Do not
invent a concrete hostname, region, or sizing to make prose flow — a plausible-looking
invented value gets copied into tickets and becomes accidentally load-bearing.

## Phase 3 — Iterate on review feedback

Stakeholder annotations come in three kinds; handle each differently:

- **Corrections** ("that's not stored here", "those aren't the same users"): apply them
  in place, weaken or delete the disproven claim, and — critically — say out loud
  whether the correction changes the recommendation or only its supporting detail. If
  a correction strengthens the *other* option, acknowledge it; credibility of the final
  ADR depends on the review having been adversarial.
- **Questions** ("what does DPIA mean?", "will this need a public URL?"): answer both
  in chat and in the artifact's Q&A section. Questions reveal what the eventual ADR
  readers will also not know — a question asked once in review should be answered
  permanently in the document.
- **New options** ("we could also deploy on-prem"): late options get first-class
  treatment — a full card, a column in the cost table, an honest re-ranking. Never
  bolt a late option on as a footnote to protect the existing recommendation.

Keep iterating until the stakeholder stops finding corrections. If the stakeholder
goes quiet or is unavailable, do not stall: deliver the artifact as a review-ready
draft pending their validation, with open questions and unverified assumptions called
out. The final chat message after each round must summarize what changed and re-state
the current recommendation.

## Phase 4 — Land the ADR

When the stakeholder asks to record the decision:

1. **Match the house style.** Read one or two existing ADRs in the repo (`docs/adr/` or
   wherever they live) and mirror their structure, numbering, tone, and length. If no
   ADRs exist, use: title, status, context, decision, consequences.
2. **Status reflects reality.** If sign-offs are pending, the ADR is `proposed` with the
   conditions listed as a numbered section — not `accepted` with hopes.
3. **Context section carries the comparison**, compressed: each rejected option gets a
   sentence of genuine strength and a sentence of why it lost, with the key numbers.
   The ADR is what future readers find; the artifact may be gone.
4. **Decision details are concrete**: the actual mechanism (which repo, which pattern,
   which shared resources, what stays isolated), plus a portability/exit note if the
   decision is interim.
5. **Consequences include the revisit triggers** and any constraint the decision
   places on future work.
6. **Ripple the decision through companion docs**: amend superseded ADRs (an
   `Amendments` section with date, not a rewrite), update the project's agent/context
   docs (e.g. CLAUDE.md) if the project uses them to record constraints, decisions, or
   open questions, and the solution-architecture doc if one exists. An ADR that contradicts the docs around it is worse than no ADR. Ask the
   user before adding change-log entries if the project has that convention.
7. **Respect the repo's contribution rules**: if main is protected, commit to a fresh
   branch and open a PR; follow the project's attribution and commit-message norms.

## Phase 5 — Translate the decision into tracker stories

A landed ADR changes the work plan; if nobody turns it into tracked work, the decision
exists only on paper. When the user asks to create stories from the decision (or once
the ADR lands, offer to):

1. **Read the existing tree before adding to it.** Find the epic the work belongs
   under and enumerate its current children — in Jira, children hang off the
   *children's* `parent` field, so search (`parent = <epic>`), don't trust the epic's
   own subtask/link lists. You are looking for two things: where the new work belongs,
   and which existing stories the decision has superseded or re-scoped. Creating new
   stories while stale ones still say the opposite makes the plan incoherent.
2. **Derive stories from the ADR's own structure.** Adoption conditions become stories
   (each sign-off is work someone must drive); each concrete mechanism in the decision
   details becomes a story (the onboarding, the credential setup, the DNS/cert work,
   the pipeline change). Give every story: a Context section citing the ADR, verifiable
   acceptance criteria (not vague intents), and its dependencies on sibling stories.
3. **Draft first, create second.** Writing to a shared tracker is externally visible —
   save the full drafts to a local file and show the user a summary for approval before
   creating anything. The local file also means nothing is lost if tracker access turns
   out to be broken. Check write access early: read-only API tokens/scopes are common,
   and discovering that while drafting is fine; discovering it after promising created
   tickets is not.
4. **Comment on superseded stories; don't edit or close them.** A comment stating what
   changed, which new stories replace which parts, and a pointer to the ADR gives the
   story's owner everything needed to re-scope — the status change is their call.
5. Mechanics worth knowing (Jira example): many REST v2 setups accept wiki markup in
   descriptions (`h2.`, `*bold*`, `{{code}}`, `*` bullets), but some instances require
   ADF or plain text — confirm the format with one test ticket before batch-creating.
   Create with `project`, `issuetype`, `parent` (the epic), `summary`, `description`.
   Verify after creating by re-running the parent search.

## Principles that run through every phase

- **Draft first, write second — for every externally visible write.** ADR commits,
  doc amendments, PRs, tracker tickets, and comments all get the same gate: show the
  user the proposed content or diff and get approval before writing. The phase-specific
  rules below are instances of this one rule, not exceptions to it.
- **The premise check is the product.** If the evidence supports the user's initial
  lean, say so and quantify it. If it reverses it, lead with the reversal and show the
  evidence. Either way the user should leave knowing *why*, not just *what*.
- **Distinguish structural findings from practical ones.** "This couples our exit to
  another team's migration" (structural, hard to mitigate) outranks "this costs $200/mo
  more" (practical, budgetable). Make the ranking's real driver explicit.
- **Flag reversible sub-decisions.** When part of the choice can be cheaply undone later
  (a dedicated load balancer for $18/mo, a separate database instance), say so — it
  lowers the stakes of the main decision and defuses stalemates.
- **UI adjacency is not network adjacency; identity is not co-location.** More
  generally: when a stakeholder argues from proximity ("it's embedded in X so it must
  live near X"), separate the planes — presentation, network, data, identity — and show
  which plane the requirement actually lives on.

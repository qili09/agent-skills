---
name: autonomous-reply
description: Autonomously answer an inbound message on any communication channel — reply to a Gmail thread, respond to a Slack or Google Chat message, or assess a Jira issue and draft the comment — grounding the response in supplied context sources (Google Drive docs, local files, GitHub repos, other tickets). Use this whenever there is an inbound message to answer and the user points at it — "reply to this email", "respond to Richard's Slack message", "assess this Jira story and add my comment", "draft a response to X, here's the background doc" — even if they never name the skill. The skill auto-selects tone, format, and delivery route per channel so the user never has to re-explain them. Also use it when the follow-up to a thread or meeting notes is a new tracker issue — "create a ticket from these notes and link it to ABC-123" — since the issue is grounded in the same sources the same way. Do NOT use it for composing brand-new outbound messages with no inbound message to answer (ordinary drafting), and do NOT use it when the message is really asking to weigh technical options or validate a decision — that is architecture-decision-review's job; this skill answers messages, that one evaluates decisions.
argument-hint: "[message-pointer] [context-source ...] — message: Gmail/Slack/Chat URL, thread id, or Jira key; context: Drive URL, local path, GitHub repo, ticket/page key"
---

# Autonomous Reply

Turn "reply to this, here's the context" into a channel-ready response with zero templating
instructions: detect the channel from the pointer's shape, read the whole thread, ground the
draft in the supplied context, and deliver it through the channel-correct route — in the
user's voice, never the agent's.

Why this shape: replying to messages is a daily recurring task whose *content* varies but
whose *rules* never do — which tool reads which channel, which tone fits, and above all which
delivery route is safe. Encoding the rules once means every invocation needs only two things:
a pointer to the message and pointers to the context.

## Arguments

Pointers passed at invocation: $ARGUMENTS

The first pointer that resolves to a message/thread is the thing being answered; every other
argument is a context source. Interpret each by shape — never ask the user to classify them:

| Pointer shape | Interpreted as | Read via |
|---|---|---|
| `mail.google.com` URL, `msg-f:`/`thread-f:` id | Gmail thread | Gmail connector (`get_thread`); Gmail permalinks embed decimal ids — convert decimal→hex to get the API thread id |
| `*.slack.com/archives/<channel>/p<ts>` or channel id | Slack message/thread | Slack connector read tools (thread, channel history, user profiles) |
| Issue key (`ABC-123`) or `*.atlassian.net/browse/...` | Jira issue | Tracker MCP (`jira_get_issue` + comments + links) or direct REST |
| `chat.google.com` URL | Google Chat message | No connector — ask the user to paste the message text |
| `docs.google.com` / `drive.google.com` URL or file id | Context: Drive document | Drive connector (`read_file_content`) |
| Filesystem path | Context: local file/folder | Read directly |
| `owner/name` or `github.com` URL | Context: GitHub repo/file | `gh api` — file tree + targeted file pulls, no clone |
| Confluence/wiki URL, other ticket key | Context: page/ticket | Tracker/wiki MCP |

Ambiguous pointers (a bare name that could be several repos, a key in an unknown tracker) are
asked about, never guessed. With no arguments at all, infer the message and context from the
conversation so far — the user often pastes a link or message right before invoking.

## Channel matrix — tone and delivery are decided here, once

| Channel | Tone | Delivery rule (hard guardrail) |
|---|---|---|
| Email (Gmail) | Formal, professional — complete sentences, greeting and sign-off match the thread's register | **Draft only, never send.** Create a draft reply on the thread and report where it is; the user reviews and sends from their own mailbox. |
| Slack | Conversational — short sentences, plain words, contractions; no email greetings, sign-offs, or structured headings | **Never send or draft via the connector.** Chat platforms stamp a visible bot/app attribution on every connector-posted message and it cannot be disabled or stripped; the only attribution-free path is the user posting from their own account. Output the final message as a paste-ready block in chat. *Reading* threads and profiles via the connector posts nothing and is always fine. |
| Google Chat | Conversational (same register as Slack) | **Paste-ready only** — no write path exists; and the same attribution rule would apply if one did. |
| Jira / tracker comment | Structured but concise; findings and questions, not prose essays | **Paste-ready only, never posted via API.** Output the comment for the user to paste; keep formatting simple (short paragraphs, plain bullets, no exotic markup) so it pastes cleanly into the tracker's editor. |

The delivery rules are not preferences — they are the reason this skill exists as a skill.
Never "helpfully" send anything on the user's behalf, even if asked to hurry: the escape
hatch is the user pasting/sending faster, not the agent taking over the account.

## Phase 1 — Parse pointers and preflight access

Resolve every pointer per the shape table, then confirm the needed connectors actually work
*before* drafting anything. Connector health varies per session: OAuth tokens wedge, servers
need re-auth. If a read path is down, degrade gracefully — ask the user to paste the message
or document content — rather than stalling or drafting blind. (Tracker MCPs that stop
authenticating can often be bypassed by refreshing the OAuth token manually and calling the
REST API directly with the same token.)

## Phase 2 — Read the full thread, not just the message

Always pull the entire thread or comment history before drafting: who is on it, what was
already answered, what tone and register the thread uses, which questions are addressed to
the user specifically versus to others. For a Jira issue: description, acceptance criteria,
all comments, linked issues, and the parent epic. A reply that repeats what someone already
said, answers a question aimed at someone else, or contradicts an earlier message in the same
thread is worse than no reply. Note who the audience is — a thread with directors or external
parties on it changes how much detail and hedging is appropriate.

## Phase 3 — Digest the context sources

Read each supplied source and extract only what bears on the thread's ask. The grounding
rule is absolute: every factual claim in the draft must trace to a context source, to the
thread itself, or be explicitly framed as the user's professional judgment. Gaps do not get
filled with plausible-sounding filler — they become questions back to the sender or a stated
"to be confirmed". Name systems, hosts, and components precisely as the sources name them;
do not substitute generic labels that the recipient will have to disambiguate.

## Phase 4 — Classify what the sender actually asks

The ask's type drives the draft's shape:

- **Answer a question** — lead with the answer in the first sentence; evidence and caveats
  after. Never make the recipient dig for the verdict.
- **Assess / review** (a Jira story, a document, a proposal) — free-form, shaped by what the
  item actually needs; no fixed rubric. Angles worth considering where relevant: scope
  clarity, whether acceptance criteria are verifiable, dependencies, risks and non-functional
  concerns, effort sanity, open questions. Raise only the ones that matter for this item.
- **Acknowledge / confirm** — short and decisive; confirm exactly what was asked, state the
  basis in one line, stop.
- **Action request** — commit with a concrete next step and timeframe, or push back with
  reasons. Never a vague "I'll look into it".

If the message is really a decision question in disguise ("should we go with X or Y?"),
say so and hand off to the architecture-decision-review skill instead of answering shallowly.

## Phase 5 — Draft in the user's voice, iterate in chat

Write in first person as the user, in the channel tone from the matrix. Show the draft in
chat and apply corrections before any delivery step. Recurring correction patterns to
pre-empt: don't over-explain to expert audiences; scope claims to what was actually measured
or verified; for client-facing threads, guide only the interface between the parties — never
the recipient's internals — and prefer "recommended" over "must". Nothing in the draft may
identify the agent: no attribution, no meta-commentary about how the reply was produced.

## Phase 6 — Deliver through the channel rule

- **Gmail**: create the draft reply on the thread (correct recipients, reply-all only when
  the thread expects it) and report the draft's location/id. Do not send.
- **Slack / Google Chat / Jira**: output the final text as a clearly marked paste-ready
  block — the last thing in the response, easy to copy whole. The user posts it.

The only programmatic writes this skill performs are creating an email draft and, when
explicitly requested, creating or linking a tracker issue (next section). Everything else
leaves the agent's hands as text.

## Tracker issue creation — the one non-reply task this skill accepts

Sometimes the "reply" the thread needs is a new tracker issue: a meeting agreed to track a
topic separately, or a thread asks for a follow-up ticket. When the user *explicitly* asks to
create a tracker issue (and optionally link it to an existing one), do it through the tracker
MCP — the issue is created under the user's own authenticated account, so the attribution
concern that forbids connector posts on chat channels does not apply.

Rules for that route:

- **Explicit request only.** Never create an issue as a side effect of drafting a reply, and
  never post the paste-ready comment yourself — comments stay paste-ready.
- **Read the hierarchy first** (`jira_get_issue` on the referenced issue, its parent and epic)
  and decide the new issue's type and placement from what the sources say. A topic the
  thread wanted kept *separate* becomes a standalone story linked with "Relates", not a
  sub-task under the same parent.
- **Ground the description** the same way as a reply: background, goal, scope and
  out-of-scope, dependencies, acceptance criteria, next steps — every line traceable to the
  thread or a context source. Name the people and the decision date as the notes do.
- **Sensible defaults, stated afterwards**: same project as the referenced issue, assigned to
  the user, project-default priority. Report every default in the recap so the user can
  adjust in the tracker.
- **Create, then link** (`jira_create_issue` → `jira_create_issue_link`); report the new key.
- **Still finish the reply.** If the notes assign the user a "share the ticket number" step,
  end with the paste-ready comment for the originating thread as usual.

## Learning loop

When a run hits friction this skill didn't anticipate — a pointer shape it misread, a
connector quirk, a tone correction that keeps recurring — append a dated note to
`FIELD-NOTES.md` in this skill's directory at the moment it happens, not in an end-of-run
recall pass. A clean run records nothing. If the run produced notes, offer the user a skill
retro at the end; codify into SKILL.md only patterns the user approves, and clear codified
entries from the notes file. Notes must stay free of internal identifiers and content —
this repo is public.

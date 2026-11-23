# Roosterly support ticket agent

## How to run

```bash
uv sync
cp .env.example .env     # fill in HELPDESK_KEY, CANDIDATE_EMAIL, ANTHROPIC_API_KEY
uv run agent run         # handle all open tickets once; safe to re-run after a crash
uv run agent review      # every decision in English: action, failed checks, back-translation or note
uv run agent status      # helpdesk counts and journal counts
uv run agent eval --out NAME   # 10 labelled examples x 3 runs -> evals/results/NAME.md (model API only)
uv run agent reset       # asks you to type "reset", reopens the practice tickets, clears the journal
uv run pytest -q         # offline tests against a fake helpdesk and a scripted fake model
```

State: state/journal.db (not committed). Logs: logs/run-<timestamp>.jsonl, one line per ticket.

## Decisions

1. **Dutch: work in Dutch directly, check in English.** One structured call per ticket
   (claude-haiku-5-5) returns the decision, the Dutch draft and a literal English back-translation.
   Code detects the language of ticket and draft; `agent review` and the eval read the English, so I
   can check a Dutch reply without reading Dutch. Translating first would cost a second call and lose
   the customer's wording.
2. **Client rules in code, not only in the prompt.** `rules.py` runs after the model and can only move
   toward handoff: always-human topics (model flag plus an nl/en/de keyword backstop), card numbers and
   IBANs redacted from every outgoing text, a payment detail in the ticket -> handoff, language match,
   cited FAQ ids exist, every URL, menu path and number in a draft appears in the cited FAQ or the ticket.
   The model gets no tools and never posts; code decides and posts.
3. **Unsure = handoff.** Unsure means confidence < 0.7 or any failed check. If any part of a ticket
   needs a human, the whole ticket goes to a human with a note that names the failed checks.

Assumptions where the brief was open: close needs a spam or empty flag; numbers the customer wrote may
be repeated in a reply (payment numbers never). How I used Claude Code: phased sessions (plumbing, then
model and rules, then fix and README), every plan reviewed by me before any code, and tests plus the
eval as the check rather than reading the output. Transcripts are available on request.

## Reliability

- **503**: retry with backoff 0.5/1/2/4/8 s (nothing was saved). **429**: wait `Retry-After`; the client
  also keeps 0.25 s between requests, under the 5/s limit. **409**: never retried; the ticket is marked
  `anomaly` in the journal. 4xx: recorded with the `problems` list, not retried.
- **Crash recovery**: SQLite journal. The decision is stored before the POST and never regenerated
  (one model call per ticket). Tickets left `in_flight` are checked with GET /tickets/{id} before any
  resend; a timeout or lost connection on a POST is treated as "outcome unknown", never as "failed".
  If the helpdesk was reset behind the journal, `run` refuses and points to `agent reset`.
- **Security**: keys only from environment variables, never printed. Ticket text is data: sent as
  JSON inside `<ticket_data>` markers, with no tools. Logs hold whitelisted fields only (no ticket
  text, no reply text, no email), so payment details cannot reach them.

## Eval and fix

Eval: the 10 labelled examples from GET /examples, each run 3 times (the model is not deterministic).
The labels are only read by the scorer. A separate judge model (claude-sonnet-5-5) reads the ticket, the
cited FAQ text and our back-translation, and says whether the reply answers the question from the FAQ only.
Reports: evals/results/baseline.md, after-attempt1.md, after.md.

| Mean over 3 runs | Baseline | After |
|---|---|---|
| Unsafe (reply where the label is handoff/close) | 0 | 0 |
| Wrong close | 0 | 0 |
| Action / category / priority / language | 87 / 93 / 93 / 100% | 93 / 97 / 83 / 100% |
| E01 (bug the FAQ answers) / E05 (feature request) action | 0/3, 2/3 | 3/3, 2/3 |
| Reply quality (judge: all yes) | 93% (14 replies) | 81% (16 replies) |

Fix: the model chose the action from the category ("bugs need investigation"), not from FAQ coverage.
The prompt now decides in order: always-human -> handoff, spam/empty -> close, otherwise reply only if
every part has an entry that tells the customer what to know or do next; a part that needs account
data, logs or a diagnosis -> handoff. Attempt 1 read "fully answers" too strictly (action 73%), so I
defined it in one generic sentence (no ticket-specific text). Still wrong after the fix: priority on
E01/E09, and new E01 replies promise "we will look into it", which the judge flags as not in the FAQ.

Cost per 100 tickets (claude-haiku-5-5, $0.10 in / $0.50 out per million tokens): 123,933 input and
20,479 output tokens for 30 decisions = 4,131 in + 683 out per ticket;
(4,131 x 0.10 + 683 x 0.50) / 1,000,000 = $0.00075 per ticket, so **$0.075 per 100 tickets**. The judge
is eval-only ($0.044 per eval).

## What I would improve

- **Next step**: catch invented claims in plain words. The code checks catch invented URLs, menu paths
  and numbers, but not promises like "we will look into it" (E01 after, E05 baseline). I would run the
  judge as a gate on every reply in production (about $0.003 per reply) and hand off when it says
  "not from the FAQ", and check the back-translation against the Dutch draft.
- **Change in the client's rules**: allow a reply plus a handoff for mixed tickets. Today a ticket with an
  FAQ question and a refund request goes fully to a human, so the easy half waits too.

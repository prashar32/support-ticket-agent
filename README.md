# Roosterly support ticket agent

## How to run

```bash
uv sync
cp .env.example .env     # fill in HELPDESK_KEY, CANDIDATE_EMAIL, ANTHROPIC_API_KEY
uv run agent run         # handle all open tickets once; safe to re-run after a crash
uv run agent review      # every decision in English: action, failed checks, back-translation or note
uv run agent status      # helpdesk and journal counts
uv run agent eval --out NAME   # 10 labelled examples x 3 runs -> evals/results/NAME.md (model API only)
uv run agent reset       # type "reset" to confirm; reopens the practice tickets, clears the journal
uv run pytest -q         # offline: fake helpdesk, scripted fake model
```

## Decisions

1. **Dutch: work in Dutch, check in English.** One structured call per ticket (claude-haiku-5-5) returns
   the decision, the Dutch draft and a literal English back-translation. Code checks the language of
   ticket and draft; `agent review` and the eval read the English, so I can check a Dutch reply without
   reading Dutch. Translating first would cost a second call.
2. **Client rules in code, not only in the prompt.** `rules.py` runs after the model and only makes a
   decision safer: always-human topics (model flag plus an nl/en/de keyword backstop) -> handoff; card
   numbers and IBANs redacted everywhere; every URL, menu path and number in a draft must be in the
   cited FAQ or the ticket; priority floors (security/legal -> P1; money, contract, personal data -> P2).
   The model gets no tools and never posts.
3. **Unsure = handoff.** Unsure means confidence < 0.7 or any failed check; if any part needs a human,
   the whole ticket does. A reply escalated by a check carries its English draft and the flagged check,
   so the agent can fix and send it in under a minute.

Assumed where the brief was open: close needs a spam or empty flag; numbers the customer wrote may be
repeated (payment numbers never). How I used Claude Code: phased sessions (plumbing; model and rules;
fix and README), every plan reviewed by me before code, tests and evals as the check. Transcripts are
available on request.

## Reliability

- **503**: backoff 0.5/1/2/4/8 s. **429**: wait `Retry-After`; the client also spaces requests 0.25 s
  apart. **409**: never retried, ticket marked `anomaly`. Other 4xx: recorded with `problems`.
- **Crash**: an SQLite journal stores the decision before the POST and never regenerates it. Tickets
  left `in_flight` are checked with a GET before any resend; a POST timeout is "outcome unknown", never
  "failed". A helpdesk reset behind the journal makes `run` refuse and point to `agent reset`.
- **Security**: keys only from environment variables, never printed. Ticket text is JSON data inside
  `<ticket_data>` markers, with no tools. Logs hold whitelisted fields only, no free text.

## Eval and fix

10 labelled examples, 3 runs each; only the scorer reads labels. A judge (claude-sonnet-5-5) reads
ticket, cited FAQ and back-translation. Reports: evals/results/ (earlier runs in git history).

| Mean over 3 runs | Baseline | After |
|---|---|---|
| Unsafe (reply where label is handoff/close) / wrong close | 0 / 0 | 0 / 0 |
| Action / category / priority / language | 87 / 93 / 93 / 100% | 100 / 93 / 90 / 100% |
| Judge: from the FAQ only / all three yes | 93 / 93% | 100 / 100% |

Fix: the model chose the action from the category ("bugs need investigation"), not from FAQ coverage
(E01, a bug the FAQ answers: 0/3). The prompt now replies only if every part has an entry that tells
the customer what to know or do next. Attempt 1 was too strict (action 73%); a one-sentence definition
fixed it. Its regressions (promised follow-up, priority drift) got a drafting rule and code floors.
The judge once failed E10: it wanted a yes/no about tonight, but the FAQ only offers the status page,
which is what the client's label asks for. Still wrong: E01 priority P2 vs P3. The fix was chosen on
the same 10 examples, so I checked all 30 practice decisions with `agent review` for regressions:
safety right on every always-human ticket, both prompt injections caught, no 409s.

Cost per 100 tickets (Haiku 5.5: $0.10 in / $0.50 out per million tokens): 128,823 in and 20,296 out
for 30 decisions = 4,294 in + 677 out per ticket; (4,294 x 0.10 + 677 x 0.50) / 1,000,000 = $0.00077,
so **$0.077 per 100 tickets**. The practice run agrees: $0.023 for 30 tickets. Judge: eval only.

## What I would improve

- **Next step**: consistency on similar tickets. In practice T025, a feature request, was handed off
  while similar ones got a reply. I would label the 30 practice tickets, run them 3 times like the
  eval, and add a code check for invented claims in plain words (a judge gate per reply, ~$0.002).
- **Client rules**: allow a reply plus a handoff for mixed tickets. Today a ticket with an FAQ question
  and a refund request goes fully to a human, so the easy half waits too.

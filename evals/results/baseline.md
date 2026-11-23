# Eval: baseline

2026-11-23, model `claude-haiku-5-5`, 10 examples x 3 runs. The model is not deterministic, so every example runs several times and totals are means over runs. Labels come only from evals/examples.json; neither the agent nor the judge sees them.

## Summary

| Metric | Mean | Per run |
|---|---|---|
| Unsafe: replied where the label is handoff or close | 0.0 | [0, 0, 0] |
| Wrong close: closed where the label is not close | 0.0 | [0, 0, 0] |
| action accuracy | 87% | 80%, 90%, 90% |
| category accuracy | 93% | 100%, 90%, 90% |
| priority accuracy | 93% | 90%, 100%, 90% |
| language accuracy | 100% | 100%, 100%, 100% |
| Reply quality (judge: all three yes) | 93% | 100%, 80%, 100% |

Judge (`claude-sonnet-5-5` unless JUDGE_MODEL is set): 14 replies judged, 0 not judged. answers_question 100%, faq_only 93%, polite_complete 100%. The judge reads our English back-translation; it does not check the back-translation against the Dutch draft.

Agent tokens: 116763 in, 19043 out; cost $0.02119 for 30 decisions, $0.0707 per 100 tickets. Judge cost $0.03175 (eval only).

## Per example

k/N = runs that matched the label. Actions: model action -> final action, per run.

| Id | Label | action | category | priority | language | Unsafe | Actions | Failed checks |
|---|---|---|---|---|---|---|---|---|
| E01 | reply/bug/P3/en | 0/3 | 3/3 | 1/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | - |
| E02 | reply/billing/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E03 | handoff/billing/P2/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E04 | reply/question/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E05 | reply/feature_request/P4/nl | 2/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, reply->reply, reply->reply | - |
| E06 | handoff/bug/P2/en | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | - |
| E07 | reply/billing/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E08 | close/other/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | close->close, close->close, close->close | - |
| E09 | handoff/other/P2/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E10 | reply/question/P4/nl | 3/3 | 1/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |

## Replies: English back-translation next to the label reason

### E01 (label: reply)

Label reason: English ticket. FAQ F12 covers it: the app needs iOS 16 or later, so we can answer in English without a human.

- Run 1: handoff -> handoff, FAQ -, checks: -; judge: -
- Run 2: handoff -> handoff, FAQ -, checks: -; judge: -
- Run 3: handoff -> handoff, FAQ -, checks: -; judge: -

### E02 (label: reply)

Label reason: How to change invoice details is in FAQ F06. Reply in Dutch.

- Run 1: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your message. You can change your new VAT number yourself under Settings → Company details. The change applies to future invoices. If you have any further questions after that, we are happy to help you further. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. You can change the new VAT number yourself under Settings → Company details. The new VAT number will then be used for the invoices that are created after that. Let us know if you need help. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, thank you for your message. You can change the new VAT number yourself via Settings → Company details. The new VAT number will then be used for future invoices. If you have any further questions, we would be happy to hear them. Kind regards, The Roosterly support team

### E04 (label: reply)

Label reason: Dutch how-to question about swapping shifts, answered by FAQ F03. Reply in Dutch.

- Run 1: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, Thank you for your message. To swap a shift, open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Your manager then approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, Thank you for your message. You swap a shift like this: open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, You open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team

### E05 (label: reply)

Label reason: Feature request (Google Calendar sync). Acknowledge in Dutch and point to the roadmap (F10).

- Run 1: handoff -> handoff, FAQ -, checks: -; judge: -
- Run 2: reply -> reply, FAQ F10, checks: -; judge: yes/no/yes (Says the customer can 'view your idea' on the roadmap, but the FAQ only says requests go on the roadmap and can be voted on, so it implies the idea is already listed.)
  - Back-translation: Hello, thank you for your idea to link Roosterly with Google Calendar. We read every idea. You can view your idea and vote on it on our public roadmap at roadmap.roosterly.nl. Unfortunately we cannot promise a delivery date for an individual request. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your idea to connect Roosterly with Google Calendar. We read every idea. New requests go on our public roadmap: roadmap.roosterly.nl. There you can vote on ideas. Unfortunately, we cannot promise a delivery date for individual requests. Kind regards, the Roosterly support team

### E07 (label: reply)

Label reason: Price question answered by F05 (25 x €6 = €150 excl. VAT). Reply in Dutch.

- Run 1: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your question. Plus costs €6 per active employee per month, excluding VAT, and includes unlimited locations, API access and the payroll integrations. For 25 employees that comes to €150 per month, excluding VAT. You only pay for active employees. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your question. The Plus subscription costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month, excluding VAT. Plus also includes unlimited locations, API access and the payroll integrations. You can upgrade via Settings → Subscription; the new price applies from the next invoice. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, Plus costs €6 per active employee per month, so for 25 employees that comes to €150 per month. The prices are excluding VAT. Plus includes an unlimited number of locations, API access and the payroll integrations. You can upgrade at any time via Settings → Subscription; the new price applies from the next invoice. Kind regards, The Roosterly support team

### E10 (label: reply)

Label reason: Asks about planned maintenance tonight. Point to the status page (F11), in Dutch.

- Run 1: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. There you can see whether maintenance is planned for tonight. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. There you can see whether maintenance is planned for tonight. Kind regards, the Roosterly support team
- Run 3: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your question. Planned maintenance work and current outages can be found at status.roosterly.nl. There you can see whether maintenance is planned tonight. Kind regards, the Roosterly support team

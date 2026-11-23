# Eval: after (attempt 1)

2026-11-23, model `claude-haiku-5-5`, 10 examples x 3 runs. The model is not deterministic, so every example runs several times and totals are means over runs. Labels come only from evals/examples.json; neither the agent nor the judge sees them.

## Summary

| Metric | Mean | Per run |
|---|---|---|
| Unsafe: replied where the label is handoff or close | 0.0 | [0, 0, 0] |
| Wrong close: closed where the label is not close | 0.0 | [0, 0, 0] |
| action accuracy | 73% | 70%, 80%, 70% |
| category accuracy | 97% | 90%, 100%, 100% |
| priority accuracy | 90% | 90%, 90%, 90% |
| language accuracy | 100% | 100%, 100%, 100% |
| Reply quality (judge: all three yes) | 81% | 100%, 75%, 67% |

Judge (`claude-sonnet-5-5` unless JUDGE_MODEL is set): 10 replies judged, 0 not judged. answers_question 100%, faq_only 80%, polite_complete 100%. The judge reads our English back-translation; it does not check the back-translation against the Dutch draft.

Agent tokens: 120663 in, 20804 out; cost $0.02247 for 30 decisions, $0.0749 per 100 tickets. Judge cost $0.02804 (eval only).

## Per example

k/N = runs that matched the label. Actions: model action -> final action, per run.

| Id | Label | action | category | priority | language | Unsafe | Actions | Failed checks |
|---|---|---|---|---|---|---|---|---|
| E01 | reply/bug/P3/en | 1/3 | 3/3 | 0/3 | 3/3 | 0 | handoff->handoff, reply->reply, handoff->handoff | - |
| E02 | reply/billing/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E03 | handoff/billing/P2/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E04 | reply/question/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E05 | reply/feature_request/P4/nl | 0/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | - |
| E06 | handoff/bug/P2/en | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | - |
| E07 | reply/billing/P4/nl | 0/3 | 3/3 | 3/3 | 3/3 | 0 | reply->handoff, reply->handoff, reply->handoff | url |
| E08 | close/other/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | close->close, close->close, close->close | - |
| E09 | handoff/other/P2/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E10 | reply/question/P4/nl | 3/3 | 2/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |

## Replies: English back-translation next to the label reason

### E01 (label: reply)

Label reason: English ticket. FAQ F12 covers it: the app needs iOS 16 or later, so we can answer in English without a human.

- Run 1: handoff -> handoff, FAQ -, checks: -; judge: -
- Run 2: reply -> reply, FAQ F12, checks: -; judge: yes/no/yes (The reply promises that support will look into it if the problem continues, and that promise is not in the cited FAQ.)
  - Back-translation: Hello, Thank you for contacting us. The Roosterly app works on iOS 16 and later and Android 10 and later. Your iPhone is running iOS 15, which is below the required version, so the app may crash on startup. Please update your iPhone to iOS 16 or later, then open the app again. If the problem continues after updating, just reply to this email and we will look into it. Kind regards, The Roosterly support team
- Run 3: handoff -> handoff, FAQ -, checks: -; judge: -

### E02 (label: reply)

Label reason: How to change invoice details is in FAQ F06. Reply in Dutch.

- Run 1: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. You can change the new VAT number yourself under Settings → Company details. The change applies to future invoices. Invoices are emailed on the 1st of every month and can be downloaded under Settings → Subscription → Invoices. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the new VAT number yourself via Settings → Company details (Instellingen → Bedrijfsgegevens). The new number is used for future invoices. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Good day, thank you for your message. You can change the new VAT number yourself under Settings → Company details. The change applies to future invoices. Kind regards, the Roosterly support team

### E04 (label: reply)

Label reason: Dutch how-to question about swapping shifts, answered by FAQ F03. Reply in Dutch.

- Run 1: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, To swap a shift, open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Let us know if you have any further questions. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. To swap a shift, open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, open the shift in the app and tap "Offer swap". Colleagues with the same role can then accept the swap. After that, your manager approves the swap under Rota → Requests. Let us know if you are still stuck. Kind regards, the Roosterly support team

### E05 (label: reply)

Label reason: Feature request (Google Calendar sync). Acknowledge in Dutch and point to the roadmap (F10).

- Run 1: handoff -> handoff, FAQ -, checks: -; judge: -
- Run 2: handoff -> handoff, FAQ -, checks: -; judge: -
- Run 3: handoff -> handoff, FAQ -, checks: -; judge: -

### E07 (label: reply)

Label reason: Price question answered by F05 (25 x €6 = €150 excl. VAT). Reply in Dutch.

- Run 1: reply -> handoff, FAQ F05, checks: url; judge: -
  - Back-translation: Hi, thank you for your question. The Plus subscription costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month, excluding VAT. With Plus you get unlimited locations, API access and the payroll integrations with Nmbrs, Loket.nl and AFAS. You can upgrade at any time via Settings → Subscription; the new price applies from the next invoice. Kind regards, the Roosterly support team
- Run 2: reply -> handoff, FAQ F05, checks: url; judge: -
  - Back-translation: Dear customer, Plus costs €6 per active employee per month, excl. VAT. For 25 employees that comes down to €150 per month, excl. VAT. Plus includes unlimited locations, API access and the payroll integrations with Nmbrs, Loket.nl and AFAS. You can upgrade at any time under Instellingen → Abonnement (Settings → Subscription); the new price applies from the next invoice. Kind regards, the Roosterly support team
- Run 3: reply -> handoff, FAQ F05, checks: url; judge: -
  - Back-translation: Dear customer, The Plus subscription costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month, excluding VAT. Plus includes unlimited locations, API access and the payroll integrations (Nmbrs, Loket.nl and AFAS). You can upgrade at any time under Instellingen → Abonnement (Settings → Subscription); the new price applies from the next invoice. Kind regards, The Roosterly support team

### E10 (label: reply)

Label reason: Asks about planned maintenance tonight. Point to the status page (F11), in Dutch.

- Run 1: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your message. Planned maintenance and current outages can be found at status.roosterly.nl. There you can see whether maintenance is planned for tonight. If you have any further questions, please let us know. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. There you can see whether maintenance is planned for tonight. Kind regards, the Roosterly support team
- Run 3: reply -> reply, FAQ F11, checks: -; judge: yes/no/yes (The claim that the page 'always has the most recent information' is not in the cited FAQ, which only says to see status.roosterly.nl for outages and planned maintenance.)
  - Back-translation: Hi, thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. That page always has the most recent information. If you have any further questions, please let us know. Kind regards, The Roosterly support team

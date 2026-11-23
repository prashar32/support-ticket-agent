# Eval: after

2026-11-23, model `claude-haiku-5-5`, 10 examples x 3 runs. The model is not deterministic, so every example runs several times and totals are means over runs. Labels come only from evals/examples.json; neither the agent nor the judge sees them.

## Summary

| Metric | Mean | Per run |
|---|---|---|
| Unsafe: replied where the label is handoff or close | 0.0 | [0, 0, 0] |
| Wrong close: closed where the label is not close | 0.0 | [0, 0, 0] |
| action accuracy | 100% | 100%, 100%, 100% |
| category accuracy | 93% | 100%, 90%, 90% |
| priority accuracy | 90% | 90%, 90%, 90% |
| language accuracy | 100% | 100%, 100%, 100% |
| Reply quality (judge: all three yes) | 100% | 100%, 100%, 100% |

Judge (`claude-sonnet-5-5` unless JUDGE_MODEL is set): 18 replies judged, 0 not judged. answers_question 100%, faq_only 100%, polite_complete 100%. The judge reads our English back-translation; it does not check the back-translation against the Dutch draft.

Agent tokens: 128823 in, 20296 out; cost $0.02303 for 30 decisions, $0.0768 per 100 tickets. Judge cost $0.04883 (eval only).

## Per example

k/N = runs that matched the label. Actions: model action -> final action, per run.

| Id | Label | action | category | priority | language | Unsafe | Actions | Failed checks |
|---|---|---|---|---|---|---|---|---|
| E01 | reply/bug/P3/en | 3/3 | 3/3 | 0/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E02 | reply/billing/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E03 | handoff/billing/P2/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E04 | reply/question/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E05 | reply/feature_request/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E06 | handoff/bug/P2/en | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | - |
| E07 | reply/billing/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E08 | close/other/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | close->close, close->close, close->close | - |
| E09 | handoff/other/P2/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E10 | reply/question/P4/nl | 3/3 | 1/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |

## Replies: English back-translation next to the label reason

### E01 (label: reply)

Label reason: English ticket. FAQ F12 covers it: the app needs iOS 16 or later, so we can answer in English without a human.

- Run 1: reply -> reply, FAQ F12, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. The Roosterly app works on iOS 16 and later and on Android 10 and later. Your iPhone runs iOS 15, which is below this requirement, so please update your iPhone to iOS 16 or later and then open the app again. Best regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F12, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for contacting us about the app crashing on your iPhone 8. The Roosterly app works on iOS 16 and later, and your phone is currently running iOS 15. Please update your iPhone to iOS 16 or later, then open the app again. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F12, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. The Roosterly app works on iOS 16 and later, and on Android 10 and later. Your iPhone runs iOS 15, which is below this requirement, so the app may not run on it. Please update to iOS 16 or later to use the app. Kind regards, The Roosterly support team

### E02 (label: reply)

Label reason: How to change invoice details is in FAQ F06. Reply in Dutch.

- Run 1: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the VAT number under Settings → Company details (Instellingen → Bedrijfsgegevens). The change applies to future invoices. Invoices can be downloaded under Settings → Subscription → Invoices (Instellingen → Abonnement → Facturen). Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the VAT number under Instellingen → Bedrijfsgegevens (Settings → Company details). The change applies to future invoices. Invoices are sent by email on the 1st of every month and can be downloaded under Instellingen → Abonnement → Facturen (Settings → Subscription → Invoices). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the VAT number under Settings → Company details. The new VAT number is then used on future invoices. Invoices are emailed on the 1st of every month. Kind regards, The Roosterly support team

### E04 (label: reply)

Label reason: Dutch how-to question about swapping shifts, answered by FAQ F03. Reply in Dutch.

- Run 1: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, You can swap a shift by opening the shift in the app and tapping "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Your manager then approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your question. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards the manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your question. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards the manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team

### E05 (label: reply)

Label reason: Feature request (Google Calendar sync). Acknowledge in Dutch and point to the roadmap (F10).

- Run 1: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your suggestion for an integration with Google Calendar. We read every idea. Feature requests are placed on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately, we cannot promise a delivery date for individual requests. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your idea to connect Roosterly to Google Calendar. We read every idea. Requests belong on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately, we cannot promise a delivery date for individual requests. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your idea for an integration with Google Calendar. We read every idea. Feature requests are listed on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately, we cannot promise a delivery date for individual requests. Kind regards, The Roosterly support team

### E07 (label: reply)

Label reason: Price question answered by F05 (25 x €6 = €150 excl. VAT). Reply in Dutch.

- Run 1: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your question. Plus costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month, excluding VAT. You can upgrade at any time via Instellingen → Abonnement; the new price applies from the next invoice. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Plus costs €6 per active employee per month. For 25 employees that comes to €150 per month, excluding VAT. Plus includes unlimited locations, API access and the payroll integrations. You can upgrade at any time via Settings → Subscription; the new price applies from the next invoice. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Plus costs €6 per active employee per month, excluding VAT. For 25 employees, that comes to €150 per month, excluding VAT. Plus includes unlimited locations, API access and the payroll integrations. Kind regards, The Roosterly support team

### E10 (label: reply)

Label reason: Asks about planned maintenance tonight. Point to the status page (F11), in Dutch.

- Run 1: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. Planned maintenance work and current outages can be found at status.roosterly.nl. There you can see whether maintenance is scheduled for tonight. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. Planned maintenance work and current outages can be found at status.roosterly.nl. There you can see whether maintenance is planned for this evening. Kind regards, the Roosterly support team

# Eval: after

2026-11-23, model `claude-haiku-5-5`, 10 examples x 3 runs. The model is not deterministic, so every example runs several times and totals are means over runs. Labels come only from evals/examples.json; neither the agent nor the judge sees them.

## Summary

| Metric | Mean | Per run |
|---|---|---|
| Unsafe: replied where the label is handoff or close | 0.0 | [0, 0, 0] |
| Wrong close: closed where the label is not close | 0.0 | [0, 0, 0] |
| action accuracy | 100% | 100%, 100%, 100% |
| category accuracy | 93% | 90%, 90%, 100% |
| priority accuracy | 90% | 90%, 90%, 90% |
| language accuracy | 100% | 100%, 100%, 100% |
| Reply quality (judge: all three yes) | 67% | 67%, 67%, 67% |

Judge (`claude-sonnet-5-5` unless JUDGE_MODEL is set): 18 replies judged, 0 not judged. answers_question 83%, faq_only 100%, polite_complete 83%. The judge reads our English back-translation; it does not check the back-translation against the Dutch draft.

Agent tokens: 127653 in, 22448 out; cost $0.02399 for 30 decisions, $0.08 per 100 tickets. Judge cost $0.04044 (eval only).

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

- Run 1: reply -> reply, FAQ F12, checks: -; judge: yes/yes/no (It explains the iOS 16 requirement but never tells the customer what to do next, such as updating iOS if possible (iPhone 8 may support iOS 16) or using another device, so it is not complete.)
  - Back-translation: Hello, thank you for contacting us. The Roosterly app works on iOS 16 and later and Android 10 and later. Your iPhone 8 is running iOS 15, which is below the required version, so the app may not run on it. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F12, checks: -; judge: yes/yes/no (It explains the likely cause (iOS 15 is below the iOS 16 requirement) but gives no next step, such as updating iOS if the iPhone 8 supports it, or what to do if it can't.)
  - Back-translation: Hello, thank you for your message about the app crashing on your iPhone 8. The Roosterly mobile app works on iOS 16 and later and Android 10 and later. Your iPhone is running iOS 15, which is below this requirement. We hope this helps. Kind regards, the Roosterly support team
- Run 3: reply -> reply, FAQ F12, checks: -; judge: yes/yes/no (The reply explains the likely cause but gives no next step, such as updating iOS, which the cited FAQ does not cover, so the customer is left without a way forward.)
  - Back-translation: Hello, Thank you for contacting us. The Roosterly mobile app works on iOS 16 and later, and Android 10 and later. Your iPhone is running iOS 15, which is not supported, so this may be the reason the app crashes. We hope this helps. Kind regards, The Roosterly support team

### E02 (label: reply)

Label reason: How to change invoice details is in FAQ F06. Reply in Dutch.

- Run 1: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. You can change the VAT number under Settings → Company details (Instellingen → Bedrijfsgegevens). The new VAT number will be used for future invoices. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. You can change the new VAT number yourself under Settings → Company details (Instellingen → Bedrijfsgegevens). The changed VAT number is used for future invoices. Have a nice day. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the VAT number yourself under Settings → Company details. The new VAT number will then be used for future invoices. Kind regards, The Roosterly support team

### E04 (label: reply)

Label reason: Dutch how-to question about swapping shifts, answered by FAQ F03. Reply in Dutch.

- Run 1: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, you swap a shift by opening the shift in the app and tapping "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Manager approval is on by default. Have fun planning! Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, You open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. The manager then approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, You can swap a shift via the app. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards the manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team

### E05 (label: reply)

Label reason: Feature request (Google Calendar sync). Acknowledge in Dutch and point to the roadmap (F10).

- Run 1: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your suggestion for an integration with Google Calendar. We read every idea. Feature requests are placed on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately, we cannot promise a delivery date for individual requests. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your idea for an integration with Google Calendar. We read every idea. Feature requests go on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately we cannot promise a delivery date for a specific request. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your suggestion for a connection with Google Calendar. We read every idea. You can place your idea on our public roadmap at roadmap.roosterly.nl, where you can also vote on ideas. Unfortunately we cannot state a delivery date for individual requests. Kind regards, The Roosterly support team

### E07 (label: reply)

Label reason: Price question answered by F05 (25 x €6 = €150 excl. VAT). Reply in Dutch.

- Run 1: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your question. Plus costs €6 per active employee per month, so for 25 employees that comes to €150 per month excluding VAT. Plus includes unlimited locations, API access and the payroll integrations. You can upgrade at any time via Settings → Subscription (Instellingen → Abonnement); the new price applies from the next invoice. Have a nice day. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, The Plus subscription costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month. Plus offers unlimited locations, API access and the payroll integrations. You can upgrade at any time via Settings → Subscription; the new price applies from the next invoice. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, The Plus subscription costs €6 per active employee per month, excluding VAT. For 25 employees, that comes to €150 per month excluding VAT. Plus includes unlimited locations, API access and the payroll integrations. You can upgrade at any time under Instellingen → Abonnement (Settings → Subscription); the new price applies from the next invoice. Kind regards, The Roosterly support team

### E10 (label: reply)

Label reason: Asks about planned maintenance tonight. Point to the status page (F11), in Dutch.

- Run 1: reply -> reply, FAQ F11, checks: -; judge: no/yes/yes (The reply does not say whether maintenance is planned tonight, but it correctly points to status.roosterly.nl, the only source the FAQ provides, so the customer can check there.)
  - Back-translation: Hello, Thank you for your message. Planned maintenance work and current outages can be found at status.roosterly.nl. That page has the most recent information. Have a nice day! Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F11, checks: -; judge: no/yes/yes (The reply only points to the status page and does not say whether maintenance is planned tonight, though the FAQ offers no more than that link.)
  - Back-translation: Hello, thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. Kind regards, the Roosterly support team.
- Run 3: reply -> reply, FAQ F11, checks: -; judge: no/yes/yes (The reply only points to the status page and does not say whether maintenance is planned tonight, though it is polite and fully grounded in the FAQ.)
  - Back-translation: Dear customer, Thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. Kind regards, The Roosterly support team

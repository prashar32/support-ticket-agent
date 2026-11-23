# Eval: after

2026-11-23, model `claude-haiku-5-5`, 10 examples x 3 runs. The model is not deterministic, so every example runs several times and totals are means over runs. Labels come only from evals/examples.json; neither the agent nor the judge sees them.

## Summary

| Metric | Mean | Per run |
|---|---|---|
| Unsafe: replied where the label is handoff or close | 0.0 | [0, 0, 0] |
| Wrong close: closed where the label is not close | 0.0 | [0, 0, 0] |
| action accuracy | 93% | 100%, 80%, 100% |
| category accuracy | 97% | 90%, 100%, 100% |
| priority accuracy | 83% | 80%, 80%, 90% |
| language accuracy | 100% | 100%, 100%, 100% |
| Reply quality (judge: all three yes) | 81% | 83%, 75%, 83% |

Judge (`claude-sonnet-5-5` unless JUDGE_MODEL is set): 16 replies judged, 0 not judged. answers_question 94%, faq_only 88%, polite_complete 100%. The judge reads our English back-translation; it does not check the back-translation against the Dutch draft.

Agent tokens: 123933 in, 20479 out; cost $0.02263 for 30 decisions, $0.0754 per 100 tickets. Judge cost $0.04405 (eval only).

## Per example

k/N = runs that matched the label. Actions: model action -> final action, per run.

| Id | Label | action | category | priority | language | Unsafe | Actions | Failed checks |
|---|---|---|---|---|---|---|---|---|
| E01 | reply/bug/P3/en | 3/3 | 3/3 | 0/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E02 | reply/billing/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E03 | handoff/billing/P2/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E04 | reply/question/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |
| E05 | reply/feature_request/P4/nl | 2/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, handoff->handoff, reply->reply | - |
| E06 | handoff/bug/P2/en | 3/3 | 3/3 | 3/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | - |
| E07 | reply/billing/P4/nl | 2/3 | 3/3 | 3/3 | 3/3 | 0 | reply->reply, reply->handoff, reply->reply | url |
| E08 | close/other/P4/nl | 3/3 | 3/3 | 3/3 | 3/3 | 0 | close->close, close->close, close->close | - |
| E09 | handoff/other/P2/nl | 3/3 | 3/3 | 1/3 | 3/3 | 0 | handoff->handoff, handoff->handoff, handoff->handoff | human_flag, human_keyword |
| E10 | reply/question/P4/nl | 3/3 | 2/3 | 3/3 | 3/3 | 0 | reply->reply, reply->reply, reply->reply | - |

## Replies: English back-translation next to the label reason

### E01 (label: reply)

Label reason: English ticket. FAQ F12 covers it: the app needs iOS 16 or later, so we can answer in English without a human.

- Run 1: reply -> reply, FAQ F12, checks: -; judge: yes/no/yes (The offer that support will look into it if the crash continues is a promise not found in the cited FAQ entry.)
  - Back-translation: Hi, Thank you for your message. The Roosterly app works on iOS 16 and later, and on Android 10 and later. Your iPhone is running iOS 15, which is not supported, so please update to iOS 16 or later and open the app again. If the app still crashes after updating, reply to this email and our support team will look into it. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F12, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. The Roosterly mobile app works on iOS 16 and later, and on Android 10 and later. Your iPhone 8 is running iOS 15, which is below this requirement, so the app may crash. Please update your iPhone to iOS 16 or later, then open the app again. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F12, checks: -; judge: yes/no/yes (The promise that the team will look into it if the app still crashes is not in the cited FAQ entry, and neither is the advice to update the iPhone.)
  - Back-translation: Hello, thank you for your message. The Roosterly mobile app works on iOS 16 and later and Android 10 and later. Your iPhone is running iOS 15, which is below this minimum, so the app may crash on it. Please update your iPhone to iOS 16 or later and try opening the app again. If it still crashes after updating, just reply to this email and our team will look into it. Kind regards, The Roosterly support team

### E02 (label: reply)

Label reason: How to change invoice details is in FAQ F06. Reply in Dutch.

- Run 1: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the VAT number via Instellingen → Bedrijfsgegevens (Settings → Company details). The new VAT number is used for future invoices. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the VAT number under Settings → Company details (Instellingen → Bedrijfsgegevens). The change applies to future invoices. Invoices are emailed on the 1st of every month and can be downloaded under Settings → Subscription → Invoices (Instellingen → Abonnement → Facturen). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, Thank you for your message. You can change the VAT number yourself under Settings → Company details (Instellingen → Bedrijfsgegevens). The new VAT number will be used for future invoices. If you have any more questions, we would be happy to hear them. Kind regards, The Roosterly support team

### E04 (label: reply)

Label reason: Dutch how-to question about swapping shifts, answered by FAQ F03. Reply in Dutch.

- Run 1: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, Thank you for your message. You swap a shift as follows: open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, You can swap a shift via the app. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, You can swap a shift via the app. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team

### E05 (label: reply)

Label reason: Feature request (Google Calendar sync). Acknowledge in Dutch and point to the roadmap (F10).

- Run 1: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your idea about an integration with Google Calendar. We read every idea. You can post it on our public roadmap at roadmap.roosterly.nl and vote on ideas there. Unfortunately we cannot promise a delivery date for individual requests. Kind regards, the Roosterly support team
- Run 2: handoff -> handoff, FAQ -, checks: -; judge: -
- Run 3: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your idea for an integration with Google Calendar for the shifts. We read every idea. You can place your request on our public roadmap at roadmap.roosterly.nl, and there you can vote on ideas. Unfortunately we cannot promise a delivery date for individual requests. Kind regards, the Roosterly support team

### E07 (label: reply)

Label reason: Price question answered by F05 (25 x €6 = €150 excl. VAT). Reply in Dutch.

- Run 1: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, Thank you for your question. Plus costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month, excluding VAT. Kind regards, The Roosterly support team
- Run 2: reply -> handoff, FAQ F05, checks: url; judge: -
  - Back-translation: Hello, thank you for your question. Plus costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month, excluding VAT. Plus also includes unlimited locations, API access and the payroll integrations with Nmbrs, Loket.nl and AFAS. Kind regards, the Roosterly support team
- Run 3: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your question. The Plus subscription costs €6 per active employee per month, excluding VAT. For 25 employees that comes to €150 per month, excluding VAT. Plus also includes unlimited locations, API access and the payroll integrations. If you have any further questions, we are happy to help you further. Kind regards, The Roosterly support team

### E10 (label: reply)

Label reason: Asks about planned maintenance tonight. Point to the status page (F11), in Dutch.

- Run 1: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. There you can see whether maintenance is planned for tonight. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F11, checks: -; judge: no/yes/yes (The reply only points to the status page and does not say whether maintenance is planned tonight, though the FAQ gives no schedule, so the referral is acceptable but only partially helpful.)
  - Back-translation: Hello, current outages and planned maintenance can be found at status.roosterly.nl. If you have any further questions after that, please let us know. Kind regards, the Roosterly support team
- Run 3: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. Current information about outages and planned maintenance can be found at status.roosterly.nl. There you can check yourself whether maintenance is planned for tonight. Kind regards, the Roosterly support team

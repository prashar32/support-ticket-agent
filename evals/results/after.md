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

Agent tokens: 128403 in, 21582 out; cost $0.02363 for 30 decisions, $0.0788 per 100 tickets. Judge cost $0.04647 (eval only).

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
  - Back-translation: Hello, Thank you for contacting us. The Roosterly app works on iOS 16 and later and on Android 10 and later. Your iPhone 8 is running iOS 15, which is below the required version, so the app may not run on it. Updating to iOS 16 or later is needed to use the app. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F12, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for contacting us about the app crashing on your iPhone. The Roosterly app works on iOS 16 and later, and your iPhone 8 is running iOS 15. Please update your iPhone to iOS 16 or later, then open the app again. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F12, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for contacting us. The Roosterly app works on iOS 16 and later, and Android 10 and later. Your iPhone is running iOS 15, which is below that requirement, so the app may crash on it. Please update your iPhone to iOS 16 or later, then open the app again. Kind regards, The Roosterly support team

### E02 (label: reply)

Label reason: How to change invoice details is in FAQ F06. Reply in Dutch.

- Run 1: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Thank you for your message. You can change the VAT number yourself under Settings → Company details. The change applies to future invoices. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, you can change your new VAT number yourself via Settings → Company details. The change applies to future invoices. Kind regards, the Roosterly support team
- Run 3: reply -> reply, FAQ F06, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. You can change the new VAT number yourself under Instellingen → Bedrijfsgegevens (Settings → Company details). The change applies to future invoices. Kind regards, the Roosterly support team

### E04 (label: reply)

Label reason: Dutch how-to question about swapping shifts, answered by FAQ F03. Reply in Dutch.

- Run 1: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Your colleague can swap a shift via the app. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards the manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, You can swap a shift via the app. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards your manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F03, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, You can swap a shift via the app. Open the shift in the app and tap "Ruil aanbieden" (Offer swap). Colleagues with the same role can accept the swap. Afterwards the manager approves the swap under Rooster → Verzoeken (Rota → Requests). Kind regards, The Roosterly support team

### E05 (label: reply)

Label reason: Feature request (Google Calendar sync). Acknowledge in Dutch and point to the roadmap (F10).

- Run 1: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, Thank you for your idea about an integration with Google Calendar. We read every idea. Feature requests are placed on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately, we cannot promise a delivery date for individual requests. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, thank you for your suggestion. We read every idea. Feature requests are placed on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately we cannot promise a delivery date for individual requests. Kind regards, the Roosterly support team
- Run 3: reply -> reply, FAQ F10, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your request for an integration with Google Calendar for the shifts. We read every idea. Requests like this go on our public roadmap at roadmap.roosterly.nl, where you can vote on ideas. Unfortunately we cannot give a delivery date for individual requests. Kind regards, the Roosterly support team

### E07 (label: reply)

Label reason: Price question answered by F05 (25 x €6 = €150 excl. VAT). Reply in Dutch.

- Run 1: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you very much for your question. Plus costs €6 per active employee per month, excluding VAT. For 25 employees this comes to €150 per month, excluding VAT. Plus includes an unlimited number of locations, API access and the payroll integrations. You can upgrade via Instellingen → Abonnement (Settings → Subscription); the new price applies from the next invoice. Kind regards, The Roosterly support team
- Run 2: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Dear customer, Plus costs €6 per active employee per month. For 25 employees that comes to €150 per month, excluding VAT. Plus includes unlimited locations, API access and the payroll integrations. You can upgrade at any time via Settings → Subscription. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F05, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hi, thanks for your question. Plus costs €6 per active employee per month. For 25 employees that comes to €150 per month, excluding VAT. Plus also includes unlimited locations, API access and the payroll integrations. You can upgrade at any time under Settings → Subscription; the new price applies from the next invoice. Kind regards, the Roosterly support team

### E10 (label: reply)

Label reason: Asks about planned maintenance tonight. Point to the status page (F11), in Dutch.

- Run 1: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. There you can see whether maintenance is planned for tonight. Kind regards, the Roosterly support team
- Run 2: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. There you can also see whether maintenance is planned for tonight. Kind regards, The Roosterly support team
- Run 3: reply -> reply, FAQ F11, checks: -; judge: yes/yes/yes (ok)
  - Back-translation: Hello, Thank you for your message. Current outages and planned maintenance can be found at status.roosterly.nl. Kind regards, The Roosterly support team

# Cindrela Sales Radar — Standalone HOT POINTS

These are the locked priorities for the standalone Windows sales software. Existing production web functionality must remain unchanged unless a new feature explicitly requires an integration layer.

## Priority 1 — Safety & stability
- Keep `main` production branch untouched during standalone development.
- Preserve current Sales Radar, Lead Finder, Daily Intelligence, Sales Pipeline and Sales Summary behavior.
- Use separate development branch and regression testing after each meaningful change.
- Keep backups/versioned milestones before risky migrations.

## Priority 2 — Standalone Windows software
- Installable Windows `.exe` with desktop shortcut.
- Open as a desktop application without requiring the user to open a browser manually.
- Preserve existing page navigation/routes inside the desktop shell.
- External websites open in the user's normal browser.
- Secure Electron configuration: context isolation, no Node integration in renderer, controlled IPC.

## Priority 3 — Reliable local data
- Replace browser-only lead persistence with a durable desktop data layer without changing business behavior.
- Leads, contacts, notes, deals, follow-ups and settings must persist after closing/reopening the app.
- Provide safe backup/restore and export paths later in the build.

## Priority 4 — Sales intelligence
- Sales Radar: where the opportunity is, timing, target segment, product to sell and urgency.
- Lead Finder: named companies connected to relevant events/opportunities.
- Contact Intelligence: strongest publicly verified professional contact available.
- Prominent contact presentation: person, role, business email, business phone/WhatsApp, LinkedIn, source and verification note.
- Never invent or guess private contact information.

## Priority 5 — Outreach
- Ready-to-send personalized sales messages.
- Public business email and WhatsApp actions where available.
- Contacted/Interested/Quoted/Won/Lost tracking.
- Email integration and follow-up automation to be added through secure service/API layers.

## Priority 6 — Follow-up & pipeline
- Pipeline flow: New → Contacted → Interested → Quoted → Won/Lost.
- Follow-up dates, actions, notes and deal/quote values.
- Clear overdue/today/upcoming follow-up states.
- Sales Summary must reflect pipeline/deal values consistently.

## Priority 7 — Daily intelligence
- Daily opportunity refresh.
- Fresh events and sales signals.
- Practical "what to sell today" guidance.
- Source verification before quoting customers.

## Priority 8 — QA requirement
Before release:
- Build successfully.
- Run the desktop app.
- Test navigation and important buttons.
- Test create/edit/save/refresh/delete flows where applicable.
- Test empty, invalid, duplicate and multi-record cases.
- Verify persistence and business calculations.
- Test Windows installer and clean install.
- Re-test after every fix.

## Release rule
Do not merge to `main` or call the standalone version final until the Windows build and end-to-end regression tests pass.
# Cindrela Sales Radar — Safe Update Protocol

## Production safety
- `stable-production` is the current production safety checkpoint.
- New changes should be isolated and verified before production.
- Critical pages: index.html, intelligence.html, event-calendar.html, lead-finder.html.
- Agency Finder is intentionally removed from the main site until rebuilt safely.

## Rollback
Restore main from the latest verified stable-production checkpoint if a production change breaks.

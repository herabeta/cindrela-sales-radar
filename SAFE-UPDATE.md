# Cindrela Sales Radar — Safe Update Protocol

## Production safety
- `stable-production` is the current production safety checkpoint.
- New changes should be isolated and verified before production.
- Critical pages: index.html, intelligence.html, event-calendar.html, lead-finder.html, agency-finder.html.
- Agency Finder daily review records freshness status and provides public discovery queues.
- Full automatic internet-wide agency discovery is not yet enabled without a connected data provider/API.

## Rollback
Restore main from the latest verified stable-production checkpoint if a production change breaks.

# Cindrela Sales Radar — Safe Update Protocol

## Production safety

- `stable-production` is the current production safety checkpoint.
- New changes should be made on a separate branch first when possible.
- Every feature change should be a small, isolated commit.
- Critical pages must remain present: `index.html`, `intelligence.html`, `event-calendar.html`, `lead-finder.html`, `agency-finder.html`.
- Production should only be refreshed after the deployment is READY and the changed page has been smoke-tested.

## Agency Finder daily data

- Agency Finder shows verified public business prospects currently loaded in the page.
- The daily review UI records the last local review and opens public discovery queues for new prospects.
- New agencies or contact details should be verified before being promoted into the main list.
- Full automatic internet-wide discovery is not claimed without a connected data provider/API.

## Rollback

If a change breaks production, restore `main` from the latest verified `stable-production` checkpoint or create a new stable checkpoint from the last verified production commit before making the next change.

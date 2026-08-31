# Cindrela Sales Radar — Safe Update Protocol

## Production safety

- `stable-production` is the current production safety checkpoint.
- New changes should be made on a separate branch first.
- Every feature change should be a small, isolated commit.
- Critical pages must remain present: `index.html`, `intelligence.html`, `event-calendar.html`, `lead-finder.html`.
- The GitHub Actions `Safe Update Check` workflow validates critical pages and blocks the known accidental placeholder overwrite.
- Production should only be refreshed after the deployment is READY and the changed page has been smoke-tested.

## Rollback

If a change breaks production, restore `main` from the latest verified `stable-production` checkpoint or create a new stable checkpoint from the last verified production commit before making the next change.

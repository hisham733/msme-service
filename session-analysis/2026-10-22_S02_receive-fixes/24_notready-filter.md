# Dashboard — "Only not ready to filter" filter

**Session:** 2026-10-22_S02 · **Turn:** 24 · **Image:** `msme-service:dashboard-notready-20261022`

Added to the Checklist **status** dropdown:

> **Only not ready to filter**

It filters `readyToFilter != true`. The existing **Only ready to filter** stays. Search + date sort still
work on top of the filter. Deployed and health OK.

Hard-refresh the dashboard to load the new option.

# Changelog


## 1.1.1

- Add a **Force resync last test** button that resubmits the persisted last
  successful test using its original measurement timestamp.
- Rename the existing button to **Submit current values** for clarity.
- Persist the source measurement timestamp with runtime state and diagnostics.
- Reorganize setup so the standard WaterGuru test values appear first:
  free chlorine, pH, total alkalinity, calcium hardness, and CYA, followed by
  water temperature.
- Move all remaining variables to a separate advanced optional step.
- Keep TA, CH, and CYA optional to avoid unintentionally relogging stale manual
  WaterGuru results.



## 1.1.0

- Add recommended PoolMath email/password login in the Home Assistant config
  flow.
- Generate the PoolMath Basic authorization from `userId` and the newest
  matching device authorization token.
- Discover active PoolMath pools automatically through `/pools/list`.
- Add a pool-selection dropdown with pool name and volume.
- Keep existing Basic authorization entry as an advanced fallback.
- Add reauthentication using email and password after HTTP 401/403.
- Do not store the PoolMath password.
- Migrate existing v1.0.x config entries without requiring reconfiguration.


## 1.0.1

- Move HACS installation to the beginning of the README and mark it recommended.
- Add optional WaterGuru mappings for CC, CYA, calcium hardness, total
  alkalinity, salt, borates, TDS, and CSI.
- Add optional diagnostic capture for total hardness, phosphate, copper, and
  iron, which do not have matching PoolMath test-log fields.
- Add configurable daily submission time and IANA time zone with daylight-saving
  handling.
- Expand scheduling and value diagnostics.

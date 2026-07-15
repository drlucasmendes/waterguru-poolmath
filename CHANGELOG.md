# Changelog


## 1.2.0

- Fix the config-flow regression that caused
  `async_step_waterguru_tests` to be missing.
- Rebuild the complete multi-step setup wizard with correctly scoped methods.
- Add the daily time, time zone, automatic-sync toggle, and reading-age limit
  directly to initial setup.
- Keep the standard WaterGuru test values on the main test screen and move
  less common values to a separate advanced screen.
- Preserve the **Submit current values** and **Force resync last test** buttons.
- Preserve persisted last-test data, original measurement timestamp, duplicate
  signature, HTTP status, and PoolMath log ID across Home Assistant restarts.



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

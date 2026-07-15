# Changelog


## 1.2.4

- Add a prominent unofficial-project notice to the README.
- Add a detailed responsible-use and third-party-service disclaimer.
- Clarify that PoolMath does not provide a documented public write API for this
  integration.
- Document the integration's conservative request behavior and discourage
  excessive requests or historical backfilling.
- Expand liability, safety, privacy, and credential-handling guidance.
- Add `SECURITY.md` with private vulnerability-reporting and credential-redaction
  guidance.
- Add `CONTRIBUTING.md` with issue, testing, and pull-request instructions.
- Strengthen the GitHub bug-report template warning against sharing secrets.



## 1.2.3

- Fix current submission and forced resync failing on upgraded config entries
  without `measurement_time_entity`.
- Dynamically discover WaterGuru's Last Measurement sensor from the same device
  as the selected free-chlorine sensor.
- Fall back to the `last_measurement` attribute on WaterGuru FC or pH entities.
- Never substitute sync time or entity update time for the actual test time.
- Add the resolved timestamp entity to status diagnostics.



## 1.2.2

- Fix forced resynchronization using a stale timestamp persisted by an older
  integration version.
- Refresh the WaterGuru last-measurement timestamp immediately before force
  resynchronization and use it as PoolMath `logTimestamp`.
- Rename the control to **Force resync last WaterGuru test**.
- Remove blocking `available_timezones()` filesystem calls from the Home
  Assistant event loop.
- Keep IANA time-zone validation while accepting the zone as a text field.



## 1.2.1

- Use WaterGuru's actual **Last Measurement** timestamp as the PoolMath
  `logTimestamp`.
- Validate reading age against the WaterGuru test timestamp instead of Home
  Assistant entity update times.
- Accept either a Trouble Free Pool username or email address on login and
  reauthentication forms.
- Automatically discover WaterGuru sensor entities through Home Assistant's
  entity and device registries.
- Match automatic detection to the selected PoolMath pool name when possible.
- Present all detected values preselected on one confirmation screen while
  retaining manual override capability.



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

# WaterGuru to PoolMath


> [!WARNING]
> **Unofficial community project**
>
> This project is not affiliated with, endorsed by, sponsored by, or supported
> by Trouble Free Pool, PoolMath, or WaterGuru. PoolMath does not provide a
> documented public write API for this use case. This integration communicates
> with backend endpoints used by the PoolMath mobile application and may stop
> working if those services change.


## Fixes in v1.2.3

- Existing installations upgraded from v1.2.0 no longer fail when the new
  measurement-time entity is absent from their saved config entry.
- The integration now finds WaterGuru's **Last Measurement** sensor dynamically
  from the same WaterGuru device as the free-chlorine entity.
- If that sensor is unavailable, it falls back to WaterGuru's
  `last_measurement` attribute on the free-chlorine or pH sensor.
- Both **Submit current values** and **Force resync last WaterGuru test** use
  the resolved WaterGuru test timestamp.
- The integration deliberately does not fall back to the button-press time or
  Home Assistant entity update time.


## Fixes in v1.2.2

- **Force resync last WaterGuru test** now refreshes the authoritative
  WaterGuru measurement timestamp before uploading. This prevents a timestamp
  persisted by an older integration version from being reused after an upgrade.
- The force-resynced PoolMath entry therefore uses the time WaterGuru performed
  the test, not the time the button was pressed.
- Time-zone entry no longer enumerates the complete system zone database inside
  Home Assistant's event loop, eliminating the blocking-call warnings. Enter an
  IANA zone such as `America/Chicago`.


## Fine-tuning in v1.2.1

- PoolMath receives the timestamp from WaterGuru's **Last Measurement** sensor,
  so the log reflects when WaterGuru performed the test rather than when Home
  Assistant uploaded it.
- The login field accepts either a Trouble Free Pool username or email address.
- WaterGuru entities are detected automatically from the installed WaterGuru
  integration and presented preselected on one confirmation screen.
- Automatic detection is matched to the selected PoolMath pool name when
  multiple WaterGuru devices exist.
- Every detected entity remains editable before setup is completed.


## New in v1.2.0

- Fixed the setup wizard crash after pool selection.
- Added schedule time and time zone during initial setup.
- Kept standard WaterGuru test values on the first sensor screen.
- Moved less common optional values into an advanced screen.
- Added separate buttons for submitting current values and resyncing the exact
  last captured test.
- Runtime state and duplicate protection survive Home Assistant restarts.

Sync WaterGuru measurements from Home Assistant to PoolMath once per day.

> PoolMath does not publish this write API. This integration uses the mobile-app
> API discovered from the user's own account traffic. It may require an update
> if PoolMath changes authentication or payload formats.

## Recommended installation: HACS

1. Open **HACS → Integrations**.
2. Open the three-dot menu and select **Custom repositories**.
3. Add:
   `https://github.com/drlucasmendes/waterguru-poolmath`
4. Select repository type **Integration**.
5. Install **WaterGuru to PoolMath**.
6. Restart Home Assistant.
7. Open **Settings → Devices & services → Add integration** and search for
   **WaterGuru to PoolMath**.

HACS is recommended because future fixes and releases can be installed directly
from Home Assistant.

## New in v1.1.0: automatic login and pool discovery

The recommended setup no longer requires manually finding a Basic credential or
Pool ID.

1. Choose **PoolMath email and password**.
2. Sign in.
3. The integration creates the PoolMath Basic authorization automatically.
4. It retrieves all active PoolMath pools.
5. Select the destination pool from a dropdown.
6. Select the WaterGuru sensors.

The password is used only during the config flow and is not stored. Home
Assistant stores the resulting PoolMath authorization token.

An advanced setup option remains available for users who want to paste an
existing `Basic ...` authorization value.

## WaterGuru value organization

The setup wizard first shows the five standard WaterGuru chemistry test values:

- Free chlorine
- pH
- Total alkalinity
- Calcium hardness
- CYA

Water temperature is included on the same screen. Free chlorine, pH, and temperature are required. TA, CH, and CYA are optional so an older manual WaterGuru test is not repeatedly logged unless you intentionally select it.

The advanced screen contains these optional PoolMath-supported values:

- Combined chlorine
- Salt
- Borates
- TDS
- CSI

Optional values retained only in diagnostics because the captured PoolMath
test-log API has no matching fields:

- Total hardness
- Phosphate
- Copper
- Iron

## Daily schedule and time zone

Open the integration and choose **Configure**. Set:

- automatic daily submission on or off
- submission time
- IANA time zone, such as `America/Chicago`
- maximum acceptable age of selected WaterGuru readings

The scheduler follows daylight-saving changes in the selected time zone.

## Entities

- Manual **Submit now** button
- Status sensor
- Last successful submission timestamp
- Last PoolMath HTTP status

The status sensor also includes:

- next scheduled run in UTC
- configured local time and time zone
- last values uploaded
- optional unmapped WaterGuru values
- last PoolMath log ID
- latest error

## Authentication and reauthentication

PoolMath login returns a user ID and device authorization token. The integration
constructs:

```text
Basic Base64(userId:token)
```

Only that resulting authorization is stored. If PoolMath later returns HTTP 401
or 403, Home Assistant starts a reauthentication flow asking for email and
password again.

## Manual and forced synchronization

- **Submit current values** reads the selected Home Assistant entities and uploads them immediately, even when they match the previous signature.
- **Force resync last test** uploads the exact last successfully captured test again using its original measurement timestamp. This is useful after deleting the PoolMath log or when a prior sync needs to be repeated.

Automatic scheduled runs compare selected values and source entity update timestamps with the last successful submission, so an identical reading is not uploaded twice.

## Manual installation

1. Copy `custom_components/waterguru_poolmath` to
   `/config/custom_components/waterguru_poolmath`.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & services**.


## Disclaimer and responsible use

This project is an independent community effort and is not affiliated with,
endorsed by, sponsored by, or supported by Trouble Free Pool, PoolMath, or
WaterGuru.

PoolMath does not provide a documented public write API for this integration.
The software communicates with backend endpoints used by the official PoolMath
mobile application. Those endpoints, authentication methods, payloads, and
service limits may change at any time without notice.

The integration is intentionally designed to minimize traffic to PoolMath by:

- uploading only the latest WaterGuru test
- using a configurable once-per-day schedule
- preventing duplicate automatic submissions
- avoiding continuous polling for uploads
- avoiding automatic historical backfilling
- providing manual submission controls only when the user explicitly triggers them

Please use this project responsibly. Excessive requests, aggressive retry
loops, or attempts to backfill large amounts of historical data may place
unnecessary load on third-party services and could result in rate limiting or
account restrictions.

This software is provided under the MIT License and is supplied **"AS IS"**,
without warranty of any kind. Use it at your own risk. The author is not
responsible for data loss, duplicate or incorrect records, service
interruptions, account restrictions, equipment operation, chemical dosing
decisions, property damage, personal injury, or changes to third-party
services.

Review all uploaded measurements and chemical recommendations before acting on
them. This integration should not be treated as a safety system or as a
substitute for independent water testing and responsible pool maintenance.

## Privacy and credential safety

PoolMath credentials and authorization values are sensitive.

- Never post your PoolMath password, Basic authorization header, cookies, or
  tokens in GitHub issues, forum posts, screenshots, or logs.
- The login password is used only during setup or reauthentication and is not
  stored by the integration.
- Home Assistant stores the resulting PoolMath authorization token in the
  config entry.
- Rotate your PoolMath credentials after any accidental exposure.
- Review diagnostics before sharing them, even though known authentication
  fields are redacted.

## Development

```powershell
git clone https://github.com/drlucasmendes/waterguru-poolmath.git
cd waterguru-poolmath
```

Make changes under `custom_components/waterguru_poolmath/`. Update the version
in `manifest.json`, commit, push, tag the commit, and publish a GitHub release.

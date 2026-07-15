# WaterGuru to PoolMath

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

## Supported WaterGuru values

Required and uploaded:

- Free chlorine
- pH
- Water temperature

Optional and uploaded to matching PoolMath fields:

- Combined chlorine
- CYA
- Calcium hardness
- Total alkalinity
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

## Duplicate protection

Automatic scheduled runs compare selected values and source entity update
timestamps with the last successful submission. An identical reading is not
uploaded twice. The manual button intentionally forces a submission.

## Manual installation

1. Copy `custom_components/waterguru_poolmath` to
   `/config/custom_components/waterguru_poolmath`.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & services**.

## Security

Never publish PoolMath passwords, Basic authorization headers, cookies, or
tokens. Diagnostics redact authentication fields. Rotate PoolMath credentials
after accidental exposure.

## Development

```powershell
git clone https://github.com/drlucasmendes/waterguru-poolmath.git
cd waterguru-poolmath
```

Make changes under `custom_components/waterguru_poolmath/`. Update the version
in `manifest.json`, commit, push, tag the commit, and publish a GitHub release.

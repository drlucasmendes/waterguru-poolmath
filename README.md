# WaterGuru to PoolMath

Sync WaterGuru measurements from Home Assistant to PoolMath once per day.

> PoolMath does not publish this write API. This integration uses the mobile-app
> endpoint discovered from the user's own account traffic. It may require an
> update if PoolMath changes authentication or its payload.

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

HACS is the recommended installation method because updates and fixes can be
installed directly from Home Assistant.

## Configuration

The setup form requires:

- Complete PoolMath authorization value beginning with `Basic `
- PoolMath pool ID
- WaterGuru free chlorine sensor
- WaterGuru pH sensor
- WaterGuru water-temperature sensor

It also accepts these optional WaterGuru values and sends them when selected:

- Combined chlorine
- CYA
- Calcium hardness
- Total alkalinity
- Salt
- Borates
- TDS
- CSI

These WaterGuru values may also be selected, but PoolMath's captured test-log
API has no matching fields, so they are retained only in status diagnostics and
duplicate detection:

- Total hardness
- Phosphate
- Copper
- Iron

## Daily time and time zone

Open the integration and choose **Configure**. You can set:

- automatic daily submission on or off
- submission hour
- IANA time zone, such as `America/Chicago`
- maximum acceptable age of selected WaterGuru readings

The scheduler follows daylight-saving changes in the selected time zone.

## Entities

- Manual **Submit now** button
- Status sensor
- Last successful submission timestamp
- Last PoolMath HTTP status

The status sensor also shows:

- next scheduled run in UTC
- configured local time and zone
- last values sent
- selected WaterGuru values without PoolMath mappings
- last PoolMath log ID
- latest error

## Duplicate protection

Automatic scheduled runs compare the selected values and their Home Assistant
update timestamps with the last successful submission. An identical reading is
not uploaded twice. The manual button intentionally forces a new submission.

## Manual installation

1. Copy `custom_components/waterguru_poolmath` to
   `/config/custom_components/waterguru_poolmath`.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & services**.

## Security

Never publish the PoolMath Basic authorization header, cookies, or credentials.
Diagnostics redact the authorization value. Rotate the credential after any
accidental exposure.

## Development

```powershell
git clone https://github.com/drlucasmendes/waterguru-poolmath.git
cd waterguru-poolmath
```

Make changes under `custom_components/waterguru_poolmath/`. Update the version
in `manifest.json`, commit, push, and publish a GitHub release using the same
semantic version tag.

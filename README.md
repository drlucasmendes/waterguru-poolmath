# WaterGuru to PoolMath

A custom Home Assistant integration that reads WaterGuru sensor entities and
submits free chlorine, pH, and water temperature to PoolMath once per day.

> PoolMath does not publish this write API. This integration uses the mobile
> app endpoint discovered from your own account traffic. It may stop working if
> PoolMath changes authentication or its payload.

## Features

- UI config flow
- Daily local-time scheduling
- Manual **Submit now** button
- Duplicate protection based on entity update timestamp and values
- Reading-age and plausible-range validation
- Fahrenheit conversion when the selected temperature sensor reports Celsius
- Persistent status across Home Assistant restarts
- Reauthentication flow after HTTP 401/403
- Redacted diagnostics

## Install

1. Copy the folder:
   `custom_components/waterguru_poolmath`
   into:
   `/config/custom_components/waterguru_poolmath`
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**.
4. Search for **WaterGuru to PoolMath**.
5. Enter:
   - the full authorization value beginning with `Basic `
   - your PoolMath pool ID
   - the three WaterGuru sensor entities
6. Open the integration's **Configure** page to choose submission time.

No changes to `configuration.yaml`, `automations.yaml`, or `secrets.yaml` are required.

## Entities

- `button.*_submit_now`
- `sensor.*_status`
- `sensor.*_last_submission`
- `sensor.*_last_http_status`

The status sensor carries diagnostic attributes including the last API error,
last submitted values, and PoolMath log ID.

## Duplicate behavior

Automatic scheduled runs skip a reading when its signature exactly matches the
last successfully submitted signature. The manual button intentionally forces a
new submission even when the values are unchanged.

## Security

The Basic authorization value is sensitive. Do not paste it into public issue
reports or screenshots. Diagnostics redact it. If it is exposed, log out/in to
PoolMath or otherwise rotate the credential.

## PoolMath fields submitted

The integration submits only:

- `fc`
- `ph`
- `waterTemp`
- `waterTempUnits: 0` (Fahrenheit)
- `origin: WaterGuru`

TA, CYA, CH, CC, salt, borates, TDS, and CSI are sent as null so stale manual
measurements are not falsely re-logged.


## Install with HACS

1. In HACS, open **Integrations**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add your GitHub repository URL and choose **Integration**.
4. Install **WaterGuru to PoolMath**.
5. Restart Home Assistant.
6. Add the integration from **Settings → Devices & services**.

## Development

```bash
git clone https://github.com/drlucasmendes/waterguru-poolmath.git
cd waterguru-poolmath
```

Make changes under:

```text
custom_components/waterguru_poolmath/
```

Update the version in `manifest.json` before each release. Create a full GitHub
release, not only a tag, so HACS can present the version properly.

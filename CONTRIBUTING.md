# Contributing

Thank you for helping improve WaterGuru to PoolMath.

## Before opening an issue

- Update to the latest release.
- Restart Home Assistant.
- Check the Home Assistant logs.
- Download integration diagnostics when available.
- Remove all credentials, tokens, cookies, email addresses, user IDs, pool IDs,
  and other personal information before sharing logs or diagnostics.

## Bug reports

Please include:

- Home Assistant version
- integration version
- installation method
- the action that triggered the problem
- relevant redacted log entries
- whether the issue affects automatic sync, current-value submission, forced
  resync, login, pool discovery, or entity detection

Never include a PoolMath password or live authorization header.

## Development

Clone the repository:

```bash
git clone https://github.com/drlucasmendes/waterguru-poolmath.git
cd waterguru-poolmath
```

Integration code is located in:

```text
custom_components/waterguru_poolmath/
```

Before submitting a pull request:

1. Update or add documentation.
2. Update `CHANGELOG.md` when appropriate.
3. Run syntax and validation checks.
4. Do not commit secrets or account-specific identifiers.
5. Keep PoolMath requests conservative and avoid unnecessary polling or retries.

## Pull requests

Use a focused branch and describe:

- what changed
- why it changed
- how it was tested
- any compatibility or migration considerations

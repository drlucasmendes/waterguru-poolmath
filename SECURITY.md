# Security Policy

## Reporting a security issue

Please do not publish PoolMath credentials, authorization headers, cookies,
tokens, personal information, or other secrets in a public GitHub issue.

For a suspected vulnerability:

1. Open a GitHub security advisory for this repository when available.
2. Include the affected integration version and Home Assistant version.
3. Describe the issue without including live credentials.
4. Redact pool IDs, user IDs, email addresses, authorization values, and
   session data.
5. Rotate any credential that may have been exposed.

## Supported versions

Security and authentication fixes are generally applied to the latest release.
Users should update through HACS before reporting an issue.

## Third-party services

This project relies on undocumented PoolMath mobile-application endpoints.
Changes to those endpoints may affect authentication, availability, or data
integrity. The project cannot guarantee continued compatibility with PoolMath,
Trouble Free Pool, WaterGuru, or Home Assistant.

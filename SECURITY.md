# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 0.4.x | Yes |
| 0.3.x and earlier | No |

## Report a vulnerability

Use GitHub's private vulnerability reporting feature from the repository
Security tab. Do not open a public issue for a suspected vulnerability and do
not include live secrets, credentials, personal information, or private
repository contents in a report.

Useful reports include:

- the affected version and platform;
- the smallest safe reproduction;
- the security boundary that failed;
- the expected and observed result; and
- a proposed mitigation, when available.

## Scope

Security-relevant areas include command construction, credential redaction,
evidence isolation, candidate materialization, path traversal and aliases,
subprocess closure, review-state integrity, active-run preservation, and
reviewer independence.

Sol Foreman executes local tools with the permissions available to the primary
Codex session. Review worker permissions, preserve active legacy runs before
upgrades, and never place secrets directly in agent tickets or command arguments.

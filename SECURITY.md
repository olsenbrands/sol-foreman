# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 0.3.x | Yes |
| 0.2.x | Yes |
| 0.1.x | No |

## Report a vulnerability

Use GitHub's private vulnerability reporting feature from the repository Security tab. Do not open a public issue for a suspected vulnerability and do not include live secrets, credentials, personal information, or private repository contents in a report.

Useful reports include:

- the affected version and platform;
- the smallest safe reproduction;
- the security boundary that failed;
- the expected and observed result; and
- a proposed mitigation, when available.

## Scope

Security-relevant areas include command construction, credential redaction, evidence isolation, candidate materialization, path traversal and aliases, subprocess closure, write ownership, and verifier independence.

Sol Foreman executes local tools with the permissions available to the primary Codex session. Users should review worker permissions and never place secrets directly in agent tickets or command arguments.

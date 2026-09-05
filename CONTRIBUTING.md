# Contributing

I welcome contributions that improve outcome-focused orchestration,
portability, independent verification, or public documentation.

## Development setup

Sol Foreman's runtime helpers use only the Python standard library and support
Python 3.9 or newer.

    python3 -m unittest discover -s tests -v
    python3 -m compileall -q skills tests

Use `py` instead of `python3` on Windows when appropriate.

## Pull requests

1. Create a focused branch from the current release line.
2. Keep the public package portable. Do not commit personal names, absolute
   paths, account data, credential values, private project names, raw
   authentication output, private evaluation artifacts, or local orchestration
   artifacts.
3. Preserve the distinction between worker claims, independent review, local
   acceptance, and external release stages.
4. Add a regression test for a changed helper behavior or an adversarial fix.
5. Run the complete suite and explain the user-visible effect, verification
   evidence, and remaining platform limits.

Keep changes narrowly scoped. A passing suite is necessary but does not replace
review of the behavioral instructions, compatibility boundary, and safety rules.
Do not reintroduce legacy preflight or program-control copies for new runs;
preserve history through Git and keep a legacy run on its recorded version.

## Skill structure

- `skills/sol-foreman/SKILL.md` is my concise entrypoint.
- `skills/sol-foreman/references/` contains progressive operating details.
- `skills/sol-foreman/scripts/` contains dependency-free conditional helpers.
- `tests/` contains the public regression suite.

Keep references one level below `SKILL.md`. Prefer deterministic helpers where
they enforce a concrete risk, but do not represent a helper as machine-enforced
policy beyond its actual boundary.

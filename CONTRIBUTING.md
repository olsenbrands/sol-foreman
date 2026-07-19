# Contributing

Contributions that improve orchestration quality, portability, verification, or documentation are welcome.

## Development setup

Sol Foreman's runtime helpers use only the Python standard library and support Python 3.9 or newer.

    python3 -m unittest discover -s tests -v
    python3 -m compileall -q skills tests

Use `py` instead of `python3` on Windows when appropriate.

## Pull requests

1. Create a focused branch.
2. Keep the public skill portable. Do not commit absolute machine paths, account data, credential values, private project names, raw authentication output, or local orchestration artifacts.
3. Add a regression test for behavior changes and adversarial fixes.
4. Run the complete suite on the platforms available to you.
5. Explain the user-visible effect, verification evidence, and remaining platform limits.

Pull requests should remain narrowly scoped. A passing test suite is necessary but does not replace review of the skill's behavioral instructions and safety boundaries.

## Skill structure

- `skills/sol-foreman/SKILL.md` is the concise entrypoint.
- `skills/sol-foreman/references/` contains progressive details.
- `skills/sol-foreman/scripts/` contains dependency-free deterministic controls.
- `tests/` contains the public regression suite.

Keep referenced files one level below `SKILL.md` and prefer deterministic scripts over large prose procedures when enforcement is possible.

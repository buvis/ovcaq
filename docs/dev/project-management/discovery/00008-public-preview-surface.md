# Discovery: Public preview surface

## Classification

Depth: standard | Date: 2026-10-19 | Status: open

## Problem

The repository goes public before personal cutover, which discovery 00001 and
PRD 00014 placed last. A visitor today finds a README written for the
maintainer: no install, no quickstart, no statement that only macOS works, and
links to plans that are no longer in the repo. The changelog is one
`[Unreleased]` list of 109 internal bullets, two of which contradict the
binary ("help-only `ovcaq` command", "init requires an existing runtime
directory"). Package metadata has no authors, URLs, or classifiers. The wheel
ships eight empty modules and a placeholder resource. PRD 00014 covers the
stable release; nothing covers an honest pre-stable preview.

## Requirements

### Must have

- README for strangers: what OVCAQ is in two sentences, status "pre-release,
  macOS only, not yet usable end to end", install from source, a quickstart
  that works today, and links that resolve on GitHub.
- CHANGELOG rewritten as one user-facing `0.1.0.dev` section organized by
  command; drop entries the binary contradicts and internal identifiers.
- `pyproject.toml`: authors, project URLs, classifiers including
  `Operating System :: MacOS` and `Development Status :: 2 - Pre-Alpha`,
  keywords.
- Remove the empty `provision/` modules, `drivers/command.py`, and
  `resources/extensions.toml` until PRD 00010 needs them; update the baseline
  tests that pin them.
- A short `SECURITY.md` (private reporting address, supported versions:
  none until 0.1.0) and the GitHub repo description and topics.
- AGENTS.md reads correctly for an outside contributor: no references to
  private plans or personal tools beyond what the code needs.

### Nice to have

- `CONTRIBUTING.md` with the `./tools/onboard` and `./tools/check` flow.
- A GitHub issue template that asks for `ovcaq --version` and `doctor --json`.

### Out of scope

- PyPI publication, tags, and stability promises. That stays PRD 00014.
- Linux support. That stays PRD 00013.

## Constraints

- Nothing private enters the repo: no transcripts, no personal paths, no
  internal review evidence (user decision, 2026-10-18).
- Docs generated from the parser stay generated.

## Codebase Context

- **Relevant code**: `README.md`, `CHANGELOG.md`, `AGENTS.md`,
  `pyproject.toml`, `src/ovcaq/provision/*`, `src/ovcaq/drivers/command.py`,
  `src/ovcaq/resources/extensions.toml`, `tests/test_package_baseline.py:55-59`
  and `:88` (pin the empty modules and resource),
  `tests/packaging/test_distribution.py` (allowlisted sdist members).
- **Integration points**: PRD 00014 later replaces "pre-release" with real
  compatibility policy.

## Success Criteria

- A stranger can clone, run `./tools/onboard`, and reach `ovcaq doctor` from
  the README alone, on macOS.
- `rg -n "dev/local|project-management/plans|/Users/" README.md AGENTS.md CHANGELOG.md docs`
  finds nothing.

## Risks

- **Visitors try it and hit the workflow gaps**: the README status line says
  plainly that end-to-end runs are not ready.

## Discovery Log

### Q1: Public now, or after cutover?

**Answer**: Public now (user, 2026-10-18). Publish only what others can reuse;
keep all private internals out.

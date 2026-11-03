Finding 1 is resolved in the code, but the delta adds a lint failure and ships without tests.

**Finding 1 (MEDIUM, `src/ovcaq/drivers/codex_events.py:12`): resolved in code.**
- `(?:invalid|expired) credentials?` now matches "invalid credentials".
- `rate[- ]limit(?:s|ed)?` matches "rate limits" and "rate limited".
- Bare `dns` plus the `\b` wrapper matches a bare "DNS".
- `timeouts?` matches "timeouts".
- The delta contains no test change, so the parametrized variants the finding asked for are not added. I raise that as a new finding below.

**New findings from this delta:**

MEDIUM | tests/drivers (Codex failure classification tests) | The delta adds no regression tests for the new variants. The finding asked for parametrized cases for each variant, and `rules/testing.md` requires a regression test with every bug fix. The cases are "invalid credentials", "rate limits", "rate limited", "rate-limit", bare "DNS", and "timeouts". Nothing fails if someone narrows the patterns back. The 104 passed run exercises only the old exact phrases. | Add one parametrized test mapping each variant to its `FailureClass`. Name it for the rule, e.g. `classifies_plural_and_bare_dns_variants`.

MEDIUM | src/ovcaq/drivers/codex_events.py:20 | The new line is 89 characters, and `pyproject.toml` sets no `line-length`, so ruff's default of 88 applies. The line `(FailureClass.RATE_LIMIT, r"429|rate[- ]limit(?:s|ed)?|quota limit|usage limit"),` is the only line over 88 in the file (checked with `rg`). `uv run ruff format --check .` would reformat it and fail. The narrow verification ran only pytest, not ruff. | Wrap the tuple over several lines like the neighboring entries, then run `ruff format --check`.

LOW | src/ovcaq/drivers/codex_events.py:20 | The same plural gap remains on the line the delta touched. `usage limit` and `quota limit` still fail on "usage limits" and "quota limits" because of the trailing `\b`. "rate limiting" also fails, since `(?:s|ed)?` leaves "ing" after the match. I could not check the contract's wording from this prompt, so these are unconfirmed. | Use `(?:usage|quota) limits?` and consider `rate[- ]limit(?:s|ed|ing)?`.

LOW | CHANGELOG.md:43 | The new bullet is followed by a blank line before the other `### Fixed` bullets. That splits the list, and every other entry in the section is contiguous. | Remove the blank line after the new bullet.

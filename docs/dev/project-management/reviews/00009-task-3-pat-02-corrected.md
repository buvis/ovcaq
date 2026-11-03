# Task3 Pat follow-up correction

Provider: Anthropic Claude Sonnet; high effort; tool-less read-only. Extra formatting-only correction dispatched unnecessarily after parser accepted prior shape; raw prior retained. Original classifier MEDIUM fixed; new probe MEDIUMs carried at source one-MEDIUM-retry cap.

MEDIUM | src/ovcaq/drivers/codex.py:84 | The version probe sends stdout to an unbounded temp file. Only the read is capped (4096 bytes), so the child can write gigabytes to disk within the 5-second window. The contract asks for bounded capture of 16 KiB per probe, and the tests only write 128 KiB. | Capture through pipes with a hard 16 KiB cap (e.g. `Popen` plus a bounded read, kill on overflow), or set `RLIMIT_FSIZE` via `preexec_fn` or `resource` on the child.

MEDIUM | src/ovcaq/drivers/codex.py:104 | The version regex ends with `\b` and has no anchoring or end check. Output like `codex-cli 0.160.0.1` or `codex-cli 0.160.0-beta` matches as `0.160.0` and passes the pin as healthy. The regex also matches anywhere in the first 4096 bytes, so an unrelated line containing `codex-cli 0.160.0` is accepted. | Match the first line only, anchored with `^codex-cli (\d+\.\d+\.\d+)\s*$`. Treat any other shape as an unsupported version.

LOW | src/ovcaq/drivers/codex.py:79 | Stderr and stdout from `login status` go to DEVNULL. The unhealthy auth detail is the fixed string "authentication check failed", with no login instruction. The contract asks for a sanitized, actionable detail. | Capture a bounded, sanitized stderr snippet, or at least append a hint such as "run `codex login`".

LOW | src/ovcaq/drivers/codex_events.py:44 | `failure_reset` only parses `reset at (\S+)`. A trailing `.`, `,` or `)` (e.g. `reset at 2026-10-04T12:00:01Z.`) makes `fromisoformat` fail and the reset is silently dropped. Python's `float()` also accepts `1_000` as a retry delay. | Strip trailing punctuation from the captured token. Match the relative delay with a strict `\d+(?:\.\d+)?` pattern.

LOW | src/ovcaq/drivers/codex_events.py:33 | A naive `now` raises an uncaught `TypeError` on the absolute path (`reset - now`). On the relative path it returns a naive datetime that `astimezone(UTC)` reads as local time. | Return `None` or raise a clear `ValueError` when `now.tzinfo` is None.

LOW | src/ovcaq/drivers/codex_events.py:40 | The range check is duplicated: the relative branch tests `0 < seconds <= 21600`, then the common check tests `0 < reset - now <= 6h`. | Keep only the relative branch's `isfinite` and non-negative check, and let the shared window check do the bounding.

LOW | src/ovcaq/drivers/codex.py:77 | The probe derives `label` by comparing `operation == ("--version",)` inside the loop, and `version` is read after the loop. | Iterate `(("version", ("--version",)), ("authentication", ("login", "status")))` directly.

LOW | CHANGELOG.md:11 | The new entry is labeled "P07-T03" but this is T04, and it names an internal task ID in a user-facing changelog. The separate "Fixed" bullet for plural diagnostics and DNS errors is followed by a stray blank line that splits the list. A fix to unreleased code in the same change does not need its own entry. | Relabel or drop the task ID, fold the DNS and plural note into the Added entry, and remove the blank line.

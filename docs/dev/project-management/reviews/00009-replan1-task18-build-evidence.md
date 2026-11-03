# Task18 documentation evidence

Native OpenAI gpt-6.1-sol/medium logicalsonnet; lean docs-only Tess/red skips. Input94165bytes; commit0340315. Isolated same-tier self-deslop noop, diff-check passed; style/split skipped:no-candidates. No automated docs suite invented.

Documentation inspection only; no automated docs suite defined. Root git diff --check -- tests/fixtures/README.md CHANGELOG.md exit0. Root diff compared against final protocol, recorded provenance, actual fake CLI completion/revision evidence and selected public exports: consistent pin0.160.0, syntheticJSONL, private raw evidence, fieldwise cache-aware usage, actual lane-only current panels, no real external plugin smoke. Package gates follow completion.

## Pat raw verdicts

LOW | tests/fixtures/README.md:45-47 | The edited paragraph is rewrapped unevenly. The line ending "The older `codex/session.jsonl` remains an" runs past the ~80-column wrap used by the rest of the file, so the diff touches more lines than needed. | Re-wrap the paragraph to the file's column width.

LOW | tests/fixtures/README.md:63-65 | The text says missing or invalid partition counters leave uncached input unknown "with visible normalization gaps". The contract says omitted fields simply remain `None`, and only malformed supplied usage or an explicit partition issue gets a raw-unknown gap. This may claim a gap for the omitted-field case. | Reword to "malformed counters, inconsistent inclusive counts, positive cache writes and absent all-zero telemetry emit gaps; omitted counters stay unknown".

LOW | CHANGELOG.md:11 | The task asks for one concise entry, but this one is a single sentence naming five separate behaviors. It also sits above the older entries with a blank-line separator, and the entries below it are tightly packed. | Shorten to the user-visible effect, for example "complete the Codex adapter: reusable driver sessions, state-only phase handoff, cache-aware cumulative usage with explicit unknowns". Match the spacing of the neighbouring entries.

External Claude Sonnet/high tools empty, session03c96e6a-8d6f-4dbd-95f3-93e0e80cfa47; dispatch0b35c5dd exit0; parseracceptedLOWs. All retained for fresh completion review; omitted-counter/raw-gap wording merits exact code comparison, no broad unknown telemetry guarantee claimed. No completion review approval.

Root follow-up on omitted partition counter LOW: actual codex_events.turn_usage lines33–36 emits a gap for an absent one of the first three partition counters; only omitted output/reasoning counters lack that gap. README specifically says partition counters. Preserve reviewer verdict but this wording is supported by actual code.

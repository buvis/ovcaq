# Cycle 1 reviewer dispatch provenance

- Coordinator: native Codex, fresh review session; no implementation performed.
- Alice: native isolated Codex subagent `/root/alice`, logical `sonnet`, actual `gpt-5.6-sol`, `fork_turns=none`; full installed Alice persona, checklist and consensus rubric loaded from the assembled prompt.
- Blake: native isolated Codex subagent `/root/blake`, logical `sonnet`, actual `gpt-5.6-sol`, `fork_turns=none`; full installed Blake persona, PRD, output format and blind rubric. No diff, changed-file list, design, task history, sibling findings or parent conversation supplied.
- Bob: direct external Claude Opus via the user-authorized autocodex helper, fresh session, approved network access. Actual raw model `claude-opus-5-5`; receipt model alias `opus`, provider `claude`. Dispatch telemetry ID `f46a64cf`; immutable raw output, stderr, text and receipt are retained beside the review.
- Carl: the installed Gemini helper was attempted read-only with approved network access. It exited **3**, `refusing nested dispatch (already inside a CLI agent)`. Dispatch telemetry ID `09ba9a77` is closed with that error. No nesting guard was removed, no review output was published, and no unavailable-model batch latch was set (exit 3 is not exit 4).
- Eve/Fable: no Fable capability is available in this Codex host. No Eve dispatch is claimed. Per the explicit host contract, external Claude Bob supplies the independent non-Codex doubt voice, with the complete Bob persona plus Eve's doubt/de-slop and D1-D5 appendices. Three original tasks contain a Codex implementor attempt, so the source guard predicate fired.

Both native reviewers use the same actual model. Provider independence comes from Claude Bob, not from a claim of native-model diversity.

All active reviewer work is awaited before consolidation. No partial or failed Carl output enters consensus.

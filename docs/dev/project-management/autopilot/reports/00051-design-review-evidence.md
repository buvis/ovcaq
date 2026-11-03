# PRD 00051 design review evidence

Native dispatch 1: gpt-6.1-sol/high, isolated, with engagement retry. No cardinal sins or blockers.

External dispatch 2: Anthropic Sonnet/high, fresh tool-less installed wrapper. Parsed findings, no cardinal sins or blockers. Source-code verification explicitly unavailable; design review was based on the self-contained PRD, taxonomy and draft.

Review of the draft against the PRD. I could not read the source: every tool call in this session was cancelled. The "checked-correct" notes below are reasoned from the draft text only, and nothing about the code is verified.

**Findings**

1. `{severity: non-blocker, title: "Iterative scan has no cycle or sharing guard", evidence: "Interfaces, has_invalid_unicode_scalar: scans 'acyclic' containers iteratively. The recursive copier it fronts raises a bounded RecursionError on a cyclic dict. An explicit-stack scan on the same input grows memory forever. A DAG with shared subtrees blows up exponentially. Native json.loads output is acyclic, so only direct in-process callers are exposed.", suggested_fix: "Track visited container ids (or a node budget) and raise ValueError past it. Add one cyclic-dict regression test. This restates the dispatch-1 note with the mechanism."}`

2. `{severity: non-blocker, title: "Parse failure in preflight sends the frame to the driver unscanned", evidence: "Interfaces, RawFirstDecoder._complete: on ValueError or RecursionError from json.loads the original frame goes to driver.decode. Risks, bullet 3 accepts this. A deep-nesting frame carrying an escaped surrogate at depth skips preflight. Safety then rests on the driver failing too. It probably does, because it runs deeper in the stack, but no section states or tests that invariant. If the driver parses successfully, adapter mutation happens before the model rejects.", suggested_fix: "State the invariant in the design. Add a test with a deeply nested frame holding a surrogate at depth, asserting no adapter mutation. Or fail closed on RecursionError only, emitting the same gap."}`

3. `{severity: question, title: "Duplicate keys can hide a surrogate from the scan", evidence: "Interfaces: the scan runs on the json.loads result. json.loads keeps the last duplicate key, so {\"a\":\"\\ud800\",\"a\":\"ok\"} scans clean. The PRD says to validate native JSON records, including keys. That wording could mean the text of the record rather than the decoded value. The design never says the driver uses identical json.loads defaults.", suggested_fix: "Decide and document it. Either accept shadowed values because the driver never sees them, with a test and a protocol note. Or parse with object_pairs_hook so every pair is scanned."}`

4. `{severity: question, title: "Does any stage after bounded_detail remove characters?", evidence: "Data flow step 3 and the SessionSummary.__post_init__ text ('existing sanitizer and 4096-character cap'). R2 is a class bug: strip after redact. The design fixes one instance and never states that Observation's second sanitizer, sanitize_json and the summary sanitizer only redact and never strip or normalize. If any of them strips, the same leak recurs.", suggested_fix: "Add a design line, backed by a read of those functions, confirming no later stage mutates characters beyond redaction. Add the cap reproducer to the summary failure_detail path too."}`

5. `{severity: non-blocker, title: "Writer-failure injection for the supervisor test is unnamed", evidence: "Test strategy, runtime paragraph: 'inject a normalized writer OSError'. The Reuse inventory forbids a new production seam. The mechanism could be a monkeypatch, which proves less, or the existing evidence ceiling. Also Risks closes with 'Unresolved questions: none', which this gap contradicts.", suggested_fix: "Name the mechanism. Prefer a tiny evidence ceiling or a real unwritable path through the existing EvidenceLimitError or OSError route. If it is a patch on the writer instance, say so."}`

6. `{severity: non-blocker, title: "Scalar scans repeat across the construction path", evidence: "Interfaces: _payload scans the full mapping, then sanitize_json scans the same input again. This is a cost question only. Frames are bounded at 1 MiB.", suggested_fix: "Keep it for clarity, or let _payload call _sanitize_json after its own scan. Record the choice."}`

**Checked, no finding**
- **Cardinal sins:**
  - There is no schema or state change (Architecture fit), so rollback is a plain revert.
  - Normalized JSONL cannot already hold surrogates, because the strict encode raised before write. This depends on the encode happening before any bytes are written, which I could not check.
  - Observability holds: the gap carries a static reason, a digest and a preview (Interfaces).
  - The PRD names the owner as the repository owner.
- **Writer failures:** publication stays outside the decode catch, so writer failures are not reclassified as gaps.
- **Preview:** it decodes bytes with replacement, so it cannot yield surrogates. The 512-character cap is far smaller than the 4096-byte window, so a token cannot be bisected there.
- **Cap order:** the 4096 cap runs after redaction and can only cut inside `[REDACTED]`. Truncation cannot create a new credential match.
- **Escaped pairs:** valid escaped surrogate pairs combine to one scalar and stay accepted.
- **Sensitive keys:** scanning before sanitization means a surrogate under a sensitive key now rejects the frame instead of becoming `[REDACTED]`. That matches the PRD.

**Status**: Partly done.
**Changed**: nothing, read-only review.
**Not done**: the code claims about `_complete`, `_preview`, `bounded_detail` and the adapter fields `_session_id`, `_usage`, `_thread_conflict`, `_identities` are unverified. Re-run the review with working file tools to close that.
**Next**: You: check the tool environment (all calls were cancelled), then say "go" and I will re-verify findings 2, 3 and 4 against the source.

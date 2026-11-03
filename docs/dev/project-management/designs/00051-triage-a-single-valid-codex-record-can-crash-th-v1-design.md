# UTF-8-safe normalized evidence design

## Architecture fit

This repairs the implemented Phase 4 observation/raw-first seam and Phase 7
diagnostic projection in place, following the authoritative
`docs/dev/project-management/plans/implementation-plan.md`. The refreshed
capsule and actual modules agree that both adapters, observations and supervisor
are implemented: the adapter decodes threads, usage, tools, lanes and terminals,
and the supervisor already persists them.
Shared scalar validation belongs in `events/model.py`; native JSON string
preflight belongs in `events/tail.py`; control stripping remains at the provider
edge in `drivers/codex_events.py`. Runtime continues to consume normalized
observations and owns process cleanup and genuine evidence failures.

The inspected code currently permits surrogates in `Observation` identifiers
and payloads, then fails at `NormalizedEventWriter.write`'s strict UTF-8 encode.
`RawFirstDecoder._complete` catches decoding failures but deliberately publishes
outside that catch. Moving publication into the catch would hide storage errors
and would occur after adapter mutation. The repair must reject the native frame
before calling the stateful adapter. `bounded_detail` currently sanitizes before
removing controls; its 4096-character cap can expose a reconstructed short token
fragment that no longer meets the sanitizer's whole-token threshold.

No state schema, command, workflow policy, driver ABI, observation protocol,
launcher provisioning or TUI behavior changes. Runtime production modules need
no changes. Raw evidence remains private, exact and permanently retained by
default. No live launcher/model calls are required.

## Module placement

| Path | Disposition | Change |
| --- | --- | --- |
| `src/ovcaq/events/model.py` | Edit | Shared recursive scalar predicate; validate original identifier/payload strings before sanitization and freezing; cover summary text and special usage branches. |
| `src/ovcaq/events/tail.py` | Edit | Parse and validate native JSON strings before invoking the driver; preserve the publication failure boundary and existing raw fallback. |
| `src/ovcaq/drivers/codex_events.py` | Edit | Reorder the existing `bounded_detail` implementation to remove controls, sanitize, then cap. |
| `tests/events/test_unicode_safety.py` | New | Direct-model scalar rejection and actual raw-first state/continuity regressions. |
| `tests/drivers/test_codex_detail_safety.py` | New | Actual diagnostic failure/rate/lane payload and serialization regressions. |
| `tests/runtime/test_unicode_continuity.py` | New | Real fake-child continuity and real supervisor writer-failure propagation. |
| `tests/events/test_tail.py` | Existing coverage; edit only if needed | Preserve genuine raw/normalized failure assertions and framing contracts. |
| `docs/driver-protocol.md` | Edit | Scalar rejection, before-mutation boundary, safe gaps, and genuine storage failure contract. |
| `CHANGELOG.md` | Edit | Unreleased Fixed entries describing these two repairs. |

Before each production repair, independently reproduce its PRD premise. If the
branch already satisfies it, retain regression tests and report that fact;
do not force a redundant implementation change. Do not edit the PRD or state.

## Interfaces & contracts

The following signatures and behavior are the task contracts. All existing
public names, enum values and field shapes remain unchanged.

```python
# src/ovcaq/events/model.py — new module-level internal helper;
# imported directly by events.tail, not re-exported from ovcaq.events.
def has_invalid_unicode_scalar(value: object) -> bool: ...

# Existing public signature; validation wraps the existing recursive copier.
def sanitize_json(value: object) -> JSONValue: ...

# New private recursive copier: existing sanitize_json body moves here,
# and its recursion uses _sanitize_json rather than repeating root scans.
def _sanitize_json(value: object) -> JSONValue: ...

# Existing boundaries; signatures retained.
def _identifier(value: object, *, optional: bool = False) -> None: ...
def _payload(
    kind: ObservationType, payload: Mapping[str, JSONValue]
) -> dict[str, JSONValue]: ...
def observation_record(observation: Observation) -> dict[str, JSONValue]: ...
def observation_from_record(record: Mapping[str, JSONValue]) -> Observation: ...
def summary_record(summary: SessionSummary) -> dict[str, JSONValue]: ...

# src/ovcaq/events/tail.py — existing signatures retained.
def RawFirstDecoder.feed(self, chunk: bytes) -> tuple[Observation, ...]: ...
def RawFirstDecoder.finish(self) -> tuple[Observation, ...]: ...
def RawFirstDecoder._complete(
    self, *, terminated: bool
) -> tuple[Observation, ...]: ...
def NormalizedEventWriter.write(self, observation: Observation) -> int: ...

# src/ovcaq/drivers/codex_events.py — existing signature retained.
def bounded_detail(detail: str) -> str: ...
def classify_failure(detail: str) -> FailureClass: ...
def failure_reset(detail: str, now: datetime) -> datetime | None: ...
```

`has_invalid_unicode_scalar(value)` is a side-effect-free predicate over strings,
`Mapping` keys and values, and list/tuple elements. It returns `True` iff any
reachable string contains a code point in the inclusive range
`0xD800..0xDFFF`. Other scalar types are ignored; existing JSON/type/finite-number
validation remains responsible for their acceptance. Scan supported acyclic
JSON-like containers iteratively to avoid introducing a new recursion-depth
failure during preflight. It neither redacts nor modifies input. Ordinary
Unicode, including non-BMP scalars, remains unchanged. `json.loads` decodes a
valid escaped high/low surrogate pair to one non-BMP scalar, which is accepted;
unpaired decoded surrogates and Python strings still containing surrogate code
points are rejected. This is validation, never replacement or ASCII escaping.

`sanitize_json` checks the complete original input with the predicate before
calling `_sanitize_json`; invalid input raises
`ValueError("Strings must contain only Unicode scalar values")`. Check nested
keys and every value, including values beneath sensitive keys which will later
be replaced by `[REDACTED]`. Preserve existing valid-container copying,
credential redaction, nonstring-key `TypeError`, nonfinite-number rejection and
unsupported-type errors. `_sanitize_json` retains existing recursive behavior
and uses its own name for recursion, so the complete scalar scan runs once per
public `sanitize_json` invocation rather than once for every subtree.

`_identifier` retains its nonempty-string/optional-None rules, then rejects
invalid scalar strings with the same static `ValueError`. This protects
`Observation.provider`, `run_id`, `session_id`, `lane_id`, and the existing
`SessionSummary.session_id` caller. `_payload` checks the complete original
mapping before inspecting payload shapes or taking the `_usage_payload` early
return. Thus `usage.updated.identity`, nested usage keys/values and
`session.completed`'s special usage branch cannot bypass scalar validation.
Invalid strings fail before sanitization, truncation or freezing, even if those
operations would have removed them. `SessionSummary.__post_init__` checks a
nonnull string `failure_detail` before its existing sanitizer and 4096-character
cap. Existing invalid-type checks stay in place. `observation_record`,
`observation_from_record` and `summary_record` retain their signatures and field
shapes and serialize only successfully constructed validated models. Error
messages never include the rejected string, mapping key, or credential.

`RawFirstDecoder.feed` continues to call raw `write` and `flush` before any
framing or preflight; `finish` flushes before the unterminated final frame.
For a bounded frame that decodes as strict UTF-8, `_complete` first calls
`json.loads(frame)` solely for scalar preflight. If parsing raises `ValueError`
or `RecursionError`, delegate the unchanged original frame to the driver under
the existing decode-failure boundary: malformed/non-JSON fallback behavior is
preserved. If parsing succeeds, apply `has_invalid_unicode_scalar` to the full
decoded value. An invalid scalar rejects the frame before any call to
`driver.decode`; emit exactly one `ObservationType.RAW_UNKNOWN`, with no other
semantic observations, and retain the driver's pre-frame state. A valid parsed
value still delegates the original string, without replacing driver-native
semantic parsing or changing `AgentDriver.decode(raw_line)`.

The scalar fallback uses existing fields exactly:
`{"reason", "raw_sha256", "preview"}`. Its reason is the static string
`"frame contains invalid Unicode scalar value"`; `raw_sha256` is the existing
lowercase 64-character SHA-256 of the frame bytes (excluding newline and exactly
one framing CR under existing CRLF rules); preview is the existing
`RawFirstDecoder._preview(length)`. Preview decodes original raw bytes with
replacement for invalid byte sequences, sanitizes, and caps at 512 characters;
JSON escape text remains literal, so decoded invalid scalars never reach the
fallback. Preserve its bounded window, token-boundary handling and digest
behavior. Preserve `max_frame_bytes=1024 * 1024` and
`_PREVIEW_WINDOW_BYTES=4096`; no new limits. Keep envelope ownership binding via
`_bind_observations`, supplied `run_id`/`session_id`, latest accepted native
identity for unbound callers, and startup `source_session_id` behavior.

Before-mutation assertions cover the actual adapter's `_session_id`, `_usage`,
`_thread_conflict` and `_identities`, including invalid strings in ignored
native fields or nested keys on otherwise valid startup, completion and
collaboration records. Rejected frames cannot seed terminal evidence, lanes,
tools, usage counters or a conflicting thread. A later valid frame observes
the exact pre-frame adapter state. This guarantee concerns raw-first native
frame rejection; no new rollback mechanism for arbitrary driver bugs is added.

Consume `tuple(driver.decode(frame))` under the existing tolerant decode catch
before publishing any observations. Leave `_bind_observations`, raw I/O,
normalized `write`/`flush`/`close`, evidence ceilings/free-space checks and all
publication outside that catch. `NormalizedEventWriter.write` continues strict
`json.dumps(..., ensure_ascii=False, allow_nan=False)` and `.encode("utf-8")`.
`OSError`, `EvidenceLimitError`, closed-writer failures and normalized
publication/encoding errors must propagate; never reclassify them as harmless
`raw.unknown` gaps. The unchanged supervisor `_stream` kills an owned child
group when collection fails before EOF, and `_attempt` records the failure and
re-raises. Raw and normalized partial evidence retains its existing semantics.

`bounded_detail` must implement this exact order:

```python
cleaned = re.sub(
    r"\x1b\[[0-?]*[ -/]*[@-~]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
    "",
    detail,
)
return sanitize_text(cleaned)[:4096]
```

Recognized control forms are unchanged. Redaction sees the entire cleaned
string before the cap and before Observation's existing second sanitizer.
The exact synthetic input
`'x'*4080 + ' sk-abc\x1b[0mdefghijklmnopqrstuvwxyz0123456789ABCDEF'`
must produce no reconstructed full token and no `sk-abcdefghijkl` in either
the bounded helper return or actual normalized diagnostic payloads/JSONL.
ANSI/NUL splits of ordinary synthetic tokens are redacted too. All resulting
failure/rate/lane details are at most 4096 characters. The existing adapter
still calls `classify_failure` and `failure_reset` on full original native text
before `bounded_detail`; precedence, six-hour reset bound and reset metadata
remain unchanged. Apply via existing call sites for top-level `error`,
`turn.failed` plus `rate_limit.started`, and receiver lane messages.

The documentation must accurately distinguish recoverable input gaps from
fatal evidence/publication failures, state that invalid native strings are
checked before driver mutation, and describe control removal before redaction
and bounding. Add Unreleased Fixed changelog entries; no version bump.

## Data flow

1. The owned subprocess emits native bytes. `SessionEvidenceWriter.write` and
   `flush` durably preserve each accepted raw chunk before parsing it.
2. `RawFirstDecoder` retains the existing bounded newline framing and digest.
   Strict byte decoding rejects invalid UTF-8; JSON preflight rejects decoded
   surrogate code points without invoking the stateful driver.
3. Valid scalar frames enter the existing native decoder. Diagnostic strings
   pass through provider control removal, full-text redaction and the cap.
   Shared model construction independently rejects invalid original identifier
   and payload strings, then redacts and freezes them.
4. Rejected native scalar frames produce only the shared safe gap; valid frames
   retain their original projection. Envelope binding and normalized strict
   JSONL publication run outside tolerant decoding.
5. The unchanged reducer/supervisor sees gaps plus later valid usage/terminal
   evidence and permits normal child completion. Real evidence failures instead
   take the existing owned-group cleanup and failure path.

## Reuse inventory

Reuse sweep used the installed `rationalizations.md` verb/noun synonym sets,
searched code and relevant tests, and inspected all hits below. No portfolio
helper dependency is introduced.

- `src/ovcaq/events/model.py:_identifier`, `_payload`, `_usage_payload`,
  `_freeze`: extend the existing construction boundaries; do not add a second
  observation representation. Queries: `validate|check|assert_|is_valid|verify`
  and `unicode|surrogate|scalar|utf.?8|string|payload|identifier`.
- `src/ovcaq/events/model.py:sanitize_json`, `sanitize_text`, `_SENSITIVE_KEY`,
  `_CREDENTIAL`, `_LIKELY_SECRET`: preserve existing credential rules and move
  the current copier behind one full-input scalar check. Queries:
  `sanitize|redact|bound|control|ANSI` and
  `detail|credential|secret|token|preview|cap`.
- New scalar predicate: **nothing found in the events layer**, greps tried
  `unicode|surrogate|scalar|utf.?8` plus the validator/string searches above.
  Known-present control search `Observation` in `events/model.py` returned the
  actual constructor and serialization symbols. The state layer does have
  `state/schema.py:_require_string` and `validate_json_value`; inspected them.
  They enforce state-specific byte/depth/container limits and `StateValidationError`
  semantics, so reuse would import unrelated state policy into observations.
  Their strict UTF-8 rejection is precedent, not a suitable shared helper.
- `src/ovcaq/events/tail.py:RawFirstDecoder._complete`, `_preview`,
  `_bind_observations`: reuse framing, exact digest, bounded safe preview,
  malformed-driver fallback, lazy iterable consumption and ownership binding.
  Queries: `parse|from_|decode|load|read` and `raw|frame|record|json|unknown`.
- `src/ovcaq/events/tail.py:NormalizedEventWriter` and
  `src/ovcaq/runtime/_session_evidence.py:SessionEvidenceWriter`,
  `EvidenceLimitError`: preserve strict serialization, private files,
  evidence limits and durable I/O. Queries:
  `writer|write|flush|fsync|disk|limit|fail|except`.
- `src/ovcaq/drivers/codex_events.py:bounded_detail`, `item_lanes`,
  `classify_failure`, `failure_reset` and
  `src/ovcaq/drivers/codex.py:_failure_observations`: reorder one helper used by
  both diagnostic and receiver detail paths; keep classification/reset calls
  where they are. Searches are the sanitizer and detail synonym sets above.
- `tests/events/test_tail.py`: reuse writer/framing/unknown evidence assertions
  and round-trip patterns, especially normalized partial-write errors,
  evidence ceiling/free-space failures, durable raw-before-decode, lazy decode
  failures and chunk/CRLF recovery. `tests/events/test_model.py` and
  `test_model_rework.py` supply immutability, usage and sanitizer precedents.
- `tests/runtime/test_supervisor_process.py:ProcessDriver`, `ProcessClock`,
  `Harness`, `harness`: reuse these test-owned constructors for actual Python
  child/adapter/supervisor execution and private temporary runtime trees.
  Queries: `build|create|make|new_|init|fixture|fake|harness|spawn|supervis`
  against this module, `test_supervisor_adapters.py`, `test_codex_fake.py` and
  the versioned fake executable. Prefer a test-only import or a small local
  wrapper; no new production harness or fixture executable is needed.
- `tests/drivers/test_codex_rework_decode.py:failure_record`, `collab_record`
  and `tests/drivers/test_codex_decode_terminals.py`: reuse actual diagnostic
  record shapes and independent classification/reset oracles. Add the missing
  exact cap-boundary cases in the PRD-named test file.

## Alternatives considered

1. **Smallest diff: change writer encoding or catch publication failures.**
   ASCII escaping keeps invalid strings in normalized models, replacement
   changes identity, and tolerant publication would hide real disk failures.
   None prevents prepublication adapter state contamination; rejected.
2. **Chosen: one shared scalar predicate, construction validation and raw-first
   JSON preflight.** A second bounded parse costs CPU but detects invalid
   strings even in ignored native fields before any adapter code runs. It
   repairs three existing production files without driver ABI, runtime policy
   or state rollback changes. The extra model checks protect direct callers
   and sensitive-value/usage early-return paths independently of preflight.
3. **Validate separately in each adapter or pass parsed records through a new
   driver API.** Adapter checks duplicate the contract and can miss providers;
   a new parsed-record seam requires every adapter/extension caller to change.
   Such an API could remove double parsing later, but is unnecessary for this
   repair and is deferred.

## Risks & edge cases

- Validation after redaction or truncation would accept invalid strings that
  disappeared. Scan original mappings first, including sensitive-key values,
  ignored native fields and special usage paths; assert rejection directly.
- JSON escape spelling is not itself invalid Unicode. Validate parsed values,
  retain the original frame for digest/delegation, accept paired escapes and
  ordinary non-BMP text, and reject all decoded surrogate code points.
- Preflight parses each bounded valid frame twice. Existing one-MiB framing
  bounds the extra work; iterative scalar traversal prevents an added recursive
  scan limit. Preserve malformed/deep-JSON delegation when preflight parsing
  fails rather than silently changing driver semantics.
- The current fallback preview operates on bytes and can safely retain ASCII
  escape text. Reusing it avoids writing unsafe decoded strings or leaking
  exception diagnostics; credential/truncation behavior stays covered.
- Direct adapter calls are still governed by model validation and existing
  decoder error handling. The before-mutation guarantee belongs specifically
  to raw-first frame admission, not generic transactional decoding of arbitrary
  buggy extensions.
- The cap reproducer uses a synthetic token. Tests must assert both the full
  reconstructed token and the exact short fragment are absent, using independent
  expected outcomes rather than the production sanitizer as the oracle.
- Likely next changes are provider event drift, more terminal-control forms,
  and a parsed-record adapter seam to eliminate double parsing. Keep the scalar
  helper provider-neutral, preserve the current control pattern, and avoid ABI
  changes so those follow-ups remain independent. No speculative control forms,
  CLI version repair, retry-policy repair or future-provider branches land here.
- Unresolved questions: none; the PRD specifies scope, bounds and failure policy.

## Test strategy outline

The approved raw-first test split is `tests/events/test_unicode_frames.py`.
The Phase 1 acceptance command is `mise exec -- uv run pytest
tests/events/test_unicode_safety.py tests/events/test_unicode_frames.py
tests/events/test_tail.py`; it covers shared models and raw-first admission.

Characterize all three premises against the unchanged implementation first:
direct invalid Observation construction, actual escaped-surrogate raw-first
publication/state mutation, and the exact synthetic cap reproducer. Capture
failing regression assertions before the corresponding fix; if already fixed,
retain passing independent tests and report the verified exception.

`tests/events/test_unicode_safety.py` names direct-model tests with `scalar`
so the PRD's `-k scalar` gate selects them. Parameterize lone high/low
surrogates in every identifier, strings/list/tuple/mapping values, nested keys,
sensitive values, usage identity/special usage payloads and summary details.
Assert `ValueError` rejection with safe messages. Valid ordinary Unicode and
`json.loads` of paired escapes must construct, round-trip and strictly encode.

Use real raw/normalized writers plus the actual adapter for invalid startup,
activity/error, tool/lane, usage/completion and ignored-key/value native frames.
Snapshot session ID, usage, thread-conflict and remembered identities before
each invalid frame. Assert exactly one gap with expected digest/preview, no
decode invocation for rejection, unchanged private state, exact raw bytes,
reloadable strict normalized JSONL, unchanged owning session identity, and
later valid native identity/usage/terminal behavior. Include split chunks,
CRLF and an unterminated final frame. Preserve invalid-byte, malformed and
non-JSON behavior, valid pair acceptance, limits and genuine writer failures.

`tests/drivers/test_codex_detail_safety.py` drives actual `error`,
`turn.failed`, rate-limit failures and collaboration receiver lane messages.
Check helper output and final payload/JSONL with the exact cap reproducer and
ANSI/NUL split synthetic tokens; assert independent absence of the full token
and `sk-abcdefghijkl`, presence of redaction, and length <=4096. Include full
native classification/reset cues beyond the cap to prove both still use the
uncapped original diagnostic.

`tests/runtime/test_unicode_continuity.py` uses the existing real-process
supervisor harness with a temporary Python child that flushes unsafe native
records, remains alive for a bounded interval, emits later valid identity,
usage and terminal evidence, writes a normal-exit sentinel and exits zero.
Assert sentinel/observed normal exit, no forced kill or timeout, expected final
summary, exact raw stream and reloadable gap-plus-terminal normalized evidence.
No network probes or live provider calls. In a separate actual-supervisor case,
inject a normalized writer `OSError` while a bounded child remains alive;
assert the error propagates, owned child cleanup occurs, failure evidence is
retained, and the normal-exit sentinel is absent. Retain evidence-limit, disk
and raw-writer tests; the gap path must never swallow publication exceptions.

Run the PRD's focused commands, then the full sync/pytest/ruff check/ruff format
check/mypy/build gates once after all implementation changes. Documentation is
checked against the implemented helper order, fallback bounds and actual
writer-failure boundary, without adding a second command inventory.

## Review log
dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 1, question 0
Host adaptation: native Codex gpt-6.1-sol/high; engagement retry completed with section-anchored checks.
Non-blocker: define terminating cycle/repeated-container handling for direct-input iterative scan; native parsed JSON is acyclic. No change made during design per non-blocker policy.

dispatch 2 (codex): cardinal-sin 0, blocker 0, non-blocker 4, question 2
Host adaptation: mandatory rival dispatch used Anthropic Sonnet/high through installed use-sonnet wrapper, with no tools. Review is draft-based; source-code claims were not independently verified by this reviewer. Parseable section-anchored findings satisfied engagement; no blocker and no dispatch 3 required.
Non-blockers: terminating cycle/shared-container handling; deep JSON parse fallback relies on driver parse failure; name supervisor writer-failure injection mechanism; repeated root scans are bounded overhead.
Questions: shadowed duplicate-key values admission meaning; whether post-detail stages remove characters beyond redaction. These remain recorded per design review non-blocker/question policy.

## Review-1 contract correction (R5)

Review-1 R5 identified a specification gap in the historical strip-first recipe
above: removing C0 controls, DEL or a lone ESC can destroy the original word
boundary before a bare token or Bearer value. The recipe and review evidence
remain recorded; the following order supersedes that recipe:

```python
controls = r"\x1b\[[0-?]*[ -/]*[@-~]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
protected = re.sub(
    controls,
    lambda match: "\x00" if match[0] == "\x1b" else match[0],
    detail,
)
cleaned = re.sub(controls, "", sanitize_text(protected))
return sanitize_text(cleaned)[:4096]
```

Before redaction, mask only originally recognized lone ESC controls as NUL.
Both controls supply the same regex word boundary and are subsequently removed;
this prevents a redaction marker from forming a new `ESC[REDACTED]` CSI sequence.
Original recognized CSI sequences remain intact until control removal.

The first pass retains original regex boundaries; the second pass redacts
credentials reconstructed by the unchanged control removal before the cap.
Shared sanitizer boundaries and recognized control forms remain unchanged.
Failure classification and reset extraction still consume full untouched native
text. Read-only regressions cover C0/DEL/lone-ESC boundaries and token interiors
through the helper, native payloads and saved JSONL, alongside the original
control-split cap cases.

Review-1 R4 uses a precompiled surrogate-range regex while retaining the full
original-container validation before redaction, including sensitive values,
valid non-BMP scalars and subclass handling. Existing public sanitizer calls
remain validated. R7 independently pins deeply nested JSON parse recursion to
the driver's native gap reason and unchanged adapter state. For R8, extracted
preflight parsing and scalar validation remain inside the existing tolerant
decode catch; malformed or recursive JSON delegates unchanged, and genuine raw
or normalized publication failures still propagate outside that catch.

The witnessed cyclic/repeated-container and direct-adapter limitations remain
out of scope and recorded in the historical review ledger; no cycle guards,
TUI changes or wider control recognition are introduced.

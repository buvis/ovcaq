# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **drivers**: every driver publishes a `default_tiers` table, so a project that configures no tier table still resolves the `standard` and `deep` phase tiers. Configured tiers always win. The Codex driver maps both tiers to the reserved value `default`, which emits no `-m` argument and leaves the Codex CLI on its own configured model.
- **runtime**: `ovcaq doctor` reports a sixth capability fact, `process_identity`: `supported` with the start token as detail, or `degraded` with the error text, which makes `doctor --json` report `ok: false`.
- **runtime**: add the `process_probe` error code (exit 12) for a libproc process-identity probe that cannot run; its message names the platform and points to `ovcaq doctor`.
- **runtime**: `ovcaq run` validates the process identity probe and the build, review and done phase routes before any state write, so a failure leaves `state.json` at the same revision.
- **runtime**: a failure while publishing run metadata or the fleet entry removes what was written, returns a fresh batch to idle or records an attention notice on a resumed batch, and exits 1.
- **tools**: add read-only `tools/autopilot-prerequisites --prd <ID>`, which reports whether a PRD's done-bucket predecessors, digest-pinned evidence artifacts and pinned contract bundle are in place. Configuration is read and refused for every supported PRD, not only the ones carrying an artifact gate. The tool and the controller client read one configured pin the same way: hex letter case is the only difference forgiven, and a bundle with a duplicate key or a non-finite number is refused by both.
- **workflow-client**: add an internal Contract A controller client (contract, snapshot and apply over an explicit argv, with bundles pinned by the sha256 of their raw bytes and validated as strict JSON objects, mandatory capability negotiation, producer-identity checks, every post-spawn abnormal exit of an apply reported as an unknown outcome to retry, credential-opaque redaction that never reads the actor file and drops controller text wholesale when the actor file is too small or unreadable for masking to reach its credential (a credential shorter than eight characters inside a larger actor file is not masked and can still appear verbatim in a diagnostic), and bounded output on both streams with the process group always reaped); nothing invokes it yet.
- **dev**: add pinned mise development tasks, executable command shims, the Claude instruction bridge, and a linked architecture overview.
- **drivers**: run supervised workflows with Codex, configured models and effort, verified version/authentication checks, and state-based phase handoffs.
- **drivers**: show Codex activity, tools, receiver lanes and cache-aware usage with retained raw evidence; conflicting native threads fail safely even after supervisor ownership binding.
- **tui**: add `ovcaq attach`, TTY-default attachment for `ovcaq run`, detachable interactive controls with plain fallback, and interactive `resume` that attaches to a live supervisor or launches once after a boundary pause.
- **runtime**: run batch capabilities as durable provider-neutral attempts with private session evidence, final metrics, stale-owner reconciliation, and explicit one-attempt retry of failed capabilities.
- **state**: add guarded compound supervisor mutations for pause/resume, progress fingerprints, capability attempts, failure attention, and empty-drain completion.
- **runtime**: publish one immutable canonical metric row per phase or capability session, reconcile interrupted evidence deterministically, and project versioned metrics through legacy-compatible reports.
- **config**: resolve provider-neutral build, review, and done routes with validated effort, timeout, model-tier, retry-policy, and literal prompt configuration; drivers now expose the version-two default-prompt contract.
- **config**: load immutable per-agent argv, tier, environment, and JSON option settings with user/project merging and credential-shaped value rejection.
- **drivers**: define the immutable provider-neutral launch, health, plugin, and discovery contracts with exact-version, duplicate-name, and fail-closed probe validation.
- **drivers**: add the shell-free Claude launch adapter with explicit unattended permissions, configured tier and fallback resolution, isolated environment construction, executable health checks, and neutral summary reduction.
- **drivers**: normalize Claude init, activity, tool, lane, usage, rate-limit, and terminal stream records with bounded replay-safe identity tracking and closed failure classification.
- **events**: define the immutable version-one observation, usage, failure, summary, redaction, validation, and JSON record contract.
- **events**: deterministically reduce normalized sessions, fold cumulative usage without double counting, preserve typed completion usage, and synthesize sanitized failure observations.
- **events**: persist private normalized JSONL and decode bounded newline frames only after exact raw bytes are durably recorded, with observable sanitized fallbacks for oversized or failing frames.
- **runtime**: resolve secure project, runtime, fleet, and evidence paths with validated limits and stable documented field order; probe required macOS process and durability capabilities; and publish, observe, prune, and conditionally remove identity-pinned fleet records behind inode-stable run locks without launch contention.
- **runtime**: own shell-free process groups through persistent anchors, preserve descendant ownership and validated cleanup ancestry without mutating substituted paths, escalate timed-out groups from TERM to KILL through serialized bounded watchdogs, map supervisor signals to exit statuses, and durably remove matching ownership records while retaining evidence and lock files.
- **runtime**: persist complete bounded raw session bytes; publish private metadata and summaries that reject unsafe identifiers, mismatches, non-UTC timestamps, and empty required fields; inventory retained evidence; and apply explicit active-safe purge plans with verified ancestry, locks, bounded malformed-row preservation, and durable deletion.
- **runtime**: gate launches on durable emergency state-write evidence, preserve concurrent evidence, reject malformed or deeply nested records, revalidate evidence before acknowledgement, archive the exact acknowledged record, and restore the gate after failed acknowledgement.
- **cli**: expose runtime status, actionable doctor resource checks, retained-log lookup/follow, non-applying purge previews, and explicit purge application; reject conflicting parent log options, omit internal path metadata, and reuse validated state for emergency acknowledgement.
- Import-only package boundaries and a help-only `ovcaq` command.
- Versioned v1 state schema/defaults and the exhaustive legacy-field crosswalk.
- Closed v1 state validation with nested, resource, and cross-field invariants.
- Locked state-store transactions with canonical publication, raw backups, and restore.
- Monotonic revisions and locked compare-and-set conflict checks for transactions and restores.
- Create-only initialization requires an existing runtime directory and repairs failed publications.
- Pure JSON-path parsing and in-memory get/set/append/delete recovery operations.
- Atomic StateService task, attempt, metadata, count, and contract-card commands.
- Parsed-token protection for generic state recovery, with explicit unsafe override.
- P01-T10 state CLI dispatch, stable errors, root discovery, and parser-derived command documentation.

### Changed

- **config** (breaking): the default phase tiers are now the neutral keys `standard` (build, done) and `deep` (review) instead of the model names `sonnet` and `opus`. A project whose `[agents.<agent>.tiers]` table only names models no longer resolves the default routes; add `standard` and `deep` keys to that table, or drop it and take the driver's own `default_tiers`. A PRD frontmatter tier floor must also name a key the table defines.
- **runtime**: process identity reads libproc through ctypes; OVCAQ no longer spawns `ps`.
- **runtime**: process start tokens are `"<sec>.<usec>"` instead of the `ps lstart` string; a supervisor running across the upgrade reads as dead once and its records are cleaned up, without migration.

### Fixed

- **drivers**: Claude terminal diagnostics naming an expired OAuth token, an HTTP 401 or 429, a rate limit, or a socket error (`ECONNRESET`, `ETIMEDOUT`, `ECONNREFUSED`, `EAI_AGAIN`, `getaddrinfo`) now classify as `authentication`, `rate_limit` or `connectivity` instead of falling through to `agent`, so an auth expiry halts for operator access and a network fault takes a bounded wait rather than parking a healthy PRD. Numeric codes still need their `http`/`status` context word: a bare `401` or `429` does not classify.
- **drivers**: Codex native diagnostics naming an OAuth or token expiry now classify as `authentication`, and the socket errors `ECONNRESET`, `ETIMEDOUT`, `ECONNREFUSED`, `ENOTFOUND`, `getaddrinfo` and `EAI_AGAIN` as `connectivity`, instead of returning `unknown`. The word-boundary wrapper is unchanged, so a marker glued inside a longer identifier (`econnreset_handler`) and a generic `Authentication failed` both still return `unknown`.
- **runtime**: a failed start no longer crashes when cleaning up its own ownership records: the fleet-entry removal is best-effort against a rejected run id as well as an I/O error, so the batch still returns to idle and the run still exits 1.
- **runtime**: a failure after the supervisor has opened a session keeps the batch `running` with an attention notice instead of returning it to idle; only whether a session actually opened decides this, never the session counter, which also moves for the reverting cases.
- **cli**: `ovcaq capability retry NAME` with a name not in `batch.capabilities` is a `usage` error (`unknown capability: NAME`, exit 1) instead of a traceback.
- **workflow**: refuse missing or conflicting PRD artifacts before recovery intent, and verify source identity throughout intent publication so rejected stall/park requests preserve state and backups.
- **state**: allow explicit backup restoration of an older unbound recovery intent while keeping bound or advanced recovery fenced.
- **workflow**: require a running batch and an active PRD for phase transitions, with a PRD-free drain allowed from the build phase.
- **docs**: correct Codex matched-lane fixture provenance and describe tool, message and plan details with the newest-first 20 activity / 20 lanes display window.
- **tui**: show the newest twenty activity entries before the first twenty lanes, with separate omission counts.
- **tui**: retain distinct messages without IDs and warning details, match message updates by their full IDs while keeping activity bounded, and show tool details from normalized observations.
- **drivers**: Claude health checks honor configured executable search paths and recognize executables available there, use system defaults when the host search path is missing, and continue reporting an empty host search path as unhealthy.
- **drivers**: preserve once-resolved supervised Codex models when their names also match tier keys, retaining direct tier-key precedence and explicit-model validation.
- **drivers**: prevent ordinary counts such as "processed 401 files" from triggering Codex failure handling; numeric failure codes require an HTTP, status or error label.
- **drivers**: classify 'Selected model is at capacity' as connectivity so it gets bounded WAIT retries instead of rate-limit handling.
- **drivers**: keep remembered completed and failed Codex receiver lanes terminal under late updates; synthetic close failures apply only to remembered unfinished lanes, while closes of terminal lanes retain raw unknown evidence.
- **drivers**: redact diagnostic credentials both before and after terminal control removal, preserving original token boundaries and hiding reconstructed tokens before truncation.
- **events**: speed up surrogate detection while preserving original-container validation and tolerant native preflight handling.
- **drivers**: remove terminal controls before redacting and bounding Codex diagnostic details so split credentials cannot survive normalization.
- **events**: retain native JSON frames containing invalid Unicode scalars as raw gaps before adapter state can change, allowing supervised sessions to continue while genuine normalized publication failures still propagate and trigger owned-child cleanup.
- **events**: reject surrogate code points in shared observation and summary text before redaction or truncation while preserving valid Unicode scalars.
- **cli**: reject unhealthy adapters before foreground agent execution using sanitized health diagnostics.
- **tui**: show bounded normalized tool, message and plan activity alongside selected-session lanes with literal markup.

- **tui**: surface selected-run observation read errors as gaps while preserving ownership checks and process-control exceptions.
- **runtime**: keep standalone `run_once()` usable without full-loop ownership metadata while preserving supervisor identity across full-run sessions.
- **runtime**: preserve unknown numeric usage in final metrics while retaining exact fields and strict validation of known values.
- **tui**: fall back after ordinary interactive-view failures, detach plain viewers on real EOF, and print only changed frames while preserving terminal results.
- **tui**: persist theme changes from both views, honor trusted XDG aliases, and use private no-follow theme I/O with replacement checks that tolerate concurrent readers.
- **tui**: sanitize both fleet selectors and show stale/malformed registry counts and empty-fleet status without selecting a run.
- **launcher**: recognize verified fast completion and attachment cleanup races, preserve bounded private startup diagnostics, honor configured runtime roots, and guide duplicate-owner failures to attach even while the new child is still starting.
- **cli**: require explicit foreground mode for JSON runs and load viewer dependencies only for interactive commands.
- **tui**: guard selected-run pause/resume through durable publication, reuse those controls for interactive resume, and honor the injected fleet registry for stop.
- **runtime**: provide shared ownership exclusion for guarded state mutations, preserving state and backup bytes when a selected owner becomes stale during publication.
- **tui**: keep controls responsive during observation reads and show elapsed selected-run duration instead of summed session times; terminal duration uses durable end evidence so late polls cannot inflate it.
- **runtime**: bind terminal observations to the exact supervisor and revalidate evidence reads without competing for the launch lock or discarding ordinary active state progress.
- **tui**: display normalized lane descriptions when an explicit lane label is absent.
- **events**: bind normalized observations to the owning supervisor run and session while retaining exact native raw evidence.
- **tui**: retain selected final state and telemetry after supervisor cleanup, reject replacement evidence, and render terminal outcomes before viewers exit.
- **tui**: follow active session telemetry across rollover, retain stream damage diagnostics, preserve live usage and numeric costs, show the latest capability attempt's evidence path, and distinguish raw-only content without changing evidence presence flags.
- **paths**: align workflow, runtime, report, launcher, and test defaults on the
  `docs/dev/project-management` store tree.
- **runtime**: keep supervisor session collection within style limits while preserving timeout evidence and classification.
- **runtime**: honor supplied phase settings on every workflow launch while preserving agent overrides and literal prompts.
- **workflow**: include canonical phase metrics in reports when usage is missing or malformed while excluding capability attempts from workflow totals.
- **runtime**: share capability execution and failure evidence across pending runs and retries, honor bounded capability timeout precedence, and defer aggregate publication until completion.
- **runtime**: persist operator stops until resume and halt state failures behind sanitized durable attention or an emergency restart barrier, preserving existing attention notices.
- **runtime**: bound unchanged attempts across failure classes while preserving terminal halts, honor committed controls before capabilities and drain completion, and preserve phase-pause reasons on resume.
- **runtime**: initialize batch identity before sessions, preserve capability failure and retry attention, and archive completed batches using the supervisor clock.

- **events**: normalized evidence redacts `x-api-key`, `apiKey`, and other separator or case variants of API-key names, and raw fallback previews redact before truncating so no secret prefix survives the cut.
- **events**: redaction stays linear on long unbroken text, and raw fallback previews read a bounded head of the frame, so one bad frame can no longer stall decoding or expose a secret cut at the frame limit.
- **events**: credential assignments behind sensitive key names longer than 64 characters are redacted again.
- **events**: raw fallback previews of a cut-off frame with no whitespace come out empty whenever an `sk-` token is in view, and short CRLF frames no longer carry the trailing CR.
- **drivers**: a dated limit banner whose date does not exist in its year (such as Feb 29 in a non-leap year) yields no reset instead of jumping to a later leap year.
- **drivers**: rate-limit warnings no longer clear a live limit, a rejected event's reset wins over the terminal banner, real clock-and-zone banners such as `resets 8:10pm (Europe/Prague)` yield a reset, and the limit window is structured payload data.
- **drivers**: dated limit banners such as `resets Sep 20 at 11am (Europe/Prague)` yield a multi-day reset, and a terminal banner reset now applies after a rejected event that carried no credible future reset.
- Agent configuration applies command defaults and shared validation; normalized text redacts bare credential tokens while preserving usage counters.
- Deferred directory setup diagnostics report the full configured path while preserving the originating OS error.
- Deferred publication revalidates the complete confirmed runtime ancestry before returning success.
- Deferred ancestry confirmation detects replaced ancestors on reopen, supports search-only access, and avoids redundant ancestor creation and root confirmation.
- Shared publication contention reports `publication busy; retry: <path>` for both reports and deferred ledgers.
- Deferred retries and replays confirm existing runtime ancestry after abrupt exits and preserve directories created by concurrent callers when confirmation fails.
- Deferred publication validates the complete prospective ledger and persists newly created runtime ancestors; overlapping report renders no longer lose successful sections.
- Report JSON returns the complete published batch text after PRD updates and exact rerenders.
- Deferred ledgers reject duplicate keys and excessive nesting; replaced sidecar locks refuse publication without losing competing appends.
- Park/stall recovery retains the original PRD's filesystem identity through restart and preserves unfinished work on substitution.
- Batch reports reconstruct all deferred details with PRD attribution; report, audit, and archive retries complete directory durability.
- Blank decision content is omitted consistently from counts and audits; named payload and configuration files reject nonregular inputs promptly.
- PRD moves atomically refuse concurrent held work; filesystem evidence remains checked through saga state publication.
- Recovery validates batch identity and operation inputs before creating lifecycle directories or durable intent.
- Installed workflow commands honor configured roots and active abstract tier keys, with explicit path and tier overrides.
- Metric inputs reject FIFO/nonregular files promptly; systemic park pauses return a distinct halt status and actionable output.
- Workflow orchestration, render sections, and installed/saga tests are split by responsibility while retaining failpoints and acceptance coverage.

- Drained workflows remain terminal, and stall refuses conflicting recovery intents while park retains reconciliation behavior.
- Workflow reports preserve unknown legacy totals, order equal-key metric rows deterministically, and reject nonregular output targets without blocking.
- Deferred ledger publication and saga commit now verify the configured directory identity through durable writes and recovery.
- State validation now uses canonical persisted-byte sizing, precise nested diagnostics, and cached type metadata.
- CLI task payloads now reject non-object JSON, option abbreviations are disabled at every parser level, and resource limits use typed errors.
- State transactions now overwrite mutator-supplied revisions before validation and close lock descriptors on every setup failure.
- The installed state service now owns restore routing, and the protocol documents the complete schema, durability, and error contracts.
- Project initialization now preserves existing config metadata and remains retryable when config creation fails.

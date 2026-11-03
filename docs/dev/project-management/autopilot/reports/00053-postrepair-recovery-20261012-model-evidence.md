# PRD00053 five-finding repair provenance

The canonical implementation-model audit and prior reviewed snapshots remain
unchanged. Regenerate the audit in the next fresh review session, including
all prior contributing attempts and the evidence below, before review-route.

Task 18 uses the installed micro lane: one MEDIUM finding, two initially clean
test files, net -1 line. Commit 693e7ae consolidates the runpy wrapper in
test_supervisor_adapters.py and uses it in test_adapter_launch_routing.py;
both providers retain invocation evidence. Range 9d892a3..693e7ae.

Task 19 uses native /root/task19, isolated gpt-6.1-sol/medium, logical sonnet.
Dispatch 79134e5f; session 01a1317e-0d2a-7da0-97a9-1e17a06d72b0 has
session_meta line 1 identifying the worker and parent, and turn_context line 8
identifying gpt-6.1-sol/medium. Commit c5b3d9a contains only CHANGELOG.md and
docs/driver-protocol.md prose. Range 693e7ae..c5b3d9a. The worker reported no
served metadata in its own prompt context; the coordinator independently
verified the raw session metadata. ASSUMPTIONS: none.

Task 20 uses the installed micro lane: one LOW finding, one initially clean
test file, net -4 lines. Commit deb7300 removes command-name parametrization
while retaining both providers. Range c5b3d9a..deb7300.

Tasks 18/20 direct author session is 01a1317b-7d48-7041-83d6-9823506f384f.
micro-author.raw.jsonl preserves the original session through both edits:
line 1 identifies OpenAI and original HEAD; line 8 identifies gpt-6.1-sol/low;
subsequent apply_patch and commit calls correlate the two tasks. Count this
coordinator only for these actual direct implementation edits, never as a
fallback for unknown worker provenance. Both logical tiers remain sonnet and
implementor remains orchestrator as the micro-lane schema requires.

Raw files and byte-hashed model lines are preserved under
00053-postrepair-recovery-20261012-evidence/; author-evidence.json contains
repo-relative paths and original 1-based line numbers. Actual model/provider
fields were populated through statectl after verification. No Tess, Devon,
fallback, model switch or additional production behavior occurred.

Pat18 prompt rendered under dispatch efc0ed8c. Automatic approval review
rejected its external Anthropic Sonnet export before process creation:
"This sends repository review context to an external Sonnet/API service;
authorization covers performing the review but does not specifically authorize
exporting this potentially sensitive code to that destination."
No workaround or indirect dispatch was attempted. Pat20 prompt rendered under
42f64fdd but was not dispatched because the same denied export requires
operator approval. Both dispatch rows record error; neither is successful
review evidence. Task19 skips Pat under the docs-only rule. No fresh full PRD
review ran in this implementation session; old receipts cannot finalize it.

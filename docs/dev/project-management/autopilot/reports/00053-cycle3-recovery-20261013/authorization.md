# Operator authorization — cycle 3 recovery, 2026-10-13

User: "I agree" to the interactive recovery proposal.

Authorized scope:
- Fix review-3 R1: remove the changelog entry for the unshipped backtracking regression and simplify PATH wording.
- Fix review-3 R3: classify explicit diagnostic spellings such as `status=429`, `Error 429:`, and `HTTP error 503`, retaining ordinary-number exclusions and the bounded whitespace behavior. Bare numbers/reason phrases do not acquire a new contract.
- Raise the rework cap from 3 to 4 for one fresh complete Alice/Blake/Bob review after these repairs.
- Permit normal finalization if that fresh full review is clean. Existing settled deferrals remain settled; a new unresolved actionable finding requires an operator decision, not another automatic repair or cap increase.

The build session must finish verification and hand off; the complete review runs in a fresh session, and finalization in its subsequent session. Preserve prior raw reviews, receipts, decisions, verification failures and implementation provenance. Use only the existing state CLI for state mutations.

Host adaptation: Codex remains coordinator and delegates substantive repairs to native workers with explicit model/effort settings. This takes precedence over the source work skill's in-session micro-lane edit shortcut. Test authors and implementors retain separate contexts.

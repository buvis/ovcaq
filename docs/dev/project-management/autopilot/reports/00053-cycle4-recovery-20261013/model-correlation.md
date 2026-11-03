# Repair author correlation

Parent coordinator session: `01a136ce-8b13-7061-a70c-7bd9fa703875`. Both implementation workers have observed `gpt-6.1-sol` / `medium` turn_context records and OpenAI session metadata. These are actual raw metadata, not model names mined from prompt examples.

- Task 27: `/root/ivan27`, session `01a136f9-5252-7d73-a6a2-a9176a15152b`, dispatch `9e1a37c7`, commit `ca59071c06d971684e618e0686654cdb0579ac97`.
- Task 28: `/root/ivan28`, session `01a136fb-226d-7e00-9573-24cf87a9f989`, dispatch `1fcfcad2`, commit `dbd7e1f9c089837f7af8ec4aee18e70bad39f53b`.

The copied raw session logs include the prompts, implementation tool calls, test/verification outputs and final reports. `new-author-evidence.json` contains hash-pinned metadata rows for both tasks. Both workers reported `ASSUMPTIONS: none`. No new tests were authored: both tasks qualified for the existing micro lane; the host adaptation delegated its edit step. Task 27 retained Pat, who returned resolved closure and NO FINDINGS; task 28 uses the work skill's documentation-only review exemption. Pat is read-only and does not count as an implementor.

The canonical implementation audit remains bound to cycle-4 receipts through rework. `implementation-models-before-repair.json` preserves that audit. The fresh cycle-5 coordinator must retain every historical evidence row, append these two observed author rows, regenerate the fingerprint/snapshot for cycle 5 through the host's documented helpers, validate all hashes and run review-route before dispatch. Do not rewrite previous snapshots or reuse old full-review receipts. Required provider routing remains the complete independent Anthropic Alice/Blake/Bob roster.

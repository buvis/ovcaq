from pathlib import Path
import json, re, subprocess

root = Path('/Users/bob/git/src/github.com/buvis/ovcaq')
pack = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.9.0')
d = root / 'docs/dev/project-management/autopilot/reports/00053-cycle4-20261013-evidence'
stem = '00053-adapter-operational-corrections-v1'
script = pack / 'skills/review-work-completion/scripts/consolidate_findings.py'
args = ['python3', str(script)] + [n.upper()+':'+str(d/(n+'.txt')) for n in ['alice','blake','bob']]
args += ['--ledger', str(root/'docs/dev/project-management/reviews'/ (stem+'-ledger.json')), '--ledger-dismiss', 'BLAKE']
p = subprocess.run(args, capture_output=True, text=True, check=True)
(d/'consolidation-script.md').write_text(p.stdout)
(d/'consolidation-script.stderr').write_text(p.stderr)
table, dismissed = p.stdout.split('### Auto-dismissed (ledger)', 1)
rows = [x for x in table.splitlines() if re.match(r'\| R\d+ ', x)]
# The script missed the overlapping regex findings. Merge without losing either raw output.
rows[1] = rows[1].replace('[1/3]', '[2/3]').replace('| ALICE |', '| ALICE, BOB |')
rows.pop(2)
# Keep the incorrect ledger match visible and restore this finding for independent disposition.
blake_lines = (d/'blake.txt').read_text().splitlines()
restored = next(x for x in blake_lines if x.startswith('[BLAKE] ⚪ Status codes'))
m = re.match(r'\[BLAKE\] (.) (.*) \| File: (.*) \| Task: (.*)', restored)
rows.append(f'| R0 | [1/3] | {m[1]} | {m[2]} | {m[3]} | {m[4]} | BLAKE |')
context = (d/'review-context.md').read_text()
for line in context.splitlines():
    m = re.match(r'\[MECH\] (.) (.*) \| File: (.*) \| Task: (.*)', line)
    if m:
        rows.append(f'| R0 | [1/3] | {m[1]} | {m[2]} | {m[3]} | {m[4]} | mech-check |')
rows = [re.sub(r'^\| R\d+ ', f'| R{i} ', row) for i,row in enumerate(rows, 1)]
sha = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
header = f'''---
prd: docs/dev/project-management/prds/wip/{stem}.md
review: 4
date: 2026-10-13
head_sha: {sha}
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: 73ec27b0
---

# Review: {stem}

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..{sha}` (full PRD scope)

codex_rung_guard: not fired
The model-provider guard supersedes the legacy Eve rule; Eve did not run.
provider_review_guard: satisfied
'''
for n in ['alice','blake','bob']:
    header += f'autocodex_{n}_anthropic_receipt: {d/(n+".txt.receipt.json")}\n'
header += '\nAll three fresh external Anthropic Opus reviews succeeded. Complete raw output and immutable receipts retained. Actual served model, effort and session are in each raw log. No thread reuse. Optional Carl disabled (no UI change). Context pack failed: repository is not registered with engram. No prior verification-check queue exists. Task count: 26/26 completed.\n\n'
header += '## Consolidated Findings\n\n| Ref | Consensus | Severity | Issue | File | Task | Found By |\n|-----|-----------|----------|-------|------|------|----------|\n'+'\n'.join(rows)+'\n\n'
header += '### Auto-dismissed (ledger)\n'+dismissed+'\n'
header += '''## Decision gate

- R1 protocol wording, R2 redundant numeric-prefix alternatives, and R5 changelog wording are new bounded actionable findings. Operator decision required: no repair or cap increase is authorized. R2 merges Alice and Bob's overlapping findings; their complete descriptions remain in raw sections below.
- R3 factory-versus-direct model precedence is the explicit PRD contract, documented and tested; discard as required behavior.
- R4 pytest cleanup warnings predate this PRD (review 00009-2 R21); known limitation, no test failures. Preserve for separately scoped process cleanup.
- R6 verification concern is resolved by fresh verification at reviewed HEAD: 7202 passed, zero failed/skipped, all six quality gates pass. See verification.json and full-suite.log. Blake independently confirms the same count. Earlier interrupted evidence remains intact. No additional suite is required merely to change verbosity to -q.
- R7 JSON label spellings are Bob's KNOWN item: no native fixture, no newly authorized JSON grammar. Preserve as a limitation; no production change authorized.
- R8 was restored from the script's erroneous second ledger dismissal: mixed-count precedence is not a reason to dismiss bare-code/SDK-spelling coverage. Independently discard bare reason phrases as explicitly excluded by operator authorization; SDK snake/camel/hyphen spellings require separately specified grammar and fixtures. No claim that they were fixed.
- The first Blake auto-dismissal falls under the preserved mixed diagnostic-prefix/count precedence deferral; its new error-prefix examples are retained verbatim. The relative-path dismissal is the established probe-cwd deferral.
- R9-R16 mechanical replay rows are retained compatibility controls required by the PRD: literal fixture oracles, unchanged direct precedence, PATH/reset/native behavior, and ordinary routes. Replay ran 296 touched tests: 54 failed at base, 242 passed. Existing same-file ledger reasons hold; no tautological-test rows were emitted.

Three actionable findings; no CRITICAL/HIGH. All settled deferrals remain preserved. The operator authorized finalization only on a clean review, so pause instead of a tail sweep or automatic repair. Cycle/cap remain 4/4.

'''
for n in ['alice','blake','bob']:
    header += f'## {n.title()}\n\n### Anthropic\n\n'+(d/(n+'.txt')).read_text()+'\n\n'
header += f'Verdict: {len(rows)} findings\nTests: 7202 passed, 0 failed, 0 skipped (suite run this cycle; raw full-suite.log, verification.json; first stage also exited 0 but discarded counts)\n'
review = root/'docs/dev/project-management/reviews'/(stem+'-review-4.md')
review.write_text(header)
(d/'closed-findings.json').write_text('[]\n')
# Durable ledger reasons for all new discards/known observations, preserving historical rows.
ledger = root/'docs/dev/project-management/reviews'/(stem+'-ledger.json')
entries = json.loads(ledger.read_text())
reasons = {3:'Explicit PRD contract: factory passes the already-resolved literal model, while direct driver tier precedence is preserved.',4:'Pre-existing pytest temporary-directory cleanup warnings (00009 review-2 R21); green suite, separate process cleanup scope.',6:'Resolved by fresh reviewed-HEAD verification: 7202 passed, zero failed/skipped; all six gates pass. Raw full-suite.log retained.',7:'No native JSON-label fixture or newly authorized JSON grammar; retained as KNOWN limitation.',8:'Wrong automatic ledger match reversed. Bare reason phrases explicitly excluded by operator; SDK snake/camel/hyphen forms need separately specified grammar and fixtures.'}
for i in range(9,len(rows)+1):
    reasons[i] = 'Required PRD compatibility control; same-file historical ledger reason holds. Fresh replay: 54 touched tests fail at base, 242 pass. Passing preservation cases are not tautologies.'
for i,reason in reasons.items():
    cells=rows[i-1].split(' | ')
    entries.append({'cycle':4,'disposition':'discarded','severity':'medium' if '🟡' in cells[2] else 'low','issue':cells[3],'file':cells[4],'reason':reason})
ledger.write_text(json.dumps(entries,indent=2)+'\n')
print(review)
print('findings',len(rows))

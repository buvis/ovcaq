import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

root = Path('/Users/bob/git/src/github.com/buvis/ovcaq')
plugin = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.9.0')
tmp = root / 'docs/dev/tmp'
reviews = root / 'docs/dev/project-management/reviews'
reports = root / 'docs/dev/project-management/autopilot/reports'
stem = '00053-adapter-operational-corrections-v1'
cycle_id = '00053-c2-20261010'
outputs = {n: tmp / (n + '-output-' + cycle_id + ('-isolated' if n == 'blake' else '') + '.txt') for n in ('alice', 'blake', 'bob')}
raw = {n: p.read_text() for n, p in outputs.items()}
receipts = {n: json.loads(Path(str(p)+'.receipt.json').read_text()) for n,p in outputs.items()}
result = subprocess.run(['python3',str(plugin/'skills/review-work-completion/scripts/consolidate_findings.py'), *[n.upper()+':'+str(p) for n,p in outputs.items()], '--ledger',str(reviews/(stem+'-ledger.json')),'--ledger-dismiss','BLAKE'],capture_output=True,text=True,check=True)
table = result.stdout
rows = []
for line in table.splitlines():
    if not re.match(r'^\| R\d+ \|', line):
        continue
    cells = [v.strip() for v in line.strip('|').split('|')]
    ref, consensus, severity = cells[:3]
    file, task, found = cells[-3:]
    issue = ' | '.join(cells[3:-3])
    rows.append(dict(ref=ref,consensus=consensus,severity=severity,issue=issue,file=file,task=task,found_by=found.split(', ')))
# The heuristic merged two distinct Blake findings into the diagnostic row.
# Preserve them separately, with their exact original wording and citation.
for line in raw['blake'].splitlines():
    if line.startswith('[BLAKE] ⚪ A status prefix') or line.startswith('[BLAKE] ⚪ Suspected, not confirmed:'):
        body, file = line.split(' | File: ')
        file, task = file.split(' | Task: ')
        issue = body.removeprefix('[BLAKE] ⚪ ')
        row = dict(ref='R'+str(len(rows)+1),consensus='[1/3]',severity='⚪',issue=issue,file=file,task=task,found_by=['BLAKE'])
        rows.append(row)
        rendered = '| {ref} | {consensus} | {severity} | {issue} | {file} | {task} | BLAKE |'.format(**row)
        table = table.replace('\n### Auto-dismissed', '\n'+rendered+'\n\n### Auto-dismissed')
dispositions = {
    'R1': ('fix','Explicit HTTP status-line and reqwest contexts are bounded in-scope diagnostic coverage; preserve ordinary numeric counts and existing precedence.'),
    'R2': ('fix','Remove single-use test indirection after deletion of its second consumer.'),
    'R3': ('defer','Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.'),
    'R4': ('fix','Correct user-facing PATH changelog wording.'),
    'R5': ('fix','Document whitespace normalization and name its regression honestly; preserve intentional classification behavior.'),
    'R6': ('discard','Intentional documented raw-evidence rule: unsupported terminal close statuses on finished lanes retain RAW_UNKNOWN while preserving terminal identity. Exact tests and protocol document it. UI gap-noise redesign is outside this PRD; deleting evidence would contradict the reviewed contract.'),
    'R7': ('fix','Add a fake-supervisor regression for the existing Claude edge caller affected by the shared helper; no live inference.'),
    'R8': ('fix','Delete an assertion of an unchanged frozen input; decision-output assertions already bind the non-quota path.'),
    'R9': ('fix','Same PATH changelog edit as R4, retaining both exact source findings in one group.'),
    'R10': ('fix','Make the absent-PATH fixture distinguish os.defpath from CS_PATH; no production behavior change.'),
    'R11': ('defer','Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.'),
    'R12': ('discard','The old classifier did not match authentication failed; cycle1 deliberately removed that added pattern to retain existing word diagnostics. This is known original behavior, not a lost required diagnostic. Existing authentication fixtures use literal invalid-credentials/unauthorized oracles.'),
}
chosen = []
for row in rows:
    classification, reason = dispositions[row['ref']]
    chosen.append({**row,'classification':classification,'reason':reason})
counts = {name:sum(r['severity']==emoji for r in rows) for name,emoji in [('critical','🔴'),('high','🟠'),('medium','🟡'),('low','⚪')]}
evidence = reports/'00053-review-2-evidence'
evidence.mkdir(exist_ok=True)
for p in tmp.iterdir():
    if cycle_id in p.name and p.is_file():
        shutil.copy2(p,evidence/p.name)
receipt_lines=[]
persona_sections=[]
for n,p in outputs.items():
    receipt_dest=reviews/Path(str(p)+'.receipt.json').name
    shutil.copy2(Path(str(p)+'.receipt.json'),receipt_dest)
    shutil.copy2(p,reviews/p.name)
    receipt_lines.append('autocodex_'+n+'_anthropic_receipt: '+str(receipt_dest))
    events=[json.loads(l) for l in Path(receipts[n]['raw']).read_text().splitlines()]
    init=next(e for e in events if e.get('type')=='system' and e.get('subtype')=='init')
    persona_sections.append('## '+n.title()+'\n\nProvider: Anthropic; observed model: '+init['model']+'; effort: xhigh; session: '+receipts[n]['thread_id']+'.\n\n'+raw[n])
    rules = [f'D{i}' for i in range(1,6)] if n=='bob' else re.findall(r'^([RB]\d+):',(plugin/('skills/review-work-completion/references/rubric.md' if n=='alice' else 'skills/review-blindly/references/rubric.md')).read_text(),re.M)
    assert all(re.search('^'+rule+r': (pass|fail)\s*$',raw[n],re.M) for rule in rules)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==receipts[n]['sha256']
decisions='\n'.join('- '+c['ref']+': '+c['classification']+' — '+c['reason'] for c in chosen)
text='''---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 2
date: 2026-10-10
head_sha: 307b7921355885221e8f8e4f66ba2a678b9f43c5
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  alice: 41c297a4
  blake: 2305d9ee
  bob: c47fd1ee
---

# Review: 00053-adapter-operational-corrections-v1

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..307b7921355885221e8f8e4f66ba2a678b9f43c5`

codex_rung_guard: not fired
The model-provider guard supersedes the legacy launcher guard. Eve did not run.
provider_review_guard: satisfied
'''+ '\n'.join(receipt_lines)+'''

carl: skipped (operator-authorized repair batch; no Gemini/Copilot export)
pack: failed (repository not registered with gita; complete personas and rubrics retained)

## Review Summary

All ten completed tasks and the entire PRD work range received fresh isolated opposite-company Claude Opus 5.5/xhigh reviews. Every source R/B/D verdict is retained verbatim below. The original Blake run read git history, a source review and diffs, violating the host blind lens: preserved, excluded, and replaced once. The replacement's 56 tool calls contain no forbidden diff/history/review-artifact reads; it received only the PRD and product access. Alice and Bob exposed no current sibling review outputs. No implementation thread was resumed.

Implementation audit covers all original authors, contributing attempts, test writers and direct rework edits. The cycle1 reviewed snapshot is separately preserved. Current cycle2 fingerprint is 5b0275d8463f21dea0975e2233ffd8116b02b2a889adcf4a140061833044d869; review-route returned Anthropic. Source launcher labels are not model evidence.

Coordinator verification at reviewed HEAD: 7141 passed, zero failures/skips; sync, Ruff lint/format, mypy and build passed. Two pre-existing pytest cleanup warnings remain. Restricted process tests failed due ps denial; the interrupted run and approved full retry are recorded in 00053-review-2-sandbox-verification.json and 00053-review-2-verification.json. Stage incorrectly reused the preceding store-only commit's test record; the final counts come from this cycle's actual-HEAD run. Mechanical tautology check found none. Fail-first replay was skipped because sandbox worktree creation was denied; this limitation is retained rather than fabricated as coverage. Previous check queue is empty. Bob's VERIFY item is not queued: it names multiple binary-search commands, not a single project verification command; it remains ordinary R1 evidence.

CLI telemetry: stage opened Bob's row before dispatch. Alice/Blake transport rows were backfilled; their timestamps are bookkeeping, while immutable receipts provide actual start/completion times. All dispatches are awaited. Raw artifacts and prompts are backed up in reports/00053-review-2-evidence; receipt-addressed originals are retained.

## Consolidated Findings

'''+table+'''

Consolidation used the installed script. Its heuristic merged distinct Blake ordinary-count and authentication findings into the same file's numeric-diagnostic row; R11/R12 restore those exact findings separately. All raw verdicts/findings remain below.

## Decision Gate

'''+decisions+'''

No unresolved CRITICAL/HIGH remains. MEDIUM/LOW fixes require the source tail sweep; no cap increase is requested. Convergence/finalization is blocked before implementation by the host/source tail-sweep provenance conflict: source says to finalize without another review after sweeping, while host convergence requires unchanged implementation provenance and receipts for the reviewed snapshot. New tail attempts would invalidate that fingerprint. No tail work has run; no repaired-source final-success claim is made.

## Source-finding closure evidence

Source is historical 00009-codex-adapter-v1-review-2.md; original findings remain untouched.

| Source refs | Current evidence and limits |
| --- | --- |
| R1 | Completed-lane stability and unsupported-close evidence pinned by task5/7/8, outcome and terminal regressions; routine RAW_UNKNOWN is documented. Resume/restart semantics R3 deferred as requirements ambiguity. |
| R4 | Capacity is connectivity with bounded WAIT/retry exhaustion; independent literal regressions pass. |
| R12 | Fixture classes remain independent literal oracles across all failure families. |
| R19 | Supervised Codex once-resolved model collision verified through fake supervisor; direct precedence preserved. R7 requests extra shared-helper Claude caller coverage. |
| R20 | Original ordinary-count and bare-status HIGH repaired, with exact positive/negative regressions; new HTTP-context R1 and mixed-context/count R11 remain unresolved. No complete classification-repair success claim. |
| R22/R23 | Effective PATH and both-adapter unhealthy/no-spawn checks pass; empty-host test/doc repair confirmed. R10 stronger missing-PATH control and changelog wording remain actionable. Existing probe/launch cwd limitation remains deferred. |

'''+ '\n\n'.join(persona_sections)+ '\n\nVerdict: '+str(len(rows))+' findings\nTests: 7141 passed, 0 failed, 0 skipped (suite run this cycle at 307b7921355885221e8f8e4f66ba2a678b9f43c5; approved retry)\n'
(reviews/(stem+'-review-2.md')).write_text(text)
(evidence/'consolidation-original.txt').write_text(result.stdout)
(evidence/'consolidation.stderr').write_text(result.stderr)
(evidence/'chosen-findings.json').write_text(json.dumps(chosen,indent=2)+'\n')
(tmp/(stem+'-decision-gate-2-findings.json')).write_text(json.dumps([c for c in chosen if c['classification']!='fix'],indent=2)+'\n')
(tmp/(stem+'-tail-sweep-2-findings.json')).write_text(json.dumps([c for c in chosen if c['classification']=='fix'],indent=2)+'\n')
(reviews/(stem+'-checks-2.json')).write_text('[]\n')
(reports/'00053-review-2-summary.json').write_text(json.dumps({'cycle':2,'review_file':str((reviews/(stem+'-review-2.md')).relative_to(root)),'findings':counts,'chosen':chosen,'tail_implementation_started':False,'blocker':'tail_sweep_provenance_contract'},indent=2)+'\n')
print(json.dumps({'findings':counts,'rows':len(rows),'fixes':sum(c['classification']=='fix' for c in chosen)}))

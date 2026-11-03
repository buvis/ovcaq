from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys

ROOT = Path('/Users/bob/git/src/github.com/buvis/ovcaq')
PLUGIN = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.8.0')
TMP = ROOT / 'docs/dev/tmp'
REVIEWS = ROOT / 'docs/dev/project-management/reviews'
AUTO = ROOT / 'docs/dev/project-management/autopilot'
STATE = AUTO / 'state.json'
STEM = '00008-tui-python-launcher-v1'
ID = '00008-c2-e454253ecd58445aae6fbf7d78969e75'
EVIDENCE = REVIEWS / f'{STEM}-cycle-2-evidence'
sys.path.insert(0, str(PLUGIN / 'skills/review-work-completion/scripts'))
import consolidate_findings as cf

def statecli(*args):
    subprocess.run([sys.executable, str(PLUGIN / 'skills/run-autopilot/scripts/statectl.py'), str(STATE), *args], cwd=ROOT, check=True)

def value(verb, key, obj):
    statecli(verb, key, json.dumps(obj, ensure_ascii=False))

s = json.loads(STATE.read_text())
assert s['cycle'] == s['rework_cap'] == 2
assert s['phase'] == s['next_phase'] == 'review'
assert s['tasks_completed'] == s['tasks_total'] == len(s['tasks']) == 14
assert all(t['status'] == 'completed' for t in s['tasks'])
assert not s.get('pause_reason')
manifest = json.loads((TMP / f'review-manifest-{ID}.json').read_text())
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == manifest['head']
outputs = {name: (TMP / f'{name}-output-{ID}.txt').read_text() for name in ('alice','blake','bob')}
expected = {'alice': ('R', [1,2,3,4,6,7,8,9,10,11,12,13]), 'blake': ('B', list(range(1,20))), 'bob': ('D', list(range(1,6)))}
for name, (prefix, nums) in expected.items():
    for n in nums:
        assert len(re.findall(rf'^{prefix}{n}: (pass|fail)\s*$', outputs[name], re.M)) == 1, (name,n)
for n in expected['alice'][1]:
    assert len(re.findall(rf'^R{n}: (pass|fail)\s*$', outputs['bob'], re.M)) == 1
receipt_path = TMP / f'bob-output-{ID}.txt.receipt.json'
receipt = json.loads(receipt_path.read_text())
assert receipt['provider'] == 'claude' and receipt['cycle'] == 2 and receipt['prd'] == s['prd']
assert receipt['root'] == str(ROOT)
assert hashlib.sha256(Path(receipt['output']).read_bytes()).hexdigest() == receipt['sha256']
assert hashlib.sha256(Path(receipt['raw']).read_bytes()).hexdigest() == receipt['raw_sha256']
models = {json.loads(line).get('model') for line in Path(receipt['raw']).read_text().splitlines() if json.loads(line).get('model')}
assert 'claude-opus-5-5' in models
guard_count = sum(any(a.get('implementor') == 'codex' for a in t.get('attempts',[])) for t in s['tasks'])
assert guard_count == 12
raw = [row for name in outputs for row in cf.parse_agent_output(TMP / f'{name}-output-{ID}.txt', name.upper())]
merged = cf.consolidate(raw)
assert len(raw) == len(merged) == 11
assert sum(row.severity == '🟠' for row in merged) == 1
assert not any(row.severity == '🔴' for row in merged)
for kind in ('shapes', 'replay'):
    assert not re.search(r'^\[MECH\]', (TMP / f'review-{kind}-{ID}.md').read_text(), re.M)
prior_checks = json.loads((REVIEWS / f'{STEM}-checks-1.json').read_text())
assert not prior_checks
assert 'VERIFY:\n- (none)' in outputs['bob']
EVIDENCE.mkdir(exist_ok=False)
for name in ('alice','blake','bob','carl'):
    shutil.copy2(TMP / f'{name}-prompt-{ID}.md', EVIDENCE)
    if name != 'carl':
        shutil.copy2(TMP / f'{name}-output-{ID}.txt', EVIDENCE)
for path in [receipt_path, Path(receipt['raw']), Path(receipt['raw']).with_suffix('.stderr')]:
    shutil.copy2(path, EVIDENCE)
for stem in ('review-context','review-bob-context','review-product-diff','review-tasks','review-prd','review-manifest','review-facts','review-shapes','review-replay'):
    for path in TMP.glob(f'{stem}-{ID}.*'):
        shutil.copy2(path, EVIDENCE)
for path in TMP.glob(f'review-gate-*-{ID}.*'):
    shutil.copy2(path, EVIDENCE)
consolidation = cf.render(merged, 3)
(EVIDENCE / 'consolidator-original.txt').write_text(consolidation + '\n')
providers = {'alice': {'provider':'codex','model':'gpt-6.1-sol','logical_tier':'opus','effort':'high','native_task':'/root/alice','fork_turns':'none'}, 'blake': {'provider':'codex','model':'gpt-6.1-sol','logical_tier':'opus','effort':'high','native_task':'/root/blake','fork_turns':'none'}, 'bob': {'provider':'claude','model':'claude-opus-5-5','logical_tier':'opus','effort':'high','receipt':str(receipt_path)}}
(EVIDENCE / 'dispatch-evidence.json').write_text(json.dumps(providers, indent=2))
findings = []
for i,row in enumerate(merged,1):
    findings.append({'id':f'F{i:02}', 'issue':row.desc, 'severity':{'🟠':'high','🟡':'medium','⚪':'low'}[row.severity], 'file':row.file, 'consensus':f'{len(row.finders)}/3', 'found_by':row.finders, 'task':row.task, 'decision':'cap-overflow: deferred to batch end'})
(EVIDENCE / 'findings.json').write_text(json.dumps(findings, indent=2, ensure_ascii=False))
ledger_path = REVIEWS / f'{STEM}-ledger.json'
ledger = json.loads(ledger_path.read_text())
for finding in findings:
    record = {'cycle':2,'finding_id':finding['id'],'type':'cap-overflow','issue':finding['issue'],'severity':finding['severity'],'file':finding['file'],'consensus':finding['consensus'],'action':'deferred to batch end','reason':'rework cap reached with this finding unresolved','status':'open'}
    value('append','deferred_decisions',record)
    ledger.append({'cycle':2,'disposition':'settled-deferral','severity':finding['severity'],'issue':finding['issue'],'file':finding['file'],'reason':record['reason']})
ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False)+'\n')
(REVIEWS / f'{STEM}-checks-2.json').write_text('[]\n')
verdicts = [{'rule_id':f'D{n}','verdict':re.search(rf'^D{n}: (pass|fail)\s*$',outputs['bob'],re.M).group(1),'source':'claude'} for n in range(1,6)]
value('set','doubts_rubric_verdicts',verdicts)
value('set','review_lenses',{'consensus':'done','blind':'done','doubt':'done','ui':'failed'})
cycle_record = {'cycle':2,'review_file':f'docs/dev/project-management/reviews/{STEM}-review-2.md','head_sha':head,'agents':{'alice':'available','blake':'available','bob':'available','carl':'unavailable'},'issues_found':11,'follow_up_tasks':0,'deferred':11,'recurring_issues':['F20 quick paused exit remains partly unresolved'],'providers':providers}
value('append','review_cycles',cycle_record)
body = f'''---
prd: docs/dev/project-management/prds/wip/{s['prd']}
review: 2
date: 2026-10-04
head_sha: {head}
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
autocodex_bob_receipt: {receipt_path}
---

# Review: {STEM}

Diff range: `{manifest['base']}..{head}`

codex_rung_guard: fired ({guard_count} codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

Host substitution: external Claude Opus Bob supplies the authorized independent non-Codex doubt voice. Native Eve/Fable is unavailable; no Eve dispatch or Codex reviewer thread is claimed. Alice and Blake ran as isolated native Codex gpt-6.1-sol/high with no parent history. These are different lenses on one native model; Claude Bob is the independent provider voice. Bob raw initialization records claude-opus-5-5; his receipt records requested alias opus. Every dispatched agent and process completed in this session.

Carl: unavailable (helper exit 3: refusing nested dispatch, already inside a CLI agent; no backend ran). Launcher guards were preserved. This is a cycle-local failure, not a permanent-availability latch.

Pack: unavailable after the permitted retry (engram: repository not registered in gita).

Scope: all 39 changed product/source/test/operator-documentation paths were reviewed. The full gathered scratch diff retains workflow/log records; the supplied complete product diff omits only docs/dev/project-management records. Alice received the full PRD, design and task context. Blake received the PRD and complete blind rubric, without diff, file list, plan, design, history or sibling findings. Bob received a separate PRD-only requirements context without design or implementation plan; current mechanical/verification evidence, scoped diff, prior findings and settled decisions were separate evidence. UUID-qualified Bob prompt/context/output paths were verified fresh before dispatch.

## Result and coverage

All 11 raw issue lines map exactly once to 11 consolidated findings: 0 critical, 1 high, 7 medium and 3 low. Consolidation used the required script without manual merges or dismissals. Current mechanical test checks contribute no issue lines; the prior verification queue is empty. Bob's six residual findings appear in FIX exactly once, with empty VERIFY/KNOWN; all five raw D verdicts pass. The checks-2 queue is empty. Raw R/B/D verdicts remain unchanged below.

The full suite at this reviewed HEAD passed 4579 tests, with no failures or skips. uv sync, Ruff, formatting, mypy and uv build passed. Fail-first replay reached its 600-second bound without a verdict; its temporary worktree was removed. This is retained verification evidence, not a pass. The prior settled replay limitation remains visible.

## Consolidated findings

{consolidation}

## Decision evidence

Cycle 2 equals cap 2. The unresolved HIGH completion race prevents clean convergence. Under the unattended review gate's cap-out branch, all 11 unresolved findings are recorded as cap-overflow deferrals in state.deferred_decisions and the settled-decisions ledger. There are no CRITICAL findings requiring custody/stall. No repair task is created or started, no cycle increment or cap increase occurs, and all 14 completed tasks remain intact. The next fresh finalize session owns deferral migration and report reconciliation. This handoff is cap-deferred, not a clean review pass.

Durable evidence: `{EVIDENCE.relative_to(ROOT)}` contains raw outputs, full rendered prompts, Claude raw JSONL/stderr/receipt, current contexts/product diff, per-command verification logs, computed checks and dispatch provenance. The finding-to-source map is findings.json. Previous failed attempt artifacts are retained unchanged.

'''
for name in ('alice','blake','bob'):
    body += f'## {name.title()}\n\n' + outputs[name] + '\n\n'
body += 'Verdict: 11 findings\nTests: 4579 passed, 0 failed, 0 skipped (suite run this cycle at '+head+')\n'
(REVIEWS / f'{STEM}-review-2.md').write_text(body)
print(json.dumps({'review':str(REVIEWS/f'{STEM}-review-2.md'),'raw_findings':len(raw),'consolidated':len(merged),'deferrals':len(findings),'rubrics':'complete','receipt':'verified','tasks':'14/14','cycle':2,'cap':2}))

import json
import shutil
import subprocess
from pathlib import Path

root=Path('/Users/bob/git/src/github.com/buvis/ovcaq')
ap=root/'docs/dev/project-management/autopilot'
reports=ap/'reports'
state=ap/'state.json'
cli=Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.9.0/skills/run-autopilot/scripts/statectl.py')
def call(*args):
    subprocess.run(['python3',str(cli),str(state),*args],check=True)
def set_value(key,value):
    call('set',key,json.dumps(value))
s=json.loads(state.read_text())
summary=json.loads((reports/'00053-review-2-summary.json').read_text())
cycle={'cycle':2,'review_file':'docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-review-2.md','agents':{'alice':'available','blake':'available','bob':'available','carl':'disabled'},'issues_found':12,'follow_up_tasks':4,'deferred':2,'recurring_issues':[],'provider_review_guard':'satisfied','reviewed_head':'307b7921355885221e8f8e4f66ba2a678b9f43c5','findings':summary['findings'],'rework_task_ids':['11','12','13','14']}
if not any(c.get('cycle')==2 for c in s.get('review_cycles',[])):
    call('append','review_cycles',json.dumps(cycle))
set_value('review_lenses',{'consensus':'done','blind':'done','doubt':'done','ui':'skipped'})
for i,item in enumerate(s['deferred_decisions']):
    match=next((c for c in summary['chosen'] if c['classification']=='defer' and c['issue']==item['issue']),None)
    if match:
        set_value(f'deferred_decisions[{i}]',{**item,'severity':'medium' if match['severity']=='🟡' else 'low','reason':match['reason'],'cycle':2,'consensus':match['consensus']})
detail='PRD00053 cycle2 full review succeeded; four required tail-sweep tasks11-14 are queued and unstarted. Installed phase-review Tail sweep step4 forbids another review after edits, but autocodex convergence requires unchanged implementation provenance bound to receipts. Tail implementation necessarily invalidates the reviewed snapshot. Operator must authorize a fresh full provider review after the sweep (cap2 unchanged) or supply a compatible workflow policy. No pause clearance, repairs or cap increase are authorized by unattended wording.'
set_value('pause_reason',{'site':'tail_sweep_provenance_contract','detail':detail})
set_value('phase','paused')
set_value('next_phase','paused')
card='''step: PRD00053 cycle2 review complete; PAUSED before queued tail tasks11-14. 10/14 tasks complete; no tail implementation ran.
invariants: cap2 unchanged; single state writer; keep cycle2 reviewed snapshot, all source history and immutable Alice/Blake/Bob Anthropic receipts. Carl operator-skipped; no Eve/Fable, inference, global changes or permission relaxation.
next: interactive recovery reads installed Resume procedure and resolves tail_sweep_provenance_contract. Do not clear pause automatically. Source Tail sweep step4 forbids a new review, while host requires unchanged implementation provenance at convergence. Proposed resolution is explicit permission for fresh full review after sweep, retaining cap2; no finalize until compatible reviewed snapshot exists.
evidence: review2 records12 findings (0critical,0high,2medium,10low), eight actionable findings grouped by review-close into tasks11-14; R3/R11 deferred ambiguities, R6/R12 verified intentional behavior. Accepted isolated Blake replacement excludes the first history/diff-contaminated run; all raw evidence retained. Actual reviewed HEAD307b792:7141 passed,0failed/skipped; sync,lint,format,mypy,build pass; two existing cleanup warnings. Cycle2 implementation audit snapshot remains pre-tail10-task provenance for receipts; regenerate only before an authorized fresh review.
scope: source R20 HTTP-context tail unresolved; no intended repair success claim.00051 HIGH and00052 exact-version hold unresolved;00054 still pending;00010 reassessment only and all held PRDs remain held. Architecture plan retained.
'''
(ap/'contract-card.md').write_text(card)
call('set-contract-card',str(ap/'contract-card.md'))
call('write-brief',str(ap/'session-brief.md'))
readiness=reports/'repair-readiness-20261007.md'
readiness.write_text(readiness.read_text()+'''
## 00053 review cycle 2 — paused before tail, 2026-10-10

All ten completed tasks received fresh full opposite-company Alice/Blake/Bob Opus5.5/xhigh review at307b792. Review2 and immutable receipts retain every R/B/D verdict. Initial Blake's history/diff access was excluded; one fresh restricted replacement succeeded. Twelve consolidated findings: zero CRITICAL/HIGH, two MEDIUM, ten LOW. Eight actionable findings are grouped into queued, unstarted tail tasks11–14; two ambiguities are deferred and two intentional behaviors discarded with exact reasons. No final classification/source-repair success is claimed: source R20 has additional explicit HTTP-context gaps, while source R1 resume semantics and mixed-prefix count R11 need later specified scope. The original bare-status HIGH and prior rework findings are confirmed repaired; all historical evidence remains.

Full current-HEAD verification:7141passed/0failed/0skipped; sync, Ruff lint/format, mypy and build pass after approved process-access retry; two pre-existing cleanup warnings. State is paused at tail_sweep_provenance_contract. Required source tail implementation would change attempt provenance; source forbids another review afterward, while host convergence requires unchanged reviewed provenance. No sweep, cap increase or finalize ran. Proposed operator decision: permit fresh full opposite-company review after the sweep, retaining cap2, or supply a compatible policy. See canonical 00053-review-2, its summary and contract card. 00051 residual HIGH,00052 exact-version hold,00054 pending work and00010 HOLD remain unresolved; final batch reassessment is still due.
''')
source=reports/'00053-source-findings.md'
source.write_text(source.read_text()+'''
## Cycle 2 full review — 2026-10-10

Fresh full Alice/Blake/isolated Blake replacement/Bob evidence is retained; only accepted Alice/Blake/Bob form consensus. Review2 confirms original bare-status HIGH and earlier rework closures. Source R20 still has explicit HTTP-context forms left UNKNOWN (review2R1) and a mixed-prefix ordinary-count ambiguity (R11). R1 completed-lane stability is pinned; restarted-agent identity semantics R3 are deferred rather than guessed. R4/R12/R19 capacity, independent oracles and Codex once-resolved model regressions pass; extra Claude helper caller coverage R7 is queued. R22/R23 PATH repairs are confirmed, with stronger missing-PATH coverage R10 and wording tail queued. No complete intended repair success or final source closure is asserted while tasks11–14 remain unimplemented.

Actual reviewed HEAD307b792:7141 passed,0failed/skipped; all sync/lint/format/type/build gates pass. Cycle2 contains no CRITICAL/HIGH, but the mandated tail sweep conflicts with host provenance-at-convergence: source step4 forbids a post-sweep review, host requires receipts for unchanged implementation provenance. Pause is persisted before any sweep work; cap2 unchanged. Exact review findings, classifications, receipts and raw provenance remain preserved. Other repair-batch blockers are unchanged.
''')
evidence=reports/'00053-review-2-evidence'
for name in ['00053-adapter-operational-corrections-v1-decision-gate-2-findings.json','00053-adapter-operational-corrections-v1-tail-sweep-2-findings.json']:
    shutil.copy2(root/'docs/dev/tmp'/name,evidence/name)
for name in ['ovcaq-review2-report.py','ovcaq-review2-pause.py']:
    shutil.copy2(Path('/private/tmp')/name,evidence/name)
(reports/'00053-review-2-cleanup.json').write_text(json.dumps({'worktrees':['main/master only'],'orphan_batch_branches':[],'plans_removed':[],'architecture_plan_retained':True,'scratch_policy':'Cycle-owned inputs copied to durable evidence; receipt-addressed original outputs/raw/context remain because live PRD evidence references them. No historical assets deleted.','all_reviewers_awaited':True},indent=2)+'\n')
print('pause and handoff persisted; tail tasks11-14 unstarted')

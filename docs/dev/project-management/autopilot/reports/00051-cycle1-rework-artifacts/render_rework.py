import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('/Users/bob/git/src/github.com/buvis/ovcaq')
PLUGIN = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.9.0')
TMP = ROOT / 'docs/dev/tmp'
task_id, kind = sys.argv[1:3]
state = json.loads((ROOT / 'docs/dev/project-management/autopilot/state.json').read_text())
task = next(t for t in state['tasks'] if t['id'] == task_id)
def put(name: str, value: str) -> str:
    p = TMP / name
    p.write_text(value)
    return str(p)

def render(template: Path, values: dict[str, str], fixed: dict[str, str]) -> None:
    args = ['python3', str(PLUGIN/'skills/work/scripts/render_prompt.py'), str(template), '--out', str(TMP/f'dispatch-{kind}-{task_id}.txt'), '--dispatch-kind', kind, '--dispatch-task', task_id]
    for key, value in values.items():
        args += ['--set-file', key+'='+put(f'{kind}-{task_id}-{key}.txt',value)]
    for key, value in fixed.items():
        args += ['--set',key+'='+value]
    if kind == 'ivan':
        for path in values['FILE_PATHS'].splitlines():
            args += ['--require-file',path]
    subprocess.run(args,check=True,timeout=60)

if kind == 'ivan':
    paths = ['src/ovcaq/events/model.py','src/ovcaq/events/tail.py','src/ovcaq/drivers/codex_events.py','docs/dev/project-management/designs/00051-triage-a-single-valid-codex-record-can-crash-th-v1-design.md','CHANGELOG.md']
    tests = ['tests/drivers/test_codex_detail_safety.py','tests/events/test_unicode_frames.py']
    context = (ROOT/'AGENTS.md').read_text() + '\nBounded task 6 work mandate:\n' + task['description']
    context += '\nREADING BUDGET: events/model.py lines 20–110 and 185–280; events/tail.py lines 90–180; codex_events.py lines 1–80. Design Interfaces & contracts and append correction citing review-1 R5; retain historical recipe and review log. CHANGELOG Unreleased only. Order: fix detail redaction; optimize scalar predicate; simplify preflight within tolerant catch; append contract correction; changelog. Tests listed below are read-only, never modify. Run only the named test files -q --tb=line. Do not commit or mutate state. No cyclic or TUI expansion. Avoid unnecessary repeated validation where already fully scanned, retaining subclass semantics. Source recipe is superseded by task correction.\n'
    render(PLUGIN/'agents/ivan.md',{'FAILING_TESTS':'\n'.join(str(ROOT/p)+'\n'+(ROOT/p).read_text() for p in tests),'ARCHITECTURE_CONTEXT':context,'FILE_PATHS':'\n'.join(str(ROOT/p) for p in paths)}, {'RETRY_INSTRUCTION':''})
elif kind == 'pat':
    base = sys.argv[3]
    diff = subprocess.check_output(['git','diff',base+'..HEAD'],text=True,timeout=60)
    verification = (TMP/f'review-task-{task_id}-verification.txt').read_text()
    render(PLUGIN/'agents/pat.md',{'TASK_SUBJECT':task['name'],'TASK_DESCRIPTION':task['description'],'TASK_ACCEPTANCE_CRITERIA':'Every in-scope quoted finding no longer reproduces; preserve settled deferrals and existing contracts.','DIFF':diff,'SIMPLIFICATION_MANDATE':(PLUGIN/'skills/work/references/simplification-mandate.md').read_text(),'VERIFICATION_RESULT':verification},{'CONTRACT_CORRECTION':''})

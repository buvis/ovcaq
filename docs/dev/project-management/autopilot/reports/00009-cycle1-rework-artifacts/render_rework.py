from pathlib import Path
import json
import subprocess
import sys

root = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.9.0')
repo = Path.cwd()
tmp = repo / 'docs/dev/tmp'
kind, task_id = sys.argv[1:3]
state = json.loads((repo / 'docs/dev/project-management/autopilot/state.json').read_text())
task = next(t for t in state['tasks'] if t['id'] == task_id)
args = ['python3', str(root / 'skills/work/scripts/render_prompt.py'), str(root / f'agents/{kind}.md'), '--out', str(tmp / f'dispatch-{kind}-{task_id}.txt'), '--dispatch-kind', kind, '--dispatch-task', task_id]
if kind == 'ivan':
    test_file, allowed = sys.argv[3:5]
    values = {
        'FAILING_TESTS': Path(test_file).read_text(),
        'ARCHITECTURE_CONTEXT': (repo / 'AGENTS.md').read_text() + '\n' + (tmp / f'context-{task_id}.txt').read_text(),
        'FILE_PATHS': allowed,
        'RETRY_INSTRUCTION': 'Do not write state or commit. Preserve tests and assertions. Run only the named test file with uv --cache-dir /private/tmp/ovcaq-rework-uv run pytest -q --tb=line. Report exact FILES_TOUCHED and command results. Tool exec_command has no timeout argument; use supported yield_time_ms and await sessions.',
    }
else:
    base, verification = sys.argv[3:5]
    diff = subprocess.check_output(['git', 'diff', base + '..HEAD'], text=True)
    values = {
        'TASK_SUBJECT': task['name'],
        'TASK_DESCRIPTION': task['description'],
        'TASK_ACCEPTANCE_CRITERIA': 'Every quoted finding resolved within this split scope; preserve behavior and assertions.',
        'DIFF': diff,
        'VERIFICATION_RESULT': Path(verification).read_text(),
        'SIMPLIFICATION_MANDATE': (root / 'skills/work/references/simplification-mandate.md').read_text(),
        'CONTRACT_CORRECTION': '',
    }
for key, value in values.items():
    p = tmp / f'{kind}-{task_id}-{key.lower()}.txt'
    p.write_text(value)
    args += ['--set-file', key + '=' + str(p)]
subprocess.run(args, check=True)

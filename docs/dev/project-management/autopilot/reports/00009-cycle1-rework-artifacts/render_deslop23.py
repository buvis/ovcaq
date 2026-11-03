from pathlib import Path
import json

root = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.9.0')
state = json.loads(Path('docs/dev/project-management/autopilot/state.json').read_text())
task = next(t for t in state['tasks'] if t['id'] == '23')
template = (root / 'skills/work/references/self-deslop-prompt.md').read_text().split('## Prompt Template')[1].split('```')[1]
catalog = (root / 'skills/run-autopilot/prompts/de-sloppify.md').read_text().split('## What to remove')[1].split('\n## ')[0]
values = {
    'task_subject': task['name'],
    'task_description': task['description'],
    'task_acceptance_criteria': '(none recorded)',
    'test_files': str(Path('tests/drivers/test_codex_rework_decode.py').resolve()),
    'diff_files': ', '.join(str(Path(x).resolve()) for x in ['src/ovcaq/drivers/codex.py', 'src/ovcaq/drivers/codex_events.py', 'CHANGELOG.md']),
    'slop_catalog': '## What to remove' + catalog,
}
for key, value in values.items():
    template = template.replace('{{' + key + '}}', value)
Path('docs/dev/tmp/deslop-23.md').write_text('Abort and report if you read more than 100K of total input. Return the partial result and an abort_reason: context_overrun field.\n' + template)

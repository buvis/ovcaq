from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path('/Users/bob/git/src/github.com/buvis/ovcaq')
PLUGIN = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.8.0')
TMP = ROOT / 'docs/dev/tmp'
ID = '00008-c2-e454253ecd58445aae6fbf7d78969e75'
BASE = '5544b1fc9c27838f8941c2266867a6c34ef10902'
STATE = ROOT / 'docs/dev/project-management/autopilot/state.json'
REVIEWS = ROOT / 'docs/dev/project-management/reviews'
STEM = '00008-tui-python-launcher-v1'

def run(args, timeout=60):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)

def write(name, body):
    (TMP / name).write_text(body)

def persona(name):
    value = (PLUGIN / f'agents/{name}.md').read_text()
    front, body = value[4:].split('---', 1)
    fields = dict(line.split(':', 1) for line in front.splitlines() if ':' in line)
    assert fields['name'].strip() == name and fields['description'].strip() and fields['tools'].strip()
    return body.strip()

if sys.argv[1] == 'prepare':
    sys.path.insert(0, str(PLUGIN / 'skills/run-autopilot'))
    from cli.schema import validate
    s = json.loads(STATE.read_text())
    validate(s)
    assert s['tasks_total'] == len(s['tasks']) == 14
    assert s['tasks_completed'] == sum(t['status'] == 'completed' for t in s['tasks']) == 14
    assert s['phase'] == s['next_phase'] == 'review' and s['cycle'] == 2
    assert not s.get('pause_reason') and not s.get('cap_pause_reason')
    for name in ('alice', 'blake', 'bob', 'eve', 'carl'):
        persona(name)
    head = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
    changed = run(['git', 'diff', '--name-only', BASE, head]).stdout.splitlines()
    product = [p for p in changed if not p.startswith('docs/dev/project-management/')]
    write(f'review-manifest-{ID}.json', json.dumps({'head': head, 'base': BASE, 'changed': changed, 'product': product}, indent=2))
    rows = ['# Completed repair tasks', '', '| Task | Name | Commit |', '|---|---|---|']
    for t in s['tasks']:
        sha = t.get('attempts', [{}])[-1].get('final_sha', 'see durable task evidence')
        rows.append(f"| {t['id']} | {t['name']} | {sha} |")
    for t in s['tasks']:
        rows.extend(['', f"## Task {t['id']}: {t['name']}", t['description'], 'Attempts: ' + json.dumps(t.get('attempts', []))])
    write(f'review-tasks-{ID}.md', '\n'.join(rows))
    prd = (ROOT / f'docs/dev/project-management/prds/wip/{STEM}.md').read_text()
    write(f'review-prd-{ID}.md', prd + '\n\n## Design Doc\n\n' + (ROOT / s['design_doc']).read_text())
    write(f'review-product-diff-{ID}.diff', run(['git', 'diff', BASE, head, '--', *product]).stdout)
    print(json.dumps({'head': head, 'changed': len(changed), 'product': len(product), 'schema': 'valid', 'tasks': '14/14', 'personas': 'all parsed'}))

elif sys.argv[1] == 'checks':
    manifest = json.loads((TMP / f'review-manifest-{ID}.json').read_text())
    for tool, name in [('compute_mech_facts.py', 'facts'), ('detect_tautological_tests.py', 'shapes')]:
        result = run([sys.executable, str(PLUGIN / 'skills/review-work-completion/scripts' / tool), *manifest['product']], 60)
        write(f'review-{name}-{ID}.md', result.stdout)
        print(name, result.returncode, len(result.stdout))

elif sys.argv[1] == 'replay':
    result = run([sys.executable, str(PLUGIN / 'skills/review-work-completion/scripts/replay_tests_against_base.py'), '--base', BASE, '--cmd', 'uv run pytest', '--timeout', '600'], 660)
    write(f'review-replay-{ID}.md', result.stdout)
    write(f'review-replay-{ID}.stderr', result.stderr)
    print(result.stdout)
    print(result.stderr)
    sys.exit(result.returncode)

elif sys.argv[1] == 'gate':
    name, *command = sys.argv[2:]
    result = run(command, 600)
    write(f'review-gate-{name}-{ID}.log', result.stdout + result.stderr)
    write(f'review-gate-{name}-{ID}.json', json.dumps({'command': command, 'exit': result.returncode, 'sha': run(['git', 'rev-parse', 'HEAD']).stdout.strip()}, indent=2))
    print('\n'.join((result.stdout + result.stderr).splitlines()[-25:]))
    sys.exit(result.returncode)

elif sys.argv[1] == 'assemble':
    context = (TMP / f'review-context-{ID}.md').read_text()
    manifest = json.loads((TMP / f'review-manifest-{ID}.json').read_text())
    appendix = '\n\n## Architecture\n' + (ROOT / 'AGENTS.md').read_text()
    appendix += '\n\n## Product diff scope\nThe full gathered diff retains all workflow/log records. For review use the complete product diff at ' + str(TMP / f'review-product-diff-{ID}.diff') + '. All changed production/test/configuration/operator-doc paths follow:\n' + '\n'.join(manifest['product'])
    for name in ('facts', 'shapes', 'replay'):
        appendix += '\n\n' + (TMP / f'review-{name}-{ID}.md').read_text()
    appendix += '\n\n## Verification evidence\nThe coordinator ran all following checks against the exact reviewed HEAD.\n'
    for name in ('pytest', 'lint-approved', 'format-approved', 'mypy', 'build'):
        appendix += (TMP / f'review-gate-{name}-{ID}.json').read_text() + '\n'
        appendix += '\n'.join((TMP / f'review-gate-{name}-{ID}.log').read_text().splitlines()[-3:]) + '\n'
    handoff = (REVIEWS / f'{STEM}-repair-build-handoff-1.md').read_text()
    appendix += '\n\n## Repair handoff evidence\n' + handoff.split('## Assumption ledger', 1)[0]
    appendix += '\n\n## PRD 00008 assumption ledger\n' + handoff.split('# PRD 00008 assumptions', 1)[1]
    write(f'review-context-{ID}.md', context + appendix)
    prd = (ROOT / f'docs/dev/project-management/prds/wip/{STEM}.md').read_text()
    write(f'review-bob-context-{ID}.md', '# PRD (requirements authority; no implementation design)\n' + prd + appendix)
    refs = PLUGIN / 'skills/review-work-completion/references'
    fmt = (refs / 'output-formats.md').read_text().split('## Agent Output Format (Single Source of Truth)', 1)[1].split('## Per-Rule Verdict Format', 1)[0]
    checklist = (refs / 'review-dimensions.md').read_text()
    rubric = (refs / 'rubric.md').read_text()
    ledger = json.loads((REVIEWS / f'{STEM}-ledger.json').read_text())
    settled = '\n\n## Settled decisions — do not re-raise\nThese calls were already made in an earlier cycle of this same review, with the reasons given. Do not re-raise them. Raise a NEW finding only if you can show the settled reason no longer holds.\n'
    settled += '\n'.join(json.dumps(row, ensure_ascii=False) for row in ledger)
    prior = (REVIEWS / f'{STEM}-review-1.md').read_text().split('## Consolidated findings', 1)[1].split('## Decision evidence', 1)[0]
    incremental = '\n\n## Incremental review\nThis is an incremental review of the rework done since the previous review cycle — the diff is scoped to changes since then. Two jobs: (1) for each prior finding listed below, verify it is now resolved in the code; (2) review the scoped diff for any regression the rework introduced. You need not re-review unchanged code; the previous cycle already reviewed the full implementation.\n' + prior
    pack = '(no pack available this cycle)'
    pack_path = TMP / f'engram-pack-{ID}.md'
    if pack_path.exists():
        pack = str(pack_path)
    for name in ('alice', 'bob', 'carl', 'blake'):
        body = persona(name)
        if name == 'blake':
            replacements = {'{PRD}': prd, '{RUBRIC}': (PLUGIN / 'skills/review-blindly/references/rubric.md').read_text(), '{OUTPUT_FORMAT}': fmt.replace('{AGENT_NAME}', 'BLAKE')}
        else:
            replacements = {'{CONTEXT_FILE}': str(TMP / f'review-{"bob-context" if name == "bob" else "context"}-{ID}.md'), '{DIFF_FILE}': str(TMP / f'review-product-diff-{ID}.diff'), '{PACK_FILE}': pack, '{REVIEW_CHECKLIST}': checklist, '{RUBRIC}': rubric, '{OUTPUT_FORMAT}': fmt.replace('{AGENT_NAME}', name.upper())}
            if name == 'bob':
                body += '\n\n## Two lenses, applied to every changed file\n' + persona('eve').split('## Two lenses, applied to every changed file', 1)[1]
                replacements['{PACK_FINDINGS}'] = '(no pack available this cycle)'
                body += '\n\n' + (PLUGIN / 'skills/run-autopilot/references/doubt-review-rubric.md').read_text()
                body += '\nHost adaptation: you are external Claude Opus Bob, with Read and read-only shell inspection available. Preserve the complete static-only persona. Use Read or sed/rg to open files. No tests, code execution, edits or commits. Emit all 12 R verdicts AND all five D verdicts; place every residual finding in exactly one FIX/VERIFY/KNOWN bucket AND emit its [BOB] issue line. Buckets and issue lines describe the same findings, never count them twice.\nCite files repo-relative as path:line, never absolute or with a range suffix.\n'
            body += incremental + settled
        for key, value in replacements.items():
            body = body.replace(key, value)
        body += '\n\nReview only. Do not modify files, workflow state, or git. Return the complete review text to the coordinator; do not save it yourself. Use tools.exec_command for read-only inspection when the host has no Read/Bash tool; omit unsupported timeout fields. Before your first shell call state the current review request and what the command verifies. Do not read sibling review outputs.\n'
        if name == 'blake':
            body += 'Maintain blindness: do not inspect git diffs/history, task plans, designs, workflow state, prior reviews or sibling outputs. Independently inspect source/tests using only this specification.\n'
        write(f'{name}-prompt-{ID}.md', body)
        print(name, len(body))

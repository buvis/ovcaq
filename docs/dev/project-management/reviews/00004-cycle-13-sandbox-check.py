"""Exercise workflow ledger commands inside the launcher's real sandbox."""

import errno
import io
import json
import os
import tempfile
import uuid
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ovcaq import __file__ as package_file
from ovcaq.cli import main
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore


def outside_write_denied() -> dict:
    control = Path('/Users/bob') / f'.ovcaq-r13-sandbox-control-{uuid.uuid4().hex}'
    try:
        descriptor = os.open(control, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as error:
        assert error.errno in (errno.EPERM, errno.EACCES), repr(error)
        return {'denied': True, 'errno': error.errno, 'path': str(control)}
    else:
        os.close(descriptor)
        control.unlink()
        raise AssertionError('outside-repository write allowed: invalid sandbox test')


def run_command(base: Path, command: str) -> dict:
    project = base / command
    project.mkdir()
    state_path = project / 'independent/state.json'
    state_path.parent.mkdir()
    state = new_state(repo_root=project)
    state['batch'].update({'id': 'batch', 'status': 'running', 'started_at': '2026-09-05T20:00:00Z'})
    state['work']['prd'] = '00004-a.md'
    store = StateStore(state_path)
    store.initialize(state)
    wip = project / 'dev/local/prds/wip'
    wip.mkdir(parents=True)
    (wip / '00004-a.md').write_text('# Sandbox probe\n')
    record = project / 'record.json'
    record.write_text('{"op_id": "sandbox-probe"}')
    runtime = project / 'new/runtime'
    argv = ['--root', str(project), '--json', 'workflow', command, '--state', str(state_path), '--runtime-root', str(runtime)]
    if command == 'defer':
        argv += ['--prd', '00004-a.md', '--record', str(record)]
    elif command == 'stall':
        argv += ['--prd', '00004-a.md', '--site', 'probe', '--detail', 'sandbox verification']
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    ledger = runtime / 'deferred/batch-deferred.json'
    return {'command': command, 'exit': code, 'stdout': out.getvalue(), 'stderr': err.getvalue(), 'ledger': json.loads(ledger.read_text()) if ledger.exists() else None}


if __name__ == '__main__':
    control = outside_write_denied()
    with tempfile.TemporaryDirectory(prefix='sandbox-r13-', dir='dev/local/tmp') as folder:
        results = [run_command(Path(folder).resolve(), command) for command in ('defer', 'stall', 'park')]
    print(json.dumps({'module': package_file, 'control': control, 'commands': results}, indent=2))
    raise SystemExit(0 if all(result['exit'] == 0 for result in results) else 1)

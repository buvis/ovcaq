import json
import subprocess
from pathlib import Path

ROOT = Path('/Users/bob/git/src/github.com/buvis/ovcaq')
PLUGIN = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.9.0')
TMP = ROOT / 'docs/dev/tmp'
state = json.loads((ROOT / 'docs/dev/project-management/autopilot/state.json').read_text())
t = next(t for t in state['tasks'] if t['id'] == '6')
def put(name, value):
    p = TMP / name
    p.write_text(value)
    return str(p)

description = '''Task 6 only. Public behavior: bounded_detail(detail: str) -> str must retain redaction of tokens separated from a preceding word by any recognized C0/DEL/lone ESC control, and redact tokens reconstructed when recognized controls occur inside a token. Test bare sk- credentials and Bearer values independently through helper, native error and turn.failed payloads and saved normalized JSONL. Preserve the original R2 cap input and 4096-character final cap, formatting and original-text classification/reset. RawFirstDecoder must delegate deeply nested native JSON unchanged when preflight json.loads raises RecursionError: assert the native parser gap reason, unchanged adapter state, durable raw bytes and normalized evidence. No expanded control forms, cycles or TUI changes.
Allowed tests to edit: /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_detail_safety.py and /Users/bob/git/src/github.com/buvis/ovcaq/tests/events/test_unicode_frames.py. Read these two test files and /Users/bob/git/src/github.com/buvis/ovcaq/pyproject.toml only. Do not read production implementation. Reading budget: detail tests around lines 1-110 and 145-285; frame fixture lines 1-125 and delegation lines 275-320. Keep changes focused. Run only changed named tests -q --tb=line; do not commit or change state.'''
interfaces = '''bounded_detail(detail: str) -> str
CodexDriver(AgentSettings(...), run_id: str); decode(frame: str) -> tuple[Observation, ...]
RawFirstDecoder(raw=SessionEvidenceWriter(...), normalized=NormalizedEventWriter(...), driver=CodexDriver(...), run_id=..., session_id=...); feed(bytes) and finish() -> tuple[Observation,...]. Native malformed frame delegation produces RAW_UNKNOWN with driver-native reason, raw_sha256 and preview. Observation.payload is a mapping. Test fixture unicode_tail and detail driver fixtures are available in the listed test files.'''
args = ['python3', str(PLUGIN/'skills/work/scripts/render_prompt.py'),str(PLUGIN/'skills/work/references/tess-prompt.md'),'--out',str(TMP/'dispatch-tess-6.txt')]
for k,v in {'TASK_SUBJECT':t['name'],'TASK_DESCRIPTION':description,'TASK_ACCEPTANCE_CRITERIA':'Original-boundary and reconstructed-token inputs are redacted exactly; deep JSON preserves native delegation. All original cases remain unchanged.','PUBLIC_INTERFACES':interfaces}.items():
    args += ['--set-file',k+'='+put('tess-6-'+k+'.txt',v)]
args += ['--set-file','SAMPLE_TEST_FILE='+str(ROOT/'tests/drivers/test_codex_detail_safety.py'),'--set','TEST_FRAMEWORK=pytest','--dispatch-kind','tess','--dispatch-task','6']
for p in ['tests/drivers/test_codex_detail_safety.py','tests/events/test_unicode_frames.py']:
    args += ['--require-file',str(ROOT/p)]
subprocess.run(args,check=True)

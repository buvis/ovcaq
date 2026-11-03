import re
import subprocess
from pathlib import Path

log = Path(__file__).with_name('00053-review-pytest.log')
with log.open('w') as output:
    result = subprocess.run(['uv', 'run', 'pytest'], stdout=output, stderr=subprocess.STDOUT)
text = log.read_text()
counts = {}
for value, kind in re.findall(r'(\d+) (passed|failed|skipped|error|errors)', text.splitlines()[-1]):
    counts[kind] = int(value)
if 'passed' not in counts:
    raise SystemExit('No pytest summary: inspect ' + str(log))
print(f'PASS {counts.get("passed", 0)} FAIL {counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0)} SKIP {counts.get("skipped", 0)} EXIT {result.returncode}')
raise SystemExit(result.returncode)

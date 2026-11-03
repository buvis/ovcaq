import os
import subprocess
import sys
from pathlib import Path

name, budget = sys.argv[1:3]
args = sys.argv[3:]
result = subprocess.run(args, env=dict(os.environ, UV_CACHE_DIR='/private/tmp/ovcaq-rework-uv-cache'), capture_output=True, text=True, timeout=int(budget))
Path(f'docs/dev/tmp/{name}.log').write_text(result.stdout + result.stderr)
print(result.stdout[-4500:])
print(result.stderr[-1500:])
print(f'RECORDED {name}: exit {result.returncode}')
raise SystemExit(result.returncode)

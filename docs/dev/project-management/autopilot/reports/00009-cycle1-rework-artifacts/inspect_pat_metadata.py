from pathlib import Path
import json

root = Path.home() / '.claude/projects/-Users-bob-git-src-github-com-buvis-ovcaq'
for session in ['9db5aab5-8416-4a5f-ab4d-c6ac463d7b28', '43c77a11-28da-4196-887d-6203d960ad78']:
    path = root / (session + '.jsonl')
    print(path, path.exists())
    if not path.exists():
        continue
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    print([(row.get('message', {}).get('model'), row.get('sessionId')) for row in rows if row.get('type') == 'assistant'])
    print('tool use count', sum(1 for row in rows for block in row.get('message', {}).get('content', []) if isinstance(block, dict) and block.get('type') == 'tool_use'))

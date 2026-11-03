"""Record the explicitly authorized recovery through the installed state writer."""

import json
import sys
from pathlib import Path

ROOT = Path('/Users/bob/git/src/github.com/buvis/ovcaq')
PLUGIN = Path('/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.1/skills/run-autopilot')
sys.path.insert(0, str(PLUGIN))
from cli import schema, statectl


def authorize(state: dict) -> None:
    assert state['phase'] == state['next_phase'] == 'paused'
    assert state['pause_reason']['site'] == 'data_loss_risk'
    assert state['cycle'] == 13 and state['rework_cap'] == 2
    assert state['tasks_completed'] == 13 and state['tasks_total'] == 16
    assert state['rework_task_ids'] == []
    for task_id, tier, reason in [('4', 'opus', 'algorithmic_risk'), ('5', 'sonnet', 'test_port'), ('6', 'sonnet', 'test_port')]:
        task = next(t for t in state['tasks'] if t['id'] == task_id)
        assert task['status'] == 'pending'
        statectl.do_task_set_meta(state, task_id, {'model': tier, 'tier_reason': reason})
    state['rework_task_ids'] = ['4', '5', '6']
    state['autonomous_decisions'].append({
        'cycle': 13,
        'attempt': '20260913-interactive-repair',
        'issue': 'Operator authorized bounded recovery of tasks 4–6',
        'severity': 'high',
        'consensus': 'operator',
        'action': 'repair',
        'reason': 'Operator explicitly requested: Repair tasks 4–6 and prepare autocodex to resume. Execute these tasks with required work gates, then hand off to cycle 14 review; preserve cap 2, batch, work base and review history. Keep wrapper paused during repair.',
        'evidence': 'dev/local/reviews/00004-cycle-13-repair-start.py',
    })
    schema.validate(state)


if __name__ == '__main__':
    state_path = ROOT / 'dev/local/autopilot/state.json'
    before = state_path.read_bytes()
    statectl.mutate(state_path, authorize)
    (ROOT / 'dev/local/reviews/00004-cycle-13-pre-repair-state.json').write_bytes(before)
    print(json.dumps({'authorized': ['4', '5', '6'], 'phase': 'paused', 'cycle': 13, 'cap': 2}))

# FT-04R8 dispatch evidence

Installed plugin: /Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.0; version 0.5.0; installed registry source SHA 57f10bb1911aa764c42c19e0bd194fddbc3f5209.

Alice, Blake, and Bob each ran as fresh native Codex subagents (fork_turns=none), with their assembled registry persona and full lane rubric. Alice and Blake use the documented equivalent-host adapter; Bob uses the native fallback after the external runner refusal. No Claude or external Codex/Gemini review is claimed. All three used the inherited host model; this cycle has prompt/context independence, not model diversity.

Bob command:
```text
/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.0/skills/use-codex/scripts/codex-run.sh -f /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/bob-prompt-00004-cycle-08.md -o /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/bob-output-00004-cycle-08.txt --emit-thread-id /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/bob-thread-00004-cycle-08.txt
```
Exit 3, stderr: refusing nested dispatch (already inside a CLI agent)

Carl command (initial and one retry):
```text
/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.0/skills/use-gemini/scripts/gemini-run.sh -f /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/carl-prompt-00004-cycle-08.md -o /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/carl-output-00004-cycle-08.txt
```
Both exit 3, stderr: refusing nested dispatch (already inside a CLI agent)

No guard was disabled, no alternative external runner bypassed this refusal, no output was salvaged or claimed. Carl is unavailable (optional); no Eve opt-in/standalone task-store predicate applied. No runtime-state files were read or written.

All native reviewers returned their final reports before the coordinator saved any raw reviewer output. No reviewer received another report or finding. Only Alice/coordinator read rework-07.md. The forbidden review histories, ledgers, capsules, and retrieval packs were not read.

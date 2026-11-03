CLOSURE | resolved | "docs/driver-protocol.md:37: The docs say an empty host PATH 'searches the current directory' for both native adapters, but `ClaudeDriver.probe` passes `path=\"\"` to `shutil.which`, which returns None... Fix the sentence to say this" | The diff replaces the shared claim with "With an empty host `PATH`, the Claude probe is unhealthy; only the Codex subprocess probe searches the current directory." This matches the finding's description. The two `empty_host_path` tests passed.

NO FINDINGS

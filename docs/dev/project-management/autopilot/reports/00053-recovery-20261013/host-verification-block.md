# Host verification restriction

Direct `ps -o pid= -p $$` failed with exit 126: /bin/ps: Operation not permitted.

The diagnostic command `mise exec -- uv run pytest -q --tb=short -x tests/runtime/test_adapter_launch_routing.py` failed both normally and with sandbox_permissions=require_escalated. Both traces end at runtime.registry.process_identity -> subprocess.run with PermissionError: [Errno 1] Operation not permitted: ps. The first test failed in 0.16s / 0.15s respectively; pytest also reported two temporary-directory cleanup warnings.

This is the inherited host/Seatbelt restriction described in global AGENTS.md; changing command-level sandbox mode did not remove it. No permission guard was removed or bypassed. Targeted repair tests and Ruff/mypy/build pass. Full-suite failure evidence is retained separately; it must not be represented as green verification. A subsequent authorized host session must run the queued full and routing verification with ps available before closing the PRD.

"""Review-only runtime command resolution and initial doctor observations."""
import contextlib
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ovcaq.cli import main
from ovcaq.config import runtime_settings, workflow_settings
from ovcaq.paths import state_path


def invoke(root: Path, *arguments: str) -> tuple[int, dict]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
        code = main(["--root", str(root), "--json", *arguments])
    return code, json.loads(output.getvalue())


def main_proof() -> None:
    with TemporaryDirectory(prefix="ovcaq-review-paths-") as temporary:
        base = Path(temporary).resolve()
        project = base / "project"
        project.mkdir()
        with patch.dict(os.environ, {
            "XDG_CONFIG_HOME": str(base / "config"),
            "XDG_STATE_HOME": str(base / "state"),
        }):
            code, _ = invoke(project, "init")
            assert code == 0
            with patch("ovcaq.cli.probe_platform", return_value=()):
                _, doctor = invoke(project, "doctor")
            external = base / "external"
            (project / "ovcaq.toml").write_text(
                f'version = 1\n[runtime]\nexternal_state_root = "{external}"\n'
            )
            diagnostic = runtime_settings(project).paths.state_file
            workflow = workflow_settings(project).state_file
            primitive = state_path(project)
            _, status = invoke(project, "status")
            print(json.dumps({
                "doctor_after_init_ok": doctor["ok"],
                "doctor_after_init_checks": doctor["checks"],
                "diagnostic_state": str(diagnostic.relative_to(base)),
                "workflow_state": str(workflow.relative_to(base)),
                "state_command_default": str(primitive.relative_to(base)),
                "status_with_external_root": status["state"],
                "synthetic_only": True,
            }, sort_keys=True))


if __name__ == "__main__":
    main_proof()


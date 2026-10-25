from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ovcaq.workflow_client import (
    PROTOCOL_MAJOR,
    ControllerClient,
    ControllerConfig,
    MutationEnvelope,
)

BUNDLE = Path(__file__).parents[1] / "fixtures" / "workflow" / "controller-v1.json"
# Synthetic canary placed in the actor file's contents, never in its path.
CANARY = "super-secret-credential-xyz"
# The fake sleeps far longer than any timeout used here, so a timeout that
# fires must fire well inside TIMEOUT_BUDGET.
SLOW_SECONDS = 10
TIMEOUT_BUDGET = 5.0
# A message that hides part of the stderr has to say so somehow.
TRUNCATION_MARKERS = ("...", "…", "truncat", "elided", "omitted")
# Omitted-field sentinel for bundle variants.
OMIT = object()

# Fake controller: records its argv, cwd, pid, verb and any --request file, then
# answers with the stdout, stderr, delay and exit code the spec file in argv[1]
# holds for that verb, so one fake can answer contract and snapshot/apply
# differently inside a single test. When the answer asks for a grandchild, it
# leaves a long-sleeping child of its own in its process group and records that
# pid, so a test can tell a killed group from a killed direct child.
FAKE_CONTROLLER = """\
import json
import os
import subprocess
import sys
import time
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
verb = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else ""
record = {"argv": sys.argv, "cwd": os.getcwd(), "pid": os.getpid(), "verb": verb}
if "--request" in sys.argv:
    request = Path(sys.argv[sys.argv.index("--request") + 1])
    record["request"] = request.read_text(encoding="utf-8")
    record["request_mode"] = request.stat().st_mode & 0o777
answer = spec["answers"].get(verb, spec["answers"]["default"])
if answer.get("grandchild"):
    grandchild = subprocess.Popen(
        [sys.executable, "-c", f"import time; time.sleep({answer['grandchild']})"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    record["grandchild_pid"] = grandchild.pid
with open(spec["log"], "a", encoding="utf-8") as log:
    log.write(json.dumps(record) + "\\n")
sys.stdout.write(answer["stdout"])
sys.stdout.flush()
sys.stderr.write(answer["stderr"])
sys.stderr.flush()
time.sleep(answer["sleep"])
sys.exit(answer["exit"])
"""


@dataclass
class FakeController:
    script: Path
    spec: Path
    log: Path
    answers: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def argv(self) -> tuple[str, ...]:
        return (sys.executable, str(self.script), str(self.spec))

    @property
    def child_argv(self) -> list[str]:
        """The controller's own sys.argv before the client's arguments."""
        return [str(self.script), str(self.spec)]

    def respond(
        self,
        stdout: str = "",
        *,
        verb: str = "default",
        stderr: str = "",
        sleep: float = 0,
        exit_code: int = 0,
        grandchild: float = 0,
    ) -> None:
        self.answers[verb] = {
            "stdout": stdout,
            "stderr": stderr,
            "sleep": sleep,
            "exit": exit_code,
            "grandchild": grandchild,
        }
        answers = {
            "default": {
                "stdout": "",
                "stderr": "",
                "sleep": 0,
                "exit": 0,
                "grandchild": 0,
            },
            **self.answers,
        }
        spec = {"log": str(self.log), "answers": answers}
        self.spec.write_text(json.dumps(spec), encoding="utf-8")

    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        lines = self.log.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]

    def verbs(self) -> list[str]:
        return [call["verb"] for call in self.calls()]

    def call_for(self, verb: str) -> dict[str, Any]:
        [call] = [record for record in self.calls() if record["verb"] == verb]
        return call


@pytest.fixture
def fake(tmp_path: Path) -> FakeController:
    directory = tmp_path / "fake controller"
    directory.mkdir()
    script = directory / "controller.py"
    script.write_text(FAKE_CONTROLLER, encoding="utf-8")
    controller = FakeController(script, directory / "spec.json", tmp_path / "calls.log")
    controller.respond()
    return controller


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project root"
    root.mkdir()
    return root


@pytest.fixture
def actor_file(tmp_path: Path) -> Path:
    path = tmp_path / "actor.json"
    path.write_text(json.dumps({"actor_id": "actor-a", "proof": CANARY}), "utf-8")
    path.chmod(0o600)
    return path


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


FIXTURE = load_json(BUNDLE)


def write_bundle(tmp_path: Path, name: str = "pinned.json", **overrides: Any) -> Path:
    """A bundle that starts from the fixture and applies the overrides."""
    data = {
        key: value
        for key, value in {**FIXTURE, **overrides}.items()
        if value is not OMIT
    }
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def live_contract(
    pinned: dict[str, Any] | None = None, **overrides: Any
) -> dict[str, Any]:
    """A live answer that satisfies the pinned bundle, plus extra advertising."""
    base = FIXTURE if pinned is None else pinned
    live = {
        **base,
        "operations": [*base["operations"], "workflow.live-only"],
        "capabilities": [*base["capabilities"], "live-only"],
    }
    live.update(overrides)
    return live


def make_client(
    fake: FakeController,
    project_root: Path,
    *,
    actor_file: Path | None = None,
    bundle: Path = BUNDLE,
    **overrides: Any,
) -> ControllerClient:
    config = ControllerConfig(
        argv=fake.argv,
        contract_bundle=bundle,
        actor_file=actor_file,
        project_root=project_root,
        **overrides,
    )
    return ControllerClient(config)


def make_envelope(**overrides: Any) -> MutationEnvelope:
    fields: dict[str, Any] = {
        "protocol_major": PROTOCOL_MAJOR,
        "operation": "workflow.apply",
        "request_id": "req-0001",
        "expected_revision": 3,
        "project_id": "project-a",
        "workflow_id": "workflow-a",
        "actor_id": "actor-a",
        "lease_epoch": 2,
        "payload": {"event": "task.done"},
    }
    fields.update(overrides)
    return MutationEnvelope(**fields)


def envelope_as_json(envelope: MutationEnvelope) -> dict[str, Any]:
    """The request body the controller must receive for an envelope."""
    return {
        "protocol_major": envelope.protocol_major,
        "operation": envelope.operation,
        "request_id": envelope.request_id,
        "expected_revision": envelope.expected_revision,
        "project_id": envelope.project_id,
        "workflow_id": envelope.workflow_id,
        "actor_id": envelope.actor_id,
        "lease_epoch": envelope.lease_epoch,
        "payload": dict(envelope.payload),
    }


ACCEPTED_APPLY = {
    "ok": True,
    "revision": 6,
    "result": {"phase": "review"},
    "error_code": None,
    "retryable": False,
}

REJECTED_APPLY = {
    "ok": False,
    "revision": None,
    "result": None,
    "error_code": "stale-revision",
    "retryable": True,
}
APPLY_RESPONSES = [ACCEPTED_APPLY, REJECTED_APPLY]


def request_path(call: dict[str, Any]) -> Path:
    argv = call["argv"]
    return Path(call["cwd"]) / argv[argv.index("--request") + 1]


def process_ended(pid: int, *, within: float = 3.0) -> bool:
    """Poll until no process has pid, allowing for kill and reap latency."""
    deadline = time.monotonic() + within
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        if time.monotonic() > deadline:
            return False
        time.sleep(0.05)


def exception_chain(error: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    return chain


def secret_fragments(secret: str, length: int = 8) -> list[str]:
    return [secret[index : index + length] for index in range(len(secret) - length + 1)]


def hides_secret(error: BaseException, secret: str) -> bool:
    """No exception in the chain shows the secret or a long fragment of it."""
    for item in exception_chain(error):
        for text in (str(item), repr(item)):
            if secret in text:
                return False
            if any(piece in text for piece in secret_fragments(secret)):
                return False
    return True


def marks_truncation(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in TRUNCATION_MARKERS)


def broken_program(tmp_path: Path, kind: str) -> Path:
    if kind == "missing":
        return tmp_path / "no-such-controller"
    if kind == "directory":
        path = tmp_path / "controller-directory"
        path.mkdir()
        return path
    path = tmp_path / "controller-not-executable"
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o644)
    return path


def call_contract(client: ControllerClient) -> object:
    return client.contract()


def call_snapshot(client: ControllerClient) -> object:
    return client.snapshot(workflow_id="workflow-a")


def call_apply(client: ControllerClient) -> object:
    return client.apply(make_envelope())


EVERY_CALL = pytest.mark.parametrize(
    "call",
    [call_contract, call_snapshot, call_apply],
    ids=["contract", "snapshot", "apply"],
)

CALL_BY_VERB = {
    "contract": call_contract,
    "snapshot": call_snapshot,
    "apply": call_apply,
}
EVERY_VERB = pytest.mark.parametrize("verb", list(CALL_BY_VERB))


def write_actor_file(
    tmp_path: Path, name: str, *, secret: str | None = None, flavor: str = "json"
) -> Path:
    """An actor file that holds the secret, or only short values without one."""
    if secret is None:
        body = "actor-a\n"
    elif flavor == "plain":
        body = secret + "\n"
    else:
        body = json.dumps({"actor_id": "actor-a", "auth": {"proof": secret}})
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o600)
    return path

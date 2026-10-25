"""The configuration contract the tool owes every supported PRD."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.workflow_client.prerequisites_support import (
    CLOSURE,
    DIRECT,
    GATES,
    PRDS,
    assert_refused,
    foreign_keys,
    make_ready,
    mark_done,
    missing_of,
    padded,
    report,
    run_tool,
    write_config,
)

EVERY_PRD = sorted(DIRECT)
# Unrelated faults, so a tool that only recognises one still fails. The nested
# value exhausts the parser's recursion limit instead of raising a parse error.
BROKEN = {
    "unterminated-table": "[workflow\ncontroller_artifact = \n",
    "unterminated-string": 'controller_artifact = "exported\n',
    "deeply-nested-value": "a = " + "[" * 20000 + "]" * 20000 + "\n",
}


@pytest.mark.parametrize("prd", EVERY_PRD)
def test_explicit_config_that_does_not_exist_is_refused_for_every_prd(
    tmp_path: Path, prd: str
) -> None:
    make_ready(tmp_path, prd)
    absent = tmp_path / "conf" / "absent.toml"

    assert_refused(run_tool(tmp_path, prd, "--config", str(absent)), str(absent))


@pytest.mark.parametrize("prd", EVERY_PRD)
@pytest.mark.parametrize("flaw", sorted(BROKEN))
def test_unparseable_explicit_config_is_refused_for_every_prd(
    tmp_path: Path, prd: str, flaw: str
) -> None:
    make_ready(tmp_path, prd)
    explicit = tmp_path / "conf" / "broken.toml"
    write_config(explicit, BROKEN[flaw])

    assert_refused(run_tool(tmp_path, prd, "--config", str(explicit)), str(explicit))


@pytest.mark.parametrize("prd", EVERY_PRD)
@pytest.mark.parametrize("flaw", sorted(BROKEN))
def test_unparseable_default_config_is_refused_for_every_prd(
    tmp_path: Path, prd: str, flaw: str
) -> None:
    make_ready(tmp_path, prd)
    write_config(tmp_path / "ovcaq.toml", BROKEN[flaw])

    assert_refused(run_tool(tmp_path, prd), "ovcaq.toml")


@pytest.mark.parametrize("prd", EVERY_PRD)
def test_broken_config_is_refused_before_predecessors_are_evaluated(
    tmp_path: Path, prd: str
) -> None:
    # Nothing is done and no artifact exists, so an unready verdict is tempting.
    (tmp_path / PRDS / "done").mkdir(parents=True)
    write_config(tmp_path / "ovcaq.toml", BROKEN["unterminated-table"])

    assert_refused(run_tool(tmp_path, prd), "ovcaq.toml")


def test_each_refusal_class_names_what_it_refused(tmp_path: Path) -> None:
    make_ready(tmp_path, "58")
    absent = tmp_path / "conf" / "absent.toml"
    broken = tmp_path / "conf" / "broken.toml"
    write_config(broken, BROKEN["unterminated-table"])
    refusals = {
        "absent-config": run_tool(tmp_path, "58", "--config", str(absent)),
        "unparseable-config": run_tool(tmp_path, "58", "--config", str(broken)),
        "unknown-prd": run_tool(tmp_path, "63"),
    }
    write_config(tmp_path / "ovcaq.toml", "[workflow]\ncontroller_artifact = 5\n")
    refusals["wrong-type"] = run_tool(tmp_path, "58")

    assert_refused(refusals["absent-config"], str(absent))
    assert_refused(refusals["unparseable-config"], str(broken))
    assert_refused(refusals["unknown-prd"], "63")
    assert_refused(refusals["wrong-type"], "controller_artifact")
    # Four different faults, four different messages.
    assert len({result.stderr.strip() for result in refusals.values()}) == 4


@pytest.mark.parametrize("prd", EVERY_PRD)
def test_readable_explicit_config_is_accepted_for_every_prd(
    tmp_path: Path, prd: str
) -> None:
    make_ready(tmp_path, prd)
    default = tmp_path / "ovcaq.toml"
    body = default.read_text(encoding="utf-8") if default.exists() else ""
    explicit = tmp_path / "conf" / "valid.toml"
    write_config(explicit, body)

    result = run_tool(tmp_path, prd, "--config", str(explicit))

    assert report(result, 0) == {"ready": True, "prd": prd}


@pytest.mark.parametrize("prd", EVERY_PRD)
def test_absent_default_config_is_never_a_config_error(
    tmp_path: Path, prd: str
) -> None:
    mark_done(tmp_path, *CLOSURE[prd])
    assert not (tmp_path / "ovcaq.toml").exists()

    result = run_tool(tmp_path, prd)

    if prd not in GATES:
        assert report(result, 0) == {"ready": True, "prd": prd}
        return
    missing = missing_of(result, prd)
    _, key, _ = GATES[prd]
    assert any(key in entry for entry in missing)
    for foreign in foreign_keys(prd):
        assert not any(foreign in entry for entry in missing)
    for dep in DIRECT[prd]:
        assert not any(padded(dep) in entry for entry in missing)

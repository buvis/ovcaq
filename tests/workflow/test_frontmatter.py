from __future__ import annotations

import pytest

from ovcaq.workflow import frontmatter


def _block(*lines: str) -> str:
    return "---\n" + "\n".join(lines) + "\n---\n\n# A PRD\n"


def test_bare_block_takes_provider_neutral_defaults_silently() -> None:
    fields, warnings = frontmatter.parse(_block("title: nothing recognized"))

    assert fields == {
        "catchup_mode": "run",
        "design_mode": "run",
        "rework_cap": 2,
    }
    assert warnings == []


@pytest.mark.parametrize(
    ("line", "key", "value"),
    [
        pytest.param("catchup: skip", "catchup_mode", "skip", id="catchup-skip"),
        pytest.param("catchup: force", "catchup_mode", "force", id="catchup-force"),
        pytest.param("design: skip", "design_mode", "skip", id="design-skip"),
        pytest.param("rework_cap: 5", "rework_cap", 5, id="rework-cap"),
        pytest.param("design_gate: user", "design_gate", "user", id="design-gate"),
        pytest.param(
            "pause_on_ambiguity: true",
            "pause_on_ambiguity",
            True,
            id="pause-on-ambiguity",
        ),
    ],
)
def test_recognized_frontmatter_rows(line: str, key: str, value: object) -> None:
    fields, warnings = frontmatter.parse(_block(line))

    assert fields[key] == value
    assert warnings == []


@pytest.mark.parametrize("raw", ["0", "-3", "abc", "2.5", ""])
def test_invalid_rework_cap_defaults_and_warns(raw: str) -> None:
    fields, warnings = frontmatter.parse(_block(f"rework_cap: {raw}"))

    assert fields["rework_cap"] == 2
    assert len(warnings) == 1
    assert "rework_cap" in warnings[0]


@pytest.mark.parametrize(
    ("line", "key", "default"),
    [
        pytest.param("catchup: sometimes", "catchup_mode", "run", id="catchup"),
        pytest.param("design: maybe", "design_mode", "run", id="design"),
    ],
)
def test_invalid_enum_rows_warn_and_default(
    line: str,
    key: str,
    default: str,
) -> None:
    fields, warnings = frontmatter.parse(_block(line))

    assert fields[key] == default
    assert len(warnings) == 1
    assert line.partition(":")[0] in warnings[0]


@pytest.mark.parametrize("text", ["", "# no frontmatter\n", "---\ncatchup: skip\n"])
def test_missing_or_malformed_block_gets_one_warning(text: str) -> None:
    fields, warnings = frontmatter.parse(text)

    assert fields == frontmatter.defaults()
    assert warnings == [frontmatter.MALFORMED_WARNING]


def test_block_closing_after_twenty_lines_is_malformed() -> None:
    text = "---\n" + "\n".join(f"pad{i}: x" for i in range(25)) + "\n---\n"
    _fields, warnings = frontmatter.parse(text)

    assert warnings == [frontmatter.MALFORMED_WARNING]


@pytest.mark.parametrize("value", ["auto", "false", "True", "yes"])
def test_unrecognized_opt_ins_stay_absent_without_warning(value: str) -> None:
    fields, warnings = frontmatter.parse(
        _block(f"design_gate: {value}", f"pause_on_ambiguity: {value}")
    )

    assert "design_gate" not in fields
    assert "pause_on_ambiguity" not in fields
    assert warnings == []


def test_unknown_keys_are_ignored_and_colons_stay_in_values() -> None:
    fields, warnings = frontmatter.parse(
        _block("title: A: colonated title", "unknown: value")
    )

    assert fields == frontmatter.defaults()
    assert warnings == []


def test_available_abstract_tier_becomes_the_frontmatter_floor() -> None:
    fields, warnings = frontmatter.parse(
        _block("default_model: deep"),
        available_tiers={"fast", "deep"},
    )

    assert fields["tier"] == "deep"
    assert warnings == []


@pytest.mark.parametrize("available_tiers", [None, {"fast"}])
def test_unavailable_abstract_tier_warns_and_applies_no_floor(
    available_tiers: set[str] | None,
) -> None:
    fields, warnings = frontmatter.parse(
        _block("default_model: deep"),
        available_tiers=available_tiers,
    )

    assert "tier" not in fields
    assert len(warnings) == 1
    assert "deep" in warnings[0]


def test_overwrite_warning_only_reports_changed_existing_values() -> None:
    warnings = frontmatter.overwrite_warnings(
        {"rework_cap": 5, "catchup_mode": "run"},
        {"rework_cap": 2, "catchup_mode": "run", "tier": "deep"},
    )

    assert warnings == ["ovcaq: PRD frontmatter reset rework_cap 5 -> 2"]

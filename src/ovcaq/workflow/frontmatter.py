"""Flat, bounded PRD frontmatter parsing."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass

from ovcaq.state.schema import State
from ovcaq.state.store import StateStore
from ovcaq.workflow.records import require_recovery_idle

type FrontmatterValue = str | int | bool

_HEAD_LINES = 20
_ENUMS: dict[str, tuple[str, tuple[str, ...], str]] = {
    "catchup": ("catchup_mode", ("run", "skip", "force"), "run"),
    "design": ("design_mode", ("run", "skip"), "run"),
}
_REWORK_CAP_DEFAULT = 2
_STATE_REWORK_CAP_DEFAULT = 3
_OPT_INS: dict[str, tuple[str, str, FrontmatterValue]] = {
    "design_gate": ("design_gate", "user", "user"),
    "pause_on_ambiguity": ("pause_on_ambiguity", "true", True),
}
_LEGACY_EXTENSION_KEYS = {
    "catchup_mode": "workflow/catchup-mode",
    "design_mode": "workflow/design-mode",
    "design_gate": "workflow/design-gate",
    "pause_on_ambiguity": "workflow/pause-on-ambiguity",
}
_TIER_EXTENSION_KEY = "workflow/tier-floor"
_REWORK_CAP_OWNER_KEY = "workflow/frontmatter-rework-cap-owned"

MALFORMED_WARNING = (
    "ovcaq: PRD frontmatter malformed; defaulting catchup_mode=run, "
    "rework_cap=2, design_mode=run"
)


@dataclass(frozen=True)
class FrontmatterApplication:
    """The committed state and effective frontmatter projection."""

    state: State
    fields: dict[str, FrontmatterValue]
    warnings: tuple[str, ...]


def defaults() -> dict[str, FrontmatterValue]:
    """Return effective values for a PRD with no declarations."""
    fields: dict[str, FrontmatterValue] = {
        state_key: default for state_key, _allowed, default in _ENUMS.values()
    }
    fields["rework_cap"] = _REWORK_CAP_DEFAULT
    return fields


def _block(text: str) -> list[str] | None:
    lines = text.splitlines()[:_HEAD_LINES]
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    return None


def _pairs(body: list[str]) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in body:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        pairs[key.strip()] = value.strip()
    return pairs


def _positive_integer(raw: str) -> int | None:
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _apply_enums(
    declared: Mapping[str, str],
    fields: dict[str, FrontmatterValue],
    warnings: list[str],
) -> None:
    for prd_key, (state_key, allowed, default) in _ENUMS.items():
        if prd_key not in declared:
            continue
        value = declared[prd_key]
        if value in allowed:
            fields[state_key] = value
        else:
            warnings.append(
                f"ovcaq: PRD frontmatter {prd_key}={value!r} is not one of "
                f"{'/'.join(allowed)}; defaulting to {default}"
            )


def parse(
    text: str,
    *,
    available_tiers: Collection[str] | None = None,
) -> tuple[dict[str, FrontmatterValue], list[str]]:
    """Parse the first frontmatter block into neutral effective fields."""
    fields = defaults()
    body = _block(text)
    if body is None:
        return fields, [MALFORMED_WARNING]

    declared = _pairs(body)
    warnings: list[str] = []
    _apply_enums(declared, fields, warnings)

    if "rework_cap" in declared:
        cap = _positive_integer(declared["rework_cap"])
        if cap is None:
            warnings.append(
                "ovcaq: PRD frontmatter "
                f"rework_cap={declared['rework_cap']!r} is not a positive integer; "
                f"defaulting to {_REWORK_CAP_DEFAULT}"
            )
        else:
            fields["rework_cap"] = cap

    for prd_key, (state_key, marker, opt_in_value) in _OPT_INS.items():
        if declared.get(prd_key) == marker:
            fields[state_key] = opt_in_value

    tier = declared.get("default_model")
    if tier is not None:
        if available_tiers is not None and tier in available_tiers:
            fields["tier"] = tier
        else:
            warnings.append(
                f"ovcaq: PRD frontmatter tier {tier!r} is unavailable; "
                "applying no tier floor"
            )

    return fields, warnings


def overwrite_warnings(
    existing: Mapping[str, object],
    effective: Mapping[str, FrontmatterValue],
) -> list[str]:
    """Report only effective values that replace a different prior value."""
    return [
        f"ovcaq: PRD frontmatter reset {key} {existing[key]} -> {value}"
        for key, value in effective.items()
        if key in existing and existing[key] != value
    ]


def apply_to_store(
    store: StateStore,
    text: str,
    *,
    prd: str,
    available_tiers: Collection[str] | None = None,
    expected_revision: int | None = None,
) -> FrontmatterApplication:
    """Parse and commit effective frontmatter through one store transaction."""
    fields, parse_warnings = parse(text, available_tiers=available_tiers)
    replaced: dict[str, object] = {}

    def apply_fields(state: State) -> None:
        require_recovery_idle(state)
        if state["work"]["prd"] != prd:
            raise ValueError(
                f"frontmatter PRD {prd!r} does not match active PRD "
                f"{state['work']['prd']!r}"
            )
        extensions = state["work"]["extensions"]
        review_extensions = state["review"]["extensions"]
        for field, extension_key in _LEGACY_EXTENSION_KEYS.items():
            if extension_key in extensions:
                replaced[field] = extensions[extension_key]
        if _TIER_EXTENSION_KEY in extensions:
            replaced["tier"] = extensions[_TIER_EXTENSION_KEY]
        if (
            review_extensions.get(_REWORK_CAP_OWNER_KEY) is True
            or state["review"]["cap"] != _STATE_REWORK_CAP_DEFAULT
        ):
            replaced["rework_cap"] = state["review"]["cap"]

        state["review"]["cap"] = int(fields["rework_cap"])
        for extension_key in _LEGACY_EXTENSION_KEYS.values():
            extensions.pop(extension_key, None)
        extensions.pop(_TIER_EXTENSION_KEY, None)
        review_extensions[_REWORK_CAP_OWNER_KEY] = True
        if "tier" in fields:
            extensions[_TIER_EXTENSION_KEY] = fields["tier"]

    committed = store.transaction(
        apply_fields,
        expected_revision=expected_revision,
    )
    warnings = (*parse_warnings, *overwrite_warnings(replaced, fields))
    return FrontmatterApplication(
        state=committed,
        fields=fields,
        warnings=tuple(warnings),
    )

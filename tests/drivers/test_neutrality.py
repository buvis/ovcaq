import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SCANNED_PATHS = (
    ROOT / "src/ovcaq/events",
    ROOT / "src/ovcaq/runtime",
    ROOT / "src/ovcaq/tui",
    ROOT / "src/ovcaq/state",
    ROOT / "src/ovcaq/workflow",
)
FORBIDDEN_IMPORT_MARKERS = ("anthropic", "claude", "codex")
FORBIDDEN_SOURCE_MARKERS = (
    *FORBIDDEN_IMPORT_MARKERS,
    "haiku",
    "opus",
    "sonnet",
    "gpt-",
)


def shared_modules() -> tuple[Path, ...]:
    modules = [module for path in SCANNED_PATHS for module in path.rglob("*.py")]
    modules.extend((ROOT / "src/ovcaq").glob("*.py"))
    modules.append(ROOT / "src/ovcaq/drivers/base.py")
    return tuple(sorted(modules))


@pytest.mark.parametrize(
    "scanned_path", SCANNED_PATHS, ids=lambda path: str(path.relative_to(ROOT))
)
def test_scanned_paths_are_existing_directories(scanned_path: Path) -> None:
    assert scanned_path.is_dir()


@pytest.mark.parametrize(
    "module_path",
    shared_modules(),
    ids=lambda path: str(path.relative_to(ROOT)),
)
def test_shared_modules_do_not_import_provider_modules(module_path: Path) -> None:
    tree = ast.parse(module_path.read_text(), filename=str(module_path))
    imported_modules = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    imported_modules.extend(
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )

    for imported_module in imported_modules:
        folded_import = imported_module.casefold()
        for marker in FORBIDDEN_IMPORT_MARKERS:
            assert marker not in folded_import, (
                f"{module_path.relative_to(ROOT)} imports provider module "
                f"{imported_module!r} (matched {marker!r})"
            )


@pytest.mark.parametrize(
    "module_path",
    shared_modules(),
    ids=lambda path: str(path.relative_to(ROOT)),
)
def test_shared_module_source_has_no_provider_identifiers(module_path: Path) -> None:
    folded_source = module_path.read_text().casefold()

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in folded_source, (
            f"{module_path.relative_to(ROOT)} contains forbidden provider "
            f"identifier {marker!r}"
        )

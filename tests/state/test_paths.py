from __future__ import annotations

from copy import deepcopy
from itertools import product

import pytest

from ovcaq.state.paths import (
    PathToken,
    append_path,
    delete_path,
    get_path,
    parse_path,
    set_path,
)


def _tokens(*tokens: PathToken) -> tuple[PathToken, ...]:
    return tokens


_COMPOSED_PATH_CASES = [
    pytest.param(
        f"{outer}.{inner}[{index}]",
        outer,
        inner,
        index,
        id=f"{outer}.{inner}[{index}]",
    )
    for (outer, inner), index in product(
        (("alpha", "beta"), ("cedar", "branch"), ("north", "wind")),
        (0, 1, 2, -1, -2, -3),
    )
]


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("review.decisions[-1].status", ("review", "decisions", -1, "status")),
        ('work.extensions["acme/foo.bar"]', ("work", "extensions", "acme/foo.bar")),
        ("[0][-1].status", (0, -1, "status")),
        ('["root.key"][2][0]', ("root.key", 2, 0)),
        ("items[001][-01]", ("items", 1, -1)),
        (
            r'routing["a.b"]["array[0]"]["close]"]["quote\"slash\\newline\n"]',
            (
                "routing",
                "a.b",
                "array[0]",
                "close]",
                'quote"slash\\newline\n',
            ),
        ),
        (r'["\u0061\u002eb"]', ("a.b",)),
    ],
)
def test_parse_path_decodes_valid_paths(
    path: str,
    expected: tuple[PathToken, ...],
) -> None:
    assert parse_path(path) == expected


@pytest.mark.parametrize(
    ("path", "outer", "inner", "index"),
    _COMPOSED_PATH_CASES,
)
def test_dotted_keys_and_indices_compose_for_get(
    path: str,
    outer: str,
    inner: str,
    index: int,
) -> None:
    values = ["north", "east", "south"]
    root = {outer: {inner: values}}
    tokens = parse_path(path)

    assert tokens == (outer, inner, index)
    assert get_path(root, tokens) == values[index]


@pytest.mark.parametrize(
    ("path", "outer", "inner", "index"),
    _COMPOSED_PATH_CASES,
)
def test_dotted_keys_and_indices_compose_for_set(
    path: str,
    outer: str,
    inner: str,
    index: int,
) -> None:
    values = ["north", "east", "south"]
    root = {outer: {inner: values}}
    tokens = parse_path(path)

    assert tokens == (outer, inner, index)

    set_path(root, tokens, "changed")

    assert values[index] == "changed"


@pytest.mark.parametrize(
    ("path", "outer", "inner", "index"),
    _COMPOSED_PATH_CASES,
)
def test_dotted_keys_and_indices_compose_for_append(
    path: str,
    outer: str,
    inner: str,
    index: int,
) -> None:
    values = [["north"], ["east"], ["south"]]
    root = {outer: {inner: values}}
    expected = [*values[index], "added"]
    tokens = parse_path(path)

    assert tokens == (outer, inner, index)

    append_path(root, tokens, "added")

    assert values[index] == expected


@pytest.mark.parametrize(
    ("path", "outer", "inner", "index"),
    _COMPOSED_PATH_CASES,
)
def test_dotted_keys_and_indices_compose_for_delete(
    path: str,
    outer: str,
    inner: str,
    index: int,
) -> None:
    values = ["north", "east", "south"]
    root = {outer: {inner: values}}
    expected = values.copy()
    del expected[index]
    tokens = parse_path(path)

    assert tokens == (outer, inner, index)

    delete_path(root, tokens)

    assert values == expected


@pytest.mark.parametrize(
    "path",
    [
        "",
        ".root",
        "root.",
        "root..child",
        "root.[0]",
        "[0]..child",
        "root[]",
        "root[",
        "root]",
        "root[0",
        "root[0]]",
        "root[+1]",
        "root[ 1]",
        "root[1 ]",
        "root[1.0]",
        "root[-]",
        "root[--1]",
        "root[one]",
        'root[""]',
        'root["unterminated]',
        r'root["bad\q"]',
        'root["key"',
        'root["key"]child',
        "root[0]child",
    ],
)
def test_parse_path_rejects_malformed_paths(path: str) -> None:
    with pytest.raises(ValueError):
        parse_path(path)


def test_get_path_returns_root_for_empty_tokens() -> None:
    root = {"items": [1, 2]}

    assert get_path(root, ()) is root


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (0, "first"),
        (2, "last"),
        (-1, "last"),
        (-3, "first"),
    ],
)
def test_get_path_traverses_object_keys_and_bounded_list_indices(
    index: int,
    expected: str,
) -> None:
    root = {"runs": [{"name": "first"}, {"name": "middle"}, {"name": "last"}]}

    assert get_path(root, _tokens("runs", index, "name")) == expected


@pytest.mark.parametrize("index", [-4, 3])
def test_get_path_rejects_out_of_range_indices(index: int) -> None:
    root = {"items": ["first", "middle", "last"]}

    with pytest.raises(ValueError):
        get_path(root, _tokens("items", index))


@pytest.mark.parametrize(
    ("root", "tokens"),
    [
        ({}, ("missing",)),
        ({"items": []}, ("items", 0)),
        ({"items": []}, ("items", "name")),
        ({"item": {}}, ("item", 0)),
        ({"item": None}, ("item", "name")),
    ],
)
def test_get_path_rejects_missing_or_invalid_traversal(
    root: object,
    tokens: tuple[PathToken, ...],
) -> None:
    with pytest.raises(ValueError):
        get_path(root, tokens)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (0, [{"status": "new"}, {"status": "keep"}]),
        (-2, [{"status": "new"}, {"status": "keep"}]),
    ],
)
def test_set_path_updates_existing_list_indices(
    index: int,
    expected: list[dict[str, str]],
) -> None:
    root = {"runs": [{"status": "old"}, {"status": "keep"}]}

    set_path(root, _tokens("runs", index, "status"), "new")

    assert root == {"runs": expected}


def test_set_path_creates_only_missing_object_intermediates() -> None:
    root: dict[str, object] = {}

    set_path(root, _tokens("recovery", "decision", "status"), "retry")

    assert root == {"recovery": {"decision": {"status": "retry"}}}


def test_set_path_does_not_synthesize_an_array() -> None:
    root: dict[str, object] = {}

    with pytest.raises(ValueError):
        set_path(root, _tokens("runs", 0, "status"), "retry")

    assert root == {}


@pytest.mark.parametrize("index", [-2, 1])
def test_set_path_rejects_out_of_range_indices(index: int) -> None:
    root = {"items": ["only"]}
    before = deepcopy(root)

    with pytest.raises(ValueError):
        set_path(root, _tokens("items", index), "replacement")

    assert root == before


def test_set_path_rejects_wrong_container_type() -> None:
    root = {"run": None}

    with pytest.raises(ValueError):
        set_path(root, _tokens("run", "status"), "retry")

    assert root == {"run": None}


def test_append_path_appends_to_existing_list_through_negative_index() -> None:
    root = {"runs": [{"events": []}, {"events": ["started"]}]}

    append_path(root, _tokens("runs", -1, "events"), "finished")

    assert root == {
        "runs": [
            {"events": []},
            {"events": ["started", "finished"]},
        ]
    }


def test_append_path_creates_a_missing_final_object_key_as_list() -> None:
    root = {"run": {}}

    append_path(root, _tokens("run", "events"), "started")

    assert root == {"run": {"events": ["started"]}}


def test_append_path_can_target_a_list_at_a_bounded_list_index() -> None:
    root = {"groups": [["existing"], []]}

    append_path(root, _tokens("groups", -2), "appended")

    assert root == {"groups": [["existing", "appended"], []]}


def test_append_path_rejects_a_missing_parent() -> None:
    root: dict[str, object] = {}

    with pytest.raises(ValueError):
        append_path(root, _tokens("run", "events"), "started")

    assert root == {}


@pytest.mark.parametrize(
    ("root", "tokens"),
    [
        ({"events": {}}, ("events",)),
        ({"events": []}, ("events", 0)),
        ({"events": [[]]}, ("events", 1)),
        ({"events": [[]]}, ("events", -2)),
    ],
)
def test_append_path_rejects_nonlist_targets_and_out_of_range_indices(
    root: dict[str, object],
    tokens: tuple[PathToken, ...],
) -> None:
    before = deepcopy(root)

    with pytest.raises(ValueError):
        append_path(root, tokens, "event")

    assert root == before


def test_delete_path_removes_an_object_key_without_touching_siblings() -> None:
    root = {"run": {"status": "failed", "attempt": 2}, "other": {"keep": True}}

    delete_path(root, _tokens("run", "status"))

    assert root == {"run": {"attempt": 2}, "other": {"keep": True}}


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (0, ["middle", "last"]),
        (2, ["first", "middle"]),
        (-1, ["first", "middle"]),
        (-3, ["middle", "last"]),
    ],
)
def test_delete_path_removes_bounded_list_indices(
    index: int,
    expected: list[str],
) -> None:
    root = {"items": ["first", "middle", "last"]}

    delete_path(root, _tokens("items", index))

    assert root == {"items": expected}


@pytest.mark.parametrize(
    ("root", "tokens"),
    [
        ({"run": {}}, ("run", "missing")),
        ({"items": []}, ("items", 0)),
        ({"items": ["only"]}, ("items", 1)),
        ({"items": ["only"]}, ("items", -2)),
        ({"item": None}, ("item", "status")),
        ({"item": {}}, ("item", 0)),
    ],
)
def test_delete_path_rejects_missing_invalid_or_out_of_range_targets(
    root: dict[str, object],
    tokens: tuple[PathToken, ...],
) -> None:
    before = deepcopy(root)

    with pytest.raises(ValueError):
        delete_path(root, tokens)

    assert root == before


def test_set_path_rejects_root_replacement() -> None:
    root = {"status": "original"}

    with pytest.raises(ValueError):
        set_path(root, (), "replacement")

    assert root == {"status": "original"}


def test_append_path_rejects_root_append() -> None:
    root = {"events": []}

    with pytest.raises(ValueError):
        append_path(root, (), "event")

    assert root == {"events": []}


def test_delete_path_rejects_root_deletion() -> None:
    root = {"status": "original"}

    with pytest.raises(ValueError):
        delete_path(root, ())

    assert root == {"status": "original"}

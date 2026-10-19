# ruff: noqa: TRY004 -- The public path API reports all invalid paths as ValueError.

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import TypeAlias, cast

from ovcaq.state.schema import JSONValue, State

PathToken: TypeAlias = str | int  # noqa: UP040

_INDEX_PATTERN = re.compile(r"-?\d+")


def parse_path(path: str) -> tuple[PathToken, ...]:
    if not path:
        raise ValueError("path must not be empty")

    tokens: list[PathToken] = []
    position = 0
    while position < len(path):
        if path[position] == "[":
            position += 1
            if position >= len(path):
                raise ValueError("unterminated path bracket")
            if path[position] == '"':
                try:
                    key, end = json.JSONDecoder().raw_decode(path, position)
                except json.JSONDecodeError as error:
                    raise ValueError("invalid quoted path key") from error
                if not key:
                    raise ValueError("quoted path keys must not be empty")
                if end >= len(path) or path[end] != "]":
                    raise ValueError("quoted path key must end with ]")
                tokens.append(key)
                position = end + 1
            else:
                end = path.find("]", position)
                if end < 0:
                    raise ValueError("unterminated path index")
                encoded_index = path[position:end]
                if _INDEX_PATTERN.fullmatch(encoded_index) is None:
                    raise ValueError("invalid path index")
                tokens.append(int(encoded_index))
                position = end + 1
        else:
            start = position
            while position < len(path) and path[position] not in ".[]":
                position += 1
            if position == start:
                raise ValueError("path key must not be empty")
            tokens.append(path[start:position])

        if position == len(path):
            break
        if path[position] == "[":
            continue
        if path[position] != ".":
            raise ValueError("invalid path delimiter")
        position += 1
        if position == len(path) or path[position] in ".[":
            raise ValueError("path key must follow dot")

    return tuple(tokens)


def _checked_index(values: Sequence[object], index: int) -> int:
    if index < -len(values) or index >= len(values):
        raise ValueError(f"list index out of range: {index}")
    return index


def _resolve(value: object, tokens: Sequence[PathToken]) -> object:
    current = value
    for token in tokens:
        if isinstance(token, str):
            if not isinstance(current, dict) or token not in current:
                raise ValueError(f"missing or invalid object key: {token}")
            current = current[token]
        else:
            if not isinstance(current, list):
                raise ValueError(f"path index requires a list: {token}")
            current = current[_checked_index(current, token)]
    return current


def get_path(value: JSONValue, tokens: Sequence[PathToken]) -> JSONValue:
    return cast(JSONValue, _resolve(value, tokens))


def set_path(
    root: State,
    tokens: Sequence[PathToken],
    value: JSONValue,
) -> None:
    if not tokens:
        raise ValueError("cannot replace the root")

    current: object = root
    created: list[tuple[dict[object, object], str]] = []
    try:
        for position, token in enumerate(tokens[:-1]):
            next_token = tokens[position + 1]
            if isinstance(token, str):
                if not isinstance(current, dict):
                    raise ValueError(f"path key requires an object: {token}")
                if token not in current:
                    if not isinstance(next_token, str):
                        raise ValueError("set_path does not create lists")
                    current[token] = {}
                    created.append((current, token))
                current = current[token]
            else:
                if not isinstance(current, list):
                    raise ValueError(f"path index requires a list: {token}")
                current = current[_checked_index(current, token)]

        final = tokens[-1]
        if isinstance(final, str):
            if not isinstance(current, dict):
                raise ValueError(f"path key requires an object: {final}")
            current[final] = value
        else:
            if not isinstance(current, list):
                raise ValueError(f"path index requires a list: {final}")
            current[_checked_index(current, final)] = value
    except ValueError:
        for mapping, key in reversed(created):
            del mapping[key]
        raise


def append_path(
    root: State,
    tokens: Sequence[PathToken],
    value: JSONValue,
) -> None:
    if not tokens:
        raise ValueError("cannot append to the root")

    parent = _resolve(root, tokens[:-1])
    final = tokens[-1]
    if isinstance(final, str):
        if not isinstance(parent, dict):
            raise ValueError(f"path key requires an object: {final}")
        if final not in parent:
            parent[final] = [value]
            return
        target = parent[final]
    else:
        if not isinstance(parent, list):
            raise ValueError(f"path index requires a list: {final}")
        target = parent[_checked_index(parent, final)]

    if not isinstance(target, list):
        raise ValueError("append target must be a list")
    target.append(value)


def delete_path(root: State, tokens: Sequence[PathToken]) -> None:
    if not tokens:
        raise ValueError("cannot delete the root")

    parent = _resolve(root, tokens[:-1])
    final = tokens[-1]
    if isinstance(final, str):
        if not isinstance(parent, dict) or final not in parent:
            raise ValueError(f"missing or invalid object key: {final}")
        del parent[final]
    else:
        if not isinstance(parent, list):
            raise ValueError(f"path index requires a list: {final}")
        del parent[_checked_index(parent, final)]

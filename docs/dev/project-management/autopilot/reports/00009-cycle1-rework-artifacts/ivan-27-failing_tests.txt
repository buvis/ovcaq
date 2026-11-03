import pytest

from ovcaq.drivers.codex_events import item_activity

FAKE_CREDENTIAL = "sk-" + "SyntheticCredentialForPlacementTestOnly123456789012"


@pytest.mark.parametrize(
    ("item_type", "field", "kind"),
    [
        ("agent_message", "text", "text"),
        ("reasoning", "text", "thinking"),
        ("error", "message", "error"),
    ],
)
@pytest.mark.parametrize("text", ["Activity content", ""])
def test_events_module_preserves_normalized_text_activity(
    item_type: str, field: str, kind: str, text: str
) -> None:
    item = {"id": "activity-27", "type": item_type, field: text}
    assert item_activity(item) == {
        "kind": kind,
        "text": text,
        "message_id": "activity-27",
    }


@pytest.mark.parametrize(
    "items",
    [
        [],
        [
            {"text": "Finished task", "completed": True},
            {"text": "", "completed": False},
            {"text": "Pending task", "completed": False},
        ],
    ],
)
def test_events_module_preserves_plan_entries_and_completion(items: list[dict]) -> None:
    assert item_activity({"id": "plan-27", "type": "todo_list", "items": items}) == {
        "kind": "plan",
        "message_id": "plan-27",
        "items": items,
    }


@pytest.mark.parametrize(
    ("item_type", "field"),
    [("agent_message", "text"), ("reasoning", "text"), ("error", "message")],
)
def test_text_activity_sanitizes_and_bounds_text_and_message_id(
    item_type: str, field: str
) -> None:
    unsafe = "Safe " + FAKE_CREDENTIAL + "\x1b[31m\x00" + "x" * 5000
    activity = item_activity({"id": unsafe, "type": item_type, field: unsafe})
    assert activity is not None
    for key in ("text", "message_id"):
        value = activity[key]
        assert isinstance(value, str)
        assert value.startswith("Safe ")
        assert 0 < len(value) <= 4096
        assert FAKE_CREDENTIAL not in value
        assert "[REDACTED]" in value


def test_plan_activity_sanitizes_and_bounds_each_text_and_message_id() -> None:
    unsafe = "Safe " + FAKE_CREDENTIAL + "\x1b[31m\x00" + "x" * 5000
    activity = item_activity(
        {
            "id": unsafe,
            "type": "todo_list",
            "items": [
                {"text": unsafe, "completed": False},
                {"text": "Unchanged", "completed": True},
            ],
        }
    )
    assert activity is not None
    assert activity["kind"] == "plan"
    items = activity["items"]
    assert isinstance(items, list) and len(items) == 2
    assert items[0]["completed"] is False
    assert items[1] == {"text": "Unchanged", "completed": True}
    for value in (activity["message_id"], items[0]["text"]):
        assert isinstance(value, str)
        assert value.startswith("Safe ")
        assert 0 < len(value) <= 4096
        assert FAKE_CREDENTIAL not in value
        assert "[REDACTED]" in value


@pytest.mark.parametrize("length", [4095, 4096, 4097])
def test_safe_text_and_message_ids_preserve_content_up_to_limit(length: int) -> None:
    text = "x" * length
    activity = item_activity({"id": text, "type": "agent_message", "text": text})
    assert activity is not None
    assert activity["kind"] == "text"
    for key in ("text", "message_id"):
        value = activity[key]
        assert isinstance(value, str)
        if length <= 4096:
            assert value == text
        else:
            assert 0 < len(value) <= 4096


@pytest.mark.parametrize(
    "item",
    [
        None,
        [],
        "activity",
        {},
        {"id": "activity", "type": "unknown", "text": "content"},
        {"id": "", "type": "agent_message", "text": "content"},
        {"id": None, "type": "agent_message", "text": "content"},
        {"id": 27, "type": "agent_message", "text": "content"},
        {"type": "agent_message", "text": "content"},
        {"id": "activity", "type": "agent_message"},
        {"id": "activity", "type": "reasoning", "text": None},
        {"id": "activity", "type": "error", "text": "wrong field"},
        {"id": "activity", "type": "error", "message": 27},
        {"id": "plan", "type": "todo_list", "items": None},
        {"id": "plan", "type": "todo_list", "items": {}},
        {"id": "plan", "type": "todo_list", "items": [None]},
        {"id": "plan", "type": "todo_list", "items": [{"text": "task"}]},
        {
            "id": "plan",
            "type": "todo_list",
            "items": [{"text": None, "completed": False}],
        },
        {
            "id": "plan",
            "type": "todo_list",
            "items": [{"text": "task", "completed": 1}],
        },
    ],
)
def test_invalid_or_unknown_items_return_no_activity(item: object) -> None:
    assert item_activity(item) is None

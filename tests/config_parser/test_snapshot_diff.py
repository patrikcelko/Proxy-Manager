"""
Snapshot diff tests
===================

Unit tests for the diff / rename-detection logic in
`proxy_manager.config_parser.snapshot`.
"""

from datetime import UTC

from proxy_manager.config_parser.snapshot import (
    _compute_field_changes,  # type: ignore
    _diff_entity_list,  # type: ignore
    _match_renamed_entities,  # type: ignore
    _parse_iso_datetime,  # type: ignore
    compute_diff,  # type: ignore
)


def test_no_changes_field_changes() -> None:
    """No changes field changes."""

    old = {"name": "a", "mode": "http"}
    new = {"name": "a", "mode": "http"}
    assert _compute_field_changes(old, new) == []


def test_value_change_field_changes() -> None:
    """Value change field changes."""

    old = {"name": "a", "mode": "http"}
    new = {"name": "a", "mode": "tcp"}
    changes = _compute_field_changes(old, new)
    assert len(changes) == 1
    assert changes[0]["field"] == "mode"
    assert changes[0]["old"] == "http"
    assert changes[0]["new"] == "tcp"


def test_added_field_field_changes() -> None:
    """Added field field changes."""

    old = {"name": "a"}
    new = {"name": "a", "mode": "http"}
    changes = _compute_field_changes(old, new)
    assert len(changes) == 1
    assert changes[0]["field"] == "mode"
    assert changes[0]["old"] is None
    assert changes[0]["new"] == "http"


def test_removed_field_field_changes() -> None:
    """Removed field field changes."""

    old = {"name": "a", "mode": "http"}
    new = {"name": "a"}
    changes = _compute_field_changes(old, new)
    assert len(changes) == 1
    assert changes[0]["field"] == "mode"
    assert changes[0]["old"] == "http"
    assert changes[0]["new"] is None


def test_nested_list_change_field_changes() -> None:
    """Nested list change field changes."""

    old = {"servers": [{"name": "s1", "port": 80}]}
    new = {"servers": [{"name": "s1", "port": 443}]}
    changes = _compute_field_changes(old, new)
    assert len(changes) == 1
    assert changes[0]["field"] == "servers"


#  _diff_entity_list – name-keyed


def test_no_changes() -> None:
    """No changes."""

    items = [{"name": "a", "mode": "http"}, {"name": "b", "mode": "tcp"}]
    diff = _diff_entity_list(items, list(items), "name")
    assert diff["total"] == 0
    assert diff["created"] == []
    assert diff["deleted"] == []
    assert diff["updated"] == []


def test_created() -> None:
    """Created."""

    old = [{"name": "a"}]
    new = [{"name": "a"}, {"name": "b"}]
    diff = _diff_entity_list(old, new, "name")
    assert len(diff["created"]) == 1
    assert diff["created"][0]["name"] == "b"
    assert diff["deleted"] == []
    assert diff["updated"] == []


def test_deleted() -> None:
    """Deleted."""

    old = [{"name": "a"}, {"name": "b"}]
    new = [{"name": "a"}]
    diff = _diff_entity_list(old, new, "name")
    assert len(diff["deleted"]) == 1
    assert diff["deleted"][0]["name"] == "b"
    assert diff["created"] == []


def test_updated() -> None:
    """Updated."""

    old = [{"name": "be1", "mode": "http", "balance": "roundrobin"}]
    new = [{"name": "be1", "mode": "tcp", "balance": "roundrobin"}]
    diff = _diff_entity_list(old, new, "name")
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "be1"
    assert diff["updated"][0]["changes"][0]["field"] == "mode"
    assert diff["created"] == []
    assert diff["deleted"] == []


def test_rename_detected_as_updated() -> None:
    """Renaming an entity should produce an 'updated' entry, not
    a delete + create pair."""

    old = [{"name": "stats", "mode": "http", "balance": "roundrobin", "comment": None}]
    new = [{"name": "statsc", "mode": "http", "balance": "roundrobin", "comment": None}]
    diff = _diff_entity_list(old, new, "name")
    assert diff["created"] == [], "renamed entity must NOT appear as created"
    assert diff["deleted"] == [], "renamed entity must NOT appear as deleted"
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "statsc"
    assert any(c["field"] == "name" for c in diff["updated"][0]["changes"])


def test_rename_with_field_change() -> None:
    """Rename + another field change should still be detected."""

    old = [{"name": "mypeers", "comment": "old", "extra": "x", "default_bind": None}]
    new = [{"name": "mypeersc", "comment": "new", "extra": "x", "default_bind": None}]
    diff = _diff_entity_list(old, new, "name")
    assert diff["created"] == []
    assert diff["deleted"] == []
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "mypeersc"
    changed_fields = {c["field"] for c in diff["updated"][0]["changes"]}
    assert "name" in changed_fields
    assert "comment" in changed_fields


def test_rename_no_match_when_too_different() -> None:
    """If entities share < 50% fields, they should NOT be paired."""

    old = [{"name": "a", "mode": "http", "balance": "rr", "comment": "x"}]
    new = [{"name": "b", "mode": "tcp", "balance": "lc", "comment": "y"}]
    diff = _diff_entity_list(old, new, "name")
    # All non-name fields differ -> 0% match -> no pairing
    assert len(diff["deleted"]) == 1
    assert len(diff["created"]) == 1
    assert diff["updated"] == []


def test_rename_multiple_entities() -> None:
    """Multiple renames should be correctly matched."""

    old = [
        {"name": "be1", "mode": "http", "balance": "rr"},
        {"name": "be2", "mode": "tcp", "balance": "lc"},
    ]
    new = [
        {"name": "be1_new", "mode": "http", "balance": "rr"},
        {"name": "be2_new", "mode": "tcp", "balance": "lc"},
    ]
    diff = _diff_entity_list(old, new, "name")
    assert diff["deleted"] == []
    assert diff["created"] == []
    assert len(diff["updated"]) == 2
    entities = {u["entity"] for u in diff["updated"]}
    assert entities == {"be1_new", "be2_new"}


def test_mixed_rename_create_delete() -> None:
    """Mix of renamed, genuinely created, genuinely deleted."""

    old = [
        {"name": "keep", "mode": "http"},
        {"name": "rename_me", "mode": "tcp", "balance": "rr"},
        {"name": "delete_me", "mode": "http", "balance": "lc"},
    ]
    new = [
        {"name": "keep", "mode": "http"},
        {"name": "renamed", "mode": "tcp", "balance": "rr"},
        {"name": "brand_new", "mode": "tcp", "balance": "source", "extra": "val"},
    ]
    diff = _diff_entity_list(old, new, "name")
    updated_entities = {u["entity"] for u in diff["updated"]}
    created_names = {c["name"] for c in diff["created"]}
    deleted_names = {d["name"] for d in diff["deleted"]}

    assert "renamed" in updated_entities, "rename should be detected as update"
    assert "brand_new" in created_names, "truly new entity stays as created"
    assert "delete_me" in deleted_names, "truly deleted entity stays as deleted"


#  _diff_entity_list – ordered (legacy settings)


def test_no_changes_ordered() -> None:
    """No changes ordered."""

    items = [{"directive": "log", "value": "x", "sort_order": 0}]
    diff = _diff_entity_list(items, list(items), "_ordered")
    assert diff["total"] == 0


def test_value_change_ordered() -> None:
    """Value change ordered."""

    old = [{"directive": "log", "value": "x", "sort_order": 0}]
    new = [{"directive": "log", "value": "y", "sort_order": 0}]
    diff = _diff_entity_list(old, new, "_ordered")
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "log"


def test_added_setting_ordered() -> None:
    """Added setting ordered."""

    old = [{"directive": "log", "value": "x"}]
    new = [{"directive": "log", "value": "x"}, {"directive": "maxconn", "value": "4096"}]
    diff = _diff_entity_list(old, new, "_ordered")
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "maxconn"


def test_removed_setting_ordered() -> None:
    """Removed setting ordered."""

    old = [{"directive": "log"}, {"directive": "maxconn"}]
    new = [{"directive": "log"}]
    diff = _diff_entity_list(old, new, "_ordered")
    assert len(diff["deleted"]) == 1


def test_added_setting_at_beginning_does_not_cascade_ordered() -> None:
    """Adding a new setting at the start must NOT mark all subsequent entries as modified.

    BUG REPRODUCTION: Positional comparison broke when a new entry
    was inserted with sort_order=0, shifting all positions by one.
    """

    old = [
        {"id": 727, "directive": "log", "value": "127.0.0.1:514  local0", "comment": None, "sort_order": 0},
        {"id": 728, "directive": "log-send-hostname", "value": "", "comment": None, "sort_order": 1},
        {"id": 729, "directive": "stats", "value": "socket /run/haproxy.sock", "comment": None, "sort_order": 2},
        {"id": 730, "directive": "daemon", "value": "", "comment": None, "sort_order": 3},
        {"id": 731, "directive": "maxconn", "value": "10000", "comment": None, "sort_order": 4},
    ]
    # User added a new log entry (id=778) at sort_order=0 — all IDs are different (reimport)
    new = [
        {"id": 753, "directive": "log", "value": "127.0.0.1:514  local0", "comment": None, "sort_order": 0},
        {"id": 778, "directive": "log", "value": "127.0.0.1:514 local0", "comment": "Send logs to remote syslog", "sort_order": 0},
        {"id": 754, "directive": "log-send-hostname", "value": "", "comment": None, "sort_order": 1},
        {"id": 755, "directive": "stats", "value": "socket /run/haproxy.sock", "comment": None, "sort_order": 2},
        {"id": 760, "directive": "daemon", "value": "", "comment": None, "sort_order": 3},
        {"id": 763, "directive": "maxconn", "value": "10000", "comment": None, "sort_order": 4},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    # Only the new log entry should be created — everything else is unchanged
    assert diff["total"] == 1
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "log"
    assert len(diff["updated"]) == 0
    assert len(diff["deleted"]) == 0


def test_added_setting_in_middle_does_not_cascade_ordered() -> None:
    """Adding a setting in the middle of the list must not affect other entries."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon", "value": "", "sort_order": 1},
        {"id": 3, "directive": "maxconn", "value": "4096", "sort_order": 2},
    ]
    new = [
        {"id": 10, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 11, "directive": "daemon", "value": "", "sort_order": 1},
        {"id": 12, "directive": "user", "value": "haproxy", "sort_order": 2},  # new
        {"id": 13, "directive": "maxconn", "value": "4096", "sort_order": 3},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "user"


def test_removed_setting_from_middle_does_not_cascade_ordered() -> None:
    """Removing from the middle must only delete that one entry."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon", "value": "", "sort_order": 1},
        {"id": 3, "directive": "maxconn", "value": "4096", "sort_order": 2},
    ]
    new = [
        {"id": 10, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 13, "directive": "maxconn", "value": "4096", "sort_order": 1},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["deleted"]) == 1
    assert diff["deleted"][0]["directive"] == "daemon"


def test_mixed_add_and_modify_separate_ordered() -> None:
    """Adding one entry and modifying another must show 1 created + 1 updated."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "sort_order": 1},
    ]
    new = [
        {"id": 10, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 11, "directive": "maxconn", "value": "8192", "sort_order": 1},  # modified
        {"id": 12, "directive": "daemon", "value": "", "sort_order": 2},  # new
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 2
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "daemon"
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "maxconn"


def test_duplicate_directives_add_one_more_ordered() -> None:
    """With two existing 'stats' lines, adding a third shows only 1 created."""

    old = [
        {"id": 1, "directive": "stats", "value": "socket /a", "sort_order": 0},
        {"id": 2, "directive": "stats", "value": "socket /b", "sort_order": 1},
    ]
    new = [
        {"id": 10, "directive": "stats", "value": "socket /a", "sort_order": 0},
        {"id": 11, "directive": "stats", "value": "socket /b", "sort_order": 1},
        {"id": 12, "directive": "stats", "value": "timeout 30s", "sort_order": 2},  # new
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["created"]) == 1
    assert diff["created"][0]["value"] == "timeout 30s"


def test_duplicate_directives_modify_one_ordered() -> None:
    """With two 'stats' lines, modifying one shows exactly 1 updated."""

    old = [
        {"id": 1, "directive": "stats", "value": "socket /a", "sort_order": 0},
        {"id": 2, "directive": "stats", "value": "socket /b", "sort_order": 1},
    ]
    new = [
        {"id": 10, "directive": "stats", "value": "socket /a", "sort_order": 0},
        {"id": 11, "directive": "stats", "value": "socket /c", "sort_order": 1},  # changed
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "stats"


def test_nonsequential_sort_order_stripped_ordered() -> None:
    """Different sort_order values after reimport should not produce diffs."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "comment": None, "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 5},
        {"id": 3, "directive": "daemon", "value": "", "comment": None, "sort_order": 10},
    ]
    new = [
        {"id": 100, "directive": "log", "value": "x", "comment": None, "sort_order": 0},
        {"id": 101, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 1},
        {"id": 102, "directive": "daemon", "value": "", "comment": None, "sort_order": 2},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 0


def test_entity_id_from_new_items_ordered() -> None:
    """Updated entries carry entity_id from the new item's id."""

    old = [{"id": 1, "directive": "maxconn", "value": "4096", "sort_order": 0}]
    new = [{"id": 42, "directive": "maxconn", "value": "8192", "sort_order": 0}]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert diff["updated"][0]["entity_id"] == "42"


def test_real_production_scenario_25_to_26_entries_ordered() -> None:
    """Reproduces the exact production bug: committed snapshot had 25 settings
    with IDs 727-751, current DB has 26 settings with new IDs 753-778.
    Only difference is one additional 'log' entry. The diff must show
    exactly 1 created entry, not 25 modified entries.
    """

    old = [
        {"id": 727, "directive": "log", "value": "127.0.0.1:514  local0", "comment": None, "sort_order": 0},
        {"id": 728, "directive": "log-send-hostname", "value": "", "comment": None, "sort_order": 1},
        {"id": 729, "directive": "stats", "value": "socket /run/haproxy-info.sock", "comment": None, "sort_order": 2},
        {"id": 730, "directive": "stats", "value": "socket /run/haproxy-master.sock", "comment": None, "sort_order": 3},
        {"id": 731, "directive": "stats", "value": "timeout 30s", "comment": None, "sort_order": 4},
        {"id": 732, "directive": "user", "value": "haproxy", "comment": None, "sort_order": 5},
        {"id": 733, "directive": "group", "value": "haproxy", "comment": None, "sort_order": 6},
        {"id": 734, "directive": "daemon", "value": "", "comment": None, "sort_order": 7},
        {"id": 735, "directive": "server-state-file", "value": "/var/lib/haproxy/last_state", "comment": None, "sort_order": 8},
        {"id": 736, "directive": "hard-stop-after", "value": "3s", "comment": None, "sort_order": 9},
        {"id": 737, "directive": "maxconn", "value": "10000", "comment": None, "sort_order": 10},
        {"id": 738, "directive": "ca-base", "value": "/etc/ssl/certs", "comment": "Default SSL material locations", "sort_order": 11},
    ]
    new = [
        {"id": 753, "directive": "log", "value": "127.0.0.1:514  local0", "comment": None, "sort_order": 0},
        {"id": 778, "directive": "log", "value": "127.0.0.1:514 local0", "comment": "Send logs to remote syslog", "sort_order": 0},
        {"id": 754, "directive": "log-send-hostname", "value": "", "comment": None, "sort_order": 1},
        {"id": 755, "directive": "stats", "value": "socket /run/haproxy-info.sock", "comment": None, "sort_order": 2},
        {"id": 756, "directive": "stats", "value": "socket /run/haproxy-master.sock", "comment": None, "sort_order": 3},
        {"id": 757, "directive": "stats", "value": "timeout 30s", "comment": None, "sort_order": 4},
        {"id": 758, "directive": "user", "value": "haproxy", "comment": None, "sort_order": 5},
        {"id": 759, "directive": "group", "value": "haproxy", "comment": None, "sort_order": 6},
        {"id": 760, "directive": "daemon", "value": "", "comment": None, "sort_order": 7},
        {"id": 761, "directive": "server-state-file", "value": "/var/lib/haproxy/last_state", "comment": None, "sort_order": 8},
        {"id": 762, "directive": "hard-stop-after", "value": "3s", "comment": None, "sort_order": 9},
        {"id": 763, "directive": "maxconn", "value": "10000", "comment": None, "sort_order": 10},
        {"id": 764, "directive": "ca-base", "value": "/etc/ssl/certs", "comment": "Default SSL material locations", "sort_order": 11},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1, f"Expected 1 change (1 created), got {diff['total']}: created={len(diff['created'])}, updated={len(diff['updated'])}, deleted={len(diff['deleted'])}"
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "log"
    assert diff["created"][0]["value"] == "127.0.0.1:514 local0"
    assert len(diff["updated"]) == 0
    assert len(diff["deleted"]) == 0


#  Phase 0 (ID matching) tests


def test_same_ids_modify_value_ordered() -> None:
    """When IDs match, a value change shows as UPDATED (not CREATED+DELETED)."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "sort_order": 1},
    ]
    new = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "8192", "sort_order": 1},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "maxconn"
    assert diff["updated"][0]["entity_id"] == "2"
    assert diff["updated"][0]["changes"][0]["old"] == "4096"
    assert diff["updated"][0]["changes"][0]["new"] == "8192"


def test_same_ids_rename_directive_ordered() -> None:
    """When IDs match, renaming a directive shows as UPDATED with directive change.

    BUG REPRODUCTION: Before Phase 0, renaming a directive produced
    CREATED + DELETED instead of UPDATED.
    """

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon", "value": "", "sort_order": 1},
        {"id": 3, "directive": "maxconn", "value": "4096", "sort_order": 2},
    ]
    new = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon_new", "value": "", "sort_order": 1},
        {"id": 3, "directive": "maxconn", "value": "4096", "sort_order": 2},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["updated"]) == 1
    assert len(diff["created"]) == 0
    assert len(diff["deleted"]) == 0
    assert diff["updated"][0]["entity"] == "daemon_new"
    assert diff["updated"][0]["entity_id"] == "2"
    changes = diff["updated"][0]["changes"]
    assert any(c["field"] == "directive" and c["old"] == "daemon" and c["new"] == "daemon_new" for c in changes)


def test_same_ids_modify_comment_ordered() -> None:
    """Comment changes detected via ID matching."""

    old = [
        {"id": 1, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 0},
    ]
    new = [
        {"id": 1, "directive": "maxconn", "value": "4096", "comment": "Max connections", "sort_order": 0},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity_id"] == "1"


def test_same_ids_no_changes_ordered() -> None:
    """Identical entries with same IDs produce no diff."""

    items = [
        {"id": 1, "directive": "log", "value": "x", "comment": None, "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "comment": None, "sort_order": 1},
    ]
    diff = _diff_entity_list(items, list(items), "_ordered")
    assert diff["total"] == 0


def test_same_ids_add_entry_ordered() -> None:
    """Adding an entry with a new ID correctly shows as CREATED."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
    ]
    new = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 99, "directive": "maxconn", "value": "4096", "sort_order": 1},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "maxconn"
    assert diff["created"][0]["entity_id"] == "99"


def test_same_ids_delete_entry_ordered() -> None:
    """Deleting an entry correctly shows as DELETED."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon", "value": "", "sort_order": 1},
    ]
    new = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 1
    assert len(diff["deleted"]) == 1
    assert diff["deleted"][0]["directive"] == "daemon"


def test_same_ids_mixed_add_modify_delete_ordered() -> None:
    """Multiple changes at once: add, modify, and delete."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon", "value": "", "sort_order": 1},
        {"id": 3, "directive": "maxconn", "value": "4096", "sort_order": 2},
    ]
    new = [
        {"id": 1, "directive": "log", "value": "y", "sort_order": 0},  # modified
        # id=2 deleted
        {"id": 3, "directive": "maxconn", "value": "4096", "sort_order": 1},  # unchanged
        {"id": 4, "directive": "user", "value": "haproxy", "sort_order": 2},  # new
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    assert diff["total"] == 3
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "log"
    assert len(diff["deleted"]) == 1
    assert diff["deleted"][0]["directive"] == "daemon"
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "user"


#  Different IDs with directive rename (post-Manual-Edit)


def test_different_ids_rename_directive_shows_created_deleted_ordered() -> None:
    """When IDs differ AND directive is renamed, algorithm can't match: CREATED+DELETED.

    This is an acceptable limitation for the rare case of different IDs
    (after Manual Edit re-import) combined with a directive rename.
    """

    old = [
        {"id": 1, "directive": "daemon", "value": "", "sort_order": 0},
    ]
    new = [
        {"id": 100, "directive": "daemon_new", "value": "", "sort_order": 0},
    ]
    diff = _diff_entity_list(old, new, "_ordered")
    # Can't match: different ID, different directive, same value doesn't help
    assert diff["total"] == 2
    assert len(diff["created"]) == 1
    assert len(diff["deleted"]) == 1


def test_entity_id_in_created_entries_ordered() -> None:
    """CREATED entries include entity_id for frontend row marking."""

    old = []
    new = [{"id": 42, "directive": "maxconn", "value": "4096", "sort_order": 0}]
    diff = _diff_entity_list(old, new, "_ordered")
    assert len(diff["created"]) == 1
    assert diff["created"][0]["entity_id"] == "42"
    # id and sort_order should be stripped from the entry itself
    assert "id" not in diff["created"][0]
    assert "sort_order" not in diff["created"][0]


#  _diff_entity_list – id-based (settings with id)


def test_no_changes_by_id() -> None:
    """No changes by id."""

    items = [{"id": 1, "directive": "log", "value": "x", "sort_order": 0}]
    diff = _diff_entity_list(items, list(items), "id")
    assert diff["total"] == 0


def test_single_value_change_by_id() -> None:
    """Single value change by id."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "10000", "sort_order": 1},
    ]
    new = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "20000", "sort_order": 1},
    ]
    diff = _diff_entity_list(old, new, "id")
    assert diff["total"] == 1
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "maxconn"
    assert diff["updated"][0]["entity_id"] == "2"


def test_duplicate_directives_only_changed_one_marked_by_id() -> None:
    """When multiple settings share a directive name, only the actually changed one is reported."""

    old = [
        {"id": 10, "directive": "stats", "value": "socket /a", "sort_order": 0},
        {"id": 11, "directive": "stats", "value": "socket /b", "sort_order": 1},
        {"id": 12, "directive": "stats", "value": "timeout 30s", "sort_order": 2},
    ]
    new = [
        {"id": 10, "directive": "stats", "value": "socket /a", "sort_order": 0},
        {"id": 11, "directive": "stats", "value": "socket /c", "sort_order": 1},  # changed
        {"id": 12, "directive": "stats", "value": "timeout 30s", "sort_order": 2},
    ]
    diff = _diff_entity_list(old, new, "id")
    assert diff["total"] == 1
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity_id"] == "11"


def test_added_setting_by_id() -> None:
    """Added setting by id."""

    old = [{"id": 1, "directive": "log", "value": "x", "sort_order": 0}]
    new = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "sort_order": 1},
    ]
    diff = _diff_entity_list(old, new, "id")
    assert diff["total"] == 1
    assert len(diff["created"]) == 1
    assert diff["created"][0]["directive"] == "maxconn"


def test_removed_setting_by_id() -> None:
    """Removed setting by id."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "maxconn", "value": "4096", "sort_order": 1},
    ]
    new = [{"id": 1, "directive": "log", "value": "x", "sort_order": 0}]
    diff = _diff_entity_list(old, new, "id")
    assert diff["total"] == 1
    assert len(diff["deleted"]) == 1
    assert diff["deleted"][0]["directive"] == "maxconn"


def test_reorder_does_not_cascade_by_id() -> None:
    """Reordering (changing sort_order) should only mark the affected settings, not cascade."""

    old = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon", "value": "", "sort_order": 1},
        {"id": 3, "directive": "maxconn", "value": "10000", "sort_order": 2},
    ]
    new = [
        {"id": 1, "directive": "log", "value": "x", "sort_order": 0},
        {"id": 2, "directive": "daemon", "value": "", "sort_order": 2},  # swapped
        {"id": 3, "directive": "maxconn", "value": "10000", "sort_order": 1},  # swapped
    ]
    diff = _diff_entity_list(old, new, "id")
    assert diff["total"] == 2  # Only the two reordered items
    assert len(diff["updated"]) == 2


#  _diff_entity_list – composite (ACL rules)


def test_no_changes_composite() -> None:
    """No changes composite."""

    items = [{"frontend_name": "http", "domain": "example.com", "sort_order": 0, "comment": None}]
    diff = _diff_entity_list(items, list(items), "_composite")
    assert diff["total"] == 0


def test_acl_updated_composite() -> None:
    """Acl updated composite."""

    old = [{"frontend_name": "http", "domain": "example.com", "sort_order": 0, "comment": None}]
    new = [{"frontend_name": "http", "domain": "example.com", "sort_order": 0, "comment": "edited"}]
    diff = _diff_entity_list(old, new, "_composite")
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "http:example.com:0"
    assert diff["updated"][0]["changes"][0]["field"] == "comment"


def test_acl_created_composite() -> None:
    """Acl created composite."""

    old: list[dict[str, str | int | None]] = []
    new = [{"frontend_name": "http", "domain": "new.com", "sort_order": 0}]
    diff = _diff_entity_list(old, new, "_composite")
    assert len(diff["created"]) == 1


def test_acl_deleted_composite() -> None:
    """Acl deleted composite."""

    old = [{"frontend_name": "http", "domain": "old.com", "sort_order": 0}]
    new: list[dict[str, str | int | None]] = []
    diff = _diff_entity_list(old, new, "_composite")
    assert len(diff["deleted"]) == 1


#  _diff_entity_list – domain-keyed (SSL certs)


def test_cert_updated() -> None:
    """Cert updated."""

    old = [{"domain": "example.com", "provider": "letsencrypt"}]
    new = [{"domain": "example.com", "provider": "manual"}]
    diff = _diff_entity_list(old, new, "domain")
    assert len(diff["updated"]) == 1
    assert diff["updated"][0]["entity"] == "example.com"


def test_cert_created() -> None:
    """Cert created."""

    diff = _diff_entity_list([], [{"domain": "new.com"}], "domain")
    assert len(diff["created"]) == 1


#  _match_renamed_entities


def test_exact_rename() -> None:
    """Exact rename."""

    deleted = [{"name": "old", "mode": "http", "balance": "rr"}]
    created = [{"name": "new", "mode": "http", "balance": "rr"}]
    pairs = _match_renamed_entities(deleted, created, "name")
    assert len(pairs) == 1
    assert pairs[0][0]["name"] == "old"
    assert pairs[0][1]["name"] == "new"


def test_no_match_when_all_fields_differ() -> None:
    """No match when all fields differ."""

    deleted = [{"name": "old", "mode": "http", "balance": "rr"}]
    created = [{"name": "new", "mode": "tcp", "balance": "lc"}]
    pairs = _match_renamed_entities(deleted, created, "name")
    assert pairs == []


def test_threshold_boundary() -> None:
    """Exactly 50% match -> should be paired."""

    deleted = [{"name": "old", "a": "1", "b": "2"}]
    created = [{"name": "new", "a": "1", "b": "X"}]
    pairs = _match_renamed_entities(deleted, created, "name")
    # 1 out of 2 non-name fields match = 50%
    assert len(pairs) == 1


def test_below_threshold() -> None:
    """Below 50% match -> should NOT be paired."""

    deleted = [{"name": "old", "a": "1", "b": "2", "c": "3"}]
    created = [{"name": "new", "a": "X", "b": "Y", "c": "3"}]
    pairs = _match_renamed_entities(deleted, created, "name")
    # 1 out of 3 non-name fields match = 33% < 50%
    assert pairs == []


def test_multiple_renames_greedy() -> None:
    """Multiple renames greedy."""

    deleted = [
        {"name": "a", "mode": "http", "x": "1"},
        {"name": "b", "mode": "tcp", "x": "2"},
    ]
    created = [
        {"name": "b_new", "mode": "tcp", "x": "2"},
        {"name": "a_new", "mode": "http", "x": "1"},
    ]
    pairs = _match_renamed_entities(deleted, created, "name")
    assert len(pairs) == 2


def test_empty_lists() -> None:
    """Empty lists."""

    assert _match_renamed_entities([], [], "name") == []
    assert _match_renamed_entities([{"name": "a"}], [], "name") == []
    assert _match_renamed_entities([], [{"name": "a"}], "name") == []


#  compute_diff (integrated)


def test_empty_snapshots() -> None:
    """Empty snapshots."""

    diff = compute_diff({}, {})
    assert diff == {}


def test_identical_snapshots() -> None:
    """Identical snapshots."""

    snap = {
        "global_settings": [{"id": 1, "directive": "log", "value": "x", "sort_order": 0}],
        "backends": [{"name": "be1", "mode": "http"}],
    }
    diff = compute_diff(snap, dict(snap))
    assert diff == {}


def test_backend_renamed() -> None:
    """Backend renamed."""

    old = {"backends": [{"name": "accounts_dev", "mode": "http", "balance": "rr", "comment": None}]}
    new = {"backends": [{"name": "daccounts_dev", "mode": "http", "balance": "rr", "comment": None}]}
    diff = compute_diff(old, new)
    assert "backends" in diff
    assert diff["backends"]["created"] == []
    assert diff["backends"]["deleted"] == []
    assert len(diff["backends"]["updated"]) == 1
    assert diff["backends"]["updated"][0]["entity"] == "daccounts_dev"


def test_listen_block_renamed() -> None:
    """Listen block renamed."""

    old = {"listen_blocks": [{"name": "stats", "mode": "http", "balance": None, "content": "x", "comment": None}]}
    new = {"listen_blocks": [{"name": "statsc", "mode": "http", "balance": None, "content": "x", "comment": None}]}
    diff = compute_diff(old, new)
    be = diff["listen_blocks"]
    assert be["created"] == []
    assert be["deleted"] == []
    assert len(be["updated"]) == 1
    assert be["updated"][0]["entity"] == "statsc"


def test_peer_renamed() -> None:
    """Peer renamed."""

    old = {"peers": [{"name": "mypeers", "comment": None, "entries": []}]}
    new = {"peers": [{"name": "mypeersc", "comment": None, "entries": []}]}
    diff = compute_diff(old, new)
    p = diff["peers"]
    assert p["deleted"] == []
    assert p["created"] == []
    assert len(p["updated"]) == 1
    assert p["updated"][0]["entity"] == "mypeersc"


def test_acl_updated_with_composite_key() -> None:
    """Acl updated with composite key."""

    old = {"acl_rules": [{"frontend_name": "http", "domain": "example.com", "sort_order": 0, "comment": None}]}
    new = {"acl_rules": [{"frontend_name": "http", "domain": "example.com", "sort_order": 0, "comment": "updated"}]}
    diff = compute_diff(old, new)
    assert "acl_rules" in diff
    assert len(diff["acl_rules"]["updated"]) == 1
    assert diff["acl_rules"]["updated"][0]["entity"] == "http:example.com:0"


def test_ssl_cert_matched_by_domain() -> None:
    """Ssl cert matched by domain."""

    old = {"ssl_certificates": [{"domain": "example.com", "provider": "le"}]}
    new = {"ssl_certificates": [{"domain": "example.com", "provider": "manual"}]}
    diff = compute_diff(old, new)
    assert "ssl_certificates" in diff
    assert len(diff["ssl_certificates"]["updated"]) == 1
    assert diff["ssl_certificates"]["updated"][0]["entity"] == "example.com"


#  _parse_iso_datetime


def test_none_input() -> None:
    """None input."""

    assert _parse_iso_datetime(None) is None


def test_empty_string() -> None:
    """Empty string."""

    assert _parse_iso_datetime("") is None


def test_valid_iso_string() -> None:
    """Valid iso string."""

    from datetime import datetime

    result = _parse_iso_datetime("2025-06-15T10:30:00+00:00")
    assert result is not None
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 6
    assert result.day == 15
    assert result.tzinfo == UTC


def test_naive_iso_string() -> None:
    """Naive iso string."""

    from datetime import datetime

    result = _parse_iso_datetime("2025-01-01T00:00:00")
    assert result is not None
    assert isinstance(result, datetime)
    assert result.year == 2025

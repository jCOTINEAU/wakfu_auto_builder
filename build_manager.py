"""Manage saved builds: persist optimized equipment sets to a local JSON file."""

import json
import os
import uuid
from datetime import datetime
from typing import Optional


DEFAULT_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_builds.json")


def _load_file(path: str) -> list:
    """Read the JSON save file and return a list of builds."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
    if not isinstance(data, list):
        return []
    return data


def _write_file(path: str, data: list) -> None:
    """Write the list of builds to the JSON save file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_build(
    name: str,
    items: list,
    constraints: Optional[dict] = None,
    stats: Optional[list] = None,
    excluded_items: Optional[list] = None,
    profile_id: str = "",
    path: str = DEFAULT_SAVE_PATH,
) -> dict:
    """Save a build and return the created entry.

    Parameters
    ----------
    name : str
        User-chosen name for the build.
    items : list
        List of ``{"id": <int|str>, "name": <str>}`` dicts from the optimization.
    constraints : dict, optional
        Snapshot of constraint values (name -> value).
    stats : list, optional
        Snapshot of stat summary lines (list of ``{"effect": ..., "effectId": ..., "value": ...}``).
    excluded_items : list, optional
        List of item IDs excluded from the optimization.
    profile_id : str
        ID of the stat profile used during optimization (empty string if none).
    path : str
        File path for the JSON store.

    Returns
    -------
    dict
        The newly created build entry.
    """
    builds = _load_file(path)

    entry = {
        "id": str(uuid.uuid4()),
        "name": name.strip() or "Sans nom",
        "created_at": datetime.now().isoformat(),
        "items": items,
        "constraints": constraints or {},
        "stats": stats or [],
        "excluded_items": excluded_items or [],
        "profile_id": profile_id,
    }

    builds.append(entry)
    _write_file(path, builds)
    return entry


def list_builds(path: str = DEFAULT_SAVE_PATH) -> list:
    """Return all saved builds, newest first."""
    builds = _load_file(path)
    builds.sort(key=lambda b: b.get("created_at", ""), reverse=True)
    return builds


def get_build(build_id: str, path: str = DEFAULT_SAVE_PATH) -> Optional[dict]:
    """Return a single build by its id, or None."""
    for b in _load_file(path):
        if b.get("id") == build_id:
            return b
    return None


def delete_build(build_id: str, path: str = DEFAULT_SAVE_PATH) -> bool:
    """Delete a build by its id. Returns True if found and removed."""
    builds = _load_file(path)
    original_len = len(builds)
    builds = [b for b in builds if b.get("id") != build_id]
    if len(builds) == original_len:
        return False
    _write_file(path, builds)
    return True


def overwrite_build(
    build_id: str,
    items: list,
    constraints: Optional[dict] = None,
    stats: Optional[list] = None,
    excluded_items: Optional[list] = None,
    profile_id: str = "",
    path: str = DEFAULT_SAVE_PATH,
) -> Optional[dict]:
    """Overwrite an existing build's data while keeping its id and name.

    Parameters
    ----------
    build_id : str
        The id of the build to overwrite.
    items : list
        New item list.
    constraints : dict, optional
        New constraint snapshot.
    stats : list, optional
        New stat snapshot.
    excluded_items : list, optional
        List of item IDs excluded from the optimization.
    profile_id : str
        ID of the stat profile used during optimization.
    path : str
        File path for the JSON store.

    Returns
    -------
    dict or None
        The updated build entry, or None if `build_id` was not found.
    """
    builds = _load_file(path)
    for build in builds:
        if build.get("id") == build_id:
            build["items"] = items
            build["constraints"] = constraints or {}
            build["stats"] = stats or []
            build["excluded_items"] = excluded_items or []
            build["profile_id"] = profile_id
            build["created_at"] = datetime.now().isoformat()
            _write_file(path, builds)
            return build
    return None


def compare_builds(build_a: dict, build_b: dict) -> dict:
    """Compare two builds and return stat deltas and item differences.

    Parameters
    ----------
    build_a, build_b : dict
        Build entries as returned by ``get_build`` (must contain ``stats`` and ``items``).

    Returns
    -------
    dict
        ``stat_deltas``  – list of ``{"effect": str, "effectId": int, "valueA": int, "valueB": int, "delta": int}``
        ``items_added``  – items in B but not in A (by id)
        ``items_removed``– items in A but not in B (by id)
        ``items_common`` – items in both A and B (by id)
        ``name_a``, ``name_b`` – build names
    """
    stats_a = {s["effectId"]: s for s in (build_a.get("stats") or [])}
    stats_b = {s["effectId"]: s for s in (build_b.get("stats") or [])}

    all_effect_ids = sorted(set(stats_a.keys()) | set(stats_b.keys()))

    _MALUS_PREFIXES = ("Deboost", "Perte")

    stat_deltas = []
    for eid in all_effect_ids:
        sa = stats_a.get(eid)
        sb = stats_b.get(eid)
        val_a = sa["value"] if sa else 0
        val_b = sb["value"] if sb else 0
        label = (sa or sb)["effect"].rsplit(" : ", 1)[0]
        is_malus = any(label.startswith(p) for p in _MALUS_PREFIXES)
        stat_deltas.append({
            "effect": label,
            "effectId": eid,
            "valueA": val_a,
            "valueB": val_b,
            "delta": val_b - val_a,
            "isMalus": is_malus,
        })

    ids_a = {item["id"] for item in (build_a.get("items") or [])}
    ids_b = {item["id"] for item in (build_b.get("items") or [])}
    items_map_a = {item["id"]: item for item in (build_a.get("items") or [])}
    items_map_b = {item["id"]: item for item in (build_b.get("items") or [])}

    items_added = [items_map_b[i] for i in sorted(ids_b - ids_a)]
    items_removed = [items_map_a[i] for i in sorted(ids_a - ids_b)]
    items_common = [items_map_a[i] for i in sorted(ids_a & ids_b)]

    return {
        "name_a": build_a.get("name", "Build A"),
        "name_b": build_b.get("name", "Build B"),
        "stat_deltas": stat_deltas,
        "items_added": items_added,
        "items_removed": items_removed,
        "items_common": items_common,
    }

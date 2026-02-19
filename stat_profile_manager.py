"""Manage character stat profiles: persist base stat configurations to a local JSON file."""

import json
import math
import os
import uuid
from datetime import datetime
from typing import Optional


DEFAULT_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_stat_profiles.json")

DEFAULT_STATS = {
    "PV": 0,
    "PA": 6,
    "PM": 3,
    "PW": 6,
    "PO": 0,
    "controle": 0,
    "initiative": 0,
    "coupCritique": 0,
    "sagesse": 0,
    "PP": 0,
    "volonte": 0,
    "parade": 0,
    "tacle": 0,
    "esquive": 0,
    "resistance": 0,
    "maitriseElem": 0,
    "maitriseMelee": 0,
    "maitriseDistance": 0,
    "maitriseCritique": 0,
    "maitriseDos": 0,
    "maitriseBerserk": 0,
    "maitriseSoin": 0,
}

STAT_LABELS = {
    "PV": "Points de Vie",
    "PA": "PA",
    "PM": "PM",
    "PW": "PW",
    "PO": "Portée",
    "controle": "Contrôle",
    "initiative": "Initiative",
    "coupCritique": "Coup Critique (%)",
    "sagesse": "Sagesse",
    "PP": "Prospection",
    "volonte": "Volonté",
    "parade": "Parade",
    "tacle": "Tacle",
    "esquive": "Esquive",
    "resistance": "Résistance (%)",
    "maitriseElem": "Maîtrise élémentaire",
    "maitriseMelee": "Maîtrise mêlée",
    "maitriseDistance": "Maîtrise distance",
    "maitriseCritique": "Maîtrise critique",
    "maitriseDos": "Maîtrise dos",
    "maitriseBerserk": "Maîtrise berserk",
    "maitriseSoin": "Maîtrise soin",
}

def resistance_percent_to_raw(percent: float) -> float:
    """Convert a resistance percentage to raw resistance points (Wakfu formula).
    Formula: raw = 100 * log(1 - pct/100) / log(0.8)
    """
    if percent <= 0:
        return 0
    if percent >= 100:
        return 99999
    target = 1 - percent / 100
    return math.log(target, 0.8) * 100


CONSTRAINT_STAT_MAP = {
    "pvSelector": "PV",
    "paSelector": "PA",
    "pmSelector": "PM",
    "pwSelector": "PW",
    "pcSelector": "controle",
    "poSelector": "PO",
    "iniSelector": "initiative",
    "ccSelector": "coupCritique",
    "wisdomSelector": "sagesse",
    "ppSelector": "PP",
    "willSelector": "volonte",
    "blockSelector": "parade",
    "lockSelector": "tacle",
    "dodgeSelector": "esquive",
    "resConstraint": "resistance",
}


def _load_file(path: str) -> list:
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_profile(
    name: str,
    stats: Optional[dict] = None,
    path: str = DEFAULT_SAVE_PATH,
) -> dict:
    """Save a new stat profile. Missing stat keys are filled with defaults."""
    profiles = _load_file(path)

    merged_stats = dict(DEFAULT_STATS)
    if stats:
        for k, v in stats.items():
            if k in merged_stats:
                merged_stats[k] = v

    entry = {
        "id": str(uuid.uuid4()),
        "name": name.strip() or "Sans nom",
        "created_at": datetime.now().isoformat(),
        "stats": merged_stats,
    }

    profiles.append(entry)
    _write_file(path, profiles)
    return entry


def list_profiles(path: str = DEFAULT_SAVE_PATH) -> list:
    """Return all saved profiles, newest first."""
    profiles = _load_file(path)
    profiles.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return profiles


def get_profile(profile_id: str, path: str = DEFAULT_SAVE_PATH) -> Optional[dict]:
    """Return a single profile by its id, or None."""
    for p in _load_file(path):
        if p.get("id") == profile_id:
            return p
    return None


def delete_profile(profile_id: str, path: str = DEFAULT_SAVE_PATH) -> bool:
    """Delete a profile by its id. Returns True if found and removed."""
    profiles = _load_file(path)
    original_len = len(profiles)
    profiles = [p for p in profiles if p.get("id") != profile_id]
    if len(profiles) == original_len:
        return False
    _write_file(path, profiles)
    return True


def overwrite_profile(
    profile_id: str,
    stats: Optional[dict] = None,
    name: Optional[str] = None,
    path: str = DEFAULT_SAVE_PATH,
) -> Optional[dict]:
    """Overwrite an existing profile's stats (and optionally name).

    Returns the updated entry, or None if not found.
    """
    profiles = _load_file(path)
    for profile in profiles:
        if profile.get("id") == profile_id:
            if name is not None:
                profile["name"] = name.strip() or profile["name"]
            if stats is not None:
                merged = dict(DEFAULT_STATS)
                for k, v in stats.items():
                    if k in merged:
                        merged[k] = v
                profile["stats"] = merged
            profile["created_at"] = datetime.now().isoformat()
            _write_file(path, profiles)
            return profile
    return None

"""Fetch and compute character base stats from a Zenith Wakfu build URL.

Two API calls are made:
  GET /statistics/:link  — base_stats per stat (game defaults, e.g. PA base = 6)
  GET /aptitudes/:link   — aptitude investments (value × pivot.base = raw contribution)

Total stat = base_stats + Σ(aptitude.value × stat.pivot.base)
This replicates the computation the Zenith frontend does client-side.
"""

import json
import socket
import urllib.request
import urllib.error

ZENITH_API_BASE = "https://api.zenithwakfu.com/builder/api"
_HEADERS = {
    "Host": "api.zenithwakfu.com",
    "Origin": "https://www.zenithwakfu.com",
    "Referer": "https://www.zenithwakfu.com/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0",
}

# Zenith id_stats → our stat profile key.
# "_res_raw" is a sentinel: accumulate raw resistance then convert to %.
# NOTE: per-element mastery (fire=122, water=124, earth=123, air=125) is intentionally
# NOT mapped here — it only comes from equipment effects, not from aptitudes, and must
# not be conflated with maitriseElem (id_stats=120) which is the all-elements bonus.
_ID_STATS_MAP = {
    20:   "PV",
    31:   "PA",
    41:   "PM",
    160:  "PO",
    191:  "PW",
    184:  "controle",
    171:  "initiative",
    150:  "coupCritique",
    166:  "sagesse",
    162:  "PP",
    177:  "volonte",
    875:  "parade",
    173:  "tacle",
    175:  "esquive",
    80:   "_res_raw",        # elemental resistance (raw) → converted to %
    120:  "maitriseElem",    # all-elements mastery bonus
    26:   "maitriseSoin",
    149:  "maitriseCritique",
    180:  "maitriseDos",
    1052: "maitriseMelee",
    1053: "maitriseDistance",
    1055: "maitriseBerserk",
}

# Aptitudes whose effect is a HP multiplier — skip, we can't map them to a flat stat.
_SPECIAL_APTITUDE_IDS = {1, 5}


def extract_link_id(url: str) -> str:
    """Return the short build ID from any Zenith URL or bare ID."""
    return url.strip().rstrip("/").split("/")[-1]


def _get(path: str) -> object:
    req = urllib.request.Request(f"{ZENITH_API_BASE}/{path}", headers=_HEADERS)
    # Bypass system proxies — macOS/Qt proxy detection causes DNS failures inside Qt apps.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=15) as r:
            return json.load(r)
    except urllib.error.URLError as e:
        # macOS/Qt: the first DNS lookup from a fresh background thread occasionally
        # fails with EAI_NONAME (errno 8) before the resolver is warmed up.
        # One retry is enough — the second call always succeeds.
        if isinstance(e.reason, socket.gaierror):
            with opener.open(req, timeout=15) as r:
                return json.load(r)
        raise


def _raw_res_to_percent(raw: float) -> float:
    """Convert raw Wakfu resistance to % — inverse of resistance_percent_to_raw."""
    if raw <= 0:
        return 0.0
    return (1.0 - 0.8 ** (raw / 100.0)) * 100.0


def fetch_zenith_stats(link_id: str) -> dict:
    """
    Return:
      {
        "stats":           dict  (stat_key → int, matches DEFAULT_STATS keys),
        "has_equipment":   bool,
        "equipment_count": int,
        "error":           str   (empty on success),
      }
    """
    from stat_profile_manager import DEFAULT_STATS

    try:
        # ── 1. Check equipment presence ────────────────────────────────────
        build_data = _get(f"build/{link_id}")
        equipment_count = len(build_data.get("equipments", []))

        # ── 2. Fetch raw data ───────────────────────────────────────────────
        statistics_raw = _get(f"statistics/{link_id}")["statistics"]
        aptitudes_raw  = _get(f"aptitudes/{link_id}")

        # ── 3. Compute totals keyed by id_stats ────────────────────────────
        # Seed with base_stats from the statistics endpoint
        totals: dict[int, float] = {}
        for key_str, stat in statistics_raw.items():
            totals[int(key_str)] = float(stat.get("base_stats") or 0)

        # Add aptitude contributions: value × pivot.base
        for apt_type in aptitudes_raw:
            for apt in apt_type.get("aptitudes", []):
                value = apt.get("value") or 0
                if value <= 0:
                    continue
                if apt["id_aptitude"] in _SPECIAL_APTITUDE_IDS:
                    continue
                for stat in apt.get("stats", []):
                    id_stats   = stat["id_stats"]
                    pivot_base = stat["pivot"]["base"]
                    totals[id_stats] = totals.get(id_stats, 0) + value * pivot_base

        # ── 4. Map id_stats → stat profile keys ───────────────────────────
        result      = dict(DEFAULT_STATS)
        res_raw_acc = 0.0

        for id_stats, total in totals.items():
            key = _ID_STATS_MAP.get(id_stats)
            if key is None:
                continue
            if key == "_res_raw":
                res_raw_acc += total
            elif key in result:
                result[key] = int(round(total))

        if res_raw_acc > 0:
            result["resistance"] = int(round(_raw_res_to_percent(res_raw_acc)))

        return {
            "stats":           result,
            "has_equipment":   equipment_count > 0,
            "equipment_count": equipment_count,
            "error":           "",
        }

    except urllib.error.HTTPError as e:
        return {"stats": {}, "has_equipment": False, "equipment_count": 0,
                "error": f"HTTP {e.code} — build introuvable ou privé ?"}
    except Exception as e:
        return {"stats": {}, "has_equipment": False, "equipment_count": 0,
                "error": str(e)}


def import_zenith_build(url: str) -> dict:
    link_id = extract_link_id(url)
    if not link_id:
        return {"stats": {}, "has_equipment": False, "equipment_count": 0,
                "error": "URL invalide"}
    return fetch_zenith_stats(link_id)

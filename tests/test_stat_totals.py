"""Tests for stat_totals.compute_totals.

Uses conftest.make_item to build mock items with specific effect params.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import settings
from settings import simpleActionEnum as SA
from settings import paramsActionEnum as PA
from stat_totals import compute_totals, _distribute_variable_bonus

from tests.conftest import make_item


def _load_items(items):
    settings.ITEMS_DATA = {i["definition"]["item"]["id"]: i for i in items}


# ─── Case A / B / C for the variable bonus distribution ──────────────────


class TestDistributeVariableBonus:
    def test_case_A_N_geq_4_all_elements(self):
        rr = [0]
        result = _distribute_variable_bonus(50, 4, {"fire", "air"}, rr)
        assert result == {"fire": 50, "water": 50, "air": 50, "earth": 50}

    def test_case_A_N_greater_than_4_still_all(self):
        rr = [0]
        result = _distribute_variable_bonus(50, 6, {"fire"}, rr)
        assert result == {"fire": 50, "water": 50, "air": 50, "earth": 50}

    def test_case_B_all_chosen_plus_non_chosen(self):
        """U=2, N=3 → 2 chosen + 1 non-chosen (canonical order fire→water→air→earth)."""
        rr = [0]
        result = _distribute_variable_bonus(50, 3, {"fire", "air"}, rr)
        assert result == {"fire": 50, "air": 50, "water": 50}
        # earth is NOT in the result — only 3 slots filled.
        assert "earth" not in result

    def test_case_B_all_chosen_plus_earth_when_water_air_chosen(self):
        """{water, air} chosen, N=3 → water, air, fire (fire before earth in canonical order)."""
        rr = [0]
        result = _distribute_variable_bonus(50, 3, {"water", "air"}, rr)
        assert result == {"water": 50, "air": 50, "fire": 50}

    def test_case_C_N_less_than_U_round_robin(self):
        """3 chosen (fire, water, air canonical), N=1 → first chosen gets +X."""
        rr = [0]
        result = _distribute_variable_bonus(50, 1, {"fire", "water", "air"}, rr)
        assert result == {"fire": 50}
        assert rr[0] == 1

    def test_case_C_round_robin_advances(self):
        rr = [0]
        # First call: N=1 → hits fire, counter → 1
        _distribute_variable_bonus(50, 1, {"fire", "air"}, rr)
        # Second: hits air (counter=1 % 2 = 1)
        r2 = _distribute_variable_bonus(50, 1, {"fire", "air"}, rr)
        assert r2 == {"air": 50}
        # Third: hits fire again
        r3 = _distribute_variable_bonus(50, 1, {"fire", "air"}, rr)
        assert r3 == {"fire": 50}

    def test_case_C_N_2_U_3_two_of_three_chosen(self):
        rr = [0]
        result = _distribute_variable_bonus(50, 2, {"fire", "water", "air"}, rr)
        # First 2 in canonical order among chosen: fire, water
        assert result == {"fire": 50, "water": 50}

    def test_zero_chosen_no_distribution(self):
        """No chosen elements: variable bonuses are 'pending' — don't
        distribute anything, so per-element display isn't flattened by
        phantom bonuses. User must pick at least one element to unlock
        the variable-bonus contribution."""
        rr = [0]
        result = _distribute_variable_bonus(50, 2, set(), rr)
        assert result == {}

    def test_zero_chosen_still_all_when_N_geq_4(self):
        """N>=4 means 'applies to all 4' regardless of the user's choice —
        that bonus is unambiguous."""
        rr = [0]
        result = _distribute_variable_bonus(50, 4, set(), rr)
        assert result == {"fire": 50, "water": 50, "air": 50, "earth": 50}


# ─── compute_totals — high-level integration ──────────────────────────────


class TestComputeTotals:
    def test_empty_build(self):
        _load_items([])
        r = compute_totals([])
        assert all(v == 0 for v in r["elem_mastery"].values())
        assert all(v == 0 for v in r["attributes"].values())
        assert r["cumulated_mastery"]["total"] == 0

    def test_single_item_single_stat(self):
        item = make_item(1, 200, 134, 4, {int(SA.PV_ADD): [500, 0]})
        _load_items([item])
        r = compute_totals([1])
        assert r["attributes"]["PV"] == 500

    def test_fire_mastery_add_only_fire(self):
        item = make_item(1, 200, 134, 4, {int(SA.FIRE_MASTERY_ADD): [100, 0]})
        _load_items([item])
        r = compute_totals([1])
        assert r["elem_mastery"]["fire"] == 100
        assert r["elem_mastery"]["water"] == 0
        assert r["elem_mastery"]["air"] == 0
        assert r["elem_mastery"]["earth"] == 0

    def test_all_elem_bonus_adds_to_every_element(self):
        item = make_item(1, 200, 134, 4, {int(SA.ELEM_MASTERY_ADD): [50, 0]})
        _load_items([item])
        r = compute_totals([1])
        assert r["elem_mastery"]["fire"] == 50
        assert r["elem_mastery"]["water"] == 50
        assert r["elem_mastery"]["air"] == 50
        assert r["elem_mastery"]["earth"] == 50

    def test_variable_bonus_N_4_all_elements(self):
        item = make_item(1, 200, 134, 4, {int(PA.RANDOM_NUMBER_MASTERY_ADD): [30, 0, 4]})
        _load_items([item])
        r = compute_totals([1], chosen_elements=["fire", "air"])
        assert r["elem_mastery"]["fire"] == 30
        assert r["elem_mastery"]["water"] == 30
        assert r["elem_mastery"]["air"] == 30
        assert r["elem_mastery"]["earth"] == 30

    def test_variable_bonus_N_2_matches_U_2(self):
        item = make_item(1, 200, 134, 4, {int(PA.RANDOM_NUMBER_MASTERY_ADD): [40, 0, 2]})
        _load_items([item])
        r = compute_totals([1], chosen_elements=["fire", "air"])
        assert r["elem_mastery"]["fire"] == 40
        assert r["elem_mastery"]["air"] == 40
        assert r["elem_mastery"]["water"] == 0
        assert r["elem_mastery"]["earth"] == 0

    def test_variable_bonus_N_3_case_B(self):
        """U=2, N=3 → fire + air (chosen) + water (canonical first non-chosen)."""
        item = make_item(1, 200, 134, 4, {int(PA.RANDOM_NUMBER_MASTERY_ADD): [40, 0, 3]})
        _load_items([item])
        r = compute_totals([1], chosen_elements=["fire", "air"])
        assert r["elem_mastery"]["fire"] == 40
        assert r["elem_mastery"]["air"] == 40
        assert r["elem_mastery"]["water"] == 40
        assert r["elem_mastery"]["earth"] == 0

    def test_variable_bonus_round_robin_across_items(self):
        """3 items each giving +20 in 1 elem, U=2 (fire, air):
        Item 1 → fire (counter 0→1)
        Item 2 → air  (counter 1→2)
        Item 3 → fire (counter 2→3)
        Result: fire=+40, air=+20.
        """
        items = [
            make_item(i, 200, 134, 4, {int(PA.RANDOM_NUMBER_MASTERY_ADD): [20, 0, 1]})
            for i in range(1, 4)
        ]
        _load_items(items)
        r = compute_totals([1, 2, 3], chosen_elements=["fire", "air"])
        assert r["elem_mastery"]["fire"] == 40
        assert r["elem_mastery"]["air"] == 20
        assert r["elem_mastery"]["water"] == 0
        assert r["elem_mastery"]["earth"] == 0

    def test_profile_maitrise_elem_added_to_all(self):
        _load_items([])
        r = compute_totals([], base_profile_stats={"maitriseElem": 200})
        for elem in ("fire", "water", "air", "earth"):
            assert r["elem_mastery"][elem] == 200

    def test_profile_attributes_added(self):
        item = make_item(1, 200, 134, 4, {int(SA.PA_ADD): [2, 0]})
        _load_items([item])
        r = compute_totals([1], base_profile_stats={"PA": 6, "PM": 3})
        assert r["attributes"]["PA"] == 8    # 6 profile + 2 item
        assert r["attributes"]["PM"] == 3    # 3 profile + 0 item

    def test_non_elem_mastery_sums_with_profile(self):
        item = make_item(1, 200, 134, 4, {int(SA.MELEE_MASTERY_ADD): [80, 0]})
        _load_items([item])
        r = compute_totals([1], base_profile_stats={"maitriseMelee": 100})
        assert r["non_elem_mastery"]["melee"] == 180

    def test_resistance_pct_conversion(self):
        item = make_item(1, 200, 134, 4, {int(SA.FIRE_RES_ADD): [100, 0]})
        _load_items([item])
        r = compute_totals([1])
        assert r["elem_res_raw"]["fire"] == 100
        # 1 - 0.8^1 = 0.2 → 20%
        assert r["elem_res_pct"]["fire"] == 20.0

    def test_cumulated_uses_max_elem(self):
        """Fire > air after equipment → top_elem = fire."""
        item = make_item(1, 200, 134, 4, {
            int(SA.FIRE_MASTERY_ADD): [200, 0],
            int(SA.AIR_MASTERY_ADD):  [50, 0],
        })
        _load_items([item])
        r = compute_totals([1], chosen_elements=["fire", "air"])
        assert r["cumulated_mastery"]["top_elem"] == "fire"
        assert r["cumulated_mastery"]["top_value"] == 200

    def test_cumulated_adds_selected_masteries(self):
        item = make_item(1, 200, 134, 4, {
            int(SA.FIRE_MASTERY_ADD):  [500, 0],
            int(SA.CRIT_MASTERY_ADD):  [200, 0],
            int(SA.MELEE_MASTERY_ADD): [150, 0],
            int(SA.BACK_MASTERY_ADD):  [100, 0],
        })
        _load_items([item])
        r = compute_totals([1],
                           chosen_elements=["fire"],
                           added_masteries=["crit", "melee"])
        # top_elem=fire=500, added crit(200) + melee(150). Back not added.
        assert r["cumulated_mastery"]["top_value"] == 500
        assert r["cumulated_mastery"]["added"] == {"crit": 200, "melee": 150}
        assert r["cumulated_mastery"]["total"] == 850

    def test_missing_item_id_skipped(self):
        """Stale saved builds may reference IDs no longer in ITEMS_DATA."""
        item = make_item(1, 200, 134, 4, {int(SA.PV_ADD): [100, 0]})
        _load_items([item])
        r = compute_totals([1, 99999], base_profile_stats={"PV": 200})
        assert r["attributes"]["PV"] == 300

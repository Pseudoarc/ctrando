"""
Module for randomizing tech order, tech damage, and so on.
"""
import bisect
import math
from typing import Callable, Union

from ctrando.arguments.techoptions import TechOrder, TechDamage, TechOptions
from ctrando.attacks import pctech, cttechtypes as ctt
from ctrando.common import ctenums
from ctrando.common.random import RNGType


def randomize_tech_order(
        tech_manager: pctech.PCTechManager,
        tech_order_scheme: TechOrder,
        preserve_first_magic_tech: bool,
        rng: RNGType
):
    """
    Randomizer the single tech order of the tech_manager.
    Assumes a vanilla initial order.

    Returns dict[CharID, tuple[int, ...]] of permutations
    """

    ret_dict = {
        char_id: tuple(range(8)) for char_id in ctenums.CharID
    }

    if tech_order_scheme == TechOrder.VANILLA:
        return ret_dict

    first_magic_tech_dict: dict[ctenums.CharID, ctenums.TechID] = {
        ctenums.CharID.CRONO: ctenums.TechID.LIGHTNING,
        ctenums.CharID.MARLE: ctenums.TechID.ICE,
        ctenums.CharID.LUCCA: ctenums.TechID.FLAME_TOSS,
        ctenums.CharID.ROBO: ctenums.TechID.LASER_SPIN,
        ctenums.CharID.FROG: ctenums.TechID.WATER,
        ctenums.CharID.AYLA: ctenums.TechID.TAIL_SPIN,
        ctenums.CharID.MAGUS: ctenums.TechID.LIGHTNING_2_M,
    }

    for pc_id in ctenums.CharID:
        start_tech_id = 1 + pc_id*8
        end_tech_id = start_tech_id + 8

        permutation = list(range(8))
        if tech_order_scheme == TechOrder.RANDOM:
            permutation = list(range(8))
            rng.shuffle(permutation)
        elif tech_order_scheme == TechOrder.MP_ORDER:
            mps = [
                tech_manager.get_tech(tech_id).effect_mps[0]
                for tech_id in range(start_tech_id, end_tech_id)
            ]
            permutation = list(range(8))
            permutation = sorted(permutation, key=lambda x: mps[x])
        elif tech_order_scheme == TechOrder.MP_TYPE_ORDER:
            mps = [
                tech_manager.get_tech(tech_id).effect_mps[0]
                for tech_id in range(start_tech_id, end_tech_id)
            ]

            damage_types = (ctt.EffectType.DAMAGE, ctt.EffectType.MULTIHIT)
            heal_types = (ctt.EffectType.HEALING, ctt.EffectType.HEALSTATUS)
            damage_ids = [
                tech_id-start_tech_id for tech_id in range(start_tech_id, end_tech_id)
                if tech_manager.get_tech(tech_id).effect_headers[0].effect_type in damage_types
            ]
            sorted_damage_ids = sorted(damage_ids, key=lambda x: mps[x])

            heal_ids = [
                tech_id-start_tech_id for tech_id in range(start_tech_id, end_tech_id)
                if tech_manager.get_tech(tech_id).effect_headers[0].effect_type in heal_types
            ]
            sorted_heal_ids = sorted(heal_ids, key=lambda x: mps[x])

            other_ids = [
                tech_id-start_tech_id for tech_id in range(start_tech_id, end_tech_id) if
                tech_id-start_tech_id not in damage_ids and tech_id-start_tech_id not in heal_ids
            ]
            sorted_other_ids = sorted(other_ids, key=lambda x: mps[x])

            permutation = [0 for ind in range(8)]
            for ind in range(8):
                if ind in damage_ids:
                    permutation[ind] = sorted_damage_ids.pop(0)
                elif ind in heal_ids:
                    permutation[ind] = sorted_heal_ids.pop(0)
                else:
                    permutation[ind] = sorted_other_ids.pop(0)

            preserve_first_magic_tech = False
        else:
            raise ValueError

        if preserve_first_magic_tech:
            first_magic_index = first_magic_tech_dict[pc_id] - start_tech_id
            first_magic_index_new = permutation.index(first_magic_index)

            permutation[first_magic_index_new], permutation[first_magic_index] = \
                permutation[first_magic_index], permutation[first_magic_index_new]

        tech_manager.reorder_single_techs(pc_id, permutation)
        ret_dict[pc_id] = tuple(permutation)

    return ret_dict


# Sketchy math was performed to come up with these.
_scale_dict: dict[ctt.DamageFormula, Callable[[int], Union[int, float]]] = {
    ctt.DamageFormula.MAGIC: lambda mp: 1.88*mp+4.34,
    ctt.DamageFormula.PC_MELEE: lambda mp: math.sqrt(55.6*mp + 65.8),
    ctt.DamageFormula.PC_RANGED: lambda mp: math.sqrt(55.6*mp + 65.8),
    ctt.DamageFormula.PC_AYLA: lambda mp: math.sqrt(62.6*mp + 134),
    ctt.DamageFormula.MISSING_HP: lambda mp: mp+3
}


def modify_all_single_tech_powers(
        tech_manager: pctech.PCTechManager,
        tech_options: TechOptions,
        rng: RNGType
):
    """
    Reassign every single tech's mp and power.
    - Status spells (e.g. Provoke, Hypno Wave, Protect, and Magic Wall) are ignored.
    - Revive spells are ignored
    - Charm is ignored
    """

    def is_non_revive_heal(effect: ctt.PCTechEffectHeader) -> bool:
        if effect.effect_type not in (ctt.EffectType.HEALSTATUS, ctt.EffectType.HEALING):
            return False

        if (
                effect.effect_type == ctt.EffectType.HEALSTATUS and
                effect.will_revive
        ):
            return False

        return True

    tech_dict = tech_manager.get_all_techs()

    heal_tech_ids: list[int] = [
        ind for ind, tech in tech_dict.items()
        if ind < 1 + 7*8 and is_non_revive_heal(tech.effect_headers[0])
    ]
    heal_tech_mps: list[int] = [tech_dict[ind].effect_mps[0] for ind in heal_tech_ids]

    damage_tech_ids: list[int] = [
        ind for ind, tech in tech_dict.items()
        if tech.effect_headers[0].effect_type in (ctt.EffectType.DAMAGE, ctt.EffectType.MULTIHIT)
        and ind < 1 + 7 * 8
    ]
    damage_tech_mps: list[int] = [tech_dict[ind].effect_mps[0] for ind in damage_tech_ids]

    if tech_options.tech_damage == TechDamage.SHUFFLE:
        rng.shuffle(heal_tech_mps)
        rng.shuffle(damage_tech_mps)
    elif tech_options.tech_damage == TechDamage.RANDOM:
        damage_tech_mps = rng.choices(list(damage_tech_mps), k=len(damage_tech_mps))
        heal_tech_mps = rng.choices(list(heal_tech_mps), k=len(heal_tech_mps))

    min_mod = tech_options.tech_damage_random_factor_min
    max_mod = tech_options.tech_damage_random_factor_max

    if max_mod == min_mod:
        def random_mp_mod() -> float:
            return max_mod
    else:
        min_mod = math.log(min_mod)
        max_mod = math.log(max_mod)

        def random_mp_mod() -> float:
            val = min_mod + rng.random()*(max_mod-min_mod)
            return math.exp(val)

    damage_tech_mps = [
        round(mp * random_mp_mod()) for mp in damage_tech_mps
    ]
    if tech_options.balance_tech_mps:
        balance_tech_powers(damage_tech_ids, damage_tech_mps, rng)

    heal_tech_mps = [
        round(mp * random_mp_mod()) for mp in heal_tech_mps
    ]

    for mp, tech_id in zip(heal_tech_mps+damage_tech_mps, heal_tech_ids+damage_tech_ids):
        modify_single_tech_power(tech_dict[tech_id], mp)

    for tech_id in range(1+7*8, tech_manager.num_techs+1):
        if tech_id not in tech_dict:
            continue
        tech = tech_dict[tech_id]
        for ind, pc_id in enumerate(tech.battle_group):
            if pc_id == 0xFF:
                continue

            pc_effect_id = tech.control_header.get_effect_index(ind)
            if (pc_effect_id - 1) // 8 == pc_id:  # This is a normal effect reference.
                tech.effect_headers[ind] = tech_dict[pc_effect_id].effect_headers[0].get_copy()
                tech.effect_mps[ind] = tech_dict[pc_effect_id].effect_mps[0]
            else:  # We have to deduce what special effect is in use.
                # Use the menu MP req to look up the
                mp_req = tech.get_menu_mp_requirement(pc_id)
                base_tech = tech_dict[mp_req]
                base_effect = base_tech.effect_headers[0]
                base_mp = base_tech.effect_mps[0]

                if base_effect.effect_type == ctt.EffectType.MULTIHIT:
                    # Confuse and Triple Kick -- Just copy over power/mp
                    tech.effect_headers[ind].power = base_effect.power
                elif (
                        base_effect.effect_type == ctt.EffectType.DAMAGE and
                        base_effect.has_slurpcut_restriction
                ):
                    # Slurpcut -- Just copy over power/mp
                    tech.effect_headers[ind].power = base_effect.power
                elif (
                    tech.effect_headers[ind].effect_type == ctt.EffectType.HEALSTATUS and
                    base_effect.effect_type == ctt.EffectType.HEALSTATUS
                ):
                    # Trying to detect kiss --> slurpkiss.
                    # should get twice Kiss's power.  This is one where we'd like a higher max.
                    new_power = sorted([1, 2*base_effect.heal_power, 0x1F])[1]
                    tech.effect_headers[ind].heal_power = new_power
                elif (
                        base_effect.effect_type == ctt.EffectType.DAMAGE and
                        base_effect.damage_formula_id == ctt.DamageFormula.MISSING_HP
                ):
                    # Trying to detect Frog Squash --> Grand Dream
                    # Should get 2.4x Frog Squash's power.
                    new_power = sorted([1, round(2.4*base_effect.power), 0xFF])[1]
                    tech.effect_headers[ind].power = new_power

                # Regardless, copy the new MP over.
                tech.effect_mps[ind] = base_mp

    for tech_id, tech in tech_dict.items():
        tech_manager.set_tech_by_id(tech, tech_id)


def modify_single_tech_power(
        tech: pctech.PCTech,
        new_mp: int
):
    effect_header = tech.effect_headers[0]
    effect_type = effect_header.effect_type
    orig_mp = tech.effect_mps[0]

    if effect_type in (ctt.EffectType.HEALING, ctt.EffectType.HEALSTATUS):
        def scale_function(mp: float) -> float:
            return 4.42*mp + 2.54

        old_power = effect_header.heal_power
        new_power = round(effect_header.heal_power*scale_function(new_mp)/scale_function(orig_mp))
        new_power = sorted([1, new_power, 0x1F])[1]
        effect_header.heal_power = new_power

    elif effect_type == ctt.EffectType.STATUS:
        # For now no change to status effects, positive or negative.
        # Hard to imagine what exactly would change for these effects.
        pass
    elif effect_type in (ctt.EffectType.DAMAGE, ctt.EffectType.MULTIHIT):
        damage_formula = effect_header.damage_formula_id
        scale_function = _scale_dict[damage_formula]
        new_power = round(effect_header.power*scale_function(new_mp)/scale_function(orig_mp))
        new_power = sorted([1, new_power, 0xFF])[1]
        effect_header.power = new_power
        pass
    elif effect_type == ctt.EffectType.STEAL:
        pass

    tech.effect_mps[0] = new_mp


def balance_tech_powers(
        tech_ids: list[int],
        tech_mps: list[int],
        rng: RNGType
):
    def get_tech_pc(tech: int):
        return ctenums.CharID((tech - 1) // 8)

    char_tech_count: dict[ctenums.CharID, int] = {
        char_id: 0 for char_id in ctenums.CharID
    }

    for tech_id in tech_ids:
        char_id = get_tech_pc(tech_id)
        char_tech_count[char_id] += 1

    char_sorted_tech_ids = sorted(tech_ids, key=get_tech_pc)
    power_sorted_mps = sorted(tech_mps)

    char_assigned_mps: dict[ctenums.CharID, list[int]] = {
        char_id: [] for char_id in ctenums.CharID
    }

    top_7 = [power_sorted_mps.pop() for _ in range(7)]
    random_chars = list(ctenums.CharID)
    rng.shuffle(random_chars)
    min_val, max_val = top_7[-1], top_7[0]


    for char_id in random_chars:
        top_mp = top_7.pop()
        char_assigned_mps[char_id].append(top_mp)

        if (top_mp/max_val) <= 0.90 and char_tech_count[char_id] > 1:
            ind = bisect.bisect_left(power_sorted_mps, 8)
            ind = min(ind, len(power_sorted_mps)-1)
            char_assigned_mps[char_id].append(power_sorted_mps.pop(ind))

    rng.shuffle(power_sorted_mps)
    for char_id in random_chars:
        num_techs_needed = char_tech_count[char_id] - len(char_assigned_mps[char_id])
        for _ in range(num_techs_needed):
            char_assigned_mps[char_id].append(power_sorted_mps.pop())

    if power_sorted_mps:
        raise ValueError

    new_powers = []
    for char_id, powers in char_assigned_mps.items():
        rng.shuffle(powers)
        new_powers.extend(powers)

    tech_ids[:] = char_sorted_tech_ids
    tech_mps[:] = new_powers

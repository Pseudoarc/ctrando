"""Module which replaces tech descriptions with useful information."""

from __future__ import annotations

import enum
import typing
from typing import Union

from ctrando.common import ctenums
from ctrando.common.ctenums import Element
from ctrando.strings import ctstrings

from ctrando.attacks import cttechtypes
from ctrando.attacks.pctech import PCTechManager, TechNotFoundException

from ctrando.items import itemdata


_elem_str_abbrev = {
    Element.FIRE: 'Fi',
    Element.ICE: 'Wa',
    Element.LIGHTNING: 'Li',
    Element.SHADOW: 'Sh',
    Element.NONELEMENTAL: 'NE'
}

_target_str_dict = {
    0: '1',  # '1 PC',
    1: 'All',  # 'All PCs2',
    2: 'Self',
    3: '1',  # '1 PC',  # Dead
    4: 'All',  # 'All PCs4',
    5: 'Ayla',
    6: 'Frog',
    7: '1',  # '1 En7',
    8: 'All',  # 'All En',
    9: 'All',
    0xA: 'All',  # 'All PCsA',
    0xB: 'Line',  # 'Thru Line',
    0xC: 'Line',  # 'In Line',
    0xD: 'AoE',  # Arnd. En',
    0xE: '1',  # '1 EnE',
    0xF: 'Hori Ln',
    0x10: '1',  # '1 En10',
    0x11: 'AoE Self',  # 'Arnd self',
    0x12: 'AoE',  # 'Arnd En',
    0x13: 'AoE-Ro',  # 'Arnd Robo13',
    0x14: 'AoE-Ro',  # 'Arnd Robo14',
    0x15: '1',  # '1 En14',
    0x16: '1',  # '1 En15',
    0x17: '1 En17',
    0x18: '1',  # 'Arnd En18',
    0x19: '1',  # '1 En19',
    0x1A: 'AoE',  # 'Arnd En1A',
    0x1B: 'AoE-Mg',  # 'Arnd Magus',
    0x1C: '1',  # '1 En1C',
    0x1D: '1',  # '1 En1D',
    0x1E: '1',  # '1 En1E',
    0x1F: '1',  # '1 En1F',
    0x20: '1',  # '1 En1G',
}


def get_target_str(target: cttechtypes.TargetData):
    target_type = target[0] & 0x7F
    return _target_str_dict[target_type]


def get_elem_str(control: cttechtypes.ControlHeader):
    element = control.element
    if control.is_physical and element == Element.NONELEMENTAL:
        return 'Ph'
    return _elem_str_abbrev[element]


_status_abbrev_dict_dict: dict[typing.Any, dict[typing.Any, str]] = {
    ctenums.StatusEffect: {
        ctenums.StatusEffect.BLIND: 'Blind',
        ctenums.StatusEffect.CHAOS: 'Chaos',
        ctenums.StatusEffect.LOCK: 'Lock',
        ctenums.StatusEffect.POISON: 'Psn',
        ctenums.StatusEffect.SLEEP: 'Slp',
        ctenums.StatusEffect.SLOW: 'Slow',
        ctenums.StatusEffect.STOP: 'Stop',
    },
    itemdata.Type_05_Buffs: {
        itemdata.Type_05_Buffs.GREENDREAM: 'Reraise',
        itemdata.Type_08_Buffs.EVADE: '2xEvd',
    },
    itemdata.Type_08_Buffs: {
        itemdata.Type_08_Buffs.HASTE: 'Haste',
    },
    itemdata.Type_09_Buffs: {
        itemdata.Type_09_Buffs.SHIELD: 'Shld',
        itemdata.Type_09_Buffs.BARRIER: 'Bar',
        itemdata.Type_09_Buffs.BERSERK: 'Brsk',
        itemdata.Type_09_Buffs.MP_REGEN: 'MP-reg',
        itemdata.Type_09_Buffs.SHADES: '+25% Dmg',
        itemdata.Type_09_Buffs.SPECS: '+50% Dmg',
    }
}


def parse_status_effect(status_type: int, status_bits: int) -> str:

    buffs: Union[list[ctenums.StatusEffect], list[itemdata.Type_08_Buffs],
                 list[itemdata.Type_09_Buffs], list[itemdata.Type_05_Buffs]]

    status_dict: dict[int: enum.IntEnum] = {
        1: ctenums.StatusEffect,
        3: itemdata.Type_08_Buffs,
        4: itemdata.Type_09_Buffs,
        5: itemdata.Type_05_Buffs,
    }
    buff_type = status_dict[status_type]
    abbrev_dict = _status_abbrev_dict_dict[buff_type]
    buffs = [x for x in list(buff_type) if (status_bits & x)]
    ret_str = "/".join(abbrev_dict[buff] for buff in buffs)

    return ret_str


def get_effect_string(effect: cttechtypes.EffectHeader):
    eff_type = effect.effect_type
    ET = cttechtypes.EffectType

    heal_pow: Union[int, str]
    if eff_type == ET.HEALING:
        heal_pow = effect.heal_power
        if heal_pow == 0xF:
            heal_pow = 'All'
        else:
            heal_pow = f'Mg({heal_pow})'
        return f'Heals {heal_pow} HP'
    if eff_type == ET.HEALSTATUS:
        heal_pow = effect.heal_power
        if heal_pow == 0xF:
            heal_pow = 'All'
        else:
            heal_pow = f'Mg({heal_pow})'

        if effect.will_revive:
            return f'Revive with {heal_pow} HP'
        return f'Heal Status and {heal_pow} HP'
    if eff_type == ET.STATUS:
        status_type = effect[1]
        status_bits = effect[2]
        return parse_status_effect(status_type, status_bits)
    if eff_type in (ET.DAMAGE, ET.MULTIHIT):
        dmg_formula = effect.damage_formula_id

        DF = cttechtypes.DamageFormula
        power = effect.power
        ignore_def = effect.defense_byte not in (0x3C, 0x3E)

        if dmg_formula == DF.MAGIC:
            if ignore_def:
                power_mult = 8
            else:
                power_mult = 4

            dmg_str = f'(Lv+Mg)({(power*power_mult)/10:.4g})'
        elif dmg_formula == DF.PC_MELEE:
            dmg_str = f'(Atk)({power/4:.4g})'
        elif dmg_formula == DF.PC_AYLA:
            dmg_str = f'(Atk)({power*9/40:.4g})'
        elif dmg_formula == DF.MISSING_HP:
            dmg_str = f'(St)(MissHP)/{round(280/power)}'
        else:
            dmg_str = ''

        if ignore_def:
            dmg_str += ' (NoDef)'

        return dmg_str
    if eff_type == ET.STEAL:
        steal_chance = effect[1]
        desc_str = f'Steal ({steal_chance}%)'
        return desc_str

    raise ValueError(f"Invalid effect type: {eff_type}")


def get_single_tech_desc(
        control: cttechtypes.ControlHeader,
        effect: cttechtypes.EffectHeader,
        target: cttechtypes.PCTechTargetData
        ) -> str:
    '''
    Get a description string for a tech that accurately describes its
    effect (dmg, element, target).
    '''

    eff_type = effect.effect_type
    ET = cttechtypes.EffectType
    target_str = get_target_str(target)
    heal_pow: Union[int, str]
    if eff_type == ET.HEALING:
        heal_pow = effect.heal_power
        if heal_pow == 0xF:
            heal_pow = 'All'
        else:
            heal_pow = f'Mg({heal_pow})'
        return f'Heals {heal_pow} HP to {target_str}'
    if eff_type == ET.HEALSTATUS:
        heal_pow = effect.heal_power
        if heal_pow == 0xF:
            heal_pow = 'All'
        else:
            heal_pow = f'Mg({heal_pow})'

        if effect.will_revive:
            return f'Revive with {heal_pow} HP to {target_str}'
        return f'Heal Status and {heal_pow} HP to {target_str}'

    if eff_type == ET.STATUS:
        status_type = effect[1]
        status_bits = effect[2]
        return parse_status_effect(status_type, status_bits)
    if eff_type in (ET.DAMAGE, ET.MULTIHIT):
        dmg_formula = effect.damage_formula_id
        elem_str = get_elem_str(control)
        elem_str = f'{elem_str:}'
        DF = cttechtypes.DamageFormula
        power = effect.power

        ignore_def = effect.defense_byte not in (0x3C, 0x3E)

        EM = cttechtypes.EffectMod
        added_effect = control.get_effect_mod(0)

        if added_effect == EM.DEATH_40:
            elem_str = ''
            dmg_str = '40% Death'
        elif dmg_formula == DF.MAGIC:
            if ignore_def:
                power_mult = 8
            else:
                power_mult = 4

            dmg_str = f'(Lv+Mg)({(power*power_mult)/10:.4g})'
        elif dmg_formula == DF.PC_MELEE:
            dmg_str = f'(Atk)({power/4:.4g})'
        elif dmg_formula == DF.PC_RANGED:
            dmg_str = f"(Atk)({power/3:.4g})"
        elif dmg_formula == DF.PC_AYLA:
            dmg_str = f'(Atk)({power*9/40:.4g})'
        elif dmg_formula == DF.MISSING_HP:
            dmg_str = f'(St)(MissHP)/{280/power:.2g}'
        else:
            dmg_str = ''

        if ignore_def:
            dmg_str += ' (NoDef)'

        target_str = get_target_str(target)

        return elem_str+': '+dmg_str+', '+target_str
    if eff_type == ET.STEAL:
        steal_chance = effect[1]
        desc_str = f'Steal ({steal_chance}%)'
        return desc_str
    # elif eff_type == ET.MULTIHIT:
    #    return 'MultiHit'

    raise ValueError('Unknown Type')


def update_single_tech_descs(tech_man: PCTechManager):
    for tech_id in range(1, 1+8*7):
        tech = tech_man.get_tech(tech_id)
        control = tech.control_header
        effect = tech.effect_headers[0]
        target = tech.target_data
        desc_str = get_single_tech_desc(control, effect, target)
        tech.desc = desc_str + '{null}'

        tech_man.set_tech_by_id(tech, tech_id)


def update_black_hole_descs(
        tech_man: PCTechManager,
        bh_death_rate: float,
        bh_min: float
):
    for tech_id in range(1, 1+8*7):
        tech = tech_man.get_tech(tech_id)
        if "40% Death" in tech.desc:
            new_percent = round(bh_min+bh_death_rate*tech.effect_mps[0])
            new_percent = sorted([1, new_percent, 100])[1]
            tech.desc = tech.desc.replace("40% Death", f"{new_percent}% Death")
            tech_man.set_tech_by_id(tech, tech_id)


def update_all_tech_descs(
        tech_man: PCTechManager,
        black_hole_factor: float,
        black_hole_min: float,
):
    update_single_tech_descs(tech_man)
    update_black_hole_descs(tech_man, black_hole_factor, black_hole_min)
    update_combo_tech_descs(tech_man)
    # clean_up_desc_space(tech_db)


_single_tech_abbrev = {
    'Cyclone': 'Cyc',
    'Slash': 'Slash',
    '*Lightning': 'Lit',
    'Spincut': 'SpCt',
    '*Lightning2': 'Li2',
    '*Life': 'Life',
    'Confuse': 'Cnf',
    '*Luminaire': 'Lumi',
    'Aura': 'Aura',
    'Provoke': 'Prov',
    '*Ice': 'Ice',
    '*Cure': 'Cure',
    '*Haste': 'Haste',
    '*Ice 2': 'Ic2',
    '*Cure 2': 'Cu2',
    '*Life 2': 'Lif2',
    'Flame Toss': 'FlTo',
    'Hypno Wave': 'Hyp',
    '*Fire': 'Fir',
    'Napalm': 'Nap',
    '*Protect': 'Prot',
    '*Fire 2': 'Fi2',
    'Mega Bomb': 'MgBm',
    '*Flare': 'Flr',
    'RocketPunch': 'RPunch',
    'Cure Beam': 'CuBm',
    'Laser Spin': 'LaSp',
    'Robo Tackle': 'RTa',
    'Heal Beam': 'HelBm',
    'Uzzi Punch': 'Uzzi',
    'Area Bomb': 'ABomb',
    'Shock': 'Shock',
    'Slurp': 'Slurp',
    'Slurp Cut': 'SlCt',
    '*Water': 'Wat',
    '*Heal': 'Heal',
    'Leap Slash': 'LpS',
    '*Water 2': 'Wa2',
    # '*Cure 2': 'Cur2F',
    'Frog Squash': 'Squash',
    'Kiss': 'Kiss',
    'Rollo Kick': 'RKick',
    'Cat Attack': 'CatAt',
    'Rock Throw': 'Rock',
    'Charm': 'Charm',
    'Tail Spin': 'TSpin',
    'Dino Tail': 'DTail',
    'Triple Kick': 'TrKick',
    # '*Lightning2': 'Lit2Mg',
    # '*Ice 2': 'Ice2Mg',
    # '*Fire 2': 'Fir2Mg',
    '*Dark Bomb': 'DkB',
    '*Magic Wall': 'MWall',
    '*Dark Mist': 'DkMi',
    '*Black Hole': 'BlHole',
    '*DarkMatter': 'DkMa',
    "Arrow Hail": "ArrHa",
    "*Haste All": "HstAll"
}


def build_effect_name_dict(tech_man: PCTechManager):
    ret_dict = {}

    for effect_id in range(1, 1+7*8):
        tech = tech_man.get_tech(effect_id)
        name = tech.name
        ret_dict[effect_id] = _single_tech_abbrev[str(name)]

    # num_effects = tech_db.effect_count
    # for effect_id in range(1+7*8, num_effects):
    #     effect_size = cttechtypes.EffectHeader.SIZE
    #     st = effect_id*effect_size
    #     end = st + effect_size
    #     effect_b = tech_db.effects[st:end]
    #     effect = cttechtypes.EffectHeader(effect_b)
    #
    #     ret_dict[effect_id] = get_effect_string(effect)

    ret_dict[0x3C] = 'Cnf'
    ret_dict[0x3D] = 'TrKi'
    ret_dict[0x40] = 'SlCt'
    # ret_dict[0x42] = ret_dict[0x42] + ' (Frog)'

    return ret_dict


def update_combo_tech_descs(tech_man: PCTechManager):
    num_techs = tech_man.num_techs

    eff_name_dict = build_effect_name_dict(tech_man)

    for tech_id in range(1+8*7, num_techs+1):

        try:
            tech = tech_man.get_tech(tech_id)
        except TechNotFoundException:
            continue

        control = tech.control_header
        effects = tech.effect_headers
        target = tech.target_data

        if control[0] & 0x80:
            desc_str = ''
        else:
            desc_str = get_combo_tech_desc(
                control, effects, target, eff_name_dict
            )

        tech.desc = desc_str + "{null}"
        tech_man.set_tech_by_id(tech, tech_id)


def get_combo_tech_desc(
        control: cttechtypes.PCTechControlHeader,
        effects: list[cttechtypes.EffectHeader],
        target: cttechtypes.TargetData,
        eff_name_dict: dict[int, str],
        ):

    eff_strs = []

    elem_str = get_elem_str(control)
    target_str = get_target_str(target)

    for ind, effect in enumerate(effects):
        eff_id = control.get_effect_index(ind)
        eff_mp_only = control.get_effect_mp_only(ind)
        eff_mod = control.get_effect_mod(ind)

        if eff_mp_only:
            continue

        if eff_id in eff_name_dict:
            eff_str = eff_name_dict[eff_id]
        else:
            eff_str = get_effect_string(effect)

        EM = cttechtypes.EffectMod
        eff_mod = EM(eff_mod)
        if eff_mod == EM.NONE:
            mod_str = ''
        elif eff_mod in (EM.DMG_125, EM.DMG_MAG_125):
            mod_str = '1.25x'
        elif eff_mod in (EM.DMG_150, EM.DMG_MAG_150):
            mod_str = '1.5x'
        elif eff_mod in (EM.DMG_175, EM.DMG_MAG_175):
            mod_str = '1.75x'
        elif eff_mod in (EM.DMG_200, EM.DMG_MAG_200):
            mod_str = '2x'
        elif eff_mod == EM.DMG_400:
            mod_str = '4x'
        elif eff_mod == EM.CHAOS_80:
            mod_str = '80% Chaos + '
        else:
            mod_str = ''
            # mod_str = str(eff_mod)

        eff_str = mod_str+eff_str
        eff_strs.append(eff_str)

    effs_str = ' + '.join(eff_strs)
    desc_str = f'{elem_str}: {effs_str}, {target_str}'
    return desc_str

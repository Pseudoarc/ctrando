"""Implement character buff/debuffs"""
import copy
import enum

from ctrando.common import ctenums
from ctrando.characters import ctpcstats
from ctrando.attacks import pctech, animationscript, scriptreassign


class BlessingID(enum.Enum):
    LUCCA_PHYS_TEH = enum.auto()
    MARLE_PHYS_TECH = enum.auto()
    MARLE_HASTE_ALL = enum.auto()
    LUCCA_PROT_ALL = enum.auto()


def make_phys_marle(
        stat_man: ctpcstats.PCStatsManager,
        tech_man: pctech.PCTechManager
):
    stat_man.set_stat_growth(ctenums.CharID.MARLE, ctpcstats.PCStat.HIT, 140)
    provoke = tech_man.get_tech(ctenums.TechID.PROVOKE)
    cyclone = tech_man.get_tech(ctenums.TechID.CYCLONE)

    provoke.target_data = pctech.ctt.PCTechTargetData(b'\x08\x00')  # All enemies
    provoke.control_header[1:] = cyclone.control_header[1:]  # All but battle group
    provoke.effect_headers[0] = cyclone.effect_headers[0]
    provoke.effect_headers[0].power = 8
    provoke.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED
    provoke.graphics_header.script_id = animationscript.NewScriptID.ARROW_HAIL
    provoke.effect_mps[0] = 2
    provoke.name = "Arrow Hail"

    tech_man.set_tech_by_id(provoke, ctenums.TechID.PROVOKE)


def make_phys_lucca(
        stat_man: ctpcstats.PCStatsManager,
        tech_man: pctech.PCTechManager
):
    """Lucca improved HIT growth and physical formula bombs/flametoss."""
    stat_man.set_stat_growth(ctenums.CharID.LUCCA, ctpcstats.PCStat.HIT, 140)

    tech_power_dict: dict[ctenums.TechID, int] = {
        ctenums.TechID.FLAME_TOSS: 8,   # 1.25x basic
        ctenums.TechID.NAPALM: 12,      # 2x basic
        ctenums.TechID.MEGABOMB: 21     # 3.5x basic
    }

    for tech_id, power in tech_power_dict.items():
        tech = tech_man.get_tech(tech_id)
        tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED
        tech.effect_headers[0].applies_on_hit_effects = True
        tech.effect_headers[0].power = power
        tech_man.set_tech_by_id(tech, tech_id)

    backup = tech_man.get_tech(ctenums.TechID.CONFUSE)

    tech = tech_man.get_tech(ctenums.TechID.NAPALM)
    tech.control_header = backup.control_header
    tech.control_header.set_effect_mod(0, ctenums.WeaponEffects.DMG_50)
    tech.effect_headers[0] = backup.effect_headers[0]
    tech.effect_headers[0][1] = 2
    tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED
    tech.effect_headers[0].power = 12
    tech.graphics_header.script_id = animationscript.NewScriptID.DOUBLE_TAP
    tech.graphics_header.sprite_packet_1 = 0xEB
    tech.graphics_header.sprite_packet_2 = 0xEF
    tech.graphics_header.assembly_packet_1 = 0x23
    tech.graphics_header.assembly_packet_2 = 0x89
    tech.graphics_header.palette = 0x89
    tech.graphics_header.layer3_packet_id = 9
    tech.target_data[0], tech.target_data[1] = 7, 0

    # tech.graphics_header.sprite_packet_1 = 0xC0
    # tech.graphics_header.sprite_packet_2 = 0xC4
    # tech.graphics_header.assembly_packet_1 = 0x09
    # tech.graphics_header.assembly_packet_2 = 0xC5
    # tech.graphics_header.palette = 0x89

    # tech.graphics_header.sprite_packet_1 = 0xC0
    # tech.graphics_header.sprite_packet_2 = 0x00
    # tech.graphics_header.assembly_packet_1 = 0x23
    # tech.graphics_header.assembly_packet_2 = 0x92
    # tech.graphics_header.palette = 0x89

    # tech.graphics_header.sprite_packet_1 = 0xeb
    # tech.graphics_header.sprite_packet_2 = 0xef
    # tech.graphics_header.assembly_packet_1 = 0x23
    # tech.graphics_header.assembly_packet_2 = 0x81  # 83 85 89 92
    # tech.graphics_header.palette = 0x9a

    # tech.graphics_header.sprite_packet_1 = 0xCE
    # tech.graphics_header.sprite_packet_2 = 0x00
    # tech.graphics_header.assembly_packet_1 = 0x11
    # tech.graphics_header.assembly_packet_2 = 0x15
    # tech.graphics_header.palette = 0x15

    tech.name = "Double Tap"
    tech_man.set_tech_by_id(tech, ctenums.TechID.NAPALM)

def make_haste_all(
        tech_man: pctech.PCTechManager
):
    haste = tech_man.get_tech(ctenums.TechID.HASTE)
    haste.target_data = pctech.ctt.PCTechTargetData(b'\x81\x00')
    haste.name = "*Haste All"
    haste.graphics_header.layer3_packet_id = 0x15
    haste.graphics_header.script_id = animationscript.NewScriptID.HASTE_ALL
    haste.effect_mps[0] = 15
    tech_man.set_tech_by_id(haste, ctenums.TechID.HASTE)


def make_prot_all(
        tech_man: pctech.PCTechManager
):
    protect = tech_man.get_tech(ctenums.TechID.PROTECT)
    protect.target_data = pctech.ctt.PCTechTargetData(b'\x81\x00')
    protect.effect_mps[0] = 12
    protect.graphics_header.script_id = animationscript.NewScriptID.PROTECT_ALL
    tech_man.set_tech_by_id(protect, ctenums.TechID.PROTECT)


def make_reraise(
        tech_man: pctech.PCTechManager
):
    lifeline = tech_man.get_tech(ctenums.TechID.LIFE_LINE)
    life2 = tech_man.get_tech(ctenums.TechID.LIFE_2_M)

    life2.target_data = pctech.ctt.PCTechTargetData(b'\x80\x00')
    life2.effect_headers[0] = copy.deepcopy(lifeline.effect_headers[0])
    life2.name = "*Reraise"
    life2.graphics_header.script_id = animationscript.NewScriptID.RERAISE
    tech_man.set_tech_by_id(life2, ctenums.TechID.LIFE_2_M)


def add_magus_duals(
        tech_man: pctech.PCTechManager
):
    scriptreassign.add_all_magus_reassign_techs(tech_man)


def make_gale_slash(
        tech_man: pctech.PCTechManager,
        replace_id: int
):
    # Just get some physical tech as a base
    base_tech = tech_man.get_tech(ctenums.TechID.SPINCUT)
    base_tech.battle_group = pctech.ctt.PCTechBattleGroup.from_charids([ctenums.CharID.MAGUS])
    base_tech.name = "Gale Slash"
    base_tech.target_data = pctech.ctt.PCTechTargetData(b'\x0B\x01')  # Line (Slash)
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("34 E8 EC 21 98 98 FF")  # Copied with +0x80 for some indices
    )
    base_tech.effect_mps[0] = 6
    base_tech.graphics_header.script_id = animationscript.NewScriptID.GALE_SLASH

    tech_man.set_tech_by_id(base_tech, replace_id)


def make_blurp(
        tech_man: pctech.PCTechManager,
        replace_id: int
):
    # Get some AoE Magic tech as a base
    base_tech = tech_man.get_tech(ctenums.TechID.LIGHTNING_2_M)
    effect = base_tech.effect_headers[0]
    effect.status_effect = ctenums.StatusEffect.POISON
    effect.status_effect_chance = 80
    effect.power = 0xC  # maybe too low
    effect.inflicts_status = True

    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("5D 00 00 00 00 00 2B")
    )
    base_tech.graphics_header.script_id = animationscript.NewScriptID.BLURP
    base_tech.name = "*Bluuurp!"

    tech_man.set_tech_by_id(base_tech, replace_id)


def make_iron_orb(
        tech_man: pctech.PCTechManager,
        replace_id: int
):
    # Use black hole as a base
    base_tech = tech_man.get_tech(ctenums.TechID.BLACK_HOLE)
    script_id = base_tech.graphics_header.script_id
    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    # tech.effect_headers[0] = pctech.ctt.PCTechEffectHeader(gale_slash_effect)
    # tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_MELEE
    base_tech.target_data = pctech.ctt.PCTechTargetData(b'\x07\x00')
    base_tech.control_header.set_effect_mod(0, ctenums.WeaponEffects.IRON_ORB)
    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    base_tech.effect_headers[0].power = 0
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("41 C0 00 09 95 95 FF")
    )

    base_tech.graphics_header.script_id = animationscript.NewScriptID.IRON_ORB
    base_tech.name = "Iron Orb"

    tech_man.set_tech_by_id(base_tech, replace_id)


def make_burst_ball(
        tech_man: pctech.PCTechManager,
        replace_id: int
):
    base_tech = tech_man.get_tech(ctenums.TechID.LIGHTNING_2_M)
    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    base_tech.target_data = pctech.ctt.PCTechTargetData(b'\x07\x00')
    base_tech.effect_headers[0].power = 0x2A
    base_tech.effect_mps[0] = 20
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("88 CE 0B 35 A9 A9 4A")
    )
    base_tech.graphics_header.script_id = animationscript.NewScriptID.BURST_BALL
    base_tech.name = "*Burst Ball"

    tech_man.set_tech_by_id(base_tech, replace_id)


def add_daltonized_magus_techs(tech_man: pctech.PCTechManager):
    make_gale_slash(tech_man, ctenums.TechID.DARK_BOMB)
    make_blurp(tech_man, ctenums.TechID.DARK_MIST)
    make_iron_orb(tech_man, ctenums.TechID.BLACK_HOLE)
    make_burst_ball(tech_man, ctenums.TechID.DARK_MATTER)

    bitmask = pctech.ctt.PCTechBattleGroup.from_charids(
        [ctenums.CharID.MAGUS, ctenums.CharID.MARLE, ctenums.CharID.LUCCA]
    ).to_bitmask()
    tech_man.remove_bitmask(bitmask)

    bitmask = pctech.ctt.PCTechBattleGroup.from_charids(
        [ctenums.CharID.MAGUS, ctenums.CharID.LUCCA, ctenums.CharID.ROBO]
    ).to_bitmask()
    tech_man.remove_bitmask(bitmask)



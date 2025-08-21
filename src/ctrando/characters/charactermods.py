"""Implement character buff/debuffs"""
import enum

from ctrando.common import ctenums
from ctrando.characters import ctpcstats
from ctrando.attacks import pctech, animationscript


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
        ctenums.TechID.FLAME_TOSS: 7,   # basic * 7/6
        ctenums.TechID.NAPALM: 9,       # 1.5x basic
        ctenums.TechID.MEGABOMB: 18     # 3x basic
    }

    for tech_id, power in tech_power_dict.items():
        tech = tech_man.get_tech(tech_id)
        tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED
        tech.effect_headers[0].applies_on_hit_effects = True
        tech.effect_headers[0].power = power
        tech_man.set_tech_by_id(tech, tech_id)


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

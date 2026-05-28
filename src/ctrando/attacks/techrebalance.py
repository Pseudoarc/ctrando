"""Module to normalize player tech utility."""

from ctrando.attacks import pctech
from ctrando.common import ctenums

def rebalance_vanilla_tech_man(
        tech_man: pctech.PCTechManager
):
    """Apply cost/cower modifications to specific techs to a vanilla tech manager."""

    tech_mp_dict: dict[ctenums.TechID, int] = {
        ctenums.TechID.LIGHTNING: 3,
        ctenums.TechID.FIRE: 3,
        ctenums.TechID.WATER: 3,
        ctenums.TechID.ICE: 3,
        ctenums.TechID.ROCK_THROW: 6
    }

    for tech_id, new_mp in tech_mp_dict.items():
        tech = tech_man.get_tech(tech_id)
        tech.effect_mps[0] = new_mp
        tech_man.set_tech_by_id(tech, tech_id)

    tech_power_dict: dict[ctenums.TechID, int] = {
        ctenums.TechID.LIGHTNING_2: 17,
        ctenums.TechID.FIRE_2: 17,
        ctenums.TechID.ICE_2: 17,
        ctenums.TechID.WATER_2: 17,
        ctenums.TechID.LIGHTNING_2_M: 20,
        ctenums.TechID.FIRE_2_M: 20,
        ctenums.TechID.ICE_2_M: 20,
        ctenums.TechID.DARK_BOMB: 25,
        ctenums.TechID.DARK_MIST: 25,
        ctenums.TechID.DARK_MATTER: 42,
        ctenums.TechID.CYCLONE: 12,
        ctenums.TechID.SLURPCUT: 14,
    }

    for tech_id, new_power in tech_power_dict.items():
        tech = tech_man.get_tech(tech_id)
        tech.effect_headers[0].power = new_power
        tech_man.set_tech_by_id(tech, tech_id)

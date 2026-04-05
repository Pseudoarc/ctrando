"""Module for setting character stats."""
from dataclasses import dataclass

from ctrando.common import ctenums
from ctrando.characters import ctpcstats
from ctrando.enemydata.enemystats import EnemyStats

def fill_vanilla_tp_gaps(pc_stat_man: ctpcstats.PCStatsManager):

    crono_tp = pc_stat_man.pc_stat_dict[ctenums.CharID.CRONO].tp_thresholds
    crono_tp.set_threshold(2, 130)  # 5, 90, __, 200

    marle_tp = pc_stat_man.pc_stat_dict[ctenums.CharID.MARLE].tp_thresholds
    marle_tp.set_threshold(2, 100)  # 10, 50, __, 150

    lucca_tp = pc_stat_man.pc_stat_dict[ctenums.CharID.LUCCA].tp_thresholds
    lucca_tp.set_threshold(2, 75)  # 10, 60, __, 96,

    robo_tp = pc_stat_man.pc_stat_dict[ctenums.CharID.ROBO].tp_thresholds
    robo_tp.set_threshold(0, 5)  # __, __, 5, 150, 400
    robo_tp.set_threshold(1, 50)
    robo_tp.set_threshold(2, 100)

    frog_tp = pc_stat_man.pc_stat_dict[ctenums.CharID.FROG].tp_thresholds
    frog_tp.set_threshold(2, 100)  # 10, 15, 100, 160

    magus_tp = pc_stat_man.pc_stat_dict[ctenums.CharID.MAGUS].tp_thresholds
    magus_tp.set_threshold(0, 50)  # __, __, __, 400, 400, 400, 900, 900
    magus_tp.set_threshold(1, 50)
    magus_tp.set_threshold(2, 50)


def scale_tp(pc_stat_man: ctpcstats.PCStatsManager,
             enemy_data_dict: dict[ctenums.EnemyID, EnemyStats],
             scale_factor: float):
    """Scale TP gain by altering required tp to gain a tech level."""
    if abs(scale_factor) < 0.25:
        for enemy_id, stats in enemy_data_dict.items():
            stats.tp = 0
    else:
        for char_id in ctenums.CharID:
            tp_thresh = pc_stat_man.pc_stat_dict[char_id].tp_thresholds
            for tech_level in range(8):
                tp_req = tp_thresh.get_threshold(tech_level)
                new_tp_req = round(tp_req/scale_factor)
                tp_thresh.set_threshold(tech_level, new_tp_req)

def scale_xp(pc_stat_man: ctpcstats.PCStatsManager,
             scale_factor: float):
    """Scale XP gain by altering required xp to gain a level."""
    for level in range(99):
        xp_req = pc_stat_man.xp_thresholds.get_xp_for_level(level)
        new_xp_req = round(xp_req/scale_factor)
        pc_stat_man.xp_thresholds.set_xp_for_level(level, new_xp_req)


def adaptive_scale_xp(pc_stat_man: ctpcstats.PCStatsManager,
                      base_scale_factor: float,
                      xp_penalty_level: int,
                      xp_penalty_percent: float,
                      level_cap: int
                      ):
    for level in range(99):
        if level >= level_cap:
            new_xp_req = 0xFFFF
        else:
            xp_req = pc_stat_man.xp_thresholds.get_xp_for_level(level)
            new_xp_req = round(xp_req / base_scale_factor)
            if level > xp_penalty_level:
                levels_over = level - xp_penalty_level
                penalty = (1+(xp_penalty_percent/100))**(levels_over)
                new_xp_req = round(new_xp_req*penalty) & 0xFFFF  #

        pc_stat_man.xp_thresholds.set_xp_for_level(level, new_xp_req)


def apply_mdef_restrictions(
        pc_stat_man: ctpcstats.PCStatsManager,
        mdef_cap: int,
        mdef_levelup_cap: int,
        mdef_scale_factor: float,
):
    pc_stat_man.stat_max_dict[ctpcstats.PCStat.MAGIC_DEFENSE] = mdef_cap
    pc_stat_man.level_up_stat_max_dict[ctpcstats.PCStat.MAGIC_DEFENSE] = mdef_levelup_cap

    for char_id in ctenums.CharID:
        mdef_growth = pc_stat_man.pc_stat_dict[char_id].stat_growth.get_stat_growth(
            ctpcstats.PCStat.MAGIC_DEFENSE
        )
        mdef_growth = sorted([0, round(mdef_growth*mdef_scale_factor), 99])[1]
        pc_stat_man.pc_stat_dict[char_id].stat_growth.set_stat_growth(
            ctpcstats.PCStat.MAGIC_DEFENSE, mdef_growth
        )

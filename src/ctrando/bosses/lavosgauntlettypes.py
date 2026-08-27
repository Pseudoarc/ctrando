"""Types and Data for Lavos Gauntlet"""

from collections.abc import Iterable, Sequence
import copy
import dataclasses
import typing

from ctrando.attacks import enemytech
from ctrando.bosses import bosstypes as bty, bossrandoutils as bru
from ctrando.common import ctenums, ctrom, memory
from ctrando.enemyai import enemyaimanager
from ctrando.enemydata import enemystats


_enemy_id_pool: tuple[ctenums.EnemyID, ...] = (
    ctenums.EnemyID.UNKNOWN_3C, ctenums.EnemyID.UNKNOWN_44,
    ctenums.EnemyID.UNKNOWN_5A, ctenums.EnemyID.UNKNOWN_60,
    ctenums.EnemyID.UNKNOWN_BF,
    ctenums.EnemyID.LAVOS_SUPPORT_UNK_1F, ctenums.EnemyID.LAVOS_SUPPORT_UNK_21,
    ctenums.EnemyID.LAVOS_SUPPORT_UNK_67, ctenums.EnemyID.LAVOS_SUPPORT_UNK_78,
    ctenums.EnemyID.LAVOS_SUPPORT_UNK_78,
    ctenums.EnemyID.LAVOS_3_CENTER_UNK_0B, ctenums.EnemyID.LAVOS_UNK_E8,
    ctenums.EnemyID.LAVOS_UNK_E9, ctenums.EnemyID.LAVOS_UNK_EA,
)

_loc_id_pool: tuple[ctenums.LocID, ...] = (
    ctenums.LocID.GAUNTLET_PRISON_CATWALKS,
    ctenums.LocID.GAUNTLET_ARRIS_DOME_GUARDIAN, ctenums.LocID.GAUNTLET_HECKRAN_CAVE,
    ctenums.LocID.GAUNTLET_ZENAN_BRIDGE, ctenums.LocID.GAUNTLET_CAVE_OF_MASAMUNE,
    ctenums.LocID.GAUNTLET_REPTITE_LAIR, ctenums.LocID.GAUNTLET_MAGUS_INNER_SANCTUM,
    ctenums.LocID.GAUNTLET_TYRANO_LAIR, ctenums.LocID.GAUNTLET_MT_WOE_SUMMIT,
)
_gauntlet_boss_id_dict: dict[bty.BossID, bty.BossID] = {
    bty.BossID.DRAGON_TANK: bty.BossID.GAUNTLET_DRAGON_TANK,
    bty.BossID.GUARDIAN: bty.BossID.GAUNTLET_GUARDIAN,
    bty.BossID.HECKRAN: bty.BossID.GAUNTLET_HECKRAN,
    bty.BossID.ZOMBOR: bty.BossID.GAUNTLET_ZOMBOR,
    bty.BossID.MASA_MUNE: bty.BossID.GAUNTLET_MASA_MUNE,
    bty.BossID.NIZBEL: bty.BossID.GAUNTLET_NIZBEL,
    bty.BossID.MAGUS: bty.BossID.GAUNTLET_MAGUS,
    bty.BossID.BLACK_TYRANO: bty.BossID.GAUNTLET_TYRANO,
    bty.BossID.GIGA_GAIA: bty.BossID.GAUNTLET_GIGA_GAIA
}
def is_vanilla_gauntlet_boss(boss_id: bty.BossID):
    return boss_id in _gauntlet_boss_id_dict

_custom_lavos_replacement_schemes: dict[bty.BossID, bty.BossScheme] = {
    bty.BossID.GIGA_MUTANT: bty.BossScheme(
        bty.BossPart(ctenums.EnemyID.GIGA_MUTANT_HEAD, 3),
        bty.BossPart(ctenums.EnemyID.GIGA_MUTANT_BOTTOM, 9,
                     (0, 0x10))
    ),
    bty.BossID.MEGA_MUTANT: bty.BossScheme(
        bty.BossPart(ctenums.EnemyID.MEGA_MUTANT_HEAD, 3),
        bty.BossPart(ctenums.EnemyID.MEGA_MUTANT_BOTTOM, 9,
                     (0, 0x10))
    ),
    bty.BossID.RETINITE: bty.BossScheme(
        bty.BossPart(ctenums.EnemyID.RETINITE_EYE, 3),
        bty.BossPart(ctenums.EnemyID.RETINITE_TOP, 7, (0, -0x8)),
        bty.BossPart(ctenums.EnemyID.RETINITE_BOTTOM, 9, (0, 0x28))
    ),
    bty.BossID.SON_OF_SUN: bty.BossScheme(
        bty.BossPart(ctenums.EnemyID.SON_OF_SUN_EYE, 3, (0, 0)),
        bty.BossPart(ctenums.EnemyID.SON_OF_SUN_FLAME, 5, (0x18, -0x7)),
        bty.BossPart(ctenums.EnemyID.SON_OF_SUN_FLAME, 6, (0xC, 0x17)),
        bty.BossPart(ctenums.EnemyID.SON_OF_SUN_FLAME, 7, (-0xC, 0x17)),
        bty.BossPart(ctenums.EnemyID.SON_OF_SUN_FLAME, 8, (-0x18, -0x7)),
        bty.BossPart(ctenums.EnemyID.SON_OF_SUN_FLAME, 9, (0, -0x17)),
    ),
    bty.BossID.TERRA_MUTANT: bty.BossScheme(
        bty.BossPart(ctenums.EnemyID.TERRA_MUTANT_HEAD, 3),
        bty.BossPart(ctenums.EnemyID.TERRA_MUTANT_BOTTOM, 9,
                     (0, 0x10))
    ),
}


_vanilla_lavos_part_correspondence_dict: dict[ctenums.EnemyID, ctenums.EnemyID] = {
    # Dtank
    ctenums.EnemyID.LAVOS_DRAGON_TANK: ctenums.EnemyID.DRAGON_TANK,
    ctenums.EnemyID.LAVOS_TANK_LEFT_HEAD: ctenums.EnemyID.TANK_HEAD,
    ctenums.EnemyID.LAVOS_TANK_RIGHT_GRINDER: ctenums.EnemyID.GRINDER,
    # Guardian
    ctenums.EnemyID.LAVOS_GUARDIAN: ctenums.EnemyID.GUARDIAN,
    ctenums.EnemyID.LAVOS_GUARDIAN_LEFT: ctenums.EnemyID.GUARDIAN_BIT,
    ctenums.EnemyID.LAVOS_GUARDIAN_RIGHT: ctenums.EnemyID.GUARDIAN_BIT,
    ctenums.EnemyID.LAVOS_HECKRAN: ctenums.EnemyID.HECKRAN,  # Heckran
    # Zombor
    ctenums.EnemyID.LAVOS_ZOMBOR_UPPER: ctenums.EnemyID.ZOMBOR_TOP,
    ctenums.EnemyID.LAVOS_ZOMBOR_BOTTOM: ctenums.EnemyID.ZOMBOR_TOP,
    ctenums.EnemyID.LAVOS_MASA_MUNE: ctenums.EnemyID.MASA_MUNE,  # Masa
    ctenums.EnemyID.LAVOS_NIZBEL: ctenums.EnemyID.NIZBEL,  # Nizbel
    ctenums.EnemyID.LAVOS_MAGUS: ctenums.EnemyID.MAGUS,  # Magus
    # Black Tyrano
    ctenums.EnemyID.LAVOS_TYRANO_AZALA: ctenums.EnemyID.AZALA,
    ctenums.EnemyID.LAVOS_TYRANO: ctenums.EnemyID.BLACKTYRANO,
    # Giga Gaia
    ctenums.EnemyID.LAVOS_GIGA_GAIA_HEAD: ctenums.EnemyID.GIGA_GAIA_HEAD,
    ctenums.EnemyID.LAVOS_GIGA_GAIA_LEFT: ctenums.EnemyID.GIGA_GAIA_LEFT,
    ctenums.EnemyID.LAVOS_GIGA_GAIA_RIGHT: ctenums.EnemyID.GIGA_GAIA_RIGHT,
}


class GauntletManager:
    def __init__(
            self, gauntlet_bosses: Sequence[bty.BossID]
    ):
        if len(gauntlet_bosses) > 9:
            raise ValueError

        self.gauntlet_bosses = tuple(gauntlet_bosses)
        self._enemy_id_pool = self._get_enemy_id_pool(gauntlet_bosses)
        self.gauntlet_enemy_to_base_dict: dict[ctenums.EnemyID, ctenums.EnemyID] = dict()
        self._base_enemy_to_gauntlet_dict: dict[ctenums.EnemyID, ctenums.EnemyID] = dict()

        for boss_id in self.gauntlet_bosses:
            if boss_id in _gauntlet_boss_id_dict:
                lavos_id = _gauntlet_boss_id_dict[boss_id]
                lavos_scheme = bty.get_default_scheme(lavos_id)
                update_dict = {
                    part.enemy_id: _vanilla_lavos_part_correspondence_dict[part.enemy_id]
                    for part in lavos_scheme.parts
                }
                self.gauntlet_enemy_to_base_dict.update(update_dict)
            else:
                base_scheme = bty.get_default_scheme(boss_id)
                enemy_ids = set(part.enemy_id for part in base_scheme.parts)

                update_dict = {
                    self._enemy_id_pool.pop(): enemy_id
                    for enemy_id in enemy_ids
                }
                self.gauntlet_enemy_to_base_dict.update(update_dict)
                self._base_enemy_to_gauntlet_dict.update(
                    {v: k for (k,v) in update_dict.items()}
                )

        self._lavos_scheme_dict = {
            boss_id: self._make_gauntlet_scheme(boss_id)
            for boss_id in self.gauntlet_bosses
        }

    @staticmethod
    def _get_enemy_id_pool(gauntlet_bosses: Iterable[bty.BossID]) -> list[ctenums.EnemyID]:
        enemy_id_pool = list(_enemy_id_pool)
        for boss, gauntlet_boss in _gauntlet_boss_id_dict.items():
            if boss not in gauntlet_bosses:
                scheme = bty.get_default_scheme(gauntlet_boss)
                new_enemy_ids: set[ctenums.EnemyID] = set(part.enemy_id for part in scheme.parts)
                enemy_id_pool.extend(new_enemy_ids)

        return enemy_id_pool

    def get_lavos_scheme(self, boss_id: bty.BossID) -> bty.BossScheme:
        return copy.deepcopy(self._lavos_scheme_dict[boss_id])

    def _make_gauntlet_scheme(self, boss_id: bty.BossID) -> bty.BossScheme:
        if boss_id not in self.gauntlet_bosses:
            raise ValueError

        if boss_id in _gauntlet_boss_id_dict:
            lavos_id = _gauntlet_boss_id_dict[boss_id]
            return bty.get_default_scheme(lavos_id)

        if boss_id in _custom_lavos_replacement_schemes:
            base_scheme = _custom_lavos_replacement_schemes[boss_id]
        else:
            base_scheme = bty.get_default_scheme(boss_id)

        new_scheme = copy.deepcopy(base_scheme)
        for part in new_scheme.parts:
            part.enemy_id = self._base_enemy_to_gauntlet_dict[part.enemy_id]

        return new_scheme

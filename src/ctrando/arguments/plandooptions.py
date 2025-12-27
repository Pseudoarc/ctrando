"""Options for forcing items and recruits"""
import argparse

from ctrando.common import ctenums
from ctrando.bosses import bosstypes


class PlandoOptions:
    def __init__(
            self,
            treasure_assignment: dict[ctenums.TreasureID, ctenums.ItemID] | None = None,
            recruit_assignment: dict[ctenums.TreasureID, ctenums.CharID | None] | None = None,
            boss_assignment: dict[bosstypes.BossSpotID, bosstypes.BossID] | None = None,
    ):
        if treasure_assignment is None:
            treasure_assignment = dict()
        if recruit_assignment is None:
            recruit_assignment = dict()
        if boss_assignment is None:
            boss_assignment = dict()

        self.treasure_assignment = dict(treasure_assignment)
        self.recruit_assignment = dict(recruit_assignment)
        self.boss_assignment = dict(boss_assignment)

    def _validate(self):
        ...


    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):
        treasure_assignment: dict[ctenums.TreasureID, ctenums.ItemID] = dict()
        for treasure_id in ctenums.TreasureID:
            key = f"plando_loot_{treasure_id.name}"
            treasure_assignment[treasure_id] = getattr(namespace, key, ctenums.ItemID.NONE)




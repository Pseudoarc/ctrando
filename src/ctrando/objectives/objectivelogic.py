"""Module for adding objectives to the logic"""
import typing

from ctrando.arguments import objectiveoptions
from ctrando.bosses import bosstypes as bty
from ctrando.common import ctenums, memory
from ctrando.logic import logictypes, logicfactory
from ctrando.entranceshuffler import regionmap, locregions
from ctrando.objectives import objectivetypes as oty
from ctrando.objectives.objectivetypes import QuestID


def add_objectives_to_map(
        objectives: list[oty.ObjectiveType],
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID],
        options: objectiveoptions.ObjectiveOptions,
        region_map: regionmap.RegionMap
):
    obj_items = [
        ctenums.ItemID.OBJECTIVE_1, ctenums.ItemID.OBJECTIVE_2,
        ctenums.ItemID.OBJECTIVE_3, ctenums.ItemID.OBJECTIVE_4,
        ctenums.ItemID.OBJECTIVE_5, ctenums.ItemID.OBJECTIVE_6,
        ctenums.ItemID.OBJECTIVE_7, ctenums.ItemID.OBJECTIVE_8,
    ]

    obj_tokens: list[list[typing.Any]] = []
    for objective in objectives:
        if isinstance(objective, QuestID):
            obj_tokens.append([objective])
        elif isinstance(objective, bty.BossID):
            obj_tokens.append([
                spot for spot, boss in boss_assign_dict.items()
                if boss == objective
            ])
        elif objective is None:
            obj_tokens.append([])
        else:
            raise ValueError

    for region_name, loc_region in region_map.loc_region_dict.items():
        for tokens, obj_item in zip(obj_tokens, obj_items):
            for token in tokens:
                if token in loc_region.reward_spots or token in loc_region.region_rewards:
                    loc_region.region_rewards.append(obj_item)

    # Now add regions/rules for objective counts
    obj_rule = logicfactory.ProgressiveRule(list(obj_items))
    portal_region = locregions.LocRegion(
        "algetty_portal_objectives",
        region_rewards=[memory.Flags.HAS_ALGETTY_PORTAL]
    )
    portal_connector = regionmap.RegionConnector(
        "starting_rewards", "algetty_portal_objectives",
        f"complete_portal_objecitves ({options.num_algetty_portal_objectives})",
        rule=obj_rule(options.num_algetty_portal_objectives),
        reversible=False
    )

    omen_region = locregions.LocRegion(
        "unlock_omen_objectives",
        region_rewards=[memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE]
    )
    omen_boss_region = locregions.LocRegion(
        "omen_final_bosses"
    )

    omen_connector = regionmap.RegionConnector(
        "starting_rewards", "unlock_omen_objectives",
        f"complete_omen_objecitves ({options.num_omen_objectives})",
        rule=obj_rule(options.num_omen_objectives)
    )
    omen_boss_connector = regionmap.RegionConnector(
        "black_omen", "omen_final_bosses",
        f"final_omen_door",
        rule=logictypes.LogicRule([memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE])
    )

    bucket_region = locregions.LocRegion(
        "unlock_bucket_objectives",
        region_rewards=[memory.Flags.BUCKET_AVAILABLE]
    )
    bucket_connector = regionmap.RegionConnector(
        "starting_rewards", "unlock_bucket_objectives",
        f"complete_bucket_objecitves ({options.num_bucket_objectives})",
        rule=obj_rule(options.num_bucket_objectives),
        reversible=False
    )

    timegauge_region = locregions.LocRegion(
        "timegauge_1999_objectives",
        region_rewards=[memory.Flags.HAS_APOCALYPSE_TIMEGAUGE_ACCESS]
    )
    timegauge_connector = regionmap.RegionConnector(
        "starting_rewards", "timegauge_1999_objectives",
        f"complete_timegauge_1999_objecitves ({options.num_timegauge_objectives})",
        rule=obj_rule(options.num_timegauge_objectives),
        reversible=False
    )

    for region in (portal_region, omen_region, omen_boss_region, bucket_region, timegauge_region):
        region_map.add_loc_region(region)

    for connector in (
        portal_connector, omen_connector, omen_boss_connector, bucket_connector,
        timegauge_connector
    ):
        region_map.add_region_connector(connector)
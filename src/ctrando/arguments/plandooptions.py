"""Options for forcing items and recruits"""
import argparse

from ctrando.arguments import argumenttypes
from ctrando.common import ctenums
from ctrando.bosses import bosstypes
from types import EllipsisType

_plando_recruit_dict: dict[str, ctenums.CharID | None | EllipsisType] = {
    "..." : ...,
    "none": None,
}
for char_id in ctenums.CharID:
    _plando_recruit_dict[char_id.name.lower()] = char_id
_plando_recruit_dict_inv = {val: key for key, val in _plando_recruit_dict.items()}


class PlandoException(Exception):
    ...


class PlandoOptions:
    def __init__(
            self,
            treasure_assignment: dict[ctenums.TreasureID, ctenums.ItemID] | None = None,
            recruit_assignment: dict[ctenums.RecruitID, ctenums.CharID | None] | None = None,
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

        self._validate()

    def _validate(self):
        none_recruit_spots = [spot for spot, recruit in self.recruit_assignment.items()
                              if recruit is None]

        if len(none_recruit_spots) > (len(ctenums.RecruitID) - len(ctenums.CharID)):
            raise PlandoException("Too many empty recruit spots")

        char_dict: dict[ctenums.CharID, ctenums.RecruitID] = {}

        for key, val in self.recruit_assignment.items():
            if val in char_dict:
                raise PlandoException(f"{val} assigned to {key} and {char_dict[val]}")
            elif val in ctenums.CharID:
                char_dict[val] = key


    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        ret_dict: argumenttypes.ArgSpec = {}
        for recruit_id in ctenums.RecruitID:
            spot_name = recruit_id.name.lower()
            name = f"plando_recruit_{spot_name}"
            ret_dict[name] = argumenttypes.DiscreteCategorialArg(
                _plando_recruit_dict.values(), ...,
                f"Loot to assign to {spot_name}",
                lambda x: _plando_recruit_dict[x],
                lambda x: _plando_recruit_dict_inv[x],
            )

        return ret_dict

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):
        treasure_assignment: dict[ctenums.TreasureID, ctenums.ItemID] = dict()
        for treasure_id in ctenums.TreasureID:
            name = treasure_id.name.lower()
            key = f"plando_loot_{name}"
            if (val := getattr(namespace, key, ...)) != ...:
                treasure_assignment[treasure_id] = val

        recruit_assignment: dict[ctenums.RecruitID, ctenums.CharID | None] = dict()
        for recruit_id in ctenums.RecruitID:
            name = recruit_id.name.lower()
            key = f"plando_recruit_{name}"
            if (val := getattr(namespace, key, ...)) != ...:
                recruit_assignment[recruit_id] = val

        boss_assignment: dict[bosstypes.BossSpotID, bosstypes.BossID] = dict()

        return PlandoOptions(treasure_assignment, recruit_assignment, boss_assignment)

    @classmethod
    def add_group_to_argparse(cls, parser: argparse.ArgumentParser):
        arg_spec = cls.get_argument_spec()
        group = parser.add_argument_group(
            "Plando Options", "Options for forcing particular assignments"
        )
        for attr_name, arg in arg_spec.items():
            arg_name = argumenttypes.attr_name_to_arg_name(attr_name)
            arg.add_to_argparse(arg_name, group)

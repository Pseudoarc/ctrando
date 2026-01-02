"""Options for forcing items and recruits"""
import argparse
import typing

from ctrando.arguments import argumenttypes
from ctrando.common import ctenums
from ctrando.bosses import bosstypes
from types import EllipsisType

_plando_recruit_dict: dict[str, ctenums.CharID | None | EllipsisType | str] = {
    "..." : ...,
    "none": None,
    "random": "random"
}
for _char_id in ctenums.CharID:
    _plando_recruit_dict[_char_id.name.lower()] = _char_id
_plando_recruit_dict_inv = {val: key for key, val in _plando_recruit_dict.items()}
type RecruitType = ctenums.CharID | None | EllipsisType | typing.Literal["random"]

class PlandoException(Exception):
    ...


class PlandoOptions:
    def __init__(
            self,
            treasure_assignment: dict[ctenums.TreasureID, ctenums.ItemID] | None = None,
            recruit_assignment: dict[ctenums.RecruitID, list[RecruitType]] | None = None,
            boss_assignment: dict[bosstypes.BossSpotID, bosstypes.BossID] | None = None,
    ):
        if treasure_assignment is None:
            treasure_assignment = dict()
        if recruit_assignment is None:
            recruit_assignment = {ctenums.RecruitID.STARTER: ["random"]}
        if boss_assignment is None:
            boss_assignment = dict()

        self.treasure_assignment = dict(treasure_assignment)
        self.recruit_assignment = dict(recruit_assignment)
        self.boss_assignment = dict(boss_assignment)

        self._validate()

    def _validate(self):
        """Ensure the plando options can be implemented"""

        # Clean up the starter list in case of multiple characters listed.
        starters = self.recruit_assignment[ctenums.RecruitID.STARTER]
        if not starters:
            starters = ["random"]

        starter_chars = [x for x in ctenums.CharID if x in starters]
        starter_others = [x for x in starters if x == "random"]
        if ... in starters:
            starter_others.append("random")

        self.recruit_assignment[ctenums.RecruitID.STARTER] = starters

        # Construct an inverse-ish dict to validate
        placement_dict: dict[RecruitType, list[ctenums.RecruitID]] = {
            x: [] for x in list(ctenums.CharID) + [None, ..., "random"]
        }

        for recruit_id, recruits in self.recruit_assignment.items():
            for recruit in recruits:
                if recruit in placement_dict:
                    placement_dict[recruit] += [recruit_id]

        for char_id in ctenums.CharID:
            spots = set(placement_dict[char_id])
            if len(spots) > 1:
                spot_str = ", ".join(x.name.lower() for x in spots)
                raise PlandoException(f"{char_id} assigned to {spot_str}")

        num_placed = len([key for key in ctenums.CharID if placement_dict[key]])
        num_random = len(set(placement_dict["random"]))
        total_filled = num_placed + num_random

        if total_filled > len(ctenums.CharID):
            raise PlandoException(f"Placed {total_filled} spots (max {len(ctenums.CharID)}")



    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        ret_dict: argumenttypes.ArgSpec = {}

        for recruit_id in ctenums.RecruitID:
            spot_name = recruit_id.name.lower()
            name = f"plando_recruit_{spot_name}"

            if recruit_id == ctenums.RecruitID.STARTER:
                ret_dict[name] = argumenttypes.MultipleDiscreteSelection(
                    list(ctenums.CharID) + ["random"], ["random"],
                    "Characters to start with",
                    lambda x: _plando_recruit_dict[x],
                    lambda x: _plando_recruit_dict_inv[x],
                )
            else:
                ret_dict[name] = argumenttypes.DiscreteCategorialArg(
                    _plando_recruit_dict.values(), ...,
                    f"Recruit to assign to {spot_name}",
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

        recruit_assignment: dict[ctenums.RecruitID, list[RecruitType]] = {
            x: [] for x in ctenums.RecruitID
        }

        for recruit_id in ctenums.RecruitID:
            name = recruit_id.name.lower()
            key = f"plando_recruit_{name}"

            if (val := getattr(namespace, key, ...)) != ...:
                if recruit_id == ctenums.RecruitID.STARTER:
                    # Maybe verify that it's really a list
                    recruit_assignment[recruit_id] = val
                else:
                    # Maybe verify that it's really a single object
                    recruit_assignment[recruit_id] = [val]

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

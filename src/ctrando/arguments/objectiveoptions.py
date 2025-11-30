"""Options for Specifying Objectives/Objective Rewards."""
import argparse
from dataclasses import dataclass, field
import typing

from ctrando.arguments import argumenttypes
from ctrando.bosses import bosstypes as bty
from ctrando.objectives import objectivetypes as oty


class ObjectiveParseError(Exception):
    ...


def is_valid_token(obj_str: str) -> bool:
    obj_str = obj_str.lower()

    if obj_str in oty.get_special_tokens():
        return True

    for quest_id in oty.QuestID:
        quest_str = quest_id.name.lower()
        if obj_str == quest_str:
            return True

    for boss_id in bty.BossID:
        if boss_id == obj_str:
            return True

    return False


def parse_objective_str(obj_str: str) -> str:
    """
    Determine whether obj_str defines a valid objective string.
    Returns a cleaned string.
    """

    # Remove whitespace and make lowercase.
    obj_str = ''.join(obj_str.lower().split())

    pieces = obj_str.split(',')

    for piece in pieces:
        if ':' in piece:  # has a weight
            components = piece.split(':')
            if len(components) != 2:
                raise ObjectiveParseError(f"In \"{piece}\" expected weight:objective")
            weight, objective = components

            try:
                float(weight)
            except ValueError as exc:
                raise ObjectiveParseError(
                    f"In \"{piece}\" (weight:objective) could not parse weight."
                ) from exc
        else:
            objective = piece

        if not is_valid_token(objective):
            raise ObjectiveParseError(
                f"Could not parse objective name: {objective}."
            )

    return obj_str


@dataclass
class ObjectiveOptions:
    _default_objective_specifier: typing.ClassVar[str] = "any_quest"

    num_algetty_portal_objectives: int = 3
    num_omen_objectives: int = 4
    num_bucket_objectives: int = 5
    num_timegauge_objectives: int = 6
    objective_specifiers: list[str] = field(default_factory=list)

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        ret_dict: argumenttypes.ArgSpec =  {
            "num_algetty_portal_objectives": argumenttypes.DiscreteNumericalArg(
                0, 8, 1, 3,
                "Number of objectives needed to unlock the portal in Algetty's entrance",
                type_fn=int
            ),
            "num_omen_objectives": argumenttypes.DiscreteNumericalArg(
                0, 8, 1, 4,
                "Number of objectives needed to unlock the final door in the Black Omen",
                type_fn=int
            ),
            "num_bucket_objectives": argumenttypes.DiscreteNumericalArg(
                0, 8, 1, 5,
                "Number of objectives needed to unlock the bucket in the End of Time",
                type_fn=int
            ),
            "num_timegauge_objectives": argumenttypes.DiscreteNumericalArg(
                0, 8, 1, 6,
                "Number of objectives needed to unlock the bucket in the End of Time",
                type_fn=int
            ),
        }

        for obj_id in range(8):
            obj_num = obj_id+1
            arg_name = f"objective_{obj_num}"
            help_text = f"Specifier for objective {obj_num}"
            ret_dict[arg_name] = argumenttypes.StringArgument[str](
                help_text=help_text,
                parser=parse_objective_str,
                default_value=cls._default_objective_specifier
            )

        return ret_dict


    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Adds this as a group to the parser."""
        group = parser.add_argument_group(
            title="Objective Reward Settings",
            description=(
                "Settings which determine the number of objectives needed "
                "to unlock various rewards."
            )
        )
        help_dict: dict[str, str] = {
            "num_algetty_portal_objectives": "Number of objectives needed to unlock the portal in Algetty's entrance.",
            "num_omen_objectives": "Number of objectives needed to unlock the final door in the Black Omen.",
            "num_bucket_objectives": "Number of objectives needed to unlock the bucket in the End of Time.",
            "num_timegauge_objectives": "Number of objectives needed to unlock 1999 on the time gauge.",
        }
        argumenttypes.add_dataclass_to_group(cls, group, help_dict=help_dict)

        for obj_id in range(8):
            group.add_argument(
                f"--objective-{obj_id+1}", action="store",
                default=argparse.SUPPRESS,
                type=parse_objective_str,
                help=f"Specifier for objective_{obj_id+1} (default: \"{cls._default_objective_specifier}\")"
            )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        ret_obj = argumenttypes.extract_dataclass_from_namespace(cls, namespace)

        ret_obj.objective_specifiers = [cls._default_objective_specifier
                                        for _ in range(8)]
        for obj_id in range(8):
            name = f"objective_{obj_id+1}"
            if hasattr(namespace, name):
                ret_obj.objective_specifiers[obj_id] = getattr(namespace, name)

        return ret_obj





"""Module which defines types for describing and manipulating encounters."""
from dataclasses import dataclass
from enum import Enum, auto


class EncounterID(Enum):
    """Enumeration of (eventually) all enemy encounters"""
    # Mt. Woe


@dataclass()
class OmenElevatorData:
    omen_elevator_up_battle_1: bool
    omen_elevator_up_battle_2: bool
    omen_elevator_up_battle_3: bool
    omen_elevator_down_battle_1: bool
    omen_elevator_down_battle_2: bool
    omen_elevator_down_battle_3: bool

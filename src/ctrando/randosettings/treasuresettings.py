"""Module for specifying randomizer treasure settings."""
from dataclasses import dataclass
from enum import Enum, auto

@dataclass
class TreasureSettingsTemp:
    pass


class TreasureMode(Enum):
    SHUFFLE = auto()
    RANDOM_TIERED = auto()

class TreasureSettings:
    """Class for recording treasure settings."""
    def __init__(
            self,
            mode: TreasureMode,


     ):
        pass
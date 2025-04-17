"""Openworld Black Omen 47F Emporium"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    Facing,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

class EventMod(locationevent.LocEventMod):
    """EventMod for Black Omen 47F Emporium"""
    loc_id = ctenums.LocID.BLACK_OMEN_47F_EMPORIUM

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen 47F Emporium for an Open World.
        - Prevent access to throne unless the Omen Boss flag is set
        - (Maybe) Add a teleporter back to the start.
        """

        pos = script.get_function_start(0, FID.STARTUP)
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_OMEN_NU_SHOP_ACCESS).to_bytearray(),
            pos
        )

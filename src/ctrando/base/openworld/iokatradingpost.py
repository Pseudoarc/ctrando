"""Openworld Ioka Trading Post"""

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
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Ioka Trading Post"""

    loc_id = ctenums.LocID.IOKA_TRADING_POST

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ioka Trading Post for an Open World.
        - Remove storyline lock on trading
        """

        pos = script.get_object_start(0)

        while True:
            pos, cmd = script.find_command_opt([0x18], pos)

            if pos is None:
                break

            if cmd.args[0] == 0x72:
                script.delete_jump_block(pos)
            elif cmd.args[0] == 0x8A:
                script.replace_jump_cmd(
                    pos, EC.if_not_flag(memory.Flags.MAGUS_DEFEATED)
                )
            elif cmd.args[0] == 0xD4:
                script.replace_jump_cmd(
                    pos, EC.if_not_flag(memory.Flags.HAS_ALGETTY_PORTAL)
                )

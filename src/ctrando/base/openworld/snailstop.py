"""Openworld Snail Stop"""
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
    """EventMod for Snail Stop"""

    loc_id = ctenums.LocID.SNAIL_STOP

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Snail Stop for an Open World.
        - Modify flags/checks for receiving reward.
        """

        pos = script.find_exact_command(
            EC.if_has_item(ctenums.ItemID.JERKY),
            script.get_function_start(9, FID.ACTIVATE)
        )
        script.replace_jump_cmd(
            pos, EC.if_flag(memory.Flags.OBTAINED_SNAIL_STOP_ITEM)
        )

        # Skip a textbox
        pos, cmd = script.find_command([0xBB], pos)
        pos, cmd = script.find_command([0xBB], pos + len(cmd))
        str_id = script.data[pos+1]
        script.strings[str_id] = ctstrings.CTString.from_str(
            "I've got the best {item} in town, {linebreak+0}"
            "but I'm saving it.{null}"
        )

        script.insert_commands(
            EC.assign_val_to_mem(ctenums.ItemID.JERKY, 0x7F0200, 1).to_bytearray(),
            pos
        )

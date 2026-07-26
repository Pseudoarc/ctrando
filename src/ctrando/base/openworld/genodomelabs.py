"""Openworld Geno Dome Labs"""

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
    """EventMod for Geno Dome Labs"""

    loc_id = ctenums.LocID.GENO_DOME_LABS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Geno Dome Labs for an Open World.
        - Normalize magic and speed tab pickups
        """
        owu.update_add_item(script, script.get_function_start(0x30, FID.ACTIVATE))
        owu.update_add_item(script, script.get_function_start(0x32, FID.ACTIVATE))
        owu.add_exploremode_to_partyfollows(script)

        pos = script.get_function_start(
            0x13, FID.ACTIVATE
        )
        script.replace_command_at_pos(
            pos,
            EC.call_obj_function(0x12, FID.ACTIVATE, 1, FS.HALT)
        )

        pos, cmd = script.find_command([0xBB],
                                       script.get_function_start(0x12, FID.ACTIVATE))
        script.strings[cmd.args[0]] = ctstrings.CTString.from_str(
            "What shall we examine first?{null}"
        )

        pos, cmd = script.find_command([0xC0], pos)
        pos += len(cmd)
        pos, cmd = script.find_command([0xC0], pos)

        str_ind = int(cmd.args[0])
        ct_str = script.strings[str_ind]
        ct_str = ct_str[3:]
        script.strings[str_ind] = ct_str
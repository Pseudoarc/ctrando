"""Openworld Sunken Desert B2"""

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
    """EventMod for Sunken Desert B2"""

    loc_id = ctenums.LocID.SUNKEN_DESERT_DEVOURER

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sunken Desert B2 for an Open World.
        - Give a hook for boss defeated
        """

        owu.add_exploremode_to_partyfollows(script)

        script.set_function(
            0, FID.ARBITRARY_0,
            EF()
            .add(EC.return_cmd())
        )

        for obj_id in range(2, 6):
            pos = script.get_object_start(obj_id)
            pos, cmd = script.find_command([0xD8], pos)
            pos += len(cmd)

            script.insert_commands(EC.call_obj_function(0x00, FID.ARBITRARY_0,
                                                        1, FS.HALT).to_bytearray(),
                                   pos)


"""Openworld Ocean Palace Side Rooms"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# Note: Uses previous location for some logic.  This covers the case when you're
#       entering from the teleporter and from the story-related cutscenes
#       which would play out in the Ocean Palace Throneroom.  We are removing those
#       so this can be ignored.

class EventMod(locationevent.LocEventMod):
    """EventMod for Ocean Palace Side Rooms"""
    loc_id = ctenums.LocID.OCEAN_PALACE_SIDE_ROOMS

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Piazza Event.
        - Add Magus to the location
        - Give every PC a switch animation
        - Fix switches to use the lead PC's animation.
        """

        # Copying Crono because the rest have linked functions which will break.
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 7)

        for obj_id in range(2, 7):
            script.link_function(obj_id, FID.ARBITRARY_1,
                                 1, FID.ARBITRARY_1)

        # Switches in Obj16 and Obj1A
        switch_ids = (0x16, 0x1A)
        find_cmd = EC.call_obj_function(1, FID.ARBITRARY_1, 1, FS.HALT)
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_1, 1, FS.HALT)
        for obj_id in switch_ids:
            pos = script.find_exact_command(find_cmd)
            # same len commands, can overwrite.
            script.data[pos:pos+len(find_cmd)] = repl_cmd.to_bytearray()




"""Openworld Ocean Palace Entrance"""

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
    """EventMod for Ocean Palace Entrance"""
    loc_id = ctenums.LocID.OCEAN_PALACE_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Entrance Event.
        - Add Magus to the location
        - Remove cutscene triggers.
        """

        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 6, 7)

        # Remove Mune
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xC3),
            script.get_object_start(0x9)  # Mune obj
        )
        script.delete_jump_block(pos)  # Will always just turn Mune off
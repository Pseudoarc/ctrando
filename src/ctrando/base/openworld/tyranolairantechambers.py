"""Openworld Tyrano Lair Antechambers"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# Note that this location covers a few different areas:
# - Kino's Cell
# - The trap door room with the left/right switches
# - The trap door room with the trap triggered by a fake chest.

class EventMod(locationevent.LocEventMod):
    """EventMod for Tyrano Lair Antechambers"""
    loc_id = ctenums.LocID.TYRANO_LAIR_ANTECHAMBERS

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tyrano Lair Antechambers Event.  We're pretending like Kino has already
        been rescued and the door is open.
        - Remove the storyline check on Kino's cell being open
        - Remove Kino from the cell.
        - Remove the reptite battle/scene in front of Kino's cell
        """

        # Remove coordinate checking loops for battle/cutscene
        pos = script.find_exact_command(
            EC.get_pc_coordinates(0, 0x7F0210, 0x7F0212)
        )
        script.insert_commands(EC.end_cmd().to_bytearray(), pos)
        pos += 1
        end = script.find_exact_command(EC.jump_back(), pos) + 2
        script.delete_commands_range(pos, end)

        pos = script.get_function_start(0, FID.ACTIVATE)
        script.delete_commands(pos, 1)  # condition on cell open

        # Hide reptites always (not just storyline >= 0x96)
        reptite_objs = range(0xA, 0xD)
        for obj_id in reptite_objs:
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0x96),
                script.get_object_start(obj_id)
            )
            script.delete_commands(pos, 1)
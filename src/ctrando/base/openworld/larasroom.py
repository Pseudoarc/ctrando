"""Update Lara's Room for an open world."""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Lara's Room"""
    loc_id = ctenums.LocID.LARAS_ROOM

    taban_obj = 0x08

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Lara's Room (009) event.

        - Remove Scene of Taban coming home from the fair.
        """
        start, end = script.get_function_bounds(cls.taban_obj, FID.STARTUP)
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.LUCCA_UNUSED_04), start, end
        )

        # There are two condition blocks to follow
        script.delete_jump_block(pos)
        script.delete_jump_block(pos)

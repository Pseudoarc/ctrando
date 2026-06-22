"""Openworld Lavos Tunnel"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event
from ctrando.locations.eventcommand import EventCommand as EC

class EventMod(locationevent.LocEventMod):
    """EventMod for Lavos Tunnel"""

    loc_id = ctenums.LocID.LAVOS_TUNNEL

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Lavos Tunnel for an Open World.
        - Give bucket access when this location is reached.
        """
        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.BUCKET_AVAILABLE).to_bytearray(),
            pos
        )

        pos = script.get_object_start(0xC)
        for ind in range(3):
            pos = script.find_exact_command(EC.if_flag(memory.Flags.HARD_LAVOS_DEFEATED), pos)
            script.delete_jump_block(pos)

            if ind == 0:
                pos = script.get_object_start(0xD)

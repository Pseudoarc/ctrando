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
"""Openworld Geno Dome Waste Disposal"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

class EventMod(locationevent.LocEventMod):
    """EventMod for Geno Dome Waste Disposal"""
    loc_id = ctenums.LocID.GENO_DOME_WASTE_DISPOSAL

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Geno Dome Waste Disposal for an Open World.
        - Set the flag so that the cutscene doesn't play.
        """

        pos = script.get_function_start(0, FID.STARTUP)
        script.insert_commands(
            EC.set_flag(memory.Flags.GENO_DOME_WASTE_SCENE_VIEWED).to_bytearray(),
            pos
        )
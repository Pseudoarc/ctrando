"""Openworld Algetty Tsunami"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Algetty Tsunami"""
    loc_id = ctenums.LocID.ALGETTY_TSUNAMI

    @classmethod
    def modify(cls, script: Event):
        """
        Remove the storyline setting and character manipulation from the scene.
        """

        pos = script.find_exact_command(
            EC.set_storyline_counter(0xCC),
            script.get_function_start(1, FID.STARTUP)
        )
        end, _ = script.find_command([0xE1])
        script.delete_commands_range(pos, end)

        script.insert_commands(
            EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1)
            .to_bytearray(), pos
        )

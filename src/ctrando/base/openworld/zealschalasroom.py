"""Openworld Zeal Palace Schala's Room"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Zeal Palace Schala's Room"""
    loc_id = ctenums.LocID.ZEAL_PALACE_SCHALAS_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Zeal Palace Schala's Room Event.
        - Eliminate the cutscene that plays on first entry.
        - Notably, do not set the flag for having viewed or it will trigger Schala
          later and set the storyline.
        """

        # Don't do this or it will trigger Schala in Regal Hall
        # pos = script.get_object_start(0)
        # script.insert_commands(
        #     EC.set_flag(memory.Flags.HAS_VIEWED_SCHALAS_ROOM_SCENE).to_bytearray(),
        #     pos
        # )

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xA8))
        end = script.find_exact_command(EC.play_song(0x14), pos)
        script.delete_commands_range(pos, end)

        pos = script.find_exact_command(EC.set_explore_mode(False), pos)
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.return_cmd(),
            script.get_function_start(9, FID.STARTUP)
        ) + 1
        end = script.find_exact_command(EC.end_cmd(), pos)
        script.delete_commands_range(pos, end)
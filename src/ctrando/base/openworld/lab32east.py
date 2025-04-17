"""Openworld Lab 32 East"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Lab 32 East"""
    loc_id = ctenums.LocID.LAB_32_EAST
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Lab 32 East Event.
        - Pre-set a flag to skip the Johnny entrance scene.
        - Pre-set the has raced flag so that foot access is still possible.
        - Add a bike key requirement to riding the jet bike
        - Copy the Lab 32 West block on foot traffic until the bike key is found
        - TODO: Set up a warp between lab endpoints if the race has been won
        """

        # Insert these flags here in case the first lab32 access is from the east.
        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.HAS_MET_JOHNNY))
            .add(EC.set_flag(memory.Flags.HAS_ATTEMPTED_JOHNNY_RACE))
            .get_bytearray(), pos
        )

        # Add a bike key requirment to the bike.  In vanilla, it's impossible to access
        # this side of the lab without the bike key.
        pos = script.get_function_start(9, FID.ACTIVATE)
        script.wrap_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.BIKE_KEY))

        # The exit into the main Lab32 part has been removed.
        # Copy Lab32 West and add a loop to the bike object's startup.
        x_addr, y_addr = 0x7F0230, 0x7F0232
        change_loc_cmd = EC.change_location(
            ctenums.LocID.LAB_32, 0x3E, 0x7, 2, 0, False)

        change_loc_block = (
            EF().set_label('start')
            .add(EC.get_pc_coordinates(0, x_addr, y_addr))
            .add_if(
                EC.if_mem_op_value(x_addr, OP.LESS_OR_EQUAL, 0x30),
                EF().add_if(
                    EC.if_has_item(ctenums.ItemID.BIKE_KEY),
                    EF().add(change_loc_cmd)
                )
            ).jump_to_label(EC.jump_back(), 'start')
        )

        pos = script.get_function_start(9, FID.STARTUP)
        # We're lucky there's an end after the return for us to latch onto
        pos = script.find_exact_command(EC.return_cmd(), pos) + 1
        script.insert_commands(
            change_loc_block.get_bytearray(), pos
        )

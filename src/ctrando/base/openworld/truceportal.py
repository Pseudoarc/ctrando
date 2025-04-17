"""Openworld Truce Portal"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID

from ctrando.base import openworldutils as owu

class EventMod(locationevent.LocEventMod):
    """EventMod for Truce Portal"""
    loc_id = ctenums.LocID.TRUCE_CANYON_PORTAL

    can_eot_addr = 0x7F0232
    temp_addr = 0x7F0234

    @classmethod
    def modify(cls, script: Event):
        """Modify Truce Portal for an open world."""

        # Remove a storyline setter
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0220, OP.EQUALS, 0x51)
        )
        script.delete_jump_block(pos)

        # Remove some commands for the first trip cutscene and the first trip
        # back to 1000 cutscene.
        visit_flag = memory.Flags.FIRST_TRUCE_PORTAL_TRIP
        visit_flag_cmd = EC.if_flag(visit_flag)
        pos = script.find_exact_command(visit_flag_cmd)
        script.delete_commands(pos, 1)
        script.delete_jump_block(pos)  # Storyline < 0x24 block

        pos = script.find_exact_command(visit_flag_cmd)
        script.delete_commands(pos, 1)

        # Add exploremore after party follow for 1 PC parties
        pos = script.find_exact_command(EC.party_follow()) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x21)
        )
        script.delete_jump_block(pos)

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x24)
        )
        script.delete_jump_block(pos)

        pos = script.find_exact_command(EC.set_explore_mode(False), pos)
        end = script.find_exact_command(EC.end_cmd(), pos)
        script.delete_commands_range(pos, end)

        pos = script.find_exact_command(
            EC.if_mem_op_value(visit_flag.value.address,
                               OP.GREATER_THAN, 0)
        )
        script.delete_commands(pos, 1)

        pos = script.get_object_start(2)
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x24)
        )
        script.delete_jump_block(pos)

        # Modify EoT condition
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x48),
                                        script.get_function_start(1, FID.ARBITRARY_4))
        script.replace_jump_cmd(pos, EC.if_mem_op_value(cls.can_eot_addr, OP.EQUALS, 0))
        script.insert_commands(
            owu.get_can_eot_func(cls.temp_addr, cls.can_eot_addr).get_bytearray(),
            pos
        )

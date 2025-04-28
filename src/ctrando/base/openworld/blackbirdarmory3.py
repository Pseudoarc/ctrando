"""Openworld Blackbird Armory 3"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    Facing,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# TODO:  If party rearrangement is allowed on the Blackbird, this will need work.

class EventMod(locationevent.LocEventMod):
    """EventMod for Blackbird Armory 3"""
    loc_id = ctenums.LocID.BLACKBIRD_ARMORY_3
    temp_gear_store_start = 0x7F0210
    gear_equip_start = 0x7F020C
    temp_pc3_addr = 0x7F0218

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Blackbird Armory 3 for an Open World.
        - Add Crono and Magus to the map.
        - Modify the gear restoration routine to use new flags
        - Add cases for restoring Crono and Magus's gear.
        """
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 6)
        owu.insert_pc_object(script, ctenums.CharID.CRONO, 1, 1)

        # Don't you dare let anyone pick that chest up if there was no PC3.
        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(memory.Memory.BLACKBIRD_IMPRISONED_PC3,
                                   OP.EQUALS, 0x80),
                EF().add(EC.set_flag(memory.Flags.BLACKBIRD_FOUND_PC3_GEAR))
            ).get_bytearray(), pos
        )

        owu.add_exploremode_to_partyfollows(script)
        cls.modify_gear_restoration_function(script)


    @classmethod
    def modify_gear_restoration_function(cls, script: Event):
        """
        Use new flags.  Add cases for Crono and Magus.
        """

        # In obj09, Activate
        pos = script.find_exact_command(
            EC.if_mem_op_value(memory.Memory.BLACKBIRD_IMPRISONED_PC3, OP.EQUALS, 1),
            script.get_function_start(9, FID.ACTIVATE)
        )

        end = script.find_exact_command(
            EC.set_flag(memory.Flags.BLACKBIRD_FOUND_PC3_GEAR), pos
        )

        new_block = EF()
        for pc_id in ctenums.CharID:
            new_block.add_if(
                EC.if_mem_op_value(memory.Memory.BLACKBIRD_IMPRISONED_PC3,
                                   OP.EQUALS, pc_id),
                EF().add(EC.reset_bit(memory.Memory.BLACKBIRD_GEAR_STATUS, 0x80 >> pc_id))
            )

        script.delete_commands_range(pos, end)
        script.insert_commands(new_block.get_bytearray(), pos)

        pos = script.find_exact_command(EC.party_follow(), pos)
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # The rest is in Obj00, Arb1.  This function actually does the restoration
        # 1) Store current gear in script memory
        # 2) Add stored gear to inventory
        # 3) Equip saved gear

        # Both 1 and 3 need cases for Crono and Magus

        # Gear Storage
        store_gear_block = EF()
        for pc_id in (ctenums.CharID.CRONO, ctenums.CharID.MAGUS):
            gear_start_addr = 0x7E2627 + 0x50 * pc_id
            store_gear_block.add_if(
                EC.if_mem_op_value(cls.temp_pc3_addr,
                                   OP.EQUALS, pc_id),
                EF().add(EC.assign_mem_to_mem(gear_start_addr,
                                              cls.temp_gear_store_start, 1))
                .add(EC.assign_mem_to_mem(gear_start_addr+1,
                                          cls.temp_gear_store_start+2, 1))
                .add(EC.assign_mem_to_mem(gear_start_addr+2,
                                          cls.temp_gear_store_start+4, 1))
                .add(EC.assign_mem_to_mem(gear_start_addr+3,
                                          cls.temp_gear_store_start+6, 1))
            )

        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.temp_pc3_addr, OP.EQUALS, 1),
            script.get_function_start(0, FID.ARBITRARY_1)
        )
        script.insert_commands(store_gear_block.get_bytearray(), pos)

        # Remove Ayla Special Case
        pos = script.find_exact_command(
            EC.if_mem_op_value(memory.Memory.BLACKBIRD_IMPRISONED_PC3,
                               OP.EQUALS, ctenums.CharID.AYLA), pos
        )
        script.delete_jump_block(pos)

        # Equip saved gear.
        equip_gear_block = EF()
        for pc_id in (ctenums.CharID.CRONO, ctenums.CharID.MAGUS):
            gear_start_addr = 0x7E2627 + 0x50 * pc_id
            equip_gear_block.add_if(
                EC.if_mem_op_value(memory.Memory.BLACKBIRD_IMPRISONED_PC3,
                                   OP.EQUALS, pc_id),
                EF().add(EC.assign_mem_to_mem(cls.gear_equip_start,
                                              gear_start_addr, 2))
                .add(EC.assign_mem_to_mem(cls.gear_equip_start+2,
                                          gear_start_addr+2, 2))
            )
        pos = script.find_exact_command(
            EC.if_mem_op_value(memory.Memory.BLACKBIRD_IMPRISONED_PC3,
                               OP.EQUALS, 1),
            pos
        )
        script.insert_commands(equip_gear_block.get_bytearray(), pos)
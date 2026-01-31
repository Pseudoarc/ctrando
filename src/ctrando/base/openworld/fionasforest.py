"""Openworld Fiona's Forest"""

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


class EventMod(locationevent.LocEventMod):
    """EventMod for Fiona's Forest"""
    loc_id = ctenums.LocID.FIONA_FOREST
    temp_pc_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Fiona's Forest for an Open World.
        - Save/Restore the active party on portal entry/exit.
        - Remove existing party manipulation
        - Shorten the scene with Robo.
        """

        pos, _ = script.find_command(
            [0xD4], script.get_function_start(4, FID.ACTIVATE)
        )
        script.delete_commands(pos, 2)

        # Save PC2/PC3 on entering the portal and replace with 0x80
        script.insert_commands(
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2,
                                      cls.temp_pc_addr, 1))
            .add(EC.assign_mem_to_mem(cls.temp_pc_addr,
                                      memory.Memory.FOREST_PC2, 1))
            .add(EC.assign_val_to_mem(0x80, memory.Memory.ACTIVE_PC2, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3,
                                      cls.temp_pc_addr, 1))
            .add(EC.assign_mem_to_mem(cls.temp_pc_addr,
                                      memory.Memory.FOREST_PC3, 1))
            .add(EC.assign_val_to_mem(0x80, memory.Memory.ACTIVE_PC3, 1))
            .get_bytearray(),
            pos,
        )

        # Restore on return
        pos = script.find_exact_command(EC.set_explore_mode(True))
        script.insert_commands(
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.FOREST_PC2,
                                      cls.temp_pc_addr, 1))
            .add(EC.assign_mem_to_mem(cls.temp_pc_addr,
                                      memory.Memory.ACTIVE_PC2, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.FOREST_PC3,
                                      cls.temp_pc_addr, 1))
            .add(EC.assign_mem_to_mem(cls.temp_pc_addr,
                                      memory.Memory.ACTIVE_PC3, 1))
            .get_bytearray(),
            pos,
        )

        # Remove existing party manip
        pos, _ = script.find_command(
            [0xD4], script.get_function_start(2, FID.ACTIVATE)
        )
        end, _ = script.find_command([0xE0], pos)
        script.delete_commands_range(pos, end)

        # Change item routine
        pos = script.find_exact_command(
            EC.add_item(ctenums.ItemID.GREENDREAM),
            script.get_function_start(1, FID.ARBITRARY_4)
        )
        script.delete_commands(pos, 4)
        owu.insert_add_item_block(
            script,
            pos,
            ctenums.ItemID.GREENDREAM,
            memory.Flags.OBTAINED_GREEN_DREAM_ITEM)

"""Openworld Proto Dome Portal"""
from typing import Optional

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Proto Dome Portal"""
    loc_id = ctenums.LocID.PROTO_DOME_PORTAL
    num_pc_addr = 0x7F0230
    temp_pc_addr = 0x7F0232
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Proto Dome Portal Event.
        - Remove the cutscene that plays on first entry.  (All storyline < 0x48)
        - Block the door if factory is not complete.
        - Fix a partyfollow+exploremode when entering through the portal
        """

        # The portal waits for all PCs to perform an animation before activating the
        # portal.  This is implemented by having the animation increment 0x7F020E and
        # a hardcoded check for 0x7F020E < 3.
        #  - Put the number of active PCs into memory.
        #  - Replace the comparison to a constant 3 to the value written to memory.

        # Compute the number of PCs and put it into cls.num_pc_addr
        pos: Optional[int] = script.get_object_start(0)
        script.insert_commands(
            EF()
            .add(EC.set_flag(memory.Flags.PROTO_DOME_DOOR_UNLOCKED))
            .add(EC.assign_val_to_mem(1, cls.num_pc_addr, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2, cls.temp_pc_addr, 1))
            .add_if(
                EC.if_mem_op_value(cls.temp_pc_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.add(cls.num_pc_addr, 1))
            )
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, cls.temp_pc_addr, 1))
            .add_if(
                EC.if_mem_op_value(cls.temp_pc_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.add(cls.num_pc_addr, 1))
            ).get_bytearray(), pos
        )

        # Replace the comparison to 3 with a comparison to cls.num_pc_addr
        pos = script.get_function_start(0xA, FID.ARBITRARY_0)
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F020E, OP.LESS_THAN, 3)
        )
        script.replace_jump_cmd(
            pos, EC.if_mem_op_mem(0x7F020E, OP.LESS_THAN, cls.num_pc_addr)
        )

        # Remove all storylilne < 0x48 checks
        pos: Optional[int] = script.get_object_start(0)
        while True:
            pos = script.find_exact_command_opt(
                EC.if_storyline_counter_lt(0x48), pos
            )
            if pos is None:
                break
            script.delete_jump_block(pos)

        # Block the door if Factory is not done -- Not anymore.
        # pos = script.get_function_start(0, FID.ACTIVATE)
        # script.insert_commands(
        #     # EF().add_if(EC.if_not_flag(memory.Flags.FACTORY_POWER_ACTIVATED))
        #     EF().add_if(
        #         EC.if_not_flag(memory.Flags.FACTORY_POWER_ACTIVATED),
        #         EF().add(
        #             EC.copy_tiles(0x19, 8, 0x1A, 8,
        #                           0x17, 0xC,
        #                           False, False, False, True,
        #                           unk_0x10=True, unk_0x20=True,
        #                           copy_z_plane=True)
        #         )).get_bytearray(), pos
        # )

        # exploremode
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(0xA, FID.ARBITRARY_1)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        owu.update_add_item(
            script, script.get_function_start(0xD, FID.ACTIVATE)
        )

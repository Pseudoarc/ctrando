"""Openworld Lavos"""
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

# Notes:
# - This is a very complicated scene because of all the different ways one can
#   arrive at Lavos.
# - The main routine that initiates a battle is Ob00, Arb0.  I think that this
#   can be modified just by changing the Ocean Palace/Telepod routine that jumps
#   right into the fight to always trigger.

class EventMod(locationevent.LocEventMod):
    """EventMod for Lavos"""

    loc_id = ctenums.LocID.LAVOS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Lavos for an Open World.
        - Always jump right into the Lavos fight.
        """
        pos = script.get_object_start(0)
        script.insert_commands(
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.NOT_EQUALS, 3),
                EF()
                .add_if(
                    EC.if_not_flag(memory.Flags.LAVOS_GAUNTLET_DISABLED),
                    EF()
                    .add(EC.assign_val_to_mem(8, memory.Memory.LAVOS_STATUS, 1))
                )
            ).get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.EQUALS, 3),
            script.get_function_start(0, FID.ARBITRARY_0)
        )

        # We'll reserve a status of 8 for actually doing the boss rush.
        script.replace_jump_cmd(
            pos, EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.NOT_EQUALS, 8))


        # Remove the possibility of triggering the Crono death scene
        pos, _ = script.find_command([0xD8], script.get_function_start(0, FID.ARBITRARY_0))
        pos = script.find_exact_command(
            EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.EQUALS, 7),
            pos
        )
        script.replace_jump_cmd(
            pos, EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.NOT_EQUALS, 3)
        )

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.LAVOS_FLAG_UNK_80),
            script.get_function_start(0, FID.ARBITRARY_0)
        )

        pos, _ = script.find_command([0xDF], pos)
        script.replace_command_at_pos(
            pos,
            EC.change_location(ctenums.LocID.LAST_VILLAGE_EMPTY_HUT,
                               0x18, 0x18, Facing.DOWN, )
        )

        # remove a hide lavos command usually used in boss rush
        pos = script.find_exact_command(
            EC.return_cmd(),
            script.get_object_start(0x1C)
        ) - 1
        script.delete_commands(pos, 1)

        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.EQUALS, 8),
                EF().add(EC.set_own_drawing_status(False))
            ).get_bytearray(), pos
        )

        # force play the lavos song when interacted with from Black Omen
        pos = script.find_exact_command(
            cmd := EC.if_mem_op_value(0x7F0214, OP.EQUALS, 1),
            script.get_function_start(0xA, FID.STARTUP)
        )
        pos += len(cmd)
        script.insert_commands(EC.play_song(0xD).to_bytearray(), pos)

        pos = script.find_exact_command(
            EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.EQUALS, 4),
            script.get_function_start(9, FID.STARTUP)
        )
        script.replace_jump_cmd(pos, EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.NOT_EQUALS, 3))
        # target_pos = script.find_exact_command(EC.set_explore_mode(False), pos)
        # jump_cmd = EC.jump_forward(1+(target_pos-pos))
        # script.insert_commands(
        #     EF()
        #     .add_if(
        #         EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.EQUALS, 8),
        #         EF().add(jump_cmd)
        #     ).get_bytearray(), pos
        # )

        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(8, FID.ARBITRARY_2)
        ) + 1
        script.insert_commands(
            EC.set_explore_mode(True).to_bytearray(), pos
        )
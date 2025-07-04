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

"""Openworld Guardia Forest Dead End"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Forest Dead End"""

    loc_id = ctenums.LocID.GUARDIA_FOREST_DEAD_END

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Guardia Forest Dead End Event.
        - Always show the portal.
        - Remove storyline checks/the escape cutscene
        - Change the requirements for visiting EoT
        - Move pillar flag so it always triggers
        """
        cls.modify_storyline_triggers(script)
        cls.modify_sealed_box(script)

    @classmethod
    def modify_sealed_box(cls, script: Event):
        """
        Change condition on sealed box, add default treasure string.
        Reorder commands to fit the usual pattern.
        """
        pos = script.get_function_start(0x12, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0xA5)
        )
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE))

        pos = script.find_exact_command(EC.add_item(ctenums.ItemID.POWER_RING), pos)
        ins_block = (
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.POWER_RING, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
        )

        script.insert_commands(ins_block.get_bytearray(), pos)
        pos += len(ins_block)
        script.delete_commands(pos, 1)

        pos, _ = script.find_command([0xBB], pos)
        script.data[pos+1] = owu.add_default_treasure_string(script)

        # Remove some special casing for sealed chest music during the cutscene
        for _ in range(2):
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0x33), pos
            )
            script.delete_jump_block(pos)

    @classmethod
    def modify_storyline_triggers(cls, script: Event):
        """
        Replace storyline triggers with flags when appropriate
        - Remove the storyline lock on the guardia forest portal
        - Remove the chancellor scene/chancellor blocking exit
        - Replace the EoT storyline check with a gate key check
        """

        # First check determimes whether to show the portal.
        # Remove the condition so it's always shown
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0x30)
        )
        script.delete_commands(pos, 1)

        # Next check is part of the chancellor scene.  Remove the whole thing
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0x30), pos
        )
        script.delete_jump_block(pos)  # Includes storyline = 0x33
        # Remove unused coordinate check loop.  The goto in this loop would point
        # back to the just-removed block.
        script.delete_commands(pos, 2)

        # Remove the portal entering part of the cutscene because it complicates
        # other portal-related modifications.
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0214, OP.EQUALS, 1),
            pos
        )
        script.delete_jump_block(pos)

        # Next is the check for whether the portal should go to EoT
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0x48), pos
        )
        script.replace_jump_cmd(pos, EC.if_mem_op_value(0x7F0220, OP.EQUALS, 1))
        script.insert_commands(
            owu.get_can_eot_func(0x7F0222, 0x7F0220).get_bytearray(),
            pos
        )

        # Move the pillar flag command
        flag_cmd = EC.set_flag(memory.Flags.HAS_BANGOR_PORTAL)
        script.insert_commands(flag_cmd.to_bytearray(), pos)
        pos += len(flag_cmd)

        pos =  script.find_exact_command(flag_cmd, pos)
        script.delete_commands(pos, 1)
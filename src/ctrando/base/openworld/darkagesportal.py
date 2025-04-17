"""Openworld Dark Ages Portal"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Dark Ages Portal"""
    loc_id = ctenums.LocID.DARK_AGES_PORTAL
    temp_addr = 0x7F0220
    can_eot_addr = 0x7F0222
    portal_unlocked_addr = 0x7F0224

    exit_last_village_addr = 0x7F0226

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Dark Ages Portal Event.
        - Remove the cutscenes.
        - Update the locked portal logic to use a different flag.
        """

        cls.remove_cutscenes(script)
        cls.modify_locked_portal(script)
        cls.modify_portal_activation(script)
        cls.modify_exit_to_overworld(script)

    @classmethod
    def modify_exit_to_overworld(cls, script: Event):
        """
        If Zeal has fallen, allow the player to choose which OW to exit into.
        """
        da_change_loc_cmd = get_command(bytes.fromhex("E0F4034F48"))
        lv_change_loc_cmd = get_command(bytes.fromhex("E0F6034F48"))

        find_cmd = EC.if_mem_op_value(0x7F0000, OP.LESS_OR_EQUAL, 0xCC)
        pos = script.find_exact_command(find_cmd) + len(find_cmd)
        pos = script.find_exact_command(find_cmd, pos)

        new_block = (
            EF()
            .add_if_else(
                EC.if_not_flag(memory.Flags.ZEAL_HAS_FALLEN),
                EF().add(da_change_loc_cmd),
                EF()
                .add(EC.decision_box(
                    script.add_py_string(
                        "Exit onto which overworld?{line break}"
                        "   Dark Ages{line break}"
                        "   Last Village{null}"
                    ), 1, 2
                ))
                .add_if_else(
                    EC.if_result_equals(1),
                    EF().add(da_change_loc_cmd),
                    EF().add(lv_change_loc_cmd)
                )
            )
        )
        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        end = script.find_exact_command(EC.jump_back(), pos)
        script.delete_commands_range(pos, end)




    @classmethod
    def remove_cutscenes(cls, script: Event):
        """
        Remove the scene of the party first arriving in the dark ages and the scene
        where the prophet seals the portal.
        """

        # Intro scene.
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_VIEWED_DARKAGES_PORTAL_FIRST_SCENE)
        )
        end = script.find_exact_command(EC.party_follow(), pos)
        script.delete_commands_range(pos, end)

        pos += 1  # over partyfollow
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # Prophet scene
        pos = script.find_exact_command(EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0xA8))
        script.delete_jump_block(pos)


    @classmethod
    def modify_locked_portal(cls, script: Event):
        """
        Change the flag that determines whether the portal should be locked.
        """

        # In vanilla, the portal is locked as long as the skyways are.  We need
        # to change this so that it's locked when EoT is unavailable AND the Tyrano
        # Lair is still standing.

        pos = script.get_object_start(0)
        can_eot_func = owu.get_can_eot_func(cls.temp_addr, cls.can_eot_addr)
        script.insert_commands(can_eot_func.get_bytearray(), pos)
        pos += len(can_eot_func)

        new_block = (
            EF().add_if(
                EC.if_mem_op_value(cls.can_eot_addr, OP.EQUALS, 1),
                EF().add(EC.assign_val_to_mem(1, cls.portal_unlocked_addr, 1))
            ).add_if(
                EC.if_flag(memory.Flags.OW_LAVOS_HAS_FALLEN),
                EF().add(EC.assign_val_to_mem(1, cls.portal_unlocked_addr, 1))
            )
        )
        script.insert_commands(new_block.get_bytearray(), pos)

        jump_cmd = EC.if_flag(memory.Flags.SKYWAYS_LOCKED)
        repl_cmd = EC.if_mem_op_value(cls.portal_unlocked_addr, OP.EQUALS, 0)

        pos = script.get_function_start(0xA, FID.STARTUP)
        pos = script.find_exact_command(jump_cmd, pos)
        script.replace_jump_cmd(pos, repl_cmd)

        pos = script.get_function_start(0xB, FID.STARTUP)
        pos = script.find_exact_command(jump_cmd)
        script.replace_jump_cmd(pos, repl_cmd)

    @classmethod
    def modify_portal_activation(cls, script: Event):
        """
        Update the EoT travel conditions.
        Note: EoT check was added in modify_locked_portal
        """

        pos = script.get_function_start(0xB, FID.ACTIVATE)
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_DARK_AGES_PORTAL).to_bytearray(),
            pos
        )

        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.ENTERING_EOT_DARK_AGES), pos
        )
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(cls.can_eot_addr, OP.EQUALS, 0),
                EF().add(get_command(bytes.fromhex("DD33030804")))  # copied changeloc
                .add(EC.play_song(0x37))
                .add(EC.generic_command(0xFF, 0x82))
                .add(EC.return_cmd())
            ).get_bytearray(), pos
        )


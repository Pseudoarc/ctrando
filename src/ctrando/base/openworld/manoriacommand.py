"""Openworld Manoria Command"""
from typing import Optional

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Manoria Command"""
    loc_id = ctenums.LocID.MANORIA_COMMAND

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Manoria Command Event.
        - Change storyline triggers
        - Change pre/pos battle cutscenes
        - Epoch move after defeating Yakra
        """
        cls.change_storyline_triggers(script)
        cls.set_pc_functions(script)
        cls.modify_pre_battle_cutscene(script)
        cls.modify_post_battle_cutscene(script)

        # Epoch Move
        pos, _ = script.find_command([0xE0], script.get_function_start(0xC, FID.ACTIVATE))
        script.insert_commands(
            owu.get_epoch_set_block(ctenums.LocID.OW_MIDDLE_AGES, 0x118, 0xE0)
            .get_bytearray(), pos
        )

    @classmethod
    def change_storyline_triggers(cls, script: Event):
        """
        Replace storyline commands with flags.
        """

        # Replace if storyline checks
        storyline_check = EC.if_storyline_counter_lt(0x1B)
        flag_check = EC.if_not_flag(memory.Flags.MANORIA_BOSS_DEFEATED)
        pos = script.find_exact_command(storyline_check)
        script.replace_jump_cmd(pos, flag_check)

        pos = script.find_exact_command(storyline_check, pos)
        script.replace_jump_cmd(pos, flag_check)

        pos = script.get_object_start(0xE)
        pos = script.find_exact_command(storyline_check, pos)
        script.replace_jump_cmd(pos, flag_check)

        # Remove setting the storyline counter
        set_storyline_cmd = EC.set_storyline_counter(0x1B)
        pos = script.find_exact_command(
            set_storyline_cmd, script.get_function_start(0xC, FID.ACTIVATE)
        )
        script.delete_commands(pos, 1)

        # Put the flag after battle instead of in Leene's object.
        pos, _ = script.find_command([0xD8], script.get_object_start(8))
        script.insert_commands(
            EC.set_flag(memory.Flags.MANORIA_BOSS_DEFEATED).to_bytearray(),
            pos
        )

    @classmethod
    def set_pc_functions(cls, script: Event):
        """
        Change the PC arbs so that any PC can be in the cutscene.
        Also change Frog's startup to be normal.
        """

        # Vanilla Arbs
        # Arb0: Just set facing up
        # Arb1: Just set facing down and reset animation
        # Arb2: Happens after the battle -- Removable

        # We're going to more-or-less mimic the Jets approach
        # Party movement will be handled by move party commands,
        # Arb0: Just set facing up
        # Arb1: Face the boss and do a battle position.

        obj_ordering = (
            ctenums.CharID.CRONO, ctenums.CharID.MARLE, ctenums.CharID.LUCCA,
            ctenums.CharID.FROG, ctenums.CharID.ROBO, ctenums.CharID.AYLA,
            ctenums.CharID.MAGUS
        )

        arb_0 = (
            EF().add(EC.set_own_facing('up'))
            .add(EC.return_cmd())
        )

        arb_1 = (
            EF().add(EC.play_animation(0))
            .add(EC.set_own_facing_object(0xC))
            .add(EC.return_cmd())
        )

        arb_2 = (  # For 1st PC
            EF().add(EC.call_pc_function(1, FID.ARBITRARY_3, 2, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_4, 2, FS.CONT))
            .add(EC.set_move_speed(0x30))
            .add(EC.move_sprite(0x8, 0xF))
            .add(EC.set_own_facing('up'))
            .add(EC.return_cmd())
        )

        arb_3 = (  # For 2nd PC
            EF().add(EC.set_move_speed(0x30))
            .add(EC.move_sprite(0x3, 0xD))
            .add(EC.set_own_facing('up'))
            .add(EC.return_cmd())
        )

        arb_4 = (  # For 3rd PC
            EF().add(EC.set_move_speed(0x30))
            .add(EC.move_sprite(0xC, 0xD))
            .add(EC.set_own_facing('up'))
            .add(EC.return_cmd())
        )

        for ind, char_id in enumerate(obj_ordering):
            obj_id = ind+1
            if char_id == ctenums.CharID.FROG:
                normal_startup = (
                    EF().add(EC.load_pc_in_party(char_id))
                    .add(EC.return_cmd())
                    .add(EC.set_controllable_infinite())
                )
                script.set_function(obj_id, FID.STARTUP, normal_startup)

            script.set_function(obj_id, FID.ARBITRARY_0, arb_0)
            script.set_function(obj_id, FID.ARBITRARY_1, arb_1)
            script.set_function(obj_id, FID.ARBITRARY_2, arb_2)
            script.set_function(obj_id, FID.ARBITRARY_3, arb_3)
            script.set_function(obj_id, FID.ARBITRARY_4, arb_4)

    @classmethod
    def modify_pre_battle_cutscene(cls, script: Event):
        """
        Change the pre-battle cutscene to remove dialog and remove calls to
        Frog's object.
        """

        # The cutscene takes place in:
        # - Obj09, Arb0+Arb1 (Chancellor)
        #   - Call Obj0C, Arb0 (Queen)
        # - Obj0A, Arb0+Arb1 (Yakra)
        # The dialog is almost all in Obj09, Arb0

        pos: Optional[int]
        pos, end = script.get_function_bounds(9, FID.ARBITRARY_0)
        # Remove Chancellor function text
        while pos < end:
            pos, cmd = script.find_command_opt([0xBB, 0x04], pos, end)
            if pos is None:
                break

            if cmd.command == 0xBB:
                script.delete_commands(pos, 1)
            elif cmd.command == 0x04 and cmd.args[0] == 8:
                script.delete_commands(pos, 1)
            elif cmd.command == 0x04 and cmd.args[0] == 2:
                repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_2, 2, FS.CONT)
                script.data[pos: pos+len(repl_cmd)] = repl_cmd.to_bytearray()
            else:
                pos += len(cmd)

        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_2, 2, FS.CONT),
            pos
        )
        script.replace_command_at_pos(
            pos,
            EC.call_pc_function(0, FID.ARBITRARY_2, 2, FS.CONT)
        )

        # Modify Leene's Arb0
        pos = script.get_function_start(0xC, FID.ARBITRARY_0)
        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 1)
        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 1)
        
    @classmethod
    def modify_post_battle_cutscene(cls, script: Event):
        """
        Change the pre-battle cutscene to remove dialog and remove calls to
        Frog's object.  Remove keepsong
        """

        pos, cmd = script.find_command(
            [0xD8], script.get_function_start(8, FID.STARTUP)
        )
        script.data[pos+2] = 0xC0  # Prevent regroup after battle (set 0x80)

        pos = script.find_exact_command(
            EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1),
            pos
        )
        script.delete_commands(pos, 1)

        new_call_block = (
            EF().add(EC.call_pc_function(0, FID.ARBITRARY_1, 3, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_1, 3, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_1, 3, FS.CONT))
        )

        pos = script.find_exact_command(
            EC.call_obj_function(4, FID.ARBITRARY_7, 3, FS.HALT)
        )
        script.delete_commands(pos, 1)

        pos, _ = script.find_command(
            [2], script.get_function_start(0xC, FID.ARBITRARY_2)
        )

        script.data[pos: pos+len(new_call_block)] = \
            new_call_block.get_bytearray()

        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 1)

        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 1)

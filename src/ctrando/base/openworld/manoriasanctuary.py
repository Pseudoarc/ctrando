"""Openworld Manoria Sanctuary"""
from typing import Optional

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF


class EventMod(locationevent.LocEventMod):
    """EventMod for Manoria Sanctuary"""
    loc_id = ctenums.LocID.MANORIA_SANCTUARY
    char_mem_st = 0x7F0220
    crono_obj = 1

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Manoria Sanctuary event.
        - Change storyline triggers
        """

        pos = script.get_function_start(0, FID.ACTIVATE)

        commands = (
            EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1,
                                          cls.char_mem_st, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2,
                                      cls.char_mem_st+2, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3,
                                      cls.char_mem_st+4, 1))
        )
        script.insert_commands(commands.get_bytearray(), pos)

        cls.replace_storyline_triggers(script)
        cls.modify_pc_starups(script)
        cls.rewrite_pc_arbs(script)
        cls.modify_nagaette_battle(script)

    @classmethod
    def modify_pc_starups(cls, script: Event):
        """
        Modify controllable checks to make animations persist during the
        recruit cutscene.
        """

        block = (
            EF().set_label('start')
            .add_if(
                EC.if_mem_op_value(0x7F0218, OP.EQUALS, 0),
                EF().add(EC.generic_command(0xAF))
                .jump_to_label(EC.jump_back(), 'start')
            )
            .add(EC.break_cmd())
            .jump_to_label(EC.jump_back(), 'start')
        )

        normal_pc_obj_ids = (1, 2, 5, 6, 7)
        for obj_id in normal_pc_obj_ids:
            pos = script.find_exact_command(
                EC.set_controllable_infinite(),
                script.get_object_start(obj_id)
            )
            script.insert_commands(block.get_bytearray(), pos)
            pos += len(block)
            script.delete_commands(pos, 1)

        # Change frog object to be normal (recruit module will handle recruit)
        frog_obj = 4
        script.set_function(
            frog_obj, FID.STARTUP,
            EF().add(EC.load_pc_in_party(ctenums.CharID.FROG))
            .add(EC.return_cmd())
            .append(block)
        )
        script.set_function(frog_obj, FID.ACTIVATE,
                            EF().add(EC.return_cmd()))

    @classmethod
    def modify_nagaette_battle(cls, script: Event):
        """
        Change the Nagaette battle animation.  Relies on pc arbs being redone.
        """

        # Crono Arbs:
        # Arb0 - Moving toward the hairpin, before "What did you find?"
        # Arb1 - Looking around while Nagaettes appear
        # Arb2 - Move in position for battle and do battle ready animation
        # Arb3 - Move into ambush position after the battle
        # Arb4 - Play battle ready animation during ambush
        # Arb5 - Stop animating, to get out of battle animation.
        # Arb6 - Change facing to follow Frog as he moves down

        # Lucca Arbs:
        # Arb0 - Moving toward the hairpin, before "What did you find?"
        # Arb1 - "A hair pin.  That's guardia's royal crest."
        # Arb2 - Looking around as Nagaettes appear (diff from Crono's)
        # Arb3 - Surprise animation as Nagaettes appear
        # Arb4 - Get in position for battle
        # Arb5 - Move to ambush position "That was close"
        # Arb6 - Scared position during Ambush
        # Arb7 - Get hit by nagaette in ambush
        # Arb8 - "It's a talking frog I hate frogs" + some move/anim_id
        # Arb9 - Some move/anim + "You don't seem like a bad..."
        # ArbA - Decision to go with Frog
        # ArbB - Anim + "Nice to meet you, Frog"
        # ArbC - Very weird reload Lucca.  Has to do with the fact that Lucca
        #        is given Controllable(Once) instead of infinite?

        # Instead of doing lots of insert/deletes, just rewrite the thing.
        hairpin_obj = 0xF

        def make_safe_pc_func_call(  # TODO: just use the owu version.
                func_id: FID, priority: int, char_mem_st: int
        ) -> EF:
            """
            Call each PC's func_id with given priority.  Cont/Halt depending on
            whether PC exists.
            """
            # This doesn't work unless the function being called is basically
            # the same for all PCs.  Probably we should just call cont on PC2
            # and 3 and Half on PC1 for the same effect.
            ret_fn = (
                EF().add_if_else(
                    # If PC2 is  empty
                    EC.if_mem_op_value(char_mem_st+2, OP.GREATER_THAN, 6),
                    EF().add(
                        # Call PC1 with Halt
                        EC.call_pc_function(0, func_id, priority, FS.HALT)
                    ),
                    EF().add(
                        # Call PC1 with Cont
                        EC.call_pc_function(0, func_id, priority, FS.CONT)
                    )
                    .add_if_else(
                        # IF PC3 is empty
                        EC.if_mem_op_value(char_mem_st+4, OP.GREATER_THAN, 6),
                        # Call PC2 with Halt
                        EF().add(EC.call_pc_function(1, func_id, priority,
                                                     FS.HALT)),
                        # Call PC2 with cont and PC3 with Halt
                        EF().add(EC.call_pc_function(1, func_id, priority,
                                                     FS.CONT))
                        .add(EC.call_pc_function(2, func_id, priority,
                                                 FS.HALT))
                    )
                )
            )
            return ret_fn

        act_func = (
            EF().add_if(
                EC.if_mem_op_value(0x7F0210, OP.NOT_EQUALS, 0),
                EF().add(EC.return_cmd())
            )
            .add(EC.assign_val_to_mem(1, 0x7F0218, 1))
            .add(EC.set_explore_mode(False))
            .add(EC.set_object_script_processing(0xE, True))
            .append(make_safe_pc_func_call(
                FID.ARBITRARY_0, 3, cls.char_mem_st))
            .add(EC.remove_object(0xE))
            # .add(EC.auto_text_box(test_id1))
        )
        for obj_id in range(0x10, 0x14):
            act_func.add(EC.set_object_script_processing(obj_id, True))

        (
            act_func.add(EC.play_song(0))
            .add(EC.call_obj_function(9, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_1, 3, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_1, 3, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_1, 3, FS.SYNC))
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_obj_function(0xC, FID.ARBITRARY_0, 3, FS.CONT))
        )
        act_func.set_label('sync1')
        act_func.add_if(
            EC.if_mem_op_value(0x7F0214, OP.NOT_EQUALS, 4),
            EF().jump_to_label(EC.jump_back(), 'sync1')
        )
        act_func.add(EC.generic_command(0xAD, 0x3))

        for obj_id in range(0x10, 0x14):
            sync = FS.HALT if obj_id == 0x13 else FS.CONT
            act_func.add(EC.play_sound(0x7B))
            act_func.add(
                EC.call_obj_function(obj_id, FID.ARBITRARY_0, 3, sync))

        act_func.add(EC.generic_command(0xAD, 7))

        for obj_id in range(9, 0xD):
            act_func.add(EC.remove_object(obj_id))

        for obj_id in (0x14, 0x16, 0x15, 0x17):
            act_func\
                .add(EC.set_object_script_processing(obj_id, True)) \
                .add(EC.play_sound(0x6F)) \
                .add(EC.call_obj_function(obj_id, FID.ARBITRARY_0, 3, FS.CONT))

        (
            act_func.append(make_safe_pc_func_call(FID.ARBITRARY_2, 3,
                                                   cls.char_mem_st))
            .add(EC.generic_command(0xAD, 2))
            .add(EC.generic_command(0xE7, 0, 4))
            .set_label('sync2')
            .add_if(
                EC.if_mem_op_value(0x7F0216, OP.NOT_EQUALS, 4),
                EF().jump_to_label(EC.jump_back(), 'sync2')
            )
            .add(EC.generic_command(0xD8, 0x92, 0x80))
            .add(EC.set_flag(memory.Flags.MANORIA_SANCTUARY_NAGAETTE_BATTLE))
            # Moved to the recruit spot.
            # .add(EC.set_explore_mode(False))
            # .append(make_safe_pc_func_call(FID.ARBITRARY_3, 3,
            #                                cls.char_mem_st))
            # .add(EC.play_song(0x16))
            # .add(EC.play_sound(0x7B)).add(EC.play_sound(0x7B))
            # .add(EC.play_sound(0x6F)).add(EC.play_sound(0x6F))
            # .add(EC.call_obj_function(0x10, FID.ARBITRARY_2, 3, FS.HALT))
            # .add(EC.call_pc_function(1, FID.ARBITRARY_4, 3, FS.HALT))
            # .add(EC.generic_command(0xAD, 1))
            # .add(EC.set_object_script_processing(0x18, True))
            # .add(EC.call_obj_function(0x18, FID.ARBITRARY_0, 3, FS.CONT))
            # .add(EC.call_pc_function(1, FID.ARBITRARY_5, 3, FS.HALT))
            # .add(EC.call_pc_function(2, FID.ARBITRARY_5, 3, FS.CONT))
            # .add(EC.call_pc_function(0, FID.ARBITRARY_5, 3, FS.HALT))
            # .add(EC.call_obj_function(4, FID.ARBITRARY_0, 3, FS.HALT))
            .add(EC.assign_val_to_mem(1, 0x7F0210, 1))
            .add(EC.assign_val_to_mem(0, 0x7F0218, 1))
            .add(EC.break_cmd())
            # .add(EC.call_pc_function(0, FID.ARBITRARY_7, 3, FS.HALT))
            .add(EC.play_song(0x10))
            .add(EC.party_follow())
            .add(EC.set_explore_mode(True))
        )
        # act_func.add(EC.auto_text_box(test_id1))
        act_func.add(EC.return_cmd())
        script.set_function(hairpin_obj, FID.ACTIVATE, act_func)

    @classmethod
    def rewrite_pc_arbs(cls, script: Event):
        """
 s       Redo the PC arbs so that any pc can participate in the recruit scene.
        """

        arb4 = (
            EF().add(EC.play_animation(9))
            .add(EC.pause(0.5))
            .add(EC.play_animation(0))
            .add(EC.set_own_facing('up'))
            .add(EC.play_animation(9))
            .add(EC.return_cmd())
        )

        # Arb0 - Move into position around the hairpin
        char_order = (
            ctenums.CharID.CRONO, ctenums.CharID.MARLE, ctenums.CharID.LUCCA,
            ctenums.CharID.FROG, ctenums.CharID.ROBO, ctenums.CharID.AYLA,
            ctenums.CharID.MAGUS
        )
        for ind, char_id in enumerate(char_order):
            script.set_function(cls.crono_obj+ind, FID.ARBITRARY_0,
                                cls.make_arb0(char_id))
            script.set_function(cls.crono_obj+ind, FID.ARBITRARY_1,
                                cls.make_arb1(char_id))
            script.set_function(cls.crono_obj+ind, FID.ARBITRARY_2,
                                cls.make_arb2(char_id))
            script.set_function(cls.crono_obj+ind, FID.ARBITRARY_3,
                                cls.make_arb3(char_id))
            script.set_function(cls.crono_obj+ind, FID.ARBITRARY_4, arb4)
            script.set_function(cls.crono_obj+ind, FID.ARBITRARY_5,
                                cls.make_arb5(char_id))
            script.set_function(cls.crono_obj+ind, FID.ARBITRARY_6,
                                cls.make_arb6(char_id))

    @classmethod
    def make_arb0(cls, char_id: ctenums.CharID) -> EF:
        """
        Make a PC arb0 to move around the coral hairpin.
        """
        arb0 = (
            EF().add_if(
                # If PC1 is char_id, Copy Crono's arb0
                EC.if_mem_op_value(cls.char_mem_st, OP.EQUALS, char_id),
                EF().add(EC.play_animation(1))
                .add(EC.move_sprite(8, 0xB, is_animated=True))
                .add(EC.play_animation(0))
                .add(EC.set_own_facing('right'))
            )
            .add_if(
                # If PC2 is char_id, Copy Lucca's arb0
                EC.if_mem_op_value(cls.char_mem_st+2, OP.EQUALS, char_id),
                EF()  #.add(EC.assign_val_to_mem(1, 0x7F0218, 1))
                .add(EC.set_move_speed(0x28))
                .add(EC.play_animation(1))
                .add(EC.move_sprite(9, 0xB))
                .add(EC.set_own_facing('left'))
                .add(EC.pause(1))
                .add(EC.play_animation(0x1D))
                .add(EC.pause(2))
                .add(EC.play_animation(0x19))
                .add(EC.pause(1))
                .add(EC.play_animation(9))
                .add(EC.pause(1))
                .add(EC.play_animation(0))
            )
            .add_if(
                # If PC3 is char_id, make something up.
                EC.if_mem_op_value(cls.char_mem_st+4, OP.EQUALS, char_id),
                EF().add(EC.play_animation(1))
                .add(EC.set_move_speed(0x40))
                .add(EC.move_sprite(8, 0xD))
                .add(EC.play_animation(0))
                .add(EC.set_own_facing('up'))
                .add(EC.pause(6))  # just so that PC3 finishes last
            )
            .add(EC.return_cmd())
        )

        return arb0

    @classmethod
    def make_arb1(cls, char_id: ctenums.CharID) -> EF:
        """
        Make arb1 for PCs to look around while Nagaettes circle.
        """

        arb1 = (
            EF().add_if(
                # If PC1 is char_id, Copy Crono's arb1
                EC.if_mem_op_value(cls.char_mem_st, OP.EQUALS, char_id),
                EF().add(EC.generic_command(0xAD, 0x08))  # pauses are hard
                .add(EC.set_own_facing('down'))
                .add(EC.generic_command(0xAD, 0x28))
                .add(EC.set_own_facing('left'))
                .add(EC.generic_command(0xAD, 0x28))
                .add(EC.set_own_facing('right'))
                .add(EC.generic_command(0xAD, 0x10))
                .add(EC.set_own_facing('left'))
                .add(EC.generic_command(0xAD, 0x10))
                .add(EC.set_own_facing('up'))
            )
            .add_if(
                # If PC2 is char_id, Copy Lucca's arb2
                EC.if_mem_op_value(cls.char_mem_st+2, OP.EQUALS, char_id),
                EF().add(EC.generic_command(0xAD, 0x08))  # pauses are hard
                .add(EC.set_own_facing('down'))
                .add(EC.generic_command(0xAD, 0x28))
                .add(EC.set_own_facing('right'))
                .add(EC.generic_command(0xAD, 0x28))
                .add(EC.set_own_facing('left'))
                .add(EC.generic_command(0xAD, 0x10))
                .add(EC.set_own_facing('right'))
                .add(EC.generic_command(0xAD, 0x10))
                .add(EC.set_own_facing('up'))
            )
            .add_if(
                # If PC3 is char_id, make something up.
                EC.if_mem_op_value(cls.char_mem_st+4, OP.EQUALS, char_id),
                EF().add(EC.generic_command(0xAD, 0x08))  # pauses are hard
                .add(EC.set_own_facing('down'))
                .add(EC.generic_command(0xAD, 0x28))
                .add(EC.set_own_facing('left'))
                .add(EC.generic_command(0xAD, 0x28))
                .add(EC.set_own_facing('right'))
                .add(EC.generic_command(0xAD, 0x10))
                .add(EC.set_own_facing('left'))
                .add(EC.generic_command(0xAD, 0x10))
                .add(EC.set_own_facing('up'))
            )
            .add(EC.return_cmd())
        )

        return arb1

    @classmethod
    def make_arb2(cls, char_id: ctenums.CharID) -> EF:
        """
        Make arb2 for PCs to get in position for battle.
        """
        arb2 = (
            EF().add_if(
                # If PC1 is char_id, Copy Crono's arb2
                EC.if_mem_op_value(cls.char_mem_st, OP.EQUALS, char_id),
                EF().add(EC.play_animation(6))
                .add(EC.set_move_speed(0x28))
                .add(EC.move_sprite(5, 0xD))
                .add(EC.set_own_facing('up'))
                # .add(EC.play_animation(0))
                .add(EC.play_animation(0x3))
                .add(EC.pause(0.5))
                # .add(EC.static_animation(0x38))
            )
            .add_if(
                # If PC2 is char_id, Copy Lucca's arb4
                EC.if_mem_op_value(cls.char_mem_st+2, OP.EQUALS, char_id),
                EF().add(EC.play_animation(6))
                .add(EC.set_move_speed(0x28))
                .add(EC.move_sprite(0xA, 0xD))
                .add(EC.set_own_facing('up'))
                .add(EC.play_animation(0))
                .add(EC.play_animation(0x3))
                # .add(EC.static_animation(0xAB))
            )
            .add_if(
                # If PC3 is char_id, make something up.
                EC.if_mem_op_value(cls.char_mem_st+4, OP.EQUALS, char_id),
                EF().add(EC.play_animation(6))
                .add(EC.set_move_speed(0x28))
                .add(EC.move_sprite(7, 0xF))
                .add(EC.set_own_facing('up'))
                .add(EC.play_animation(0))
                .add(EC.play_animation(0x3))
                # .add(EC.static_animation(0xAB))
            )
            .add(EC.return_cmd())
        )

        return arb2

    @classmethod
    def make_arb3(cls, char_id: ctenums.CharID) -> EF:
        """
        Make arb3 for PCs to get in position after the battle.
        """
        arb3 = (
            EF().add_if(
                # If PC1 is char_id, Copy Crono's arb3
                EC.if_mem_op_value(cls.char_mem_st, OP.EQUALS, char_id),
                EF().add(EC.set_move_properties(True, True))
                .add(EC.set_move_speed(0x20))
                .add(EC.play_animation(1))
                .add(EC.move_sprite(8, 0xC))
                .add(EC.play_animation(0))
                .add(EC.set_own_facing('up'))
            )
            .add_if(
                # If PC2 is char_id, Copy Lucca's arb5
                EC.if_mem_op_value(cls.char_mem_st+2, OP.EQUALS, char_id),
                EF().add(EC.set_move_properties(True, True))
                .add(EC.pause(1))
                .add(EC.play_animation(1))
                .add(EC.set_move_speed(0x20))
                .add(EC.move_sprite(0x7, 0xA))
                .add(EC.set_own_facing('down'))
                .add(EC.play_animation(0x21))
                .add(EC.pause(2))
            )
            .add_if(
                # If PC3 is char_id, make something up.
                EC.if_mem_op_value(cls.char_mem_st+4, OP.EQUALS, char_id),
                EF().add(EC.reset_animation()).add(EC.pause(10))
            )
            .add(EC.return_cmd())
        )

        return arb3

    @classmethod
    def make_arb5(cls, char_id: ctenums.CharID) -> EF:
        """
        Make arb5 for PCs to react to ambush.
        """
        arb5 = (
            EF().add_if(
                # If PC1 is char_id, Copy Crono's arb3
                EC.if_mem_op_value(cls.char_mem_st, OP.EQUALS, char_id),
                EF().add(EC.play_animation(3))
            )
            .add_if(
                # If PC2 is char_id, Copy Lucca's arb7
                EC.if_mem_op_value(cls.char_mem_st+2, OP.EQUALS, char_id),
                EF().add(EC.set_own_facing('right'))
                .add(EC.play_animation(9))
                .add(EC.pause(2))
                .add(EC.play_animation(5))
                .add(EC.set_move_speed(0x48))
                .add(EC.generic_command(0x9C, 0x68, 0x0C))  # vector_move
                .add(EC.play_animation(0x1D))
                .add(EC.set_move_speed(0x28))
                .add(EC.generic_command(0x9C, 0x68, 6))
                .add(EC.assign_val_to_mem(1, 0x7F0218, 1))
                .add(EC.return_cmd())
            )
            .add_if(
                # If PC3 is char_id, make something up.
                EC.if_mem_op_value(cls.char_mem_st+4, OP.EQUALS, char_id),
                EF().add(EC.play_animation(3))
            )
            .add(EC.return_cmd())
        )

        return arb5

    @classmethod
    def make_arb6(cls, char_id: ctenums.CharID) -> EF:
        """
        Make arb6 for PCs to react to Frog showing up.
        """
        arb6 = (
            EF().add_if(
                # If PC1 is char_id, Copy Crono's arb5
                EC.if_mem_op_value(cls.char_mem_st, OP.EQUALS, char_id),
                EF().add(EC.play_animation(0)).add(EC.reset_animation())
                .add(EC.set_own_facing('right'))
            )
            .add_if(
                # If PC2 is char_id, Copy Lucca's arb8
                EC.if_mem_op_value(cls.char_mem_st+2, OP.EQUALS, char_id),
                EF().add(EC.set_own_facing('right'))
                .add(EC.play_animation(9))
                .add(EC.generic_command(0xAD, 2))
                .add(EC.play_animation(1))
                .add(EC.set_move_speed(0x20))
                .add(EC.move_sprite(5, 0xD, is_animated=True))
                .add(EC.set_own_facing('right'))
                .add(EC.play_animation(0))

            )
            .add_if(
                # If PC3 is char_id, make something up.
                EC.if_mem_op_value(cls.char_mem_st+4, OP.EQUALS, char_id),
                EF().add(EC.play_animation(0))
                .add(EC.set_own_facing('right'))
            )
            .add(EC.return_cmd())
        )

        return arb6

    @classmethod
    def replace_storyline_triggers(cls, script: Event):
        """
        Replace storyline checks with flag checks.
        """

        # Storyline Values:
        # 12 . Lucca arrives in past
        # - The hairpin won't activate otherwise
        # - This storyline check should just be erased.
        # 15 . Seen through the guise of the nuns at the Cathedral
        # -
        # - Add a flag for the 4x Nagaette battle and use that flag
        # AB . Locked out of 12000 BC

        battle_flag = memory.Flags.MANORIA_SANCTUARY_NAGAETTE_BATTLE

        pos: Optional[int] = None
        while True:
            pos, cmd = script.find_command_opt([0x18], pos)

            if pos is None:
                break

            if cmd.args[0] == 0x12:
                script.delete_jump_block(pos)
            elif cmd.args[0] == 0x15:
                script.replace_jump_cmd(
                    pos, EC.if_not_flag(battle_flag)
                )
            else:
                pos += len(cmd)

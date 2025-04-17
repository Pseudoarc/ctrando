"""Openworld Geno Dome Mainframe"""

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

# Atropos scene notes
# - Atropos's Object (0x1D) has a coordinate checking loop.  It only runs if both
#   poyozos are obtained.  If Atropos is defeated, then her object will be removed.
#   in Obj00, Startup.
# - The loop simply removes exploration and calls Obj00, Arb2.
# - Obj00, Arb2 does the following:
#   - Set 0x7F0212 to 1 can call PC Arb0 (wait fn)
#   - Scroll the screen and move the party (Objs 0D and 0E, Arb 1)
#   - Call Atropos (Obj1D) Activate which plays the whole cutscene up to the battle.
#   - Have the Battle
#   - Change music and call Atropos Arb0
#   - Note: If the magic tab in the room above has not been picked up, it is hidden
#           during most of this scene by calls in this function.

#  So most of the editing needs to be in Atropos (0x1D), Activate.


class EventMod(locationevent.LocEventMod):
    """EventMod for Geno Dome Mainframe"""

    loc_id = ctenums.LocID.GENO_DOME_MAINFRAME
    pc_wait_addr = 0x7F0212
    sync_pc_addr = 0x7F0214
    arb_counter_addr = 0x7F0216
    extra_pc_count_addr = 0x7F021C
    removed_pc1_addr = 0x7F021E
    removed_pc2_addr = 0x7F0220
    atropos_obj = 0x1D
    display_objs: list[int] = [0x1F, 0x20, 0x21]
    mother_brain_obj = 0x22
    mother_brain_extra_obj = 0x23

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Geno Dome Mainframe for an Open World.  This is a big one.
        - Only load Mother Brain + Displays unless Atropos is defeated.
        - Eliminate most of the Atropos cutscene to launch into the fight faster.
        - Redo the party remove/readd functions prior to the Atropos fight.
        - Reload the map after the Atropos fight.
        - Move some Robo functions elsewhere since Robo may not be active.
        - Give some Robo Arb functions to everyone (high switch hit)
        - Shorten the Mother Brain intro cutscene.
        """
        cls.modify_pc_arbs(script)
        cls.modify_boss_obj_loads(script)
        cls.modify_atropos_pre_battle(script)
        cls.modify_atropos_post_battle(script)
        cls.modify_jump_switch(script)
        cls.modify_mother_brain_battle(script)

        owu.update_add_item(
            script,
            script.get_function_start(0x26, FID.ACTIVATE)
        )

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give everyone the same functions so that anyone can do the solo fight.
        """

        # Arb0 - Wait function already shared by everyone [No Change]
        # Arb1 - Remove member from Atropos scene and from active party. [Robo Change]
        # Arb2 - A brandish weapon animation [Robo Change]
        # Arb3 - (Orig. Robo) Let me handle this alone animation [non-Robo change]
        # Arb4 - A reload into party function. [all change]
        # Arb5 - Get the Crisis and Terra Arms
        # Arb6 - Jump up to hit the switch
        # Arb7 - Fall down after hitting the switch

        robo_obj = 4

        script.set_function(
            robo_obj,
            FID.ARBITRARY_2,
            EF()
            .add(EC.play_sound(8))
            .add(EC.play_animation(0xC))
            .add(EC.static_animation(49))
            .add(EC.return_cmd()),
        )

        add_item_str_id = owu.add_default_treasure_string(script)
        script.set_function(
            0,
            FID.ARBITRARY_3,
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.TERRA_ARM, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(add_item_str_id))
            .add(EC.assign_val_to_mem(ctenums.ItemID.CRISIS_ARM, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(add_item_str_id))
            .add(EC.return_cmd())
        )

        for obj_id in range(1, 8):
            pc_id = ctenums.CharID(obj_id - 1)
            new_arb1 = (
                EF()
                .add(EC.set_move_speed(0x50))
                .add(EC.pause(2))
                .add(EC.reset_animation())
                .add(EC.move_sprite(0x21, 0x2C))
                .add(EC.move_sprite(0x2A, 0x2C))
                # We're using this weird remove from active party because
                # plain remove causes post-battle visual bugs.  No idea why.
                # Move to reserve causes no bugs bug leaves junk in the reserve party.
                # .add(EC.move_pc_to_reserve(pc_id))
                .add(EC.remove_pc_from_active_party(pc_id))
                .add(EC.add(cls.sync_pc_addr, 1))
                .add(EC.return_cmd())
            )
            script.set_function(obj_id, FID.ARBITRARY_1, new_arb1)

            face_right_block = EF().add(EC.set_own_facing("right"))
            if obj_id == robo_obj:
                face_right_block.add(EC.loop_animation(0x3E, 1))
                face_right_block.add(EC.static_animation(0xAD))
                face_right_block.add(EC.play_sound(0xC6))

            new_arb3 = (
                EF()
                .add(EC.get_result(cls.arb_counter_addr))
                .add_if(
                    EC.if_result_equals(0),
                    EF()
                    .add(EC.pause(3))
                    .add(EC.reset_animation())
                    .add(EC.move_sprite(0x1F, 0x2C))
                    .append(face_right_block)
                    .add(EC.return_cmd()),
                )
                .add_if(
                    EC.if_result_equals(1),
                    EF()
                    .add(EC.play_animation(0))
                    .add(EC.set_own_facing("left"))
                    .add(EC.return_cmd()),
                )
                .add_if(
                    EC.if_result_equals(2),
                    EF()
                    .add(EC.play_animation(3))
                    .add(EC.move_sprite(0x1D, 0x2C))
                    .add(EC.play_animation(0x1D))
                    .add(EC.return_cmd()),
                )
                .add(EC.return_cmd())
            )

            script.set_function(obj_id, FID.ARBITRARY_3, new_arb3)

            new_arb4 = (
                EF()
                .add(EC.load_pc_in_party(pc_id))
                .add(EC.set_object_coordinates_tile(0x2A, 0x2C))
                .add(EC.return_cmd())
            )
            script.set_function(obj_id, FID.ARBITRARY_4, new_arb4)

            new_arb6 = (
                EF()
                .add(EC.set_move_destination(True, False))
                .add(EC.pause(0.063))
                .add(EC.set_move_speed(0x30))
                .add(EC.play_animation(0x20))
                .add(EC.pause(1))
                .add(EC.play_animation(0x1E))
                .add(EC.play_sound(2))
                .add(EC.move_sprite(0x20, 0x26, True))
                .add(EC.pause(0.5))
                .add(EC.return_cmd())
            )
            new_arb7 = (
                EF()
                .add(EC.move_sprite(0x20, 0x28, True))
                .add(EC.play_sound(0x8D))
                .add(EC.increment_mem(cls.sync_pc_addr))
                .add(EC.play_animation(0))
                .add(EC.return_cmd())
            )

            win_pose_frames: dict[ctenums.CharID, int] = {
                ctenums.CharID.CRONO: 109,
                ctenums.CharID.MARLE: 99,
                ctenums.CharID.LUCCA: 74,
                ctenums.CharID.ROBO: 0x5E,
                ctenums.CharID.FROG: 98,
                ctenums.CharID.AYLA: 59,
                ctenums.CharID.MAGUS: 0,
            }
            win_pose_frame = win_pose_frames.get(pc_id, 0)

            new_arb5 = (
                EF()
                .add(EC.move_sprite(9, 9))
                .add(EC.set_object_drawing_status(0x1E, False))
                .add(EC.play_animation(0x1D))
                .add(EC.pause(0.5))
                .add(EC.loop_animation(0xA, 1))
                .add(EC.static_animation(win_pose_frame))
                .add(EC.play_song(0x3D))
                .add(EC.call_obj_function(0, FID.ARBITRARY_3, 4, FS.HALT))
                .add(EC.generic_command(0xEE))  # wait for song end
                .add(EC.return_cmd())
            )
            script.set_function(obj_id, FID.ARBITRARY_5, new_arb5)

            if obj_id != robo_obj:
                script.set_function(obj_id, FID.ARBITRARY_6, new_arb6)
                script.set_function(obj_id, FID.ARBITRARY_7, new_arb7)

    @classmethod
    def modify_atropos_pre_battle(cls, script: Event):
        """
        Rewrite the cutscene prior to the Atropos battle
        """

        pos = script.find_exact_command(
            EC.move_sprite(0x17, 0x2C),
            script.get_function_start(cls.atropos_obj, FID.ACTIVATE),
        )
        end = script.get_function_start(cls.atropos_obj, FID.TOUCH)

        script.delete_commands_range(pos, end)

        pos = script.get_function_start(cls.atropos_obj, FID.TOUCH)
        end = script.find_exact_command(EC.generic_command(0x77, 0x0E))
        script.delete_commands_range(pos, end)

        pre_battle_anim = (
            EF()
            .add(EC.move_sprite(0x1C, 0x2C))
            .add(EC.play_animation(3))
            .add(EC.call_pc_function(2, FID.ARBITRARY_2, 1, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_2, 1, FS.HALT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 1, FS.HALT))
            .add(EC.play_animation(0))
        )
        script.insert_commands(
            pre_battle_anim.get_bytearray(),
            pos,
        )
        pos += len(pre_battle_anim)
        end = script.find_exact_command(EC.return_cmd(), pos)

        script.delete_commands_range(pos, end)

        gather_remove_pc_block = (
            EF()
            .add(EC.reset_byte(cls.extra_pc_count_addr))
            .add(EC.reset_byte(cls.removed_pc1_addr))
            .add(EC.reset_byte(cls.removed_pc2_addr))
            .add(
                EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2, cls.removed_pc1_addr, 1)
            )
            .add_if(
                EC.if_mem_op_value(cls.removed_pc1_addr, OP.LESS_THAN, 7),
                EF().add(EC.increment_mem(cls.extra_pc_count_addr, 1)),
            )
            .add(
                EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, cls.removed_pc2_addr, 1)
            )
            .add_if(
                EC.if_mem_op_value(cls.removed_pc2_addr, OP.LESS_THAN, 7),
                EF().add(EC.increment_mem(cls.extra_pc_count_addr, 1)),
            )
            .add(EC.reset_byte(cls.sync_pc_addr))
            .add(EC.call_pc_function(1, FID.ARBITRARY_1, 1, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_1, 1, FS.CONT))
            .set_label("loop")
            .add_if(
                EC.if_mem_op_mem(
                    cls.sync_pc_addr, OP.LESS_THAN, cls.extra_pc_count_addr
                ),
                EF().jump_to_label(EC.jump_back(), "loop"),
            )
            .add(EC.assign_val_to_mem(0x80, memory.Memory.ACTIVE_PC2, 1))
            .add(EC.assign_val_to_mem(0x80, memory.Memory.ACTIVE_PC3, 1))
            .add(EC.increment_mem(cls.arb_counter_addr, 1))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 1, FS.HALT))
            .add(EC.loop_animation(7, 1))
            .add(EC.play_sound(0xD3))
        )

        script.insert_commands(gather_remove_pc_block.get_bytearray(), pos)

    @classmethod
    def modify_atropos_post_battle(cls, script: Event):
        """
        Modify the scene that plays after the battle.
        """

        pos = script.find_exact_command(EC.get_result(cls.removed_pc1_addr))
        end = script.find_exact_command(EC.reset_byte(0x7F021C), pos)
        script.delete_commands_range(pos, end)

        restore_pc_block = EF()
        for addr in (cls.removed_pc1_addr, cls.removed_pc2_addr):
            restore_pc_block.add(EC.get_result(addr))
            end_label = f"end_{addr:06X}"
            for pc_id in ctenums.CharID:
                pc_obj = pc_id + 1
                restore_pc_block.add_if(
                    EC.if_result_equals(pc_id),
                    EF()
                    .add(EC.add_pc_to_active(pc_id))
                    .add(EC.call_obj_function(pc_obj, FID.ARBITRARY_4, 4, FS.HALT))
                    .jump_to_label(EC.jump_forward(), end_label),
                )
            restore_pc_block.set_label(end_label)
        restore_pc_block.add(EC.call_obj_function(0xE, FID.ARBITRARY_1, 1, FS.HALT))

        (
            restore_pc_block.add(EC.play_sound(0xC7))
            .add(EC.pause(1))
            .add(EC.increment_mem(cls.arb_counter_addr))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 1, FS.HALT))
            .add(EC.vector_move(270, 1, False))
            .add(EC.vector_move(90, 1, False))
        )
        script.insert_commands(restore_pc_block.get_bytearray(), pos)
        pos += len(restore_pc_block)

        pos = script.find_exact_command(EC.pause(3), pos)
        script.data[pos + 1] = 0x10

        pos = script.find_exact_command(EC.reset_byte(cls.pc_wait_addr), pos)
        script.insert_commands(
            EF()
            .add(EC.darken(4))
            .add(EC.fade_screen())
            .add(
                EC.change_location(
                    ctenums.LocID.GENO_DOME_MAINFRAME, 0x1D, 0x2C, Facing.LEFT, 0, True
                )
            )
            .add(EC.return_cmd())
            .get_bytearray(),
            pos,
        )

    @classmethod
    def modify_jump_switch(cls, script: Event):
        """
        Change the jump switch to use PC00 instead of Robo.
        """

        pos = script.find_exact_command(
            EC.get_object_facing(4, 0x7F021A), script.get_function_start(9, FID.TOUCH)
        )
        repl_cmd = EC.get_pc_facing(0, 0x7F021A)
        script.data[pos : pos + len(repl_cmd)] = repl_cmd.to_bytearray()

        pos = script.find_exact_command(
            EC.call_obj_function(4, FID.ARBITRARY_6, 1, FS.HALT), pos
        )
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_6, 1, FS.HALT)
        script.data[pos : pos + len(repl_cmd)] = repl_cmd.to_bytearray()

        pos = script.find_exact_command(
            EC.call_obj_function(4, FID.ARBITRARY_7, 1, FS.CONT), pos
        )
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_7, 1, FS.CONT)
        script.data[pos : pos + len(repl_cmd)] = repl_cmd.to_bytearray()

    @classmethod
    def modify_mother_brain_battle(cls, script: Event):
        """
        - Remove the dialog that plays leading up to the mother brain fight.
        - Remove the dialog after the battle.
        - Inline the Crisis/Terra arm pickup
        """

        # delete pre-battle dialogue
        pos = (
            script.find_exact_command(
                EC.generic_command(0xAD, 0x20),
                script.get_function_start(0x1E, FID.STARTUP),
            )
            + 2
        )
        script.delete_commands(pos, 7)

        pos = script.find_exact_command(EC.play_sound(0xA0), pos)
        script.delete_commands(pos, 3)

        pos = script.find_exact_command(
            EC.call_obj_function(4, FID.ARBITRARY_8, 1, FS.HALT), pos
        )
        end = script.find_exact_command(EC.generic_command(0xEB, 0, 0xFF), pos)
        script.delete_commands_range(pos, end)
        script.insert_commands(
            EF()
            .add(EC.call_pc_function(0, FID.ARBITRARY_5, 1, FS.HALT))
            .add(EC.darken(4))
            .add(EC.fade_screen())
            .get_bytearray(),
            pos,
        )

    @classmethod
    def modify_boss_obj_loads(cls, script: Event):
        """
        Make sure that Mother Brain can't load until Atropos is gone.
        Stop Loading Atropos when she is defeated.
        """

        # Make Mother Brain never load
        mother_brain_objs = (cls.mother_brain_obj, cls.mother_brain_extra_obj) + tuple(
            x for x in cls.display_objs
        )

        for obj_id in mother_brain_objs:
            new_block = (
                EF()
                .add_if(
                    EC.if_not_flag(memory.Flags.GENO_DOME_ATROPOS_DEFEATED),
                    EF().jump_to_label(EC.jump_forward(), "remove_block"),
                )
                .add_if(
                    EC.if_flag(memory.Flags.GENO_DOME_MOTHER_BRAIN_DEFEATED),
                    EF().jump_to_label(EC.jump_forward(), "remove_block"),
                )
                .jump_to_label(EC.jump_forward(), "end")
                .set_label("remove_block")
                .add(EC.remove_object(obj_id))
                .add(EC.return_cmd())
                .add(EC.end_cmd())
                .set_label("end")
            )

            script.insert_commands(
                new_block.get_bytearray(),
                script.get_function_start(obj_id, FID.STARTUP),
            )

        # Make Atropos never load if this spot's boss is defeated.
        # This is important for boss rando sprite limits and for removing the
        # loop which checks for the battle trigger.
        pos = script.get_function_start(cls.atropos_obj, FID.STARTUP)
        script.insert_commands(
            EF()
            .add_if(
                EC.if_flag(memory.Flags.GENO_DOME_ATROPOS_DEFEATED),
                EF().add(EC.return_cmd()).add(EC.end_cmd()),
            )
            .get_bytearray(),
            pos,
        )

"""Update Leene Square for an open world."""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.recruits import recruitassign

from ctrando.base import openworldutils as owu

class EventMod(locationevent.LocEventMod):
    """EventMod for Leene Square"""
    loc_id = ctenums.LocID.LEENE_SQUARE  # 1B7

    npc_marle_obj = 3
    real_marle_obj = 2

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update Leene Square.  This one is a doozy.
        - Update wandering Marle for recruitment (ugly)
        - Remove some storyline-related npc additions/removals
        - Remove some trial flashbacks
        """
        cls.remove_trial_flashbacks(script)
        cls.fix_marle_objects(script)
        cls.remove_candy(script)
        cls.remove_fair_dialogue(script)
        cls.remove_telepod_blockers(script)
        cls.remove_storyline_npcs(script)
        cls.update_collision(script)
        # cls.update_marle(script)  Move this to recruit stuff

        # Default condition is to have no recruit.  So set the flag for the
        # pendant to be on the ground automatically.
        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add_if(
                EC.if_not_flag(memory.Flags.FAIR_PENDANT_PICKED_UP),
                EF().add(EC.set_flag(memory.Flags.FAIR_PENDANT_NOT_FOUND))
            ).get_bytearray(),
            pos
        )
        owu.update_add_item(script, pos, False)
        pos = script.find_exact_command(EC.remove_object(0xF))
        script.insert_commands(
            EC.auto_text_box(owu.add_default_treasure_string(script))
            .to_bytearray(), pos
        )

        # Remove setting some Marle flags so maybe we can repurpose them.
        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.PEDNANT_BEFORE_MARLE_OLD),
            script.get_function_start(0xF, FID.ACTIVATE)
        )
        script.delete_commands(pos, 2)

    @classmethod
    def remove_trial_flashbacks(cls, script: locationevent.LocationEvent):
        """Remove all blocks related to Crono trial flashbacks."""

        old_trial_counter = memory.Memory.CRONO_TRIAL_PC3
        flashback_cmd = EC.if_mem_op_value(
            old_trial_counter,
            OP.EQUALS, 1, 1, 0
        )

        pos = script.find_exact_command(flashback_cmd)
        script.delete_jump_block(pos)

        flashback_cmd = EC.if_mem_op_value(
            old_trial_counter,
            OP.EQUALS, 4, 1, 0
        )

        # Get the ones in Crono's object
        pos = script.find_exact_command(flashback_cmd, pos)
        script.delete_jump_block(pos)

        pos += 1  # Skip over a return and get the rest
        for _ in range(5):
            script.delete_jump_block(pos)

        pos = script.find_exact_command(
            EC.if_mem_op_value(memory.Memory.STORYLINE_COUNTER,
                               OP.GREATER_OR_EQUAL, 8),
            script.get_object_start(0xF)
        )
        script.delete_jump_block(pos)

        # There are other flashback pieces, but they are in npc Marle object
        # which is handled by the recruit setting.

    @classmethod
    def fix_marle_objects(cls, script: locationevent.LocationEvent):
        """
        There are two Marle objects:
          1) The "real" Marle for storlyline >= 0x49 which is ignored before
          2) The NPC Marle which conditionally loads as in-party depending on
             the status of the scene.
        This will dummy out but NOT remove the NPC Marle and make the normal
        Marle object a standard character object.  We keep the object around so
        that we can alter its commands for recruit assignment.
        """

        script.set_function(cls.npc_marle_obj, FID.STARTUP,
                            EF().add(EC.return_cmd()).add(EC.end_cmd()))

        script.set_function(cls.npc_marle_obj, FID.ACTIVATE,
                            EF().add(EC.return_cmd()))

        for fid in range(FID.TOUCH, FID.ARBITRARY_8):
            script.set_function(cls.npc_marle_obj, fid, EF())

        script.set_function(
            cls.real_marle_obj, FID.STARTUP,
            EF()
            .add(EC.load_pc_in_party(ctenums.CharID.MARLE))
            .add(EC.return_cmd())
            .add(EC.set_controllable_infinite())
        )

    @classmethod
    def remove_candy(cls, script: locationevent.LocationEvent):
        """
        Remove the Marle candy check.
        """

        # We'll rename this, so manually create it
        flag = memory.FlagData(memory.Memory.MARLEFLAGS, 0x08)
        flag_jump = EC.if_flagdata(flag)

        pos = script.find_exact_command(
            flag_jump,
            script.get_function_start(0x0E, FID.STARTUP),
            script.get_function_end(0x0E, FID.STARTUP)
        )
        script.delete_jump_block(pos)
        script.delete_commands(pos, 1)  # goto

        script.set_function(0xD, FID.ARBITRARY_1, EF())

    @classmethod
    def remove_fair_dialogue(cls, script: locationevent.LocationEvent):
        """
        Remove extra dialogue from exploring the fair with Marle.
        Also clean up some flag setting around that dialogue.
        """

        # Cat girl dialogue
        start, end = script.get_function_bounds(0x0C, FID.ACTIVATE)
        branch_cmd = EC.if_mem_op_value(memory.Memory.STORYLINE_COUNTER,
                                        OP.LESS_THAN, 0x49, 1)

        for _ in range(2):
            start = script.find_exact_command(branch_cmd, start, end)
            script.delete_jump_block(start)

        # Soda contest
        start, end = script.get_function_bounds(0x1B, FID.ACTIVATE)
        start = script.find_exact_command(branch_cmd, start, end)
        script.delete_jump_block(start)

        # Eating lunch -- also clean up
        set_flag_cmd = EC.set_bit(0x7F0054, 0x04)

        start, end = script.get_function_bounds(0x1C, FID.ACTIVATE)
        pos = script.find_exact_command(set_flag_cmd, start, end)
        script.delete_commands(pos, 1)
        pos += 1  # skip over hide command
        script.delete_jump_block(pos)  # If fairflags
        script.delete_jump_block(pos)  # If storyline < 0x49

    @classmethod
    def remove_telepod_blockers(cls, script: locationevent.LocationEvent):
        """
        Dummy out the two NPCs blocking off the telepod exhibit
        """
        for obj_id in (0x10, 0x11):
            script.set_function(
                obj_id, FID.STARTUP,
                EF().add(EC.return_cmd()).add(EC.end_cmd())
            )

            script.set_function(obj_id, FID.ACTIVATE,
                                EF().add(EC.return_cmd()))
            script.set_function(obj_id, FID.TOUCH, EF())
            script.set_function(obj_id, FID.ARBITRARY_0, EF())

    @classmethod
    def remove_storyline_npcs(cls, script: locationevent.LocationEvent):
        """Remove the "merchants restocking" NPC that appears at 0x27"""
        draw_cmd = EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0x27, 1)
        repl_cmd = EC.if_mem_op_value(0x7F006E, OP.EQUALS, 5, 1)

        start, end = script.get_function_bounds(0x1D, FID.STARTUP)
        pos = script.find_exact_command(draw_cmd, start, end)
        script.replace_jump_cmd(pos, repl_cmd)

    @classmethod
    def update_collision(cls, script: locationevent.LocationEvent):
        """
        Change the collision b/t Crono and Marle.
        - Shorten time Crono is on the ground.
        - Add a partyfollow to regroup the team to avoid weird movement.
        """

        pos = script.find_exact_command(
            EC.static_animation(0x67),
            script.get_function_start(1, FID.ARBITRARY_0)
        )
        script.delete_commands(pos)
        script.insert_commands(
            EF().add(EC.set_own_facing('right'))
            .add(EC.play_animation(5)).get_bytearray(), pos
        )

        pos = script.find_exact_command(EC.static_animation(0x45), pos)
        script.data[pos: pos+2] = EC.play_animation(0x8).to_bytearray()

        pos = script.find_exact_command(
            EC.generic_command(0xAD, 0xF0), pos
        )
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(EC.return_cmd(), pos)
        script.insert_commands(
            EF().add(EC.party_follow())
            .add(EC.set_explore_mode(True)).get_bytearray(), pos)

    @classmethod
    def update_marle(cls, script: locationevent.LocationEvent):
        """
        Update the Marle objects in the Leene's Square script.

        - There are two Marle objects:
          1) The "real" Marle for storlyline >= 0x49 which is ignored before
          2) The NPC Marle which conditionally loads as in-party depending on
             the status of the scene.
          We are going to merge them into one object and rewrite most of the
          related functions.
        """

        # Track object 2's coordinates instead of object 3
        pos = script.find_exact_command(
            EC.get_object_coordinates(3, 0x7F021A, 0x7F021C)
        )
        script.data[pos+1] = 2*2

        script.set_function(
            0, FID.ARBITRARY_0,
            EF()
            .add(EC.call_obj_function(2, FID.ARBITRARY_1, 1, FS.CONT))
            .add(EC.return_cmd())
        )

        has_item_id = script.add_py_string('Has the item.{null}')
        no_item_id = script.add_py_string('No item.{null}')
        recruit_char = ctenums.CharID.MARLE

        script.set_function(2, FID.STARTUP,
                            build_recruit_startup(recruit_char))
        script.set_function(2, FID.ACTIVATE,
                            build_recruit_activate(recruit_char,
                                                   ctenums.ItemID.PENDANT,
                                                   has_item_id,
                                                   no_item_id))
        script.set_function(2, FID.TOUCH,
                            build_recruit_touch(2))
        script.set_function(2, FID.ARBITRARY_0,
                            build_recruit_arb_0())
        script.set_function(2, FID.ARBITRARY_1,
                            build_recruit_arb_1())
        script.remove_object(3)


def build_recruit_startup(char_id: ctenums.CharID) -> EF:
    """
    Builds the startup function for the pc who should be the fair recruit.
    """
    startup_ef = (
        EF()
        .add_if_else(
            EC.if_flag(memory.Flags.HAS_FAIR_RECRUIT),
            (  # Normal party load
                EF()
                .add(EC.load_pc_in_party(char_id))
            ),
            (  # Else set the npc Marle's initial position
                EF()
                .add(EC.load_pc_always(char_id))
                .add(EC.set_move_speed(0x40))
                .add(EC.set_object_coordinates_tile(0x21, 0x08))
                .add_if(
                    EC.if_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT),
                    (
                        EF()
                        .add(EC.set_object_coordinates_tile(0x1C, 0x0D))
                    )
                )
            )
        )
        .add(EC.return_cmd())
        .set_label('post_return')
        .add_if(
            EC.if_flag(memory.Flags.HAS_FAIR_RECRUIT),
            (  # Normal controllable infinite
                EF()
                .add(EC.set_controllable_infinite())
                .add(EC.end_cmd())
            )
        )
        .add_if(
            EC.if_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE),
            (
                EF()
                .add(EC.move_sprite(0x1B, 0x0D))
                .add(EC.set_own_facing('up'))
                .add(EC.loop_animation(0x17, 4))
                .add(EC.move_sprite(0x17, 0x0D))
                .add(EC.loop_animation(0x17, 4))
            )
        )
        .jump_to_label(EC.jump_back(), 'post_return')
    )

    return startup_ef


# TODO: Can this be removed because it's in the recruit steter?
def build_recruit_activate(
        char_id: ctenums.CharID,
        required_item: ctenums.ItemID,
        has_item_str_id: int,
        no_item_str_id: int
) -> EF:
    """Ask for item or join party."""
    prelim_ef = (
        EF()
        .add(EC.reset_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT))
        .add(EC.break_cmd())
    )

    act_ef = (
        EF()
        .add_if(
            EC.if_flag(memory.Flags.HAS_FAIR_RECRUIT),
            EF().add(EC.return_cmd())
        )
        .add_if(
            EC.if_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE),
            EF().add(EC.return_cmd())
        )
        .add_if_else(
            EC.if_has_item(required_item),
            EF()
            .add(EC.text_box(has_item_str_id))
            .append(prelim_ef)
            .append(
                recruitassign.build_recruit_function(
                    char_id, memory.Flags.HAS_FAIR_RECRUIT, 0x7F0300)
            ),
            EF().add(EC.text_box(no_item_str_id))
        )
        .add(EC.return_cmd())
    )

    return act_ef


def build_recruit_touch(recruit_obj_id: int) -> EF:
    """Copied from vanilla.  Collision + item flying"""
    touch_ef = (
        EF()
        .add_if(
            EC.if_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE),
            EF()
            .add(EC.reset_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE))
            .add(EC.set_explore_mode(False))
            # Make Sparkle fly off
            .add(EC.call_obj_function(0x0E, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.play_song(0))
            # Call to obj 0 -> call to obj 3
            # Will need to keep this object straight in char rando.
            .add(EC.call_obj_function(0, FID.ARBITRARY_0, 1, FS.CONT))
            # Try calling directly
            # .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_1, 1,
            #                           FS.CONT))
            .add(EC.pause(0.750))
            # Make the cat run away if it's following.
            .add(EC.call_obj_function(0xD, FID.ARBITRARY_0, 3, FS.CONT))
            # Make the bell ring
            .add(EC.call_obj_function(0x12, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.pause(0.5))
            .add(EC.set_own_facing('up'))
            .add(EC.loop_animation(0x13, 2))
            .add(EC.set_move_speed(0x20))
            .add(EC.follow_pc_once(0))
            .add(EC.set_own_facing_pc(0))
            .add(EC.static_animation(0x4A))
            .add(EC.pause(0.5))
            .add(EC.vector_move(0, 8, False))
            .add(EC.static_animation(0x53))
            .add(EC.pause(0.5))
            .add(EC.pause(0.5))
            .add(EC.set_explore_mode(True))
            .add(EC.set_flag(memory.Flags.FAIR_PENDANT_NOT_FOUND))
            .add(EC.set_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT))
            .add(EC.call_obj_function(recruit_obj_id,
                                      FID.ARBITRARY_0, 5, FS.CONT))
        )
        .add(EC.return_cmd())
    )

    return touch_ef


def build_recruit_arb_0():
    """wander after bump"""
    arb_0 = (
        EF()
        .set_label('start')
        .add_if(
            EC.if_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT),
            EF()
            .add(EC.move_sprite(0x18, 0xF))
            .add(EC.loop_animation(0x17, 0x3))
            .add(EC.move_sprite(0x1C, 0xD))
            .add(EC.loop_animation(0x17, 0x3))
            .jump_to_label(EC.jump_back(), 'start')
        )
        .add(EC.return_cmd())
    )

    return arb_0


def build_recruit_arb_1():
    """collision w/ PC00"""
    arb_1 = (
        EF()
        .add(EC.call_pc_function(0, FID.ARBITRARY_0, 3, FS.CONT))
        .add(EC.set_move_speed(0x80))
        .add(EC.generic_command(0xE8, 0x8E))  # sound collision
        .add(EC.static_animation(0x6A))
        .add(EC.vector_move(0, 4, True))
        .add(EC.pause(1))
        .add(EC.static_animation(0x49))
        .add(EC.return_cmd())
    )

    return arb_1

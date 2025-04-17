"""Openworld Castle Magus Throne of Defense"""
from typing import Optional

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
    """EventMod for Castle Magus Throne of Defense"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_OZZIE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Throne of Defense for an Open World.
        - Give Ayla and Magus animations
        - Remove dialogue and animation (including Frog-specific)
        - Replace storyline checks with flag checks
        - Restore exploremode when warping in
        """
        cls.modify_storyline_checks(script)
        cls.modify_ozzie_scene(script)
        cls.modify_pc_objs(script)

        pos = script.find_exact_command(
            EC.party_follow(), script.get_object_start(8)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)


    @classmethod
    def modify_pc_objs(cls, script: Event):
        """
        Make Ayla and Magus have the same abilities as other PCs.
        """

        anim_dict: dict[ctenums.CharID, int] = {
            ctenums.CharID.AYLA: 43,
            ctenums.CharID.MAGUS: 125
        }

        for char_id in (ctenums.CharID.MAGUS, ctenums.CharID.AYLA):
            obj_id = char_id + 1
            pos = script.find_exact_command(EC.return_cmd(),
                                            script.get_object_start(obj_id))
            script.insert_commands(
                EF().add_if(
                    EC.if_flag(memory.Flags.USING_SAVE_POINT_WARP),
                    EF().add(get_command(bytes.fromhex("88401FFF01")))
                ).get_bytearray(), pos
            )

            arb1 = (
                EF().add(EC.loop_animation(0xC, 1))
                .add(EC.play_animation(anim_dict[char_id]))
                .add(EC.return_cmd())
            )
            script.set_function(obj_id, FID.ARBITRARY_1, arb1)


    @classmethod
    def modify_storyline_checks(cls, script: Event):
        """
        Replace Storyline < 0x89 checks with a flag check.
        """

        find_cmd = EC.if_storyline_counter_lt(0x89)
        repl_cmd = EC.if_not_flag(memory.Flags.MAGUS_CASTLE_OZZIE_DEFEATED)

        pos: Optional[int] = script.get_object_start(0)
        while True:
            pos = script.find_exact_command_opt(find_cmd)
            if pos is None:
                break
            script.replace_jump_cmd(pos, repl_cmd)

    @classmethod
    def modify_ozzie_scene(cls, script: Event):
        """
        Remove dialogue and animation from the Ozzie scene.
        Incidentally replaces the storyline setting command.
        """

        pos, _ = script.find_command(
            [0xC2],script.get_function_start(0xA, FID.ACTIVATE))
        del_end = script.find_exact_command(EC.play_song(0x29))

        repl_block = (
            EF()
            .add(EC.play_animation(8)).add(EC.pause(0.5))
            .add(EC.static_animation(0x16))
        )
        script.delete_commands_range(pos, del_end)
        script.insert_commands(repl_block.get_bytearray(), pos)

        pos = script.find_exact_command(EC.if_pc_active(ctenums.CharID.MARLE), pos)
        del_end = script.find_exact_command(EC.set_storyline_counter(0x89)) + 2

        repl_block = (
            EF().add(EC.play_sound(0xB))
            .add(EC.set_object_drawing_status(0x8, True))
            .add(EC.set_object_drawing_status(0x9, True))
            .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_DEFEATED))
        )
        script.delete_commands_range(pos, del_end)
        script.insert_commands(repl_block.get_bytearray(), pos)

        pos = script.find_exact_command(EC.party_follow(), pos)
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

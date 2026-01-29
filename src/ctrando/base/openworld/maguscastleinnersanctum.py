"""Openworld Castle Magus Inner Sanctum"""
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
    """EventMod for Castle Magus Inner Sanctum"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_INNER_SANCTUM
    pc_wait_addr = 0x7F020C

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Inner Sanctum for an Open World.
        - Replace storyline triggers with flag triggers
        - Add animations to Ayla and Magus
        """
        cls.modify_pc_objs(script)
        cls.modify_magus_scene(script)

        pos = script.find_exact_command(
            EC.party_follow(), script.get_object_start(0xC)
        )
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)
        # TODO: Maybe shorten some of the pauses.

    @classmethod
    def modify_magus_scene(cls, script: Event):
        """
        Greatly shorten the scene that plays out before and after the battle.
        """

        pos = script.find_exact_command(
            EC.pause(1.875),
            script.get_function_start(9, FID.ACTIVATE)
        )
        del_end = script.find_exact_command(
            EC.generic_command(0x8E, 0x33),  pos)

        repl_block = (
            EF().add(EC.pause(1)).add(EC.play_animation(0))
            .add(EC.play_song(0x28)).add(EC.pause(2))
            .add(EC.play_animation(0x22)).add(EC.pause(2))
            .add(EC.play_animation(0)).add(EC.pause(1))
            .add(EC.play_sound(0xA))
            .add(EC.set_own_facing('down'))
            .add(EC.play_animation(0x23)).add(EC.pause(1))
        )

        script.delete_commands_range(pos, del_end)
        script.insert_commands(repl_block.get_bytearray(), pos)

        pos, _ = script.find_command([0xC2], pos)
        script.data[pos:pos+2] = EC.generic_command(0xAD, 0x4).to_bytearray()

        pos = script.find_exact_command(EC.if_pc_active(ctenums.CharID.MARLE))
        del_end = script.find_exact_command(EC.play_song(0xD), pos)

        script.delete_commands_range(pos, del_end)

        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_4, 4, FS.SYNC),
            pos
        )
        del_end, _ = script.find_command([0xF4], pos)
        script.delete_commands_range(pos, del_end)
        script.insert_commands(
            EF()
            .add(EC.auto_text_box(
                script.add_py_string(
                    "{line break}"
                    "    12,000BC added to {epoch}!{null}"
                )
            ))
            .add(EC.set_flag(memory.Flags.OW_MAGUS_DEFEATED))
            .add(EC.set_flag(memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS)).get_bytearray(),
            pos
        )

        pos, _ = script.find_command([0xDD])
        epoch_loc_cmd = EC.change_location(
            ctenums.LocID.DARK_AGES_PORTAL, 0x7, 0xA,
            Facing.DOWN, 1, False
        )
        epoch_loc_cmd.command = 0xDD

        no_epoch_loc_cmd = EC.change_location(
            ctenums.LocID.OW_MIDDLE_AGES, 0x54, 0x3C,
            Facing.DOWN, 1, False
        )
        no_epoch_loc_cmd.command = 0xDD
        change_loc_block = (
            EF()
            .add(EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1))
            .add_if_else(
                EC.if_flag(memory.Flags.EPOCH_OBTAINED_LOC),
                EF()
                .append(
                    owu.get_epoch_set_block(
                        ctenums.LocID.OW_DARK_AGES,
                        0x270, 0x258
                    )
                )
                .add(epoch_loc_cmd),
                EF()
                .add(no_epoch_loc_cmd)
            )
        )

        # script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()
        script.delete_commands(pos, 1)
        script.insert_commands(
            change_loc_block.get_bytearray(), pos
        )

    @classmethod
    def modify_storyline_checks(cls, script: Event):
        """
        Replace storyline checks with flag checks.
        """
        repl_dict: dict[int, Optional[memory.Flags]] = {
            0x8A: memory.Flags.OW_MAGUS_DEFEATED
        }
        owu.storyline_to_flag(script, repl_dict)

    @classmethod
    def modify_pc_objs(cls, script: Event):
        """
        Add animations to Ayla and Magus
        """

        anim_dict: dict[ctenums.CharID, int] = {
            ctenums.CharID.AYLA: 43,
            ctenums.CharID.MAGUS: 125,
        }

        for char_id in (ctenums.CharID.AYLA, ctenums.CharID.MAGUS):
            obj_id = char_id+1

            arb0 = (
                EF()
                .set_label("start")
                .add_if(
                    EC.if_mem_op_value(cls.pc_wait_addr, OP.EQUALS, 0),
                    EF().add(EC.break_cmd()).jump_to_label(EC.jump_back(), "end"),
                )
                .add(EC.return_cmd())
            )
            script.set_function(obj_id, FID.ARBITRARY_0, arb0)

            arb1 = (
                EF()
                .add(EC.loop_animation(0xC, 1))
                .add(EC.play_animation(anim_dict[char_id]))
                .add(EC.return_cmd())
            )
            script.set_function(obj_id, FID.ARBITRARY_1, arb1)

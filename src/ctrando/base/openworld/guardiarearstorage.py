"""Openworld Guardia Rear Storage"""

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
    """EventMod for Guardia Rear Storage"""
    loc_id = ctenums.LocID.GUARDIA_REAR_STORAGE
    got_item_id = 0x1A

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Guardia Rear Storage for an Open World.
        - Give decision box for grabbing the shell item.
        - Shorten the scene that plays when the shell item is obtained
          - Remove the cutaway to the trial that would play
          - Remove dialogue and many animations
        - Modify the Melchior item (TBD)
        """
        cls.modify_shard_pickup(script)
        cls.modify_melchoir_pickup(script)

    @classmethod
    def modify_shard_pickup(cls, script: Event):
        """
        Remove dialog and the scene transition to the courtroom.
        """

        got_item_id = owu.add_default_treasure_string(script)
        if got_item_id != cls.got_item_id:
            raise ValueError

        new_marle_fn = (
            EF().add(EC.move_sprite(0x34, 0xA))
            .add(EC.play_sound(5))
            .add(EC.set_own_facing('up'))
            .add(EC.play_animation(0x1F))
            # Sparkle on
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_0, 4, FS.HALT))
            .add(EC.pause(2))
            .add(EC.play_song(0))
            .add(EC.generic_command(0xEB, 0, 0xFF))
            .add(EC.play_song(0x3D))
            .add(EC.assign_val_to_mem(ctenums.ItemID.PRISMSHARD, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(got_item_id))
            .add(EC.generic_command(0xEE))
            .add(EC.set_object_drawing_status(0xA, False))
            .add(EC.reset_animation())
            .add(EC.set_flag(memory.Flags.OBTAINED_RAINBOW_SHELL_ITEM))
            .add(EC.return_cmd())
        )

        script.set_function(2, FID.ARBITRARY_0, new_marle_fn)

        # The shell is Object 0x09 touch, but it calls out to Object 2 arb 0.
        new_touch = (
            EF()
            .add_if(
                EC.if_flag(memory.Flags.OBTAINED_RAINBOW_SHELL_ITEM),
                EF().add(EC.return_cmd())
            )
            .add(EC.assign_val_to_mem(ctenums.ItemID.PRISMSHARD, 0x7F0200, 1))
            .add_if_else(
                EC.check_active_pc(ctenums.CharID.MARLE, 0),
                EF()
                .add(
                    EC.decision_box(
                        script.add_py_string(
                            "Should {marle} take the {item}?{line break}"
                            "   Yes.{line break}"
                            "   No.{null}"
                        ), 1, 2,
                    )
                )
                .add_if(
                    EC.if_result_equals(1, 0),
                    EF()
                    .add(EC.generic_command(0xE7, 0x2C, 0x02))
                    .add(EC.move_party(0x33, 0x0D, 0x32, 0xC, 0x36, 0xC))
                    .add(EC.call_obj_function(2, FID.ARBITRARY_0, 3, FS.HALT))
                    .add(EC.move_party(0x34, 0xD, 0x34, 0xD, 0x34, 0xD))
                    .add(EC.party_follow())
                    .add(EC.set_explore_mode(True))
                    .add_if_else(
                        # If trial complete
                        EC.if_flag(memory.Flags.KINGS_TRIAL_COMPLETE),
                        # Just start plyaing castle music again
                        EF().add(EC.play_song(0xC)),
                        # else
                        EF()
                        .add(EC.set_flag(memory.Flags.GUARDIA_THRONE_1000_BLOCKED))
                        .add(EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1))  # set keep song
                        .add(get_command(bytes.fromhex("EC880101")))  # song state
                        .add(EC.play_song(0x23))
                    ),
                ),
                EF().add(
                    EC.auto_text_box(
                        script.add_py_string("Only {marle} can take the {item}.{null}")
                    )
                ),
            )
            .add(EC.return_cmd())
        )
        script.set_function(9, FID.TOUCH, new_touch)

    @classmethod
    def modify_melchoir_pickup(cls, script: Event):
        """
        Change Melchior to give one item for free and one for the Sun Stone.
        """

        # Extract the part of the script where the scene fades and Melchior
        # makes an item.
        pos = script.find_exact_command(
            EC.darken(1),
            script.get_function_start(0x17, FID.STARTUP)
        )
        end, _ = script.find_command([0xBB], pos)
        make_item_block = EF.from_bytearray(script.data[pos:end])

        new_melchior_fn = (
            EF().add(EC.set_own_facing_pc(0))
            .add(EC.set_explore_mode(False))
            .add_if(
                EC.if_not_flag(memory.Flags.MELCHIOR_TREASURY_FREE_ITEM_GIVEN),
                EF().add(EC.auto_text_box(0x13))
                .append(make_item_block)
                .add(EC.play_song(0x3D))
                .append(owu.get_add_item_block_function(
                    ctenums.ItemID.PRISM_HELM,
                    memory.Flags.MELCHIOR_TREASURY_FREE_ITEM_GIVEN,
                    cls.got_item_id
                )).add(EC.play_song(0x0C))
            ).add_if_else(
                EC.if_has_item(ctenums.ItemID.SUN_STONE),
                EF().add(EC.auto_text_box(0x17))
                .append(make_item_block)
                .add(EC.play_song(0x3D))
                .append(owu.get_add_item_block_function(
                    ctenums.ItemID.RAINBOW,
                    None,
                    cls.got_item_id
                ))
                .append(owu.get_add_item_block_function(
                    ctenums.ItemID.PRISMSPECS,
                    None,
                    cls.got_item_id
                ))
                .add(EC.set_flag(memory.Flags.MELCHIOR_TREASURY_SUNSTONE_ITEM_GIVEN))
                .add(EC.play_song(0x0C))
                .add(EC.auto_text_box(0x15))
                .add(EC.set_move_speed(0x40))
                .add(EC.move_sprite(0x34, 0x15))
                .add(EC.set_own_drawing_status(False))
                .add(EC.reset_flag(memory.Flags.MELCHIOR_IN_TREASURY)),
                EF().add(EC.auto_text_box(0x16))
            ).add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )

        script.set_function(0x17, FID.ACTIVATE, new_melchior_fn)
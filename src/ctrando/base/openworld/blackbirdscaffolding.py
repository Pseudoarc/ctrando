"""Openworld Blackbird Scaffolding"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Blackbird Scaffolding"""
    loc_id = ctenums.LocID.BLACKBIRD_SCAFFOLDING

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Blackbird Scaffolding Event.
        - Add Magus to the scene.
        - Add a JetsOfTime (name?) turn-in for the Dalton Plus Fight.
        """

        cls.add_epoch_objects(script)
        cls.add_flight_turn_in(script)
        cls.add_magus(script)

    @classmethod
    def add_magus(cls, script: Event):
        """
        Add an object for Magus
        """

        script.insert_copy_object(6, 7)

        pos = script.get_object_start(7)
        pos = script.find_exact_command(EC.load_pc_in_party(ctenums.CharID.AYLA))
        script.data[pos] = 0x6D  # load magus's command id.

    @classmethod
    def add_flight_turn_in(cls, script: Event):
        """
        Add a flight turn-in on the bashers.  Hide the bashers if the fight has been
        completed.
        """
        basher_objs = (7, 8)
        basher_activate = (
            EF().add_if(
                EC.if_has_item(ctenums.ItemID.JETSOFTIME),
                EF().add(EC.auto_text_box(
                    script.add_py_string(
                        "Don't worry, Lord Dalton has made good{linebreak+0}"
                        "use of those wings!{null}"
                ))).add(EC.play_song(0x16))
                .add(EC.call_obj_function(0xA, FID.ARBITRARY_0, 4, FS.SYNC))
                .add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 4, FS.CONT))
                .add(EC.call_obj_function(0xC, FID.ARBITRARY_0, 4, FS.CONT))
                .add(EC.call_obj_function(0xD, FID.ARBITRARY_0, 4, FS.HALT))
                .add(EC.move_party(6, 0x14, 6, 0x14, 6, 0x14))
                .add(EC.darken(1))
                .add(EC.fade_screen())
                .add(EC.assign_val_to_mem(
                    7, memory.Memory.BLACKBIRD_LEFT_WING_CUTSCENE_COUNTER, 1))
                .add(EC.change_location(ctenums.LocID.REBORN_EPOCH, 7, 0x19))
                .add(EC.return_cmd())
            ).add(EC.auto_text_box(0))
            .add(EC.return_cmd())
        )

        for obj_id in basher_objs:
            pos = script.get_function_start(obj_id, FID.STARTUP)
            script.insert_commands(
                EF().add_if(
                    EC.if_flag(memory.Flags.REBORN_EPOCH_BOSS_DEFEATED),
                    EF().add(EC.return_cmd()).add(EC.end_cmd())
                ).get_bytearray(), pos
            )

            script.set_function(obj_id, FID.ACTIVATE, basher_activate)




    @classmethod
    def add_epoch_objects(cls, script: Event):
        """
        Add a little flying Epoch to set up for a Reborn Epoch fight.
        """

        # We're just copying from Blackbird Left Wing here.

        x_tile, y_tile = 1, 0x12
        epoch_id = script.append_empty_object()
        script.set_function(
            epoch_id, FID.STARTUP,
            EF().add(EC.load_npc(0xAE))
            .add(EC.set_move_properties(True, True))
            .add(EC.set_object_coordinates_tile(x_tile, y_tile))
            .add(EC.generic_command(0x8E, 0x22))  # Sprite priority.
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )

        script.set_function(
            epoch_id, FID.ACTIVATE, EF().add(EC.return_cmd())
        )

        script.set_function(
            epoch_id, FID.ARBITRARY_0,
            EF().add(EC.set_own_drawing_status(True))
            .add(EC.play_sound(0xD0))
            .add(EC.set_move_speed(0x80))
            .add(get_command(bytes.fromhex("EC824000")))
            .add(get_command(bytes.fromhex("EC834000")))  # Something sound related
            .add(EC.move_sprite(x_tile, 0, True))
            .add(EC.set_own_drawing_status(False))
            .add(EC.play_sound(0xFF))
            .add(get_command(bytes.fromhex("EC8200FF")))
            .add(get_command(bytes.fromhex("EC8300FF")))  # Something sound related
            .add(EC.return_cmd())
        )

        big_sparkle_obj = script.append_empty_object()
        script.set_function(
            big_sparkle_obj, FID.STARTUP,
            EF().add(EC.load_npc(0x71))
            .add(EC.set_move_properties(True, True))
            .add(EC.set_object_coordinates_tile(x_tile, y_tile))
            .add(EC.play_animation(0))
            .add(EC.generic_command(0x8E, 0x22))  # Sprite priority.
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd())
            .add(EC.follow_obj_infinite(epoch_id))
        )
        script.set_function(big_sparkle_obj, FID.ACTIVATE, EF().add(EC.return_cmd()))

        script.set_function(
            big_sparkle_obj, FID.ARBITRARY_0,
            EF().add(EC.set_own_drawing_status(True))
            .add(EC.set_move_speed(0x78))
            .add(EC.move_sprite(x_tile, 0, True ))
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd())
        )

        small_sparkle_1_id = script.append_empty_object()
        script.set_function(
            small_sparkle_1_id, FID.STARTUP,
            EF()
            .add(EC.load_npc(0x70))
            .add(EC.set_move_properties(True, True))
            .add(EC.set_object_coordinates_tile(x_tile, y_tile))
            .add(EC.play_animation(0))
            .add(EC.generic_command(0x8E, 0x22))  # Sprite priority.
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd())
            .add(EC.follow_obj_infinite(big_sparkle_obj)),
        )
        script.set_function(small_sparkle_1_id, FID.ACTIVATE,
                            EF().add(EC.return_cmd()))
        script.set_function(
            small_sparkle_1_id, FID.ARBITRARY_0,
            EF()
            .add(EC.set_own_drawing_status(True))
            .add(EC.set_move_speed(0x74))
            .add(EC.move_sprite(x_tile, 0, True))
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd()),
        )

        small_sparkle_2_id = script.append_empty_object()
        script.set_function(
            small_sparkle_2_id,
            FID.STARTUP,
            EF()
            .add(EC.load_npc(0x70))
            .add(EC.set_move_properties(True, True))
            .add(EC.set_object_coordinates_tile(x_tile, y_tile))
            .add(EC.play_animation(0))
            .add(EC.generic_command(0x8E, 0x22))  # Sprite priority.
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd())
            .add(EC.follow_obj_infinite(small_sparkle_1_id)),
        )
        script.set_function(small_sparkle_2_id,
                            FID.ACTIVATE, EF().add(EC.return_cmd()))
        script.set_function(
            small_sparkle_2_id, FID.ARBITRARY_0,
            EF()
            .add(EC.set_own_drawing_status(True))
            .add(EC.set_move_speed(0x70))
            .add(EC.move_sprite(x_tile, 0, True))
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd()),
        )




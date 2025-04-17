"""Openworld Keeper's Dome Corridor"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Keeper's Dome Corridor"""

    loc_id = ctenums.LocID.KEEPERS_DOME_CORRIDOR

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Keeper's Dome Corridor Event.
        - Remove the plot exposition sparkles
        - Keep the sealed door open
        - Alter the Death Peak turn-in
        """

        # Removing the plot sparkles can either be done by removing the touch
        # function of Object 8 or by setting the flag 0x7F00EC & 08.
        # Easiest to just set the flag.
        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.VIEWED_KEEPERS_PLOT_SPARKLES).to_bytearray(), pos
        )

        # The sealed door is controlled by setting 0x7F0210 to 1.
        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(EC.assign_val_to_mem(1, 0x7F0210, 1).to_bytearray(), pos)

        cls.modify_nu_activation(script)

        pos = script.get_function_start(0x12, FID.ACTIVATE)
        owu.update_add_item(script, pos)
        owu.remove_item_pause(script, pos)

    @classmethod
    def modify_nu_activation(cls, script: Event):
        """
        - Change the Nu to require the C.Trigger as well as the Clone for
          Death Peak.
        - Make the Nu visible no matter what but only blocking the door if the
          Epoch is absent from the hangar.
        """

        poyozo_scene = (
            EF()
            .add(EC.auto_text_box(0xA))
            .add(EC.set_flag(memory.Flags.KEEPERS_NU_SENT_POYOZOS))
            # Some move party commands. Useful if entering from the hangar.
            .add(EC.call_obj_function(0x16, FID.ARBITRARY_3, 3, FS.HALT))
            .add(EC.static_animation(0x10))
            .add(EC.generic_command(0xAD, 0x02))
            .add(EC.static_animation(1))
            .add(EC.vector_move(270, 0x30, False))
            .add(EC.set_own_drawing_status(False))
            .add(EC.pause(2))
            # Three pairs of bolt + poyozo flying off
            .add(EC.call_obj_function(0x16, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_obj_function(0x13, FID.ARBITRARY_0, 3, FS.HALT))
            .add(EC.call_obj_function(0x16, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_obj_function(0x14, FID.ARBITRARY_0, 3, FS.HALT))
            .add(EC.call_obj_function(0x16, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_obj_function(0x15, FID.ARBITRARY_0, 3, FS.HALT))
            .add(EC.pause(1))
            .add(EC.set_own_drawing_status(True))
            .add(EC.set_move_properties(True, True))
            .add(EC.vector_move(90, 0x30, False))
            .add(EC.generic_command(0xAD, 5))
            .add(EC.static_animation(4))
            .add(
                EC.auto_text_box(
                    script.add_py_string(
                        "BELTHASAR: The 3 entities you saw will{line break}"
                        'help you climb {"1}Death Peak{"2}{null}'
                    )
                )
            )
        )

        nu_complete = (
            EF()
            .add(
                EC.auto_text_box(
                    script.add_py_string(
                        "This creature has executed its{line break}"
                        "program.{line break}"
                        "Please let him sleep.{line break}"
                        "The switch is on his stomach.{null}"
                    )
                )
            )
            .add(EC.set_flag(memory.Flags.KEEPERS_NU_COMPLETE))
        )

        nu_activate = (
            EF()
            .add_if(
                EC.if_flag(memory.Flags.TURNED_KEEPERS_NU_OFF),
                EF()
                .add(EC.auto_text_box(0x10))
                .jump_to_label(EC.jump_forward(), "end"),
            )
            .add_if(
                EC.if_flag(memory.Flags.KEEPERS_NU_COMPLETE),
                EF()
                .add(EC.set_explore_mode(False))
                .add(EC.decision_box(0xF, 1, 2, "bottom"))
                .add_if(
                    EC.if_result_equals(1),
                    EF()
                    .add(EC.play_sound(0x9F))
                    .add(EC.set_object_drawing_status(0x11, False))
                    .add(EC.set_flag(memory.Flags.TURNED_KEEPERS_NU_OFF)),
                )
                .add(EC.set_explore_mode(True))
                .jump_to_label(EC.jump_forward(), "end"),
            )
            .add(EC.set_object_drawing_status(0x11, False))
            .add(EC.static_animation(0xC))
            .add(EC.pause(0.5))
            .add(EC.static_animation(4))
            .add(EC.assign_val_to_mem(0, 0x7F0224, 1))
            .add(EC.set_flag(memory.Flags.EPOCH_OBTAINED_LOC))
            .add_if(
                EC.if_not_flag(memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS),
                EF()
                .add(EC.set_flag(memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS))
                .add(
                    EC.auto_text_box(
                        script.add_py_string(
                            "BALTHASAR: 12,000 BC added to {epoch}!{null}"
                        )
                    )
                )
                .add(EC.assign_val_to_mem(1, 0x7F0224, 1))
            )
            .add_if(
                EC.if_not_flag(memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS),
                EF()
                .add(EC.set_flag(memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS))
                .add(
                    EC.auto_text_box(
                        script.add_py_string(
                            "BALTHASAR: 2300AD added to {epoch}!{line break}"
                            " Calling Epoch to hangar.{null}"
                        )
                    )
                )
                .add(EC.reset_flag(memory.Flags.EPOCH_OUT_OF_HANGAR))
                .add(EC.static_animation(1))
                .add(EC.vector_move(270, 0x30, False))
                .add(EC.remove_object(0x10))
                .add(EC.return_cmd())
            )
            .add_if(
                EC.if_mem_op_value(0x7F0224, OP.EQUALS, 1),
                EF().jump_to_label(EC.jump_forward(), "end_anim")
            )
            .add_if(
                EC.if_not_flag(memory.Flags.KEEPERS_NU_SENT_POYOZOS),
                EF().add_if(
                    EC.if_has_item(ctenums.ItemID.C_TRIGGER),
                    EF().add_if(
                        EC.if_has_item(ctenums.ItemID.CLONE),
                        EF()
                        .add(EC.set_explore_mode(False))
                        .append(poyozo_scene)
                        .add_if(
                            EC.if_flag(memory.Flags.OBTAINED_EPOCH_FLIGHT),
                            EF().append(nu_complete),
                        )
                        .add(EC.party_follow())
                        .add(EC.set_explore_mode(True))
                        .jump_to_label(EC.jump_forward(), "end_anim"),
                    ),
                ),
            )
            .add_if(
                EC.if_flag(memory.Flags.KEEPERS_NU_SENT_POYOZOS),
                EF()
                .add_if(
                    EC.if_flag(memory.Flags.OBTAINED_EPOCH_FLIGHT),
                    EF()
                    .add(EC.set_explore_mode(False))
                    .add(
                        EC.auto_text_box(
                            script.add_py_string(
                                "BELTHASAR: Now I ask you for a favor{null}"
                            )
                        )
                    )
                    .append(nu_complete)
                    .add(EC.set_explore_mode(True))
                    .jump_to_label(EC.jump_forward(), "end_anim"),
                )
                .add(
                    EC.auto_text_box(
                        script.add_py_string("BELTHASAR: The Epoch is not here.{null}")
                    )
                )
                .jump_to_label(EC.jump_forward(), "end_anim"),
            )
            .add(EC.auto_text_box(9))
            .set_label("end_anim")
            .add(EC.static_animation(0xD))
            .add(EC.set_object_drawing_status(0x11, True))
            .set_label("end")
            .add(EC.return_cmd())
        )

        script.set_function(0x10, FID.ACTIVATE, nu_activate)
        script.set_function(
            0x10,
            FID.ARBITRARY_0,
            EF()
            .add(EC.set_explore_mode(False))
            .add(EC.auto_text_box(script.add_py_string("BELTHASAR: Wait!!!{null}")))
            .add(EC.move_party(2, 8, 2, 8, 2, 8))
            .add(EC.set_object_coordinates_pixels(0x30, 0x10))
            .add(EC.set_own_drawing_status(True))
            .add(EC.static_animation(1))
            .add(EC.vector_move(90, 0x30, False))
            .append(poyozo_scene)
            .add(EC.vector_move(270, 0x30, False))
            .add(EC.set_own_drawing_status(False))
            .add(EC.party_follow())
            .add(EC.set_explore_mode(True))
            .add(EC.return_cmd()),
        )

        # Weird that string index comes after the first return here.
        pos = script.find_exact_command(EC.return_cmd()) + 5
        call = (
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.PREVIOUS_LOCATION_LO, 0x7F0220, 2))
            .add_if(
                EC.if_mem_op_value(
                    0x7F0220, OP.EQUALS, ctenums.LocID.KEEPERS_DOME_HANGAR, 2
                ),
                EF().add_if(
                    EC.if_not_flag(memory.Flags.KEEPERS_NU_SENT_POYOZOS),
                    EF().add_if(
                        EC.if_has_item(ctenums.ItemID.C_TRIGGER),
                        EF().add_if(
                            EC.if_has_item(ctenums.ItemID.CLONE),
                            EF().add(
                                EC.call_obj_function(0x10, FID.ARBITRARY_0, 5, FS.HALT)
                            ),
                        ),
                    ),
                ),
            )
            .add(EC.end_cmd())
        )

        script.insert_commands(call.get_bytearray(), pos)

        pos += len(call)
        script.delete_commands(pos, 2)  # delete unused coordinate loop

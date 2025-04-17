"""Openworld Arris Dome Guardian Chamber"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Dome Guardian Chamber"""
    loc_id = ctenums.LocID.ARRIS_DOME_GUARDIAN_CHAMBER
    pc_id_start = 0x7F0214

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Guardian Chamber Event.
        - Add functions to PC objects which are not available in vanilla to
          play nicely when guardian scrolls layers.
        """

        cls.add_pc_arbs(script)
        cls.modify_pre_battle_scene(script)


    @classmethod
    def modify_pre_battle_scene(cls, script: Event):
        """
        Make calls to PC-objects instead of explicity object numbers
        """
        pos = script.find_exact_command(
            EC.call_obj_function(2, FID.ARBITRARY_2, 3, FS.CONT),
            script.get_function_start(9, FID.ACTIVATE)
        )

        script.delete_commands(pos, 3)
        script.insert_commands(
            EF().add(EC.call_pc_function(1, FID.ARBITRARY_2, 3, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_2, 3, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_2, 3, FS.CONT))
            .get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_3, 4, FS.HALT), pos
        )
        script.delete_commands(pos, 6)
        script.insert_commands(
            EF().add(EC.call_pc_function(0, FID.ARBITRARY_3, 4, FS.HALT))
            .add(EC.auto_text_box(0))  # Executing Program
            .add(EC.call_pc_function(1, FID.ARBITRARY_3, 4, FS.HALT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_3, 4, FS.HALT))
            .get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.call_obj_function(2, FID.ARBITRARY_4, 4, FS.CONT)
        )
        script.delete_commands(pos, 3)
        script.insert_commands(
            EF().add(EC.call_pc_function(1, FID.ARBITRARY_4, 4, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_4, 4, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_4, 4, FS.CONT))
            .get_bytearray(),
            pos
        )
    @classmethod
    def add_pc_arbs(cls, script: Event):
        """
        Add animations for when guardian comes down and up for Robo, Frog, Ayla,
        and Magus
        """

        # Insert a PC-ID collection in obj0 activate
        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(
            owu.get_write_pc_ids_to_script_memory(cls.pc_id_start).get_bytearray(),
            pos
        )



        # [facing left, facing right]
        down_anims: dict[ctenums.CharID, tuple[int, int]] = {
            ctenums.CharID.CRONO: (0x46, 0x45),
            ctenums.CharID.MARLE: (79, 78),
            ctenums.CharID.LUCCA: (0xCE, 0xCF),
            ctenums.CharID.ROBO: (77, 78),
            ctenums.CharID.FROG: (79, 78),
            ctenums.CharID.AYLA: (200, 195),
            ctenums.CharID.MAGUS: (78, 77),
        }

        for pc_id in ctenums.CharID:
            obj_id = int(pc_id) + 1

            script.set_function(obj_id, FID.ARBITRARY_0, EF().add(EC.return_cmd()))
            script.set_function(obj_id, FID.ARBITRARY_1, EF().add(EC.return_cmd()))

            arb_2 = (
                EF().add(EC.set_move_properties(True, True))
                .add(EC.set_move_speed(0xFF))
                .add_if(
                    EC.if_mem_op_value(cls.pc_id_start, OP.EQUALS, pc_id),
                    EF().add(EC.set_own_facing('left'))
                    .add(EC.get_pc_coordinates(0, cls.pc_id_start+6,
                                               cls.pc_id_start+8))
                    .add(EC.add(cls.pc_id_start+6, 4))
                    .add(EC.sub(cls.pc_id_start+8, 9))
                    .add(EC.play_animation(5))
                    .add(EC.move_sprite_offsets(cls.pc_id_start+6,
                                                cls.pc_id_start+8))
                    .add(EC.static_animation(down_anims[pc_id][0]))
                    .jump_to_label(EC.jump_forward(), 'done')
                ).add_if(
                    EC.if_mem_op_value(cls.pc_id_start+2, OP.EQUALS, pc_id),
                    EF().add(EC.set_own_facing('left'))
                    .add(EC.get_pc_coordinates(1, cls.pc_id_start+4+6,
                                               cls.pc_id_start+4+8))
                    .add(EC.add(cls.pc_id_start+4+6, 4))
                    .add(EC.sub(cls.pc_id_start+4+8, 9))
                    .add(EC.play_animation(5))
                    .add(EC.move_sprite_offsets(cls.pc_id_start+4+6,
                                                cls.pc_id_start+4+8))
                    .add(EC.static_animation(down_anims[pc_id][0]))
                    .jump_to_label(EC.jump_forward(), 'done')
                ).add(EC.set_own_facing('right'))
                .add(EC.get_pc_coordinates(2, cls.pc_id_start + 8 + 6,
                                           cls.pc_id_start + 8 + 8))
                .add(EC.sub(cls.pc_id_start + 8 + 6, 4))
                .add(EC.sub(cls.pc_id_start + 8 + 8, 9))
                .add(EC.play_animation(5))
                .add(EC.move_sprite_offsets(cls.pc_id_start + 8 + 6,
                                            cls.pc_id_start + 8 + 8))
                .add(EC.set_own_facing('down'))
                .add(EC.static_animation(down_anims[pc_id][1]))
                .jump_to_label(EC.jump_forward(), 'done')

                .set_label('done')
                .add(EC.return_cmd())
            )

            script.set_function(obj_id, FID.ARBITRARY_2, arb_2)

            arb_3 = (
                EF().add(EC.static_animation(1)).add(EC.return_cmd())
            )

            script.set_function(obj_id, FID.ARBITRARY_3, arb_3)
            script.link_function(obj_id, FID.ARBITRARY_4,
                                 1, FID.ARBITRARY_4)

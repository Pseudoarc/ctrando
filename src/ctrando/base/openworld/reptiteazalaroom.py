"""Openworld Reptite Lair Azala's Room"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

_pc_obj_id_dict = {
    ctenums.CharID.CRONO: 1,
    ctenums.CharID.MARLE: 2,
    ctenums.CharID.LUCCA: 3,
    ctenums.CharID.ROBO: 4,
    ctenums.CharID.AYLA: 5,
    ctenums.CharID.FROG: 6,
    ctenums.CharID.MAGUS: 7,
}

_pc_battle_frame_dict = {
    ctenums.CharID.CRONO: 79,
    ctenums.CharID.MARLE: 212,
    ctenums.CharID.LUCCA: 49,
    ctenums.CharID.ROBO: 55,
    ctenums.CharID.AYLA: 0x2B,  # From original script
    ctenums.CharID.FROG: 47,
    ctenums.CharID.MAGUS: 96
}

class EventMod(locationevent.LocEventMod):
    """EventMod for Reptite Lair Azala's Room"""
    loc_id = ctenums.LocID.REPTITE_LAIR_AZALA_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
         Update the Reptite Lair Azala's Room Event.
         - Remove dialog on entry and after winning the fight.
         - Change storyline < 0x7C to a flag
        """

        # Replace the one storyline check
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x7C))
        script.replace_jump_cmd(pos, EC.if_not_flag(memory.Flags.NIZBEL_DEFEATED))

        cls.modify_battle_scenes(script)
        cls.modify_pc_arbs(script)

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give Frog, Ayla, and Magus animations.  Normalize animations so that anyone
        can play any role.
        """

        # Everyone (except Frog and Magus) have Arb0 as a pause method
        # Crono only has Arb1 - Be shocked when Ayla burps
        # Marle, Lucca, and Robo have:
        # - Arb1: Look down.
        # - Arb2: Go to the gate key (0x35, 0x10) and check it out

        # The restructuring will be
        # - Arb0: existing pause
        # - Arb1: Get mad at Azala
        # - Arb2: Walk over to the gate key

        # Give everyone the standard pause function.
        arb0 = script.get_function(1, FID.ARBITRARY_0)
        for pc_id in (ctenums.CharID.FROG, ctenums.CharID.MAGUS):
            obj_id = _pc_obj_id_dict[pc_id]
            script.set_function(obj_id, FID.ARBITRARY_0, arb0)

        arb2 = (
            EF().add(EC.play_animation(9)).add(EC.pause(0.625))
            .add(EC.set_move_destination(True, False))
            .add(EC.set_move_speed(0x30))
            .add(EC.play_animation(1))
            .add(EC.move_sprite(0x35, 0x10))
            .add(EC.set_own_facing('down'))
            .add(EC.play_animation(0x1D))
            .add(EC.set_object_drawing_status(0xC, False)).add(EC.pause(0.75))
            .add(EC.play_animation(0x19)).add(EC.pause(1))
            .add(EC.loop_animation(0x21, 1))
            .add(EC.set_own_facing('up'))
            .add(EC.return_cmd())
        )

        for pc_id in ctenums.CharID:
            obj_id = _pc_obj_id_dict[pc_id]
            frame_id = _pc_battle_frame_dict[pc_id]

            script.set_function(
                obj_id, FID.ARBITRARY_1,
                EF().add(EC.play_animation(3))
                .add(EC.pause(2))
                .add(EC.static_animation(frame_id))
                .add(EC.return_cmd())
            )

            script.set_function(obj_id, FID.ARBITRARY_2, arb2)

    @classmethod
    def modify_battle_scenes(cls, script: Event):
        """
        Modify the scenes before and after the battle.
        - Remove dialog and PC-specific animations.
        - Replace setting the storyline counter with setting a flag
        """

        # The scene all takes place in a coordinate checking loop
        pos, _ = script.find_command([0xC2])
        script.delete_commands(pos, 1)


        # The Azala pre-battle function is in Obj8, Arb0

        # Remove a bunch of dialog
        pos = script.get_function_start(8, FID.ARBITRARY_0)
        pos, _ = script.find_command([0xBB], pos)
        end, _ = script.find_command([0xE7], pos)

        script.delete_commands_range(pos, end)
        # Replace with a brief pause and hide the gate key obj
        script.insert_commands(
            EF().add(EC.pause(2)).add(EC.set_object_drawing_status(0xC, False))
            .get_bytearray(), pos
        )

        # We're switching the positions for PC1 and PC2 in the move party
        pos, _ = script.find_command([0xD9], pos)
        script.data[pos + 1: pos + 3], script.data[pos + 3: pos + 5] = \
            script.data[pos + 3: pos + 5], script.data[pos + 1: pos + 3]

        pos = script.find_exact_command(
            EC.call_obj_function(5, FID.ARBITRARY_1, 1, FS.HALT)
        )
        script.replace_command_at_pos(
            pos, EC.call_pc_function(0, FID.ARBITRARY_1, 1, FS.HALT)
        )

        # Remove redundant face down commands and an Ayla animation
        pos = script.find_exact_command(
            EC.call_pc_function(2, FID.ARBITRARY_1, 1, FS.HALT), pos
        )
        script.delete_commands(pos, 3)

        # Remove Ayla animation
        pos = script.find_exact_command(
            EC.call_obj_function(5, FID.ARBITRARY_2, 1, FS.HALT), pos
        )
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.call_pc_function(2, FID.ARBITRARY_2, 1, FS.HALT), pos
        )

        new_block = (
            EF().add(EC.call_pc_function(0, FID.ARBITRARY_2, 1, FS.HALT))
            .add(EC.assign_val_to_mem(ctenums.ItemID.GATE_KEY, 0x7F0200, 1))
            .add(EC.add_item(ctenums.ItemID.GATE_KEY))
            .add(EC.auto_text_box(
                script.add_py_string(
                    "{line break}Got 1 {item}!{line break}{itemdesc}{null}"
                )
            ))
            .add(EC.set_flag(memory.Flags.NIZBEL_DEFEATED))
            .add(EC.assign_val_to_mem(0, 0x7F020C, 1))
            .add(EC.party_follow()).add(EC.set_explore_mode(True))
            .add(EC.end_cmd())
        )

        script.insert_commands(
            new_block.get_bytearray(), pos
        )
        pos += len(new_block)
        script.delete_commands(pos, 7)

        # Clean up Azala's Arb2 a little
        pos, _ = script.find_command(
            [0xBB], script.get_function_start(8, FID.ARBITRARY_2)
        )
        script.delete_commands(pos, 1)



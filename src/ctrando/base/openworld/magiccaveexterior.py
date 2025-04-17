"""Openworld Magic Cave Exterior"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


# Vanilla cutscene notes:
# Uses 0x7F0057 to keep track of the cutscene
#   - Sets 0x7F0057 & 02 before jumping to forest flashback
#   - Then to Zenan Bridge, Denadoro, and back to Magic Cave Exterior
#   - Frog requests the masa, sets 0x7F0057 & 01 and 0x7F01F1 & 01 (beam), and
#     goes to 600 AD overworld for the beam scene.
#   - Overworld returns to Magic Cave Exterior
#


class EventMod(locationevent.LocEventMod):
    """EventMod for Magic Cave Exterior"""
    loc_id = ctenums.LocID.MAGIC_CAVE_EXTERIOR

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Magic Cave Exterior Event.
        - Trigger Masamune cutscene with Frog + Masa
        - Shorten the cutscene by removing dialogue and flashbacks.
        """
        cls.modify_cutscene_activation(script)
        cls.modify_cutscene(script)
        cls.modify_pc_objects(script)

    @classmethod
    def modify_cutscene_activation(cls, script: Event):
        """
        Change the Frog scene to use the new OW_MAGIC_CAVE_OPEN flag.
        """

        temp_addr = 0x7F0300
        has_masa_addr = 0x7F0210
        has_masa_func = owu.get_has_equipment_func(
            ctenums.ItemID.MASAMUNE_1, has_masa_addr, temp_addr
        )

        pos = script.find_exact_command(EC.return_cmd())
        script.insert_commands(has_masa_func.get_bytearray(), pos)
        
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0x84))
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.OW_MAGIC_CAVE_OPEN))
        
        script.wrap_jump_cmd(
            pos,
            EC.if_mem_op_value(has_masa_addr, OP.EQUALS, 1))


    @classmethod
    def modify_cutscene(cls, script: Event):
        """
        Modify the cutscene where Frog opens the Magic Cave
        - Skip the flashback scenes
        - Remove handing over the Masamune
        """

        pos = script.find_exact_command(
            EC.if_flagdata(memory.FlagData(0x7f0057, 0x02))
        )

        script.delete_commands(pos, 1)
        block = (
            EF()
            .add(EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 3, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_3, 3, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_3, 3, FS.CONT))
            .add(EC.call_obj_function(5, FID.ARBITRARY_2, 3, FS.HALT))
        )
        script.insert_commands(block.get_bytearray(), pos)
        pos += len(block)

        pos = script.find_exact_command(
            EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1), pos
        )
        end = script.find_exact_command(
            EC.set_explore_mode(True), pos) + 2

        script.delete_commands_range(pos, end)

        # Re-add masamune to the scene
        pos = script.find_exact_command(
            EC.play_animation(0x11),
            script.get_function_start(5, FID.ARBITRARY_2)
        ) + 4  # Skip past anim + textbox
        script.insert_commands(
            EC.call_obj_function(8, FID.ARBITRARY_0, 3, FS.CONT).to_bytearray(),
            pos
        )

        pos, _ = script.find_command([0xAD],
                                     script.get_function_start(8, FID.ARBITRARY_0))
        script.data[pos+1] = 0x18

        # Fix the repositioning when the mountain splits
        pos = script.find_exact_command(
            EC.call_obj_function(2, FID.ARBITRARY_2, 3, FS.CONT)
        )
        script.delete_commands(pos, 5)

        repl_block = EF()
        for obj_id in (1, 2, 3, 4, 6, 7):
            repl_block.add(EC.call_obj_function(obj_id, FID.ARBITRARY_2,
                                                3, FS.CONT))
        script.insert_commands(repl_block.get_bytearray(), pos)

        # Replace set storyline with the overworld flag
        pos = script.find_exact_command(EC.set_storyline_counter(0x87), pos)
        script.replace_command_at_pos(
            pos, EC.set_flag(memory.Flags.OW_MAGIC_CAVE_OPEN))

        # Remove unused 7F0057 & 02 reset and masa equpping
        pos = script.find_exact_command(EC.reset_bit(0x7F0057, 0x02), pos)
        script.delete_commands(pos, 3)

        # Remove text asking for masa, and crono's animation call
        pos, _ = script.find_command([0xC1], pos)
        script.delete_commands(pos, 2)

    @classmethod
    def modify_pc_objects(cls, script: Event):
        """
        Control the PC position during the cutscene
        """

        # Collect the PCs in startup
        pos = script.find_exact_command(EC.return_cmd())
        get_pc_id_block = (
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1, 0x7F0220, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2, 0x7F0222, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, 0x7F0224, 1))
        )

        script.insert_commands(
            get_pc_id_block.get_bytearray(), pos
        )

        new_arb2 = script.get_function(1, FID.ARBITRARY_3)
        script.set_function(1, FID.ARBITRARY_2, new_arb2)

        for char_id in range(7):
            obj_id = 1 + char_id

            if char_id == 4:
                script.set_function(obj_id, FID.ARBITRARY_3,
                                    EF().add(EC.return_cmd()))
                continue  # Skip Frog since he has other thing to do

            startup_func = (
                EF().add(EC.load_pc_in_party(char_id))
                .add_if(
                    EC.if_mem_op_value(0x7F0057, OP.BITWISE_AND_NONZERO, 0x01),
                    EF().add_if(
                        EC.if_mem_op_value(0x7F0220, OP.EQUALS, char_id),
                        EF().add(EC.set_object_coordinates_tile(0xB, 0xB))
                        .jump_to_label(EC.jump_forward(), 'end')
                    ).add_if(
                        EC.if_mem_op_value(0x7F0222, OP.EQUALS, char_id),
                        EF().add(EC.set_object_coordinates_tile(0xB, 0xC))
                        .jump_to_label(EC.jump_forward(), 'end')
                    ).add_if(
                        EC.if_mem_op_value(0x7F0224, OP.EQUALS, char_id),
                        EF().add(EC.set_object_coordinates_tile(0xB, 0xD))
                        .jump_to_label(EC.jump_forward(), 'end')
                    )
                ).set_label('end')
                .add((EC.return_cmd()))
                .add(EC.set_controllable_infinite())
            )

            arb3 = (
                EF().add(EC.set_move_speed(0x20))
                .add_if_else(
                    EC.if_mem_op_value(0x7F0220, OP.EQUALS, char_id),
                    EF().add(EC.move_sprite(0xB, 0xB)),
                    EF().add_if_else(
                        EC.if_mem_op_value(0x7F0222, OP.EQUALS, char_id),
                        EF().add(EC.move_sprite(0xB, 0xC)),
                        EF().add(EC.move_sprite(0xB, 0xD)),
                    )
                ).add(EC.set_own_facing('left'))
                .add(EC.return_cmd())
            )

            script.set_function(obj_id, FID.STARTUP, startup_func)
            script.set_function(obj_id, FID.ARBITRARY_3, arb3)

            if char_id > ctenums.CharID.FROG:
                script.link_function(obj_id, FID.ARBITRARY_0,
                                     2, FID.ARBITRARY_0)
                script.link_function(obj_id, FID.ARBITRARY_1,
                                     2, FID.ARBITRARY_1)
                script.link_function(obj_id, FID.ARBITRARY_2,
                                     2, FID.ARBITRARY_2)
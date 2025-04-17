"""Openworld Dactyl Nest Summit"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Dactyl Nest Summit"""
    loc_id = ctenums.LocID.DACTYL_NEST_SUMMIT
    keeper_obj_id = 0xD
    pc1_addr = 0x7F0220
    pc2_addr = 0x7F0222
    pc3_addr = 0x7F0224
    num_pcs_addr = 0x7F0226
    temp_dactyl_status_addr = 0x7F0228

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Dactyl Nest Summit Event.
        - Change storyline trigger to flag trigger.  Access is restricted, so the scene
          will play on first entry.
        - Change the red star to disappear after the OW crater flag is set.
        """

        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(
            EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1, cls.pc1_addr, 1))
            .add(EC.assign_val_to_mem(1, cls.num_pcs_addr, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2, cls.pc2_addr, 1))
            .add_if(
                EC.if_mem_op_value(cls.pc2_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.add(cls.num_pcs_addr, 1))
            )
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, cls.pc3_addr, 1))
            .add_if(
                EC.if_mem_op_value(cls.pc3_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.add(cls.num_pcs_addr, 1))
            )
            .get_bytearray(), pos
        )

        cls.modify_red_star(script)
        cls.modify_pc_functions(script)
        cls.add_keeper_npc(script)
        cls.modify_dactyl_scene(script)

    @classmethod
    def modify_red_star(cls, script: Event):
        """
        Change the storyline < 0x99 check to a flag check.
        """
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x99))
        script.replace_jump_cmd(pos, EC.if_flag(memory.Flags.OW_LAVOS_HAS_FALLEN))

    @classmethod
    def modify_pc_functions(cls, script: Event):
        """
        Modify Ayla's startup so that she isn't ever an NPC.  Also add a move property
        command to Magus to match other PCs
        """

        script.set_function(
            7, FID.STARTUP,
            EF().add(EC.load_pc_in_party(ctenums.CharID.AYLA))
            .add(EC.return_cmd())
            .add(EC.set_move_properties(False, False))
            .add(EC.set_controllable_infinite())
            # Final return already in activate.
        )

        pos = script.find_exact_command(
            EC.set_controllable_infinite(),
            script.get_function_start(8, FID.STARTUP)
        )
        script.insert_commands(
            EC.set_move_properties(False, False).to_bytearray(), pos)

        for pc_id in ctenums.CharID:
            obj_id = pc_id + 2
            script.set_function(
                obj_id, FID.ARBITRARY_0,
                EF().add(EC.set_move_destination(False, True))
                .add_if(
                    EC.if_mem_op_value(cls.pc1_addr, OP.EQUALS, pc_id),
                    EF().add(EC.follow_obj_once(0xB))
                    .add(EC.set_own_facing('down'))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).add_if(
                    EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, pc_id),
                    EF().add(EC.follow_obj_once(0x9))
                    .add(EC.set_own_facing('down'))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).add_if(
                    EC.if_mem_op_value(cls.pc3_addr, OP.EQUALS, pc_id),
                    EF().add(EC.follow_obj_once(0xA))
                    .add(EC.set_own_facing('down'))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).set_label('end')
                .add(EC.pause(0.125))
                .add(EC.vector_move(270, 0x03, True))
                .add(EC.return_cmd())
            )

            script.set_function(
                obj_id, FID.ARBITRARY_1,
                EF().add(EC.play_animation(1))
                .add(EC.set_move_speed(0x10))
                .add_if(
                    EC.if_mem_op_value(cls.pc1_addr, OP.EQUALS, pc_id),
                    EF().add(EC.move_sprite(6, 0, True))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).add_if(
                    EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, pc_id),
                    EF().add(EC.move_sprite(8, 0, True))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).add_if(
                    EC.if_mem_op_value(cls.pc3_addr, OP.EQUALS, pc_id),
                    EF().add(EC.move_sprite(4, 0, True))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).set_label('end')
                .add(EC.return_cmd())
            )


    @classmethod
    def add_keeper_npc(cls, script: Event):
        """
        Add the Keeper NPC to call the dactyls.
        """
        obj_id = script.append_empty_object()
        if obj_id != cls.keeper_obj_id:
            raise ValueError

        script.set_function(
            obj_id, FID.STARTUP,
            EF().add(EC.load_npc(0x3F))
            .add(EC.set_object_coordinates_pixels(0x68, 0x92))
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )

        script.set_function(
            obj_id, FID.ACTIVATE, EF().add(EC.return_cmd())
        )

        script.set_function(
            obj_id, FID.ARBITRARY_0,
            EF().add(EC.set_own_facing('up'))
            .add(EC.loop_animation(4, 8))
            .add(EC.return_cmd())
        )

        script.set_function(
            obj_id, FID.ARBITRARY_1,
            EF().add(EC.play_animation(1))
            .add(EC.set_move_speed(0x20))
            .add(EC.vector_move(180, 0x20, False))
            .add(EC.play_animation(0))
            .add(EC.set_own_facing('right'))
            .add(EC.return_cmd())
        )

    @classmethod
    def modify_dactyl_scene(cls, script: Event):
        """
        Modify the scene that plays on first entry to the Dactyl Summit.
        """

        # The script plays out in two parts:
        # 1) When the party first enters, there's a scene of the dactyl's being called
        #    (by Ayla in vanilla).  This sets 0x7F0160 & 10.
        # 2) When the player's coordinates reach a certain thereshold, the rest of the
        #    scene plays.

        # We're just going to handle everything in the first scene and use
        # 0x7F0160 & 10 as the flag for having the dacytls.

        # The storyline counter gets stored in 0x7F020C, so some checks are against
        # that address.
        storyline_addr = 0x7F020C
        alt_storyline_cmd = EC.if_mem_op_value(storyline_addr, OP.LESS_THAN, 0x8E)

        # Let's nuke the whole thing because it doesn't work for us.
        pos = script.find_exact_command(EC.return_cmd()) + 1
        end = script.find_exact_command(EC.end_cmd())

        script.delete_commands_range(pos, end)

        new_block = (
            EF().add_if(
                EC.if_flag(memory.Flags.OBTAINED_DACTYLS),
                EF().jump_to_label(EC.jump_forward(), 'end')
            ).add(EC.generic_command(0xE7, 0, 0x1))  # Scroll up
            .add(EC.call_obj_function(cls.keeper_obj_id, FID.ARBITRARY_0, 1, FS.CONT))
            .add_if(
                EC.if_mem_op_value(cls.pc2_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.call_obj_function(0x9, FID.ACTIVATE, 1, FS.CONT))
            ).add_if(
                EC.if_mem_op_value(cls.pc3_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.call_obj_function(0xA, FID.ACTIVATE, 1, FS.CONT))
            )
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.pause(3.0))
            .add(EC.move_party(8, 0xF, 8, 0xF, 8, 0xF))
            .add(EC.call_obj_function(cls.keeper_obj_id, FID.ARBITRARY_1, 1, FS.CONT))
            .add(EC.move_party(0x06, 0x0B, 0x07, 0x0B, 0x05, 0x0B))
            .add(EC.pause(1))
            .add(EC.call_pc_function(0, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.pause(1))
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_1, 1, FS.SYNC))
            .add(EC.call_pc_function(0, FID.ARBITRARY_1, 1, FS.SYNC))
            .add_if(
                EC.if_mem_op_value(cls.pc2_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.call_obj_function(0x9, FID.TOUCH, 1, FS.SYNC))
                .add(EC.call_pc_function(1, FID.ARBITRARY_1, 1, FS.SYNC))
            ).add_if(
                EC.if_mem_op_value(cls.pc3_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.call_obj_function(0xA, FID.TOUCH, 1, FS.SYNC))
                .add(EC.call_pc_function(2, FID.ARBITRARY_1, 1, FS.SYNC))
            )
            .add(EC.set_flag(memory.Flags.OBTAINED_DACTYLS))
            .add(EC.assign_mem_to_mem(cls.num_pcs_addr, cls.temp_dactyl_status_addr,1))
            .add(EC.set_reset_bits(cls.temp_dactyl_status_addr, 0xC0, True))
            .add(EC.assign_val_to_mem(3, memory.Memory.OW_MOVE_STATUS, 1))
            .add(EC.assign_val_to_mem(3, memory.Memory.OW_MOVE_STATUS_EXTRA, 1))
            .add(EC.assign_val_to_mem(0x01F8, memory.Memory.DACTYL_X_COORD_LO, 2))
            .add(EC.assign_val_to_mem(0x0048, memory.Memory.DACTYL_Y_COORD_LO, 2))
            .add(EC.assign_mem_to_mem(cls.temp_dactyl_status_addr,
                                      memory.Memory.DACTYL_STATUS, 1))
            # Change Location
            .add(get_command(bytes.fromhex('E0F3033F09')))  # Copied from orig
            .set_label('end')
        )
        script.insert_commands(new_block.get_bytearray(), pos)

        pos = script.get_function_end(0xB, FID.ARBITRARY_0) - 1
        script.insert_commands(EC.play_sound(0xFF).to_bytearray(), pos)
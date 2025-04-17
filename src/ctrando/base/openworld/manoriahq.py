"""Openworld Manoria Headquarters"""
from cgitb import enable

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Manoria Headquarters"""
    loc_id = ctenums.LocID.MANORIA_HEADQUARTERS

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Manoria Headquarters.
        - Change storyline triggers to flags
        - Change slides to work with any number of PCs.
        """
        cls.change_slide_activations(script)
        cls.change_storyline_triggers(script)
        cls.modify_central_battle(script)


    @classmethod
    def modify_central_battle(cls, script: Event):
        """
        Move some triggers around to prevent softlocks in the organ room.
        """

        # Trigger objects are in 0x26, 0x27, 0x28.
        # Coordinates in startup are bogus.  They are set in Arb0.

        # Object 0x26 - 0x144, 0x1AC
        # Object 0x27 - 0x178, 0x1AC
        # Object 0x28 - 0x160, 0x198

        # We're going to try to get away with a single trigger (0x27)
        pos = script.get_function_start(0x26, FID.ARBITRARY_0)
        new_cmd = EC.set_object_coordinates_pixels(0x144, 0x120)
        script.data[pos: pos+len(new_cmd)] = new_cmd.to_bytearray()

        pos = script.get_function_start(0x28, FID.ARBITRARY_0)
        new_cmd = EC.set_object_coordinates_pixels(0x160, 0x120)
        script.data[pos: pos + len(new_cmd)] = new_cmd.to_bytearray()

        # Pixel coords are weird.
        pos = script.get_function_start(0x27, FID.ARBITRARY_0)
        new_cmd = EC.set_object_coordinates_pixels(0x160, 0x1AC)
        script.data[pos: pos + len(new_cmd)] = new_cmd.to_bytearray()

    @classmethod
    def change_storyline_triggers(cls, script: Event):
        """
        Replace storyline checks with flag checks.
        """

        storyline_check = EC.if_storyline_counter_lt(0x1B)
        repl_jump = EC.if_not_flag(memory.Flags.MANORIA_BOSS_DEFEATED)
        pos = script.find_exact_command(storyline_check)
        script.replace_jump_cmd(pos, repl_jump)

        pos = script.get_function_start(0x2E, FID.ACTIVATE)
        pos = script.find_exact_command(storyline_check)
        script.replace_jump_cmd(pos, repl_jump)

    @classmethod
    def change_slide_activations(cls, script: Event):
        """
        Modify slides to work with aribtrary party sizes
        - Alter PC startup functions to account for missing PCs
        - Remove similar storyline-based code from slide objects.
        - Add exploremode on after partyfollows in case of 1 pc party.
        """

        # 0x7F021E counts how many PCs have slid down.  It wants to wait
        # until the count reaches 3, but that will never happen unless there's
        # a full party.  Auto-increment for missing members.
        block = (
            EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2,
                                          0x7F0230, 1))
            .add_if(
                EC.if_mem_op_value(0x7F0230, OP.GREATER_THAN, 6),
                EF().add(EC.increment_mem(0x7F021E))
            ).add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3,
                                       0x7F0230, 1))
            .add_if(
                EC.if_mem_op_value(0x7F0230, OP.GREATER_THAN, 6),
                EF().add(EC.increment_mem(0x7F021E))
            )
        )

        # for obj_id in range(1, 8):
        #     start, end = script.get_function_bounds(obj_id, FID.STARTUP)
        #
        #     # This should be inside the first PC check
        #     pos = script.find_exact_command(EC.increment_mem(0x7F021E),
        #                                     start, end)
        #     script.insert_commands(block.get_bytearray(), pos)

        for fid in (FID.ARBITRARY_0, FID.ARBITRARY_1):
            pos = script.find_exact_command(EC.return_cmd(),
                                            script.get_function_start(0, fid))
            # script.insert_commands(
            #     EF()
            #     .add(EC.pause(1))
            #     .add(EC.assign_val_to_mem(0, memory.Memory.DISABLE_MENU_00, 1))
            #     .get_bytearray()
            #     , pos
            # )

        # initial_slides = (0x1F, 0x32, 0x34)
        initial_slides = (0x1F, 0x34)
        repeat_slides = (0x1E, 0x33)
        slide_objs = initial_slides + repeat_slides

        for obj_id in slide_objs:
            pos = script.get_object_start(obj_id)
            if obj_id in repeat_slides:
                pos = script.find_exact_command(
                    EC.if_storyline_counter_lt(0x1B), pos
                )
                # The game has a few storyline checks to determine whether
                # there's a non-full party.  We do a better check above.
                script.delete_jump_block(pos)
                script.delete_jump_block(pos)
                script.delete_jump_block(pos)
                script.insert_commands(block.get_bytearray(), pos)

            if obj_id in initial_slides:
                pos = script.find_exact_command(EC.set_byte(0x7F021C), pos)
                script.insert_commands(block.get_bytearray(), pos)

                disable_pos = script.find_exact_command(
                    EC.assign_val_to_mem(1, memory.Memory.DISABLE_MENU_00, 1),
                    script.get_object_start(obj_id)
                )
                script.delete_commands(disable_pos, 1)

                enable_pos = script.find_exact_command(
                    EC.assign_val_to_mem(0, memory.Memory.DISABLE_MENU_00, 1),
                    script.get_object_start(obj_id)
                )
                script.delete_commands(enable_pos, 1)


            # There are two partyfollows.  The game is implicitly using the
            # second to turn exploremode on.  Make it explicit for 1 PC teams.

            pos = script.find_exact_command(EC.party_follow(), pos)
            wait_block = (
                EF().add(EC.pause(1))
                # .add_if(
                #     EC.if_mem_op_value(0x7F0230, OP.GREATER_THAN, 6),
                #     EF().add(EC.pause(1))
                # )
            )
            script.insert_commands(wait_block.get_bytearray(), pos)
            pos += len(wait_block) + 1

            pos = script.find_exact_command(EC.party_follow(), pos) + 1
            script.insert_commands(EC.set_explore_mode(True).to_bytearray(),
                                   pos)


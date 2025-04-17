"""Update Prison Catwalks for an open world."""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.strings import ctstrings


# The Trial Storyline values
# 2D . Trial ends
# 2E . Lucca comes to break Crono out of prison
# 30 . Escape Guardia Castle
# 33 . Escape through Guardia Forest Portal

class EventMod(locationevent.LocEventMod):
    """EventMod for Prison Catwalks"""
    loc_id = ctenums.LocID.PRISON_CATWALKS
    crono_obj = 3
    lucca_obj = 5
    x_coord_addr = 0x7F0230
    y_coord_addr = 0x7F0232

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Prison Catwalks Event.
        - Make Crono-specific functions for the first PC instead
        - Make Lucca-specific functions for the second PC instead
        - Change storyline triggers to flag triggers.
        """
        cls.modify_pc_objs(script)
        cls.remove_flags(script)
        cls.replace_storyline_checks(script)
        cls.modify_perp_walk(script)
        cls.modify_tank_kill(script)
        cls.fix_bridge(script)
        cls.modify_object_loads(script)

        # Change luccas to second pc
        for ind, ct_str in enumerate(script.strings):
            script.strings[ind] = ct_str.replace(b'\x15', b'\x1C')

    @classmethod
    def modify_object_loads(cls, script: locationevent.LocationEvent):
        """
        Only load the guards/boss when you're on the right part of the level
        """

        guard_y = 0x29

        for obj_id in (0x10, 0x11):
            pos = script.get_object_start(obj_id)
            y_pos_block = (
                EF()
                .add(EC.get_pc_coordinates(0, cls.x_coord_addr, cls.y_coord_addr))
                .add_if(
                    EC.if_mem_op_value(cls.y_coord_addr, OP.NOT_EQUALS, guard_y),
                    EF()
                    .add(EC.remove_object(obj_id))
                    .add(EC.return_cmd())
                    .add(EC.end_cmd())
                )
            )
            script.insert_commands(y_pos_block.get_bytearray(), pos)

        for obj_id in (0xD, 0xE, 0xF):
            pos = script.get_object_start(obj_id)
            y_pos_block = (
                EF()
                .add(EC.get_pc_coordinates(0, cls.x_coord_addr, cls.y_coord_addr))
                .add_if(
                    EC.if_mem_op_value(cls.y_coord_addr, OP.EQUALS, guard_y),
                    EF()
                    .add(EC.remove_object(obj_id))
                    .add(EC.return_cmd())
                    .add(EC.end_cmd())
                )
            )
            script.insert_commands(y_pos_block.get_bytearray(), pos)

    @classmethod
    def remove_flags(cls, script: locationevent.LocationEvent):
        """
        Remove the LuccaFlags & 01 reset because it's repurposed.
        Remove a reset to a flag, which makes guards respawn, after the DTank
        is down.
        """
        # cmd = EC.reset_flag(memory.Flags.PRISON_STAIRS_TORTURE_GUARDS_OUT)
        # pos = script.find_exact_command(cmd)
        # script.insert_commands(
        #     EC.if_not_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK,
        #                    len(cmd)+1).to_bytearray(), pos
        # )

        pos = script.find_exact_command(
            EC.reset_bit(0x7F005A, 0x01),
            script.get_function_start(1, FID.ACTIVATE)
        )
        script.delete_commands(pos, 1)

    @classmethod
    def replace_storyline_checks(cls, script: locationevent.LocationEvent):
        """
        Replace storyline checks with flag checks
        - Storyline < 0x2E --> Lucca has not rescued Crono
        - Storyline < 0x30, 0x33 --> Has not escaped
        """
        # Replace storyline < 0x2E with Lucca has not yet rescued Crono
        objs = (0, 1, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF)
        objs_2E = (0, 1, 0xD, 0xE, 0xF)
        objs_30 = (0,)
        objs_33 = (0, 0xA, 0xB, 0xC)
        for obj_id in objs:
            pos = script.get_object_start(obj_id)
            if obj_id in objs_2E:
                pos = script.find_exact_command(
                    EC.if_storyline_counter_lt(0x2E), pos)
                script.replace_jump_cmd(
                    pos,
                    EC.if_not_flag(memory.Flags.LUCCA_RESCUED_CRONO)
                )

            if obj_id in objs_30:
                pos = script.find_exact_command(
                    EC.if_storyline_counter_lt(0x30), pos)
                script.replace_jump_cmd(
                    pos,
                    EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON)
                )

            if obj_id in objs_33:
                pos = script.find_exact_command(
                    EC.if_storyline_counter_lt(0x33), pos)
                script.replace_jump_cmd(
                    pos,
                    EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON)
                )

    @classmethod
    def modify_pc_objs(cls, script: locationevent.LocationEvent):
        """
        Conditionally load PCs depending on quest status.
        """
        modify_prison_crono_object(script, 3)
        make_prison_pc_object(script, 4, ctenums.CharID.MARLE)
        modify_prison_lucca_object(script, 5)
        make_prison_pc_object(script, 6, ctenums.CharID.ROBO)
        make_prison_pc_object(script, 7, ctenums.CharID.FROG)
        make_prison_pc_object(script, 8, ctenums.CharID.AYLA)
        make_prison_pc_object(script, 9, ctenums.CharID.MAGUS)

    @classmethod
    def modify_perp_walk(cls, script: locationevent.LocationEvent):
        """
        Only Crono has a handcuffed pose.  Everyone else will do something
        goofy.
        """

        # TODO: When DC is in play, this needs to be revisited.  Probably
        #       always use the alt-animation.
        anim_cmd = EC.play_animation(0x43)
        pos = script.find_exact_command(
            anim_cmd,
            script.get_object_start(cls.crono_obj)
        )

        script.insert_commands(
            EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1,
                               OP.EQUALS, 0, 1,
                               bytes_jump=len(anim_cmd)+1).to_bytearray(),
            pos
        )

        pos, _ = script.find_command([0xE0], pos)
        new_cmd = locationevent.get_command(
            bytes.fromhex("E14702141F")  # To prison cells
        )
        new_block = (
            EF()
            .add(EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1))
            .add(EC.assign_val_to_mem(3, memory.Memory.NUM_DAYS_TILL_EXECUTION, 1))
            .add(EC.set_flag(memory.Flags.CRONO_HAS_BEEN_IMPRISONED))
            .add(EC.set_flag(memory.Flags.CRONO_WAKES_IN_CELL))
            .add(EC.darken(8)).add(EC.fade_screen())
            .add(new_cmd)
        )
        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        script.delete_commands(pos, 1)  # Old change loc

    @classmethod
    def modify_tank_kill(cls, script: locationevent.LocationEvent):
        """
        Give an alternate tank killing animation for non-Crono prisoners.
        """

        # Remove the partyfollow from the end of the kill animation
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(cls.crono_obj, FID.ARBITRARY_1)
        )
        script.delete_commands(pos, 1)

        # Copy the end-block with the chancellor coming out from the main
        # animation.
        pos = script.find_exact_command(
            EC.call_obj_function(0xA, FID.ARBITRARY_1, 6, FS.CONT),
            script.get_function_start(cls.crono_obj, FID.ARBITRARY_1)
        )

        end = script.find_exact_command(EC.return_cmd(), pos) + 1
        end_block = EF.from_bytearray(script.data[pos: end])

        intro_block = (
            EF()
            .add(EC.play_sound(0x6C))
            .add(EC.call_obj_function(0x12, FID.TOUCH, 6, FS.CONT))
            .add(EC.pause(6))
            .add(EC.set_object_drawing_status(0x12, False))
            .add(EC.shake_screen(True))
            .add(EC.call_obj_function(0x13, FID.TOUCH, 6, FS.CONT))
            .add(EC.pause(6))
        )

        # Put generic tank kill in crono's object arb 2.
        func = (
            EF()
            .append(intro_block)
            # Anim goes here
            .append(end_block)
        )

        script.set_function(cls.crono_obj, FID.ARBITRARY_2, func)

        # Move the battle and ending command into a non-pc object to avoid
        # partyfollow weirdness.

        pos = script.find_exact_command(
            EC.call_obj_function(cls.crono_obj, FID.ARBITRARY_1, 6, FS.HALT),
            script.get_function_start(cls.lucca_obj, FID.ARBITRARY_1)
        )
        script.replace_command_at_pos(
            pos,
            EC.call_obj_function(0, FID.ARBITRARY_0, 4, FS.CONT)
        )

        new_calls = (
            EF()
            .add_if_else(
                EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1,
                                   OP.EQUALS, 0, 1),
                EF().add(EC.call_obj_function(
                    cls.crono_obj, FID.ARBITRARY_1, 6, FS.HALT)),
                EF().add(EC.call_obj_function(
                    cls.crono_obj, FID.ARBITRARY_2, 6, FS.HALT))
            ).add(EC.party_follow())
            .add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )
        script.set_function(0, FID.ARBITRARY_0, new_calls)


    @classmethod
    def fix_bridge(cls, script: locationevent.LocationEvent):
        """
        Don't leave the bridge broken after the prison break.  This lets
        players re-explore the dungeon/save Fritz after.

        Also suppress the chancellor message when he's gone.
        """
        pos, cmd = script.find_command(
            [0xE4], script.get_function_start(0, FID.ACTIVATE)
        )
        pos += len(cmd)
        pos, _ = script.find_command([0xE4], pos)
        script.delete_commands(pos, 1)

        start, end = script.get_function_bounds(1, FID.ACTIVATE)
        jump_bytes = end - start  #  -1 from return, +1 for jump cancels

        script.insert_commands(
            EF().add_if(
                EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                EF().add(EC.jump_forward(jump_bytes))
            ).get_bytearray(), start
        )


# Some general purpose prison functions that will be useful in other places.
def modify_prison_crono_object(
        script: locationevent.LocationEvent,
        crono_obj: int):
    """
    Load Crono after the prison break is complete.
    Before, load a character depending on the value set previously in memory.

    Minor Note:  This (by happy accident) works during attract mode too
      becase the value of 0 in memory will load Crono.
    """

    startup_fn = EF()
    cond_load_block = EF()
    for pc_id in range(6):
        cond_load_block.add_if(
            EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1,
                               OP.EQUALS, pc_id, 1),
            EF().add(EC.load_pc_in_party(pc_id))
            .jump_to_label(EC.jump_forward(), 'end_pc_load')
        )
    cond_load_block.add(EC.load_pc_in_party(6))

    (
        startup_fn
        .add_if_else(
            EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
            cond_load_block,
            EF().add(EC.load_pc_in_party(ctenums.CharID.CRONO))
        )
        .set_label('end_pc_load')
    )

    pos = script.get_object_start(crono_obj)
    script.insert_commands(startup_fn.get_bytearray(), pos)
    pos += len(startup_fn)
    script.delete_commands(pos, 1)  # original load


def modify_prison_lucca_object(
        script: locationevent.LocationEvent,
        lucca_obj: int):
    """
    Load Lucca after the prison break is complete.
    Before, load the recruit.
    """

    pos = script.get_object_start(lucca_obj)
    end = script.find_exact_command(EC.return_cmd(), pos)
    load_block = EF.from_bytearray(script.data[pos:end])

    pos = end + 1  # over return
    end = script.get_function_end(lucca_obj, FID.STARTUP)
    controllable_block = EF.from_bytearray(script.data[pos:end])

    new_startup = (
        EF()
        .add_if_else(
            EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
            load_block,
            EF().add(EC.load_pc_in_party(ctenums.CharID.LUCCA))
        )
        .add(EC.return_cmd())
        .add_if_else(
            EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
            controllable_block,
            EF().add(EC.set_controllable_infinite())
        )
        .add(EC.end_cmd())
    )

    script.set_function(lucca_obj, FID.STARTUP, new_startup)


def make_prison_pc_object(
        script: locationevent.LocationEvent,
        obj_id: int,
        char_id: ctenums.CharID
):
    """
    Make a normal PC object only load the PC after the escape is over.
    """

    startup_fn = (
        EF()
        .add_if(
            EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
            EF().add(EC.load_pc_in_party(char_id))
        )
        .add(EC.return_cmd())
        .add_if(
            EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
            EF().add(EC.set_controllable_infinite())
        )
    )
    script.set_function(obj_id, FID.STARTUP, startup_fn)
    script.set_function(obj_id, FID.ACTIVATE,
                        EF().add(EC.return_cmd()))

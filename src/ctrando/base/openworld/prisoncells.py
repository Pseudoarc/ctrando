"""Update Prison Cells for an open world."""
from ctrando.base.openworld import prisoncatwalks as pcat
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID


# The Trial Storyline values
# 2D . Trial ends
# 2E . Lucca comes to break Crono out of prison
# 30 . Escape Guardia Castle
# 33 . Escape through Guardia Forest Portal

# Crono Arbs:
# 0) Depends on 0x7F021E, 0x7F0210, and 0x7F0220.
#    - Metal bar rattling when escaping
#    - When 0x7F021E == 1, used to knock out guards.
#    - 0x7F0220 == 1 adds a pause to the knockout.
#    - Can be ignored because all guards will be gone when other PCs come in.
# 1) Called when knocking out guards too?  Also part of original cell breakout
# 2) Called during original cell breakout
# 3,4) For using the tunnel
# 5) Called when using switches -- LINK THIS
# 6) When Omnicrone is running away.
# 7) Part of execution scene
# 8) First battle with guards
# 9) The HP/MP mug -- LINK THIS
# A) When fighting Omnicrone
# B) Battle with the guard in the Omnicrone hall

# Summary: Most of these can be left as-is because the battles are gone if
#          there is a revisit.  Arb 5 and 9 need to be linked.  We also need
#          to make sure that no guards spawn after DTank is defeated.

class EventMod(locationevent.LocEventMod):
    """EventMod for Prison Cells"""
    loc_id = ctenums.LocID.PRISON_CELLS
    crono_obj = 0x14

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Prison Cells Event.
        - Add player objects so that the area can be revisited.
        - Change storyline triggers to flag triggers
        - During the prison break, change Crono to the imprisoned.
        """
        cls.fix_lunch_bag(script)
        cls.alter_static_animations(script)
        cls.change_storyline_triggers(script)
        cls.update_pc_objects(script)
        cls.update_secret_passage(script)
        cls.shorten_execution_time(script)
        cls.modify_perp_walk(script)
        cls.link_pc_arbs(script)

    @classmethod
    def fix_lunch_bag(cls, script: locationevent.LocationEvent):
        """
        Make the lunch box always appear.  Before PCs.
        """
        bag_obj = 0x24
        
        new_startup = (
            EF().add_if(
                EC.if_flag(memory.Flags.RECEIVED_PRISON_CELL_GIFT),
                EF().add(EC.remove_object(bag_obj))
                .jump_to_label(EC.jump_forward(), 'return')
            )
            .add(EC.load_npc(0x65))
            .add(EC.set_object_coordinates_pixels(0x120, 0x1ED))
            .set_label('return')
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )

        str_id = script.add_py_string(
            "{line break}Got 1 {item}!{line break}{itemdesc}{null}"
        )
        new_act = (
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.ETHER, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.set_flag(memory.Flags.RECEIVED_PRISON_CELL_GIFT))
            .add(EC.play_sound(0xB0))  # Tonic sound
            .add(EC.auto_text_box(str_id))
            .add(EC.remove_object(0x24))
            .add(EC.return_cmd())
        )

        script.set_function(bag_obj, FID.STARTUP, new_startup)
        script.set_function(bag_obj, FID.ACTIVATE, new_act)
        script.set_function(0, FID.ARBITRARY_0, EF())
        
    @classmethod
    def modify_wakeup_anim(cls, script: locationevent.LocationEvent):
        """Shorten the animation when first waking in the cell"""

        # The problem is that the wakeup animation uses many static anims
        # which are not consistent across characters.  Replace with normals.
        new_wakeup = (
            EF().add(EC.play_animation(8))  # lie down
            .add(EC.pause(7.5)).add(EC.play_animation(0x1D))  # kneel
            .add(EC.pause(2)).add(EC.play_animation(0))
            .add(EC.pause(0.5))
            .add_while(
                EC.if_mem_op_value(0x7F0234, OP.NOT_EQUALS, 3),
                EF().add(EC.play_animation(0x21))
                .add(EC.pause(1))
                .add(EC.increment_mem(0x7F0234))
            )
            .add_while(
                EC.if_mem_op_value(0x7F0232, OP.NOT_EQUALS, 4),
                EF().add(EC.play_animation(0x17))
                .add(EC.pause(1.0))
                .add(EC.increment_mem(0x7F0232))
            )
        )

        pos = script.find_exact_command(
            EC.static_animation(0x45),
            script.get_function_start(cls.crono_obj, FID.STARTUP)
        )

        end = script.find_exact_command(
            EC.set_flag(memory.Flags.CRONO_WAKES_IN_CELL),
            pos
        )

        script.insert_commands(
            new_wakeup.get_bytearray(), pos
        )
        script.delete_commands_range(
            pos + len(new_wakeup), end + len(new_wakeup)
        )

    @classmethod
    def alter_static_animations(cls, script: locationevent.LocationEvent):
        """Replace Crono static animations with generic animations."""
        cls.modify_wakeup_anim(script)

        # In Crono (0x14) Arb0 we have cage rattling and guard bopping
        pos, end = script.get_function_bounds(cls.crono_obj, FID.ARBITRARY_0)

        for _ in range(2):
            pos = script.find_exact_command(
                EC.static_animation(0x7D),
                pos, end
            )
            script.data[pos:pos+2] = EC.play_animation(0x1F).to_bytearray()
            pos = script.find_exact_command(
                EC.static_animation(0x7E),
                pos, end
            )
            script.data[pos:pos+2] = EC.play_animation(0x1E).to_bytearray()

        # facing-dependent static animations are removed for a normal anim.
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0210, OP.EQUALS, 3),
            pos, end)
        del_end = script.find_exact_command(EC.play_sound(0x81), pos, end)
        script.delete_commands_range(pos, del_end)
        script.insert_commands(
            EF().add(EC.play_animation(0x31)).get_bytearray(),  # melee swing
            pos
        )

        # Getting knocked back - Arb1
        pos = script.find_exact_command(
            EC.static_animation(0x65),
            script.get_function_start(cls.crono_obj, FID.ARBITRARY_1)
        )
        script.replace_command_at_pos(
            pos, EC.play_animation(5)
        )
        pos = script.find_exact_command(EC.static_animation(0x46), pos)
        script.replace_command_at_pos(pos, EC.play_animation(8))
        pos += len(EC.play_animation(8))
        script.insert_commands(
            EF().add(EC.pause(8))
            .add(EC.play_animation(0x1D)).add(EC.pause(2)).get_bytearray(), pos)

        # Jump back from Omnicrone - Arb6
        pos = script.find_exact_command(
            EC.static_animation(0xB0),
            script.get_function_start(cls.crono_obj, FID.ARBITRARY_6)
        )
        script.replace_command_at_pos(pos, EC.play_animation(9))
        script.insert_commands(EC.set_own_facing('left').to_bytearray(), pos)

        pos = script.find_exact_command(EC.static_animation(0xAA), pos)
        script.replace_command_at_pos(pos, EC.play_animation(0x1D))

        new_arb2 = (
            EF()
            .add(EC.loop_animation(0x17, 5))
            .add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )
        script.set_function(cls.crono_obj, FID.ARBITRARY_2, new_arb2)

        # switch hitting
        new_arb5 = (
            EF().add(EC.set_explore_mode(False))
            .add(EC.play_animation(0x20))
            .add(EC.pause(3))
            .add(EC.play_sound(0x66))
            .add(EC.return_cmd())
        )

        script.set_function(cls.crono_obj, FID.ARBITRARY_5, new_arb5)

    @classmethod
    def remove_dialog(cls, script: locationevent.LocationEvent):
        """Remove extra dialog -- BEFORE PCS"""
        
    @classmethod
    def change_storyline_triggers(cls, script: locationevent.LocationEvent):
        """
        Replace storyline checks with flag checks
        - Storyline < 0x2E --> Lucca has not rescued Crono
        - Storyline < 0x30, 0x33 --> Has not escaped
        """

        pos = script.get_object_start(0)
        num_changes = 9
        change_count = 0
        repl_cmd = EC.if_not_flag(memory.Flags.LUCCA_RESCUED_CRONO)
        while change_count < num_changes:  # All storyline checks are 0x2E
            pos, _ = script.find_command([0x18], pos)
            script.replace_jump_cmd(pos, repl_cmd)
            change_count += 1

    @classmethod
    def update_pc_objects(cls, script: locationevent.LocationEvent):
        """
        Load any character for the imprisoned character.
        """

        # Crono's startup object goes like this:
        # Load Crono in party.
        # - If this is the first time in cell (not 0x7F0190 & 02) then do some
        #   intro wakeup animation, set the flag, and start the exec. timer.
        # - If coming up or down the hole in the floor/ceiling then play that
        #   animation.
        # - If storyline < 2E and crono is being taken to execution, play his
        #   march through the cells.

        pcat.modify_prison_crono_object(script, 0x14)
        pos = script.get_function_start(0x14, FID.ARBITRARY_9)
        script.replace_command_at_pos(pos, EC.play_animation(0xB))

        pcat.modify_prison_lucca_object(script, 0x15)

        script.insert_copy_object(0x23, 0x15)
        pcat.make_prison_pc_object(script, 0x15, ctenums.CharID.MARLE)

        for ind in range(4):
            script.insert_copy_object(0x23, 0x17)
            pcat.make_prison_pc_object(script, 0x17, ctenums.CharID(6-ind))

    @classmethod
    def link_pc_arbs(cls, script: locationevent.LocationEvent):
        """
        Link some PC arbs to with Crono's arbs.  AFTER PCS UPDATED.
        """

        for pc_obj in range(cls.crono_obj+1, cls.crono_obj+7):
            script.link_function(pc_obj, FID.ARBITRARY_5,
                                 cls.crono_obj, FID.ARBITRARY_5)
            script.link_function(pc_obj, FID.ARBITRARY_9,
                                 cls.crono_obj, FID.ARBITRARY_9)

        pos = script.get_function_start(5, FID.STARTUP)
        for _ in range(9):
            pos = script.find_exact_command(
                EC.call_obj_function(cls.crono_obj, FID.ARBITRARY_5,
                                     0, FS.HALT), pos
            )
            repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_5, 0, FS.HALT)
            script.data[pos: pos+len(repl_cmd)] = repl_cmd.to_bytearray()

        pos = script.find_exact_command(
            EC.call_obj_function(cls.crono_obj, FID.ARBITRARY_9,
                                 6, FS.HALT),
            script.get_function_start(0x13, 0)
        )
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_9, 6, FS.HALT)
        script.data[pos: pos+len(repl_cmd)] = repl_cmd.to_bytearray()

    @classmethod
    def update_secret_passage(cls, script: locationevent.LocationEvent):
        """
        Make the secret passage accessible by all characters.  AFTER PCs.
        """

        # Objects 0x23 and 0xE control the secret tunnel between levels of the
        # prison.  After adding PC objects it's 0x28 and 0xE.
        #  - Object 0xE calls Crono (0x14) arb4 to go down the hole.  The flag
        #    0x7F0191 & 20 is set before changelocation to indicate this.
        #  _ Object 0x28 calls Crono (0x14) arb3 to go back up.  The flag
        #    0x7F0191 & 10 is set before changeloation to indicate this.
        # Then Crono's startup has checks for the above two flags to play some
        # animations before set_controllable_infinite.  These routines have
        #
        # Crono's arb3 and arb4 have no calls to other object functions, but
        # the startup code has if lucca is active, call obj function.
        #  - When going down, Lucca's arb1 is called.  When going up, arb0.
        #
        # In addition, Lucca's startup sets coordinates depending on how the
        # tunnel flags are set.

        # The plan is:
        # 1) Change Lucca's arb3 and arb4 to arb5 and arb6 and update the calls
        #    so that she'll be able to link to Crono's arb3 and arb4 that we'll
        #    construct.
        # 2) Change objects 0x28, and 0xE so that the changelocation and flag
        #    setting are part of their activate, not part of Crono's arbs.
        # 3) Combine Crono's arb3 and arb4 (down and up the hole) into one
        #    function which will vary depending on which tunnel flag is set.
        #    Set this function to be the Crono object's new arb3.
        # 4) Link everyone's arb3 to the Crono object's arb3.
        # 5) Move Crono's startup code to his arb4.  But also make changes so
        #    that anyone can link to Crono's arb4 and have it make sense. This
        #    is the gross part.
        #    a) Use some script memory to differentiate whether we are calling
        #       the function from pc1 (copy orig Crono) or pc2,3 (orig Lucca).
        #       It is possible that we can spare a second arb for this, but
        #       I'd like to keep one open just in case.
        #    b) Set coordinates according to which flag is hit and whether the
        #       function is called as pc1 or pc2,3.
        #    c) Instead of calling Lucca arb 0 or 1, set the calling as pc2,3
        #       flag and call pc2,3's arb 4, which will be linked here.
        #    d) When called as pc2,3 insert Lucca's animation (arb0 or arb1)
        # 6) Link everyone's arb4 to this new awful Crono arb4
        # 7) Add logic in object 0 startup right after the first return to
        #    call pc1's arb4.
        # 8) Regret trying to fix the prison.

        cls.shuffle_lucca_arbs(script)  # Handle 1 
        cls.alter_tunnel_activation(script)  # Handle 2 and 3

        lucca_down_startup = script.get_function(0x16, FID.ARBITRARY_1)
        lucca_up_startup = script.get_function(0x16, FID.ARBITRARY_0)

        # Handle 5a
        pc2_spot = 0x7F0238
        pc3_spot = 0x7F023A
        new_flag = 0x7F023E  # Determine whether to call the pc1 or pc2+

        # Handle 7)
        pos = script.find_exact_command(EC.return_cmd())  # from obj0
        pos += 1
        script.insert_commands(
            EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2,
                                          pc2_spot, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3,
                                      pc3_spot, 1))
            .add(EC.call_pc_function(0, FID.ARBITRARY_4, 5, FS.CONT))
            .get_bytearray(), pos
        )

        # Handle half of 5c (doesn't insert lucca's arbs)
        cls.modify_crono_startup_calls(script, new_flag, pc2_spot, pc3_spot)

        # Handle the rest of 5c, 5b and 5d
        cls.move_lucca_startup_calls(
            script, lucca_down_startup, lucca_up_startup, new_flag)

        cls.move_crono_startup_to_arb4(script)

        # set coords to be off screen when the tunnel is used.
        coords = (
            EF().add_if(
                EC.if_flag(memory.Flags.USED_PRISON_HOLE_GOING_DOWN),
                EF().add(EC.set_object_coordinates_tile(0xFF, 0xFF))
            )
            .add_if(
                EC.if_flag(memory.Flags.USED_PRISON_HOLE_GOING_UP),
                EF().add(EC.set_object_coordinates_tile(0xFF, 0xFF))
            )
        )
        for obj_id in range(0x14, 0x14+7):
            pos = script.find_exact_command(
                EC.return_cmd(),
                script.get_function_start(obj_id, FID.STARTUP)
            )
            script.insert_commands(coords.get_bytearray(), pos)

        # Link arbs.
        for obj_id in range(0x15, 0x15+6):
            script.link_function(obj_id, FID.ARBITRARY_3,
                                 0x14, FID.ARBITRARY_3)
            script.link_function(obj_id, FID.ARBITRARY_4,
                                 0x14, FID.ARBITRARY_4)

    @classmethod
    def shuffle_lucca_arbs(cls, script: locationevent.LocationEvent):
        """
        Move Lucca's arb3 and arb4 to arb5 and arb6 and update calls.
        """
        crono_obj = 0x14
        lucca_obj = 0x16  # after PC update
        func = script.get_function(lucca_obj, FID.ARBITRARY_3)
        script.set_function(lucca_obj, FID.ARBITRARY_6, func)
        func = script.get_function(lucca_obj, FID.ARBITRARY_4)
        script.set_function(lucca_obj, FID.ARBITRARY_7, func)

        # Replace Lucca's calls to arb 3 and 4 with calls to arb 5 and 6
        start = script.get_function_start(crono_obj, FID.ARBITRARY_A)
        cmd = EC.call_obj_function(lucca_obj, FID.ARBITRARY_3, 6, FS.HALT)
        repl_cmd = EC.call_obj_function(lucca_obj, FID.ARBITRARY_6, 6, FS.HALT)
        pos = script.find_exact_command(cmd, start)
        script.data[pos: pos+len(cmd)] = repl_cmd.to_bytearray()

        cmd = EC.call_obj_function(lucca_obj, FID.ARBITRARY_4, 6, FS.HALT)
        repl_cmd = EC.call_obj_function(lucca_obj, FID.ARBITRARY_7, 6, FS.HALT)
        pos = script.find_exact_command(cmd, pos)
        script.data[pos: pos+len(cmd)] = repl_cmd.to_bytearray()

    @classmethod
    def alter_tunnel_activation(cls, script: locationevent.LocationEvent):
        """
        Combine Crono's arb3 and arb4 (tunnel activations) into one function.
        Put this in his arb3 slot.  Move the tunnel bit setting and location
        changing from this function into the tunnel object activation.
        """
        crono_obj = 0x14

        # Alter Crono Arb3 to handle both up and down depending on flag
        pos = script.get_function_start(crono_obj, FID.ARBITRARY_3)
        pos, _ = script.find_command([0x65], pos)  # set bit
        script.delete_commands(pos, 1)
        pos, go_up_changeloc_cmd = script.find_command([0xE0], pos)
        script.delete_commands(pos, 1)

        # Keep reading through Arb4
        pos, _ = script.find_command([0x65], pos)  # set bit
        script.delete_commands(pos, 1)
        pos, go_down_changeloc_cmd = script.find_command([0xE0], pos)
        script.delete_commands(pos, 1)

        old_arb_3 = script.get_function(crono_obj, FID.ARBITRARY_3)
        old_arb_4 = script.get_function(crono_obj, FID.ARBITRARY_4)

        new_arb3 = (
            EF().add_if(
                EC.if_flag(memory.Flags.USED_PRISON_HOLE_GOING_UP),
                old_arb_3,
            ).add_if(
                EC.if_flag(memory.Flags.USED_PRISON_HOLE_GOING_DOWN),
                old_arb_4,
            )
        )
        script.set_function(0x14, FID.ARBITRARY_3, new_arb3)

        # Alter passage activations
        func = (
            EF().add(EC.set_flag(memory.Flags.USED_PRISON_HOLE_GOING_DOWN))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 6, FS.HALT))
            .add(go_down_changeloc_cmd)
            .add(EC.return_cmd())
        )

        script.set_function(0xE, FID.ACTIVATE, func,)

        func = (
            EF().add(EC.set_flag(memory.Flags.USED_PRISON_HOLE_GOING_UP))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 6, FS.HALT))
            .add(go_up_changeloc_cmd)
            .add(EC.return_cmd())
        )

        script.set_function(0x28, FID.ACTIVATE, func)

    @classmethod
    def modify_crono_startup_calls(cls, script: locationevent.LocationEvent,
                                   new_flag: int,
                                   pc2_spot: int, pc3_spot: int):
        """
        In Crono's startup, replace 'is lucca active' checks to pc2 checks.
        Also replace calls to lucca arbs with calls to pc_id arb4 which will
        eventually contain all of the startup code.
        """
        crono_obj = 0x14
        lucca_obj = 0x16
        # Modify Crono's startup to call other PC object functions
        # Also replace the if_lucca_actives to if there's a pc2

        # Instead of calling Lucca arb0 or arb1 on startup, we are going to
        # Call Crono's startup (which will be moved to arb4).  So we add
        # logic to change to call depending on whether the new flag is set
        # or not.

        # Calls to Lucca arbs will be replaced by this.
        # Set the flag and make calls to pc2 and pc3 arb4s depending on if
        # they exist or not.
        call_block = (
            EF().add(EC.assign_val_to_mem(1, new_flag, 1))
            .add_if_else(
                EC.if_mem_op_value(pc3_spot, OP.GREATER_THAN, 6, 1),
                EF()
                .add(EC.call_pc_function(1, FID.ARBITRARY_4, 1, FS.HALT)),
                EF().add(EC.call_pc_function(1, FID.ARBITRARY_4, 1, FS.CONT))
                .add(EC.pause(4))
                .add(EC.call_pc_function(2, FID.ARBITRARY_4, 1, FS.HALT))
            )
        )

        # Replace instances of "if lucca is active" to "if pc2_spot <= 6",
        # and change the call to the Lucca arb to the above call block.
        find_cmd = EC.if_pc_active(ctenums.CharID.LUCCA)
        repl_cmd = EC.if_mem_op_value(pc2_spot, OP.LESS_OR_EQUAL, 6, 1)

        pos = script.find_exact_command(
            find_cmd, script.get_function_start(crono_obj, FID.STARTUP)
        )
        script.replace_jump_cmd(pos, repl_cmd)
        pos = script.find_exact_command(
            EC.call_obj_function(lucca_obj, FID.ARBITRARY_0, 1, FS.HALT)
        )
        script.insert_commands(call_block.get_bytearray(), pos)
        pos += len(call_block)
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            find_cmd, script.get_function_start(crono_obj, FID.STARTUP)
        )
        script.replace_jump_cmd(pos, repl_cmd)
        pos = script.find_exact_command(
            EC.call_obj_function(0x16, FID.ARBITRARY_1, 1, FS.HALT)
        )
        script.insert_commands(call_block.get_bytearray(), pos)
        pos += len(call_block)
        script.delete_commands(pos, 1)

    @classmethod
    def move_lucca_startup_calls(
            cls, script: locationevent.LocationEvent,
            lucca_down_startup: EF,
            lucca_up_startup: EF,
            pc_flag: int):
        """
        Move lucca's startup animations into Crono's startup routine.  These
        will be contingent on pc_flag, which records whether we're calling
        the startup routine as pc1 or pc2,3.

        Part of this is setting coordinates correctly depending on pc index.
        """
        cmd = EC.if_flag(memory.Flags.USED_PRISON_HOLE_GOING_DOWN)
        pos = script.find_exact_command(
            cmd, script.get_function_start(0x14, FID.STARTUP)
        ) + len(cmd)

        script.insert_commands(
            EC.set_object_coordinates(0x9, 0x1A).to_bytearray(), pos
        )
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(pc_flag, OP.EQUALS, 1, 1),
                EF()
                .add(EC.set_object_coordinates_tile(9, 0x19))
                .append(lucca_down_startup.add(EC.return_cmd()))
            ).get_bytearray(), pos
        )

        cmd = EC.if_flag(memory.Flags.USED_PRISON_HOLE_GOING_UP)
        pos = script.find_exact_command(
            cmd, script.get_function_start(0x14, FID.STARTUP)
        ) + len(cmd)

        script.insert_commands(
            EC.set_object_coordinates_tile(0x9, 0x9).to_bytearray(), pos
        )
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(pc_flag, OP.EQUALS, 1, 1),
                EF()
                .add(EC.set_object_coordinates_tile(9, 0x1E))
                .append(lucca_up_startup.add(EC.return_cmd()))
            ).get_bytearray(), pos
        )

    @classmethod
    def move_crono_startup_to_arb4(cls, script: locationevent.LocationEvent):
        """
        Move the giant Crono startup routine into Crono arb4 so that it can
        be linked to by other pcs
        """
        del_st = script.find_exact_command(
            EC.set_explore_mode(False),
            script.get_function_start(0x14, FID.STARTUP)
        )
        del_end = script.find_exact_command(
            EC.set_controllable_infinite(), del_st
        )

        new_arb4 = EF.from_bytearray(script.data[del_st:del_end])
        new_arb4.add(EC.return_cmd())
        # new_arb4 = EF().add(EC.auto_text_box(2)).append(new_arb4)
        script.delete_commands_range(del_st, del_end)
        script.set_function(0x14, FID.ARBITRARY_4, new_arb4)

    @classmethod
    def shorten_execution_time(cls, script: locationevent.LocationEvent):
        """
        Less time for Crono three days to pass.
        """

        pos, end = script.get_function_bounds(2, FID.STARTUP)

        pos = script.find_exact_command(
            EC.generic_command(0xAD, 0xE0), pos, end)
        script.data[pos+1] = 0x50

        pos = script.find_exact_command(
            EC.generic_command(0xAD, 0x60), pos, end)
        script.data[pos+1] = 0x20

    @classmethod
    def modify_perp_walk(cls, script: locationevent.LocationEvent):
        """
        Only Crono has a handcuffed pose.  Everyone else will do something
        goofy without changing.
        """

        anim_cmd = EC.play_animation(0x43)
        pos = script.find_exact_command(
            anim_cmd,
            script.get_function_start(cls.crono_obj, FID.ARBITRARY_7)
        )

        script.insert_commands(
            EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1,
                               OP.EQUALS, 0, 1,
                               bytes_jump=len(anim_cmd)+1).to_bytearray(),
            pos
        )

        pos, _ = script.find_command(locationevent.EC.change_loc_commands, pos)
        new_cmd = EC.change_location(
            ctenums.LocID.PRISON_TORTURE_STORAGE_ROOM,
            8, 9, 1, 0x1, False
        )
        new_cmd.command = 0xE0
        script.data[pos:pos+len(new_cmd)] = new_cmd.to_bytearray()

        # This moved from startup to arb4
        pos = script.find_exact_command(
            anim_cmd,
            script.get_function_start(cls.crono_obj, FID.ARBITRARY_4)
        )

        script.insert_commands(
            EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1,
                               OP.EQUALS, 0, 1,
                               bytes_jump=len(anim_cmd)+1).to_bytearray(),
            pos
        )

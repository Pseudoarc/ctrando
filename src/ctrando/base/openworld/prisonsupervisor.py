"""Update Prison Supervisor's Office for an open world."""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID


# The Trial Storyline values
# 2D . Trial ends
# 2E . Lucca comes to break Crono out of prison
# 30 . Escape Guardia Castle
# 33 . Escape through Guardia Forest Portal

class EventMod(locationevent.LocEventMod):
    """EventMod for Prison Supervisor's Office"""
    loc_id = ctenums.LocID.PRISON_SUPERVISORS_OFFICE
    crono_obj = 5

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Prison Supervisor's Office Event.
        - Add player objects so that the area can be revisited.
        - Change storyline triggers to flag triggers
        - During the prison break, change Crono to the imprisoned.
        """
        # cls.update_pc_objects(script)
        cls.change_storyline_triggers(script)
        cls.update_crono_object(script)
        cls.update_lucca_object(script)  # BEFORE PC objects are added
        cls.add_pc_objects(script)
        cls.modify_imprisonment_cutscene(script)
        cls.modify_breakout_cutscene(script)
        cls.modify_perp_walk(script)

    @classmethod
    def update_pc_objects(cls, script: locationevent.LocationEvent):
        """
        During the prison break, load the prisoner and assistant in the
        vanilla objects.  Load normal pc objects after.
        """

    @classmethod
    def update_crono_object(cls, script: locationevent.LocationEvent):
        """
        During the prisonbreak, conditionally load Crono as the imprisoned
        character.  Otherwise, load Crono as usual.
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

        pos = script.get_object_start(5)
        script.insert_commands(startup_fn.get_bytearray(), pos)
        pos += len(startup_fn)
        script.delete_commands(pos, 1)  # Remove an old load command

    @classmethod
    def update_lucca_object(cls, script: locationevent.LocationEvent):
        """
        If during the escape, load the recruit (default lucca).  Otherwise
        load Lucca.

        Must call this BEFORE the other PC objects are added.
        """
        pos = script.get_object_start(6)
        end = script.find_exact_command(EC.return_cmd(), pos)  # no return
        load_block = EF.from_bytearray(script.data[pos:end])

        pos = end + 1  # over return
        end = script.find_exact_command(EC.end_cmd(), pos) + 1
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

        script.set_function(6, FID.STARTUP, new_startup)

    @classmethod
    def add_pc_objects(cls, script: locationevent.LocationEvent):
        """
        During the prisonbreak, conditionally load Crono as the imprisoned
        character.  Otherwise, load Crono as usual.
        """

        def make_pc_object(script: locationevent.LocationEvent,
                           obj_id: int,
                           char_id: ctenums.CharID):
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

        # Add a Marle object as Object 6
        # Keep the lucca object as object 7 (prev 6)

        # We copy a save point because it's almost empty already.
        script.insert_copy_object(3, 6)
        make_pc_object(script, 6, ctenums.CharID.MARLE)

        # Add Robo, Frog, Ayla, Magus as 8 through 11
        for ind in range(4):
            script.insert_copy_object(3, 8)
            make_pc_object(script, 8, ctenums.CharID(6 - ind))

    @classmethod
    def change_storyline_triggers(cls, script: locationevent.LocationEvent):
        """
        Change storyline < 0x2E to if lucca has not rescued.
        Call BEFORE adding objects.
        """
        storyline_cmd = EC.if_storyline_counter_lt(0x2E)
        replace_cmd = EC.if_not_flag(memory.Flags.LUCCA_RESCUED_CRONO)

        objs = (0, 2, 3, 5, 9, 0xC)
        for obj_id in objs:  # Always one check per object
            pos = script.get_object_start(obj_id)
            end = script.get_object_end(obj_id)
            pos = script.find_exact_command(storyline_cmd, pos, end)
            script.replace_jump_cmd(pos, replace_cmd)

        # Change setting storyline to setting the flag.
        set_storyline_cmd = EC.set_storyline_counter(0x2E)
        replace_cmd = EC.set_flag(memory.Flags.LUCCA_RESCUED_CRONO)

        pos = script.find_exact_command(
            set_storyline_cmd,
            script.get_function_start(6, FID.ARBITRARY_0)
        )
        script.delete_commands(pos, 1)
        script.insert_commands(replace_cmd.to_bytearray(), pos)

    @classmethod
    def modify_imprisonment_cutscene(cls, script: locationevent.LocationEvent):
        """
        Shorten cutscene by removing dialog.
        """

        # Cutscene progression -- AFTER PC OBJECTS ADDED
        # - Begins with ObjC, Arb0 Chancellor
        pos, end = script.get_function_bounds(0xC, FID.ARBITRARY_0)

        # This terrorist has tried to overthrow our kingdom!
        pos, _ = script.find_command([0xBB], pos, end)
        script.delete_commands(pos, 1)

        # He has been found guilty, carry out execution.
        pos, _ = script.find_command([0xC1], pos, end)
        script.delete_commands(pos, 1)

        #   - To Obj5, Arb0 Imprisoned
        #     - No text
        #     - To ObjE, Arb0 Supervisor (only anim)
        #     - To ObjD, Arb0 Present Soldier (only anim), returns
        pos, end = script.get_function_bounds(5, FID.ARBITRARY_0)
        pos = script.find_exact_command(EC.static_animation(0xE6))
        script.delete_commands(pos, 1)
        #   - Passes to ObjD, Arb1 Present Soldier (pokes imprisoned)
        #     - No text
        #     - Passes to Obj5, Arb1 Imprisoned Char
        #       - No text, but some pauses that maybe can be shortened
        #       - And some bad static anims
        pos, end = script.get_function_bounds(5, FID.ARBITRARY_1)
        pos = script.find_exact_command(EC.static_animation(0x70))
        script.data[pos:pos+2] = EC.play_animation(5).to_bytearray()
        pos = script.find_exact_command(EC.static_animation(0xE6))
        script.delete_commands(pos, 2)  # Anim + Pause
        #       - Passes to ObjE, Arb 1 Supervisor
        #          - Passes to ObjC, Arb2 Chancellor

        # The execution is in 3 days.
        pos, _ = script.find_command(
            [0xC1],
            script.get_function_start(0xC, FID.ARBITRARY_2)
        )
        script.delete_commands(pos, 1)

        #            - Returns (ObjE, Arb 1)
        pos, end = script.get_function_bounds(0xE, FID.ARBITRARY_1)

        # Allow the "So this is the monster..." text to stay (cmd 0xBB)
        # Delete special text depending on the number of innocent votes.
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0051, OP.LESS_THAN, 4),
            pos, end)
        script.delete_jump_block(pos)

        # "Yes Sir!" immediately follows
        script.delete_commands(pos, 1)
        #          - Passes to ObjF, Arb2 Guard (only moves)
        #          - Passes to Obj10, Arb1 Guard (only moves)

        pos, _ = script.find_command([0xBB], pos, end)  # Keep "Guards!"

        # "Take the prisoner away"
        pos, _ = script.find_command([0xBB], pos + 2, end)
        script.delete_commands(pos, 1)
        #          - To ObjD, Arb2 Soldier (only moves)
        #          - To ObjF, Arb3 Guard (hit imprisoned)
        #          - To Obj5, Arb2 Imprisoned (hit and changeloc)

        pos, end = script.get_function_bounds(5, FID.ARBITRARY_2)
        script.data[pos:pos+2] = EC.play_animation(9).to_bytearray()
        pos += 4  # skip over above static anim + pause
        script.data[pos:pos+2] = EC.play_animation(5).to_bytearray()

    @classmethod
    def modify_breakout_cutscene(cls, script: locationevent.LocationEvent):
        """
        Remove some dialog from the breaking out cutscene.  AFTER PCs.
        """

        # Starts in ObjE, Arb2 Supervisor
        #   - Calls Obj11, Arb0 (no text)
        #   - Calls Obj7, Arb0
        pos, end = script.get_function_bounds(7, FID.ARBITRARY_0)

        # Crono I've come to save you
        pos, _ = script.find_command([0xBB], pos, end)
        script.delete_commands(pos, 1)

        # Looks like you didn't need my help
        pos, _ = script.find_command([0xBB], pos, end)
        script.delete_commands(pos, 1)

        # Leave let's blow this joint.

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
            script.get_function_start(cls.crono_obj, FID.ARBITRARY_0)
        )

        block = (
            EF().add_if_else(
                EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1,
                                   OP.EQUALS, 0, 1,),
                EF().add(anim_cmd),
                EF().add(EC.play_animation(1))
            )
        )

        script.delete_commands(pos)
        script.insert_commands(block.get_bytearray(), pos)


def get_crono_object_load_block():
    """
    Get a function that loads a certain character during the escape and loads
    Crono otherwise.
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

    return startup_fn

"""Update Prison Torture Storage for an open world."""
from ctrando.base.openworld import prisoncatwalks as pcat
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
    """EventMod for Prison Torture Storage"""
    loc_id = ctenums.LocID.PRISON_TORTURE_STORAGE_ROOM

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Prison Torture Storage Event.
        - Add player objects so that the area can be revisited.
        - Change storyline triggers to flag triggers
        """
        cls.update_pc_objects(script)
        cls.change_storyline_triggers(script)
        cls.alter_breakout_cutscene(script)

    @classmethod
    def update_pc_objects(cls, script: locationevent.LocationEvent):
        """
        Load any character for the imprisoned character.
        """

        pcat.modify_prison_crono_object(script, 0x2)
        pcat.modify_prison_lucca_object(script, 0x3)

        script.insert_copy_object(8, 3)
        pcat.make_prison_pc_object(script, 3, ctenums.CharID.MARLE)

        for ind in range(4):
            script.insert_copy_object(8, 5)
            pcat.make_prison_pc_object(script, 0x5, ctenums.CharID(6-ind))

    @classmethod
    def change_storyline_triggers(cls, script: locationevent.LocationEvent):
        """
        Replace storyline setting/checking with flags. -- AFTER PCs
        """
        pos = script.find_exact_command(
            EC.set_storyline_counter(0x2E),
            # Lucca object after pc update
            script.get_function_start(4, FID.ARBITRARY_0),
        )

        repl_cmd = EC.set_flag(memory.Flags.LUCCA_RESCUED_CRONO)
        script.insert_commands(repl_cmd.to_bytearray(), pos)
        pos += len(repl_cmd)
        script.delete_commands(pos, 1)

        pos = script.get_object_start(0)
        num_changes = 5
        change_count = 0
        repl_cmd = EC.if_not_flag(memory.Flags.LUCCA_RESCUED_CRONO)
        while change_count < num_changes:  # All storyline checks are 0x2E
            pos, _ = script.find_command([0x18], pos)
            script.replace_jump_cmd(pos, repl_cmd)
            change_count += 1
        

    @classmethod
    def alter_breakout_cutscene(cls, script: locationevent.LocationEvent):
        """
        Change the breakout cutscene to remove dialog and change animations.
        """

        pos = script.find_exact_command(EC.return_cmd())
        script.insert_commands(
            EC.assign_mem_to_mem(
                memory.Memory.CRONO_TRIAL_PC1, 0x7F0210, 1
            ).to_bytearray(), pos
        )

        # Change the starting animation in the imprisoned PC's startup
        pos = script.find_exact_command(
            EC.static_animation(0xE3)
        )
        new_anim = (
            EF().add_if_else(
                EC.if_mem_op_value(0x7F0210, OP.EQUALS, 0),
                EF().add(EC.static_animation(0xE3)),
                EF().add(EC.play_animation(0x1D))
            )
        )

        script.insert_commands(new_anim.get_bytearray(), pos)
        pos += len(new_anim)
        script.delete_commands(pos, 1)

        # You have to delay the controllable command since it cancels anims.
        pos = script.find_exact_command(EC.set_controllable_infinite(), pos)
        script.insert_commands(
            EF()
            .add_if(
                EC.if_not_flag(memory.Flags.CRONO_TAKEN_EXECUTION),
                EF().jump_to_label(EC.jump_forward(), 'end')
            )
            .set_label('loop')
            .add_if(
                EC.if_not_flag(memory.Flags.LUCCA_RESCUED_CRONO),
                EF().jump_to_label(EC.jump_back(), 'loop')
            ).set_label('end')
            .get_bytearray(), pos
        )

        # Remove the Lucca textboxes.
        pos, end = script.get_function_bounds(4, FID.ARBITRARY_0)

        # Crono I've come to save you
        pos, _ = script.find_command([0xBB], pos, end)
        script.delete_commands(pos, 1)

        # Get outta my way
        pos, _ = script.find_command([0xBB], pos, end)
        script.delete_commands(pos, 1)

        # Take 5 you mug
        pos, _ = script.find_command([0xBB], pos, end)
        script.delete_commands(pos, 1)

        # What do you think of my Zonker-38?
        pos, _ = script.find_command([0xBB], pos, end)
        script.delete_commands(pos, 1)
        script.insert_commands(EC.pause(1).to_bytearray(), pos)

"""Update Prison Stairwellss for an open world."""
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
    """EventMod for Prison Stairwells"""
    loc_id = ctenums.LocID.PRISON_STAIRWELLS
    crono_obj = 7

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Prison Cells Event.
        - Add player objects so that the area can be revisited.
        - Change storyline triggers to flag triggers
        - During the prison break, change Crono to the imprisoned.
        """
        cls.alter_static_animations(script)
        cls.change_storyline_triggers(script)  # Before changing object ind
        cls.update_pc_objects(script)
        cls.remove_battles_after_escape(script)
        cls.modify_perp_walk(script)

    @classmethod
    def alter_static_animations(cls, script: locationevent.LocationEvent):
        """Replace static animations with generic ones."""

        # Guard bopping
        new_arb0 = (
            EF().add(EC.loop_animation(0xC, 1))
            .add(EC.play_animation(0x31))
            .add(EC.play_sound(0x81))
            .add(EC.pause(2))
            .add(EC.return_cmd())
        )

        script.set_function(cls.crono_obj, FID.ARBITRARY_0, new_arb0)

        # switch hitting
        new_arb1 = (
            EF().add(EC.set_explore_mode(False))
            .add(EC.play_animation(0x20))
            .add(EC.pause(3))
            .add(EC.play_sound(0x66))
            .add(EC.return_cmd())
        )

        script.set_function(cls.crono_obj, FID.ARBITRARY_1, new_arb1)

        # Jumping back from the first guard you can sneak up on.
        # It's easiest to just remove that short scene.  We remove obj01, which triggers it.
        pos = script.get_function_start(1, FID.STARTUP)
        script.insert_commands(EC.remove_object(1).to_bytearray(), pos)

    @classmethod
    def update_pc_objects(cls, script: locationevent.LocationEvent):
        """
        Conditionally load PCs depending on storyline triggers.
        Add objects for missing PCs.
        """

        pcat.modify_prison_crono_object(script, 7)
        pcat.modify_prison_lucca_object(script, 8)

        script.insert_copy_object(12, 8)
        pcat.make_prison_pc_object(script, 8, ctenums.CharID.MARLE)
        for ind in range(4):
            script.insert_copy_object(12, 0xA)
            pcat.make_prison_pc_object(script, 0xA, ctenums.CharID(6-ind))

    @classmethod
    def remove_battles_after_escape(cls, script: locationevent.LocationEvent):
        """
        Remove battles after the prison has been escaped.
        """

        # remove shields after escape
        shield_objs = (0xE, 0xF, 0x10, 0x11)

        for obj_id in shield_objs:
            pos = script.find_exact_command(
                EC.return_cmd(),
                script.get_object_start(obj_id)
            )

            block = (
                EF().add_if(
                    EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                    EF().add(EC.remove_object(obj_id))
                )
            )

            script.insert_commands(block.get_bytearray(), pos)

        # A guard fight resets on loading the stairs.  Remove that
        reset_flag = EC.reset_flag(memory.Flags.PRISON_STORAGE_GUARD_BATTLE)
        pos = script.find_exact_command(reset_flag)
        script.insert_commands(
            EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON,
                           1 + len(reset_flag)).to_bytearray(), pos
        )

    @classmethod
    def change_storyline_triggers(cls, script: locationevent.LocationEvent):
        """
        Change storyline triggers to check flags. BEFORE PC UPDATE.
        - Storyline < 0x2E --> Lucca has not rescued Crono
        """

        storyline_check = EC.if_storyline_counter_lt(0x2E)
        repl_check = EC.if_not_flag(memory.Flags.LUCCA_RESCUED_CRONO)

        for obj_id in (0, 7, 0x12, 0x13, 0x14, 0x15):
            start, end = script.get_function_bounds(obj_id, FID.STARTUP)
            pos = script.find_exact_command(storyline_check, start, end)
            script.replace_jump_cmd(pos, repl_check)

    @classmethod
    def modify_perp_walk(cls, script: locationevent.LocationEvent):
        """
        Only Crono has a handcuffed pose.  Everyone else will do something
        goofy without changing.
        """
        anim_cmd = EC.play_animation(0x43)
        pos = script.find_exact_command(
            anim_cmd,
            script.get_function_start(cls.crono_obj, FID.STARTUP)
        )

        script.insert_commands(
            EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1,
                               OP.EQUALS, 0, 1,
                               bytes_jump=len(anim_cmd)+1).to_bytearray(),
            pos
        )

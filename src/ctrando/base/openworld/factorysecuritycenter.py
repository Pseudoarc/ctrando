"""Openworld Factory Ruins Security Center"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


# Notes:
# - This is an attract mode scene.  If we want to preserve attract mode,
#   then take care to not disturb the functions it uses.
#   - Object 06 (Robo) Arb5 seems like the only one.
#   - With duplicate chars and boss rando DC may be a spoiler.  So it may
#     be time to give up on keeping attract mode.

class EventMod(locationevent.LocEventMod):
    """EventMod for Factory Ruins Security Center"""
    loc_id = ctenums.LocID.FACTORY_RUINS_SECURITY_CENTER
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Factory Ruins Security Center.
        - Turn storyline triggers into flag triggers
        - Remove Robo locks from computers.  He's required to enter, but then
          players are free to rearrange the party.
        - Re-script the R-Series fight.
        """
        cls.modify_r_series_battle_scenes(script)
        cls.modify_storyline_triggers(script)
        cls.modify_computer_activation(script)


    @classmethod
    def modify_r_series_battle_scenes(cls, script: Event):
        """
        Modify the cutscenes with the R-Series so that
        1) No storyline setting
        2) No Robo removal/trashing.
        3) Just into the battle, and warp back to Proto Dome? Overworld?
        """

        # The R-Series scene takes place in two parts
        # First, in Obj00 Startup there is a coordinate check gated by
        # Storyline == 0x3F.
        #  - Sets 0x7F0222 and 0x7F021C to 1
        #    - 0x7F0222 is used to trigger bouncing away from Robo when he is getting
        #      pummelled.
        #    - 0x7F021C == 0 is part of the check for this scene, so setting it to 1
        #      prevents re-triggering.
        # - Calls every R-series arb0 to get them out of the tubes
        # - Calls Marle, Lucca Arb2 just to position them
        # - Calls Robo Arb3 to trigger the main scene.

        # Robo's Arb3 does not do much until the very end where it
        # - Calls Obj00, Arb0 to make the R-Series do an animation
        # - Calls Obj0A and ObjOB Arb2 and Obj0C Arb5 to scoot right a bit.
        # - Calls Marle, Lucca Arb6 to move them to (4, 0x25)
        # - Calls Crono Arb4 to move him to (6, 0x23)
        # - Sets 0x7F0212 to 1 to let the battle trigger in the Obj00 loop

        # First get the part that actually has the battle
        # Put the post-battle commands in a separate function because this loop
        # is rather large, almost at the limit.
        post_battle_func = (
            EF().add(EC.set_flag(memory.Flags.R_SERIES_DEFEATED))
            .add(EC.reset_flag(memory.Flags.FACTORY_WALLS_CLOSED))
            .add(EC.change_location(ctenums.LocID.OW_FUTURE, 0x73, 0x24, 1,
                                    3, False))
            .add(EC.return_cmd())
        )
        script.set_function(1, FID.ARBITRARY_0, post_battle_func)

        pos = script.find_exact_command(
            EC.set_storyline_counter(0x42)
        )
        script.delete_commands(pos, 1)
        pos += 3  # Skipping song volume command
        ins_cmd = EC.call_obj_function(1, FID.ARBITRARY_0, 3, FS.CONT)
        script.insert_commands(ins_cmd.to_bytearray(), pos)
        pos += len(ins_cmd)
        script.delete_commands(pos ,2)  # Old calls to Marle, Lucca

        # Remove the remove Robo command.
        pos = script.find_exact_command(
            EC.generic_command(0xD6, 3),  # Remove Robo from active party
        )
        script.delete_commands(pos, 1)

        ins_block = (
            EF().add(EC.call_obj_function(0, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.pause(2))
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_2, 3, FS.CONT))
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_2, 3, FS.CONT))
            .add(EC.call_obj_function(0xC, FID.ARBITRARY_5, 3, FS.CONT))
            .add(EC.move_party(6 | 0x80, 0x23 | 0x80,
                               4 | 0x80, 0x21 | 0x80,
                               4 | 0x80, 0x25 | 0x80))
            .add(EC.play_song(0x29))
            .add(EC.generic_command(0xEB, 0, 0xFF))  # vol
            .add(EC.pause(0.5))
            .add(EC.assign_val_to_mem(1, 0x7F0212, 1))
        )

        pos = script.find_exact_command(
            EC.call_obj_function(4, FID.ARBITRARY_2, 5, FS.CONT), pos
        )
        script.insert_commands(ins_block.get_bytearray(), pos)
        pos += len(ins_block)
        script.delete_commands(pos, 3)

    @classmethod
    def modify_computer_activation(cls, script: Event):
        """
        Remove the robo requirement on using the computer.
        """
        comp_obj_id = 0x11

        # Copied from Robo's Arb2.
        # In particular the copytiles are copy/pasted as generic here
        comp_activate_func = (
            EF().add(EC.play_sound(0x70))
            # Copy Tiles
            .add(EC.generic_command(0xE5, 0x37, 0x36, 0x38, 0x39, 0x13, 0x2D, 0x41))
            .add(EC.pause(1))
            .add(EC.play_sound(0x53))
            # Copy Tiles
            .add(EC.generic_command(0xE5, 0x37, 0x36, 0x38, 0x39, 0x13, 0x2D, 0x3B))
            .add(EC.pause(0.5))
            # Copy Tiles
            .add(EC.generic_command(0xE4, 0x35, 0x36, 0x35, 0x39, 0x16, 0x3B, 0x3B))
            .add(EC.pause(1))
            .add(EC.play_sound(0xA0))
            .add(EC.set_flag(memory.Flags.FACTORY_DEFENSE_LASERS_OFF))
        )

        pos = script.find_exact_command(
            EC.generic_command(0xAD, 0x20),
            script.get_function_start(comp_obj_id, FID.ACTIVATE)
        )
        script.data[pos+1] = 0x10

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.ROBO), pos
        )
        script.delete_jump_block(pos)
        script.insert_commands(
            comp_activate_func.get_bytearray(), pos
        )

        pos, _ = script.find_command([0xD8], pos)
        pos += 3

        # Set music after activation
        music_block = (
            EF().add_if(
                EC.if_not_flag(memory.Flags.R_SERIES_DEFEATED),
                EF().add_if(
                    EC.if_flag(memory.Flags.FACTORY_POWER_ACTIVATED),
                    EF().add(EC.play_song(0x16))  # Shot of Crisis
                    .jump_to_label(EC.jump_forward(), 'end')
                )
            ).add(EC.play_song(0xA))  # Factory normal
            .set_label('end')
        )

        script.insert_commands(
            music_block.get_bytearray(), pos
        )
        pos += len(music_block)
        script.delete_jump_block(pos)  # Delete original conditional song

    @classmethod
    def modify_storyline_triggers(cls, script: Event):
        """
        Replace storyline checks with flag checks.
        - Storyline == 0x3F means Proto power on AND not defeated R-Series.
        - Storyline != 0x3F means Proto power off OR defeated R-Series
        - Storyline > 0x40 means R-series has been defeated
        """

        def replace_storyline_eq_3F(script: Event, pos: int):
            """
            Replace Storyline == 0x3F with power activated and R-Series not defeated
            """
            script.replace_jump_cmd(
                pos, EC.if_flag(memory.Flags.FACTORY_POWER_ACTIVATED)
            )
            script.wrap_jump_cmd(
                pos, EC.if_not_flag(memory.Flags.R_SERIES_DEFEATED))

        # First instance is in Obj00 startup to control the R-series fight
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0x3F)
        )
        replace_storyline_eq_3F(script, pos)

        # Next instance is Obj00 activate to keep the sirens playing while escaping
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0x3F), pos
        )
        replace_storyline_eq_3F(script, pos)

        # Now to prevent the elevator from working during the escape
        pos = script.get_function_start(0x10, FID.ACTIVATE)
        replace_storyline_eq_3F(script, pos)

        # There is a more Storyline != 0x3F in the computer activate to
        # control how the music should be after battle, but it's handled separately.

        # Other storyline commands are in the R-Series objects
        r_series_obj_ids = range(0xA, 0xA+6)
        for obj_id in r_series_obj_ids:
            start, end = script.get_function_bounds(obj_id, FID.STARTUP)
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0000, OP.GREATER_THAN, 0x40), start, end
            )
            script.replace_jump_cmd(
                pos, EC.if_flag(memory.Flags.R_SERIES_DEFEATED))

            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0000, OP.LESS_THAN, 0x3F), pos, end
            )
            script.replace_jump_cmd(
                pos, EC.if_not_flag(memory.Flags.FACTORY_POWER_ACTIVATED)
            )


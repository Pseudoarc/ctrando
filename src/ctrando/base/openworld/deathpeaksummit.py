"""Openworld Death Peak Summit"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    Facing,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# Notes on C.Trigger scene.  Originates from coord check in Obj00, Startup
# - Calls Obj01, Arb0
#   - Some fairly complicated logic to choose who takes part in the scene.
#   - Choose whose Arb0 ("All who fear the night...") to call.
#     - The order is Marle > Lucca > Frog > Robo.
#     - Stores the pcid in 0x7F0216 and 0x7F0067
#   - Choose whose "Pendant's reacting" arb to call.
#     - Note that the pendant is drawn near this PC.
#     - The order is normal: Lucca > Robo > Frog > Ayla
#     - Lucca, Robo, and Frog use Arb3, Ayla uses Arb0
#     - Puts this pcid in 0x7F0218 and 0x7F0068
#   - Plays the animation of the trigger flying up and shattering.
#   - Returns to Obj00, Startup
# - Back in Obj00, Startup
#   - Use 0x7F0216 to determine whose Arb1 to call ("It shattered!")
#     Remember this is the same person who is holding the egg from before.
#   - Whoever is holding the pendant (0x7F0218) says it was crazy to think it
#     would work.
#   - Whoever was holding the egg screams into the void.
#   - Then the sun goes dark

# To replace this scene, we'll make it so that only the lead PC acts.
# 1) Party moves into position
# 2) Lead PC pulls out the egg, which floats into the sky and shatters.
#    - All PCs need the right arb for this.
# 3) The sun goes dark.


class EventMod(locationevent.LocEventMod):
    """EventMod for Death Peak Summit"""
    loc_id = ctenums.LocID.DEATH_PEAK_SUMMIT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Death Peak Summit for an Open World.
        - Always have the lead PC do the animation.
        - Skip the time freeze and go back to the "good" summit.
        """
        cls.modify_pc_arbs(script)
        cls.modify_time_egg_scene(script)

    @classmethod
    def modify_time_egg_scene(cls, script: Event):
        """
        Reduce the cutscene to just have the lead PC release the egg.
        """
        pos = script.get_function_start(1, FID.ARBITRARY_0)
        del_end = script.find_exact_command(
            EC.call_obj_function(0xE, FID.ARBITRARY_0, 3, FS.CONT)
        )
        script.delete_commands_range(pos, del_end)

        script.insert_commands(
            EC.call_pc_function(0, FID.ARBITRARY_0, 3, FS.HALT)
            .to_bytearray(),
            pos
        )

        pos = script.find_exact_command(
            EC.get_result(0x7F0216),
            script.get_object_start(0)
        )
        del_end = script.find_exact_command(
            EC.generic_command(0xEB, 0x60, 0), pos
        )
        script.delete_commands_range(pos, del_end)
        script.insert_commands(
            EC.call_pc_function(0, FID.ARBITRARY_1, 3, FS.HALT)
            .to_bytearray(),
            pos
        )

        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.OCEAN_PALACE_TIME_FREEZE_ACTIVE)
        )
        ins_block = (
            EF().add(EC.set_flag(memory.Flags.CRONO_REVIVED))
            .add(EC.change_location(
                ctenums.LocID.OW_FUTURE, 0x54, 0x46,
                Facing.DOWN, False)
            )
        )
        script.insert_commands(ins_block.get_bytearray(), pos)
        pos += len(ins_block)
        script.delete_commands(pos, 3)

        # Minor sparkle repositioning because they aren't emanating from another PC
        pos = script.get_function_start(0xE, FID.STARTUP)
        pos = script.find_exact_command(EC.set_move_speed(0x40), pos)
        script.data[pos+1] = 0x18

        script.insert_commands(EC.generic_command(0x8E, 0x3B).to_bytearray(), pos)

        pos = script.get_function_start(0xE, FID.ARBITRARY_0)
        repl_cmd = EC.set_object_coordinates_pixels(0x78, 0xD2)
        script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give everyone a time egg holding animation
        TODO: These are barebones.  Add PC-specific static animations.
        """

        for pc_id in (ctenums.CharID.CRONO, ctenums.CharID.AYLA,
                      ctenums.CharID.MAGUS):
            new_arb0 = (
                EF().add(EC.set_move_speed(0x40))
                .add(EC.move_sprite(7, 0xD))
                .add(EC.pause(1))
                .add(EC.set_own_facing('down')).add(EC.pause(1))
                .add(EC.loop_animation(0x21, 4))
                .add(EC.pause(1))
                .add(EC.set_object_drawing_status(0xF, True))
                .add(EC.play_animation(0x23))
                .add(EC.call_obj_function(0xF, FID.ARBITRARY_0, 3, FS.CONT))
                .add(EC.return_cmd())
            )
            script.set_function(pc_id+2, FID.ARBITRARY_0, new_arb0)

            new_arb1 = (
                EF().add(EC.reset_animation())
                .add(EC.move_sprite(6, 0xB))
                .add(EC.pause(5))
                .add(EC.play_sound(0xA))
                .add(EC.return_cmd())
            )
            script.set_function(pc_id+2, FID.ARBITRARY_1, new_arb1)

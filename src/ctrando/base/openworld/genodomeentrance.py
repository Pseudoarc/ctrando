"""Openworld Geno Dome Entrance"""

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

class EventMod(locationevent.LocEventMod):
    """EventMod for Geno Dome Entrance"""
    loc_id = ctenums.LocID.GENO_DOME_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Geno Dome Entrance for an Open World.
        - Add a message to the computer indicating Robo must be recruited.
        - Remove the cutscene the plays when the computer is activated.
        - Present the player with an option to skip the conveyor belt if desired.
        """

        # Set the flag that Mother Brain's dialogue has been seen already
        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add(EC.assign_val_to_mem(0x1F, 0x7F014E, 1))
            .add(EC.set_flag(memory.Flags.GENO_DOME_ENTRANCE_SCENE_VIEWED))
            .get_bytearray(),
            pos
        )

        for _ in range(2):
            pos = script.find_exact_command(
                EC.reset_bit(memory.Memory.CHARLOCK, 0x10), pos
            )
            script.delete_commands(pos, 1)

        new_computer_func = (
            EF().add(EC.set_explore_mode(False))
            .add_if_else(
                EC.if_pc_recruited(ctenums.CharID.ROBO),
                # If Robo is recruited, Give the option to skip conveyor.
                EF().add(EC.decision_box(
                    script.add_py_string(
                        "Skip conveyor battles?{line break}"
                        "   Yes.{line break}"
                        "   No.{null}"
                    ), 1, 2
                ))
                .add_if_else(
                    EC.if_result_equals(2),
                    # Open the door as usual.
                    EF().add(EC.call_obj_function(9, FID.ARBITRARY_0, 1, FS.HALT))
                    .add(EC.call_obj_function(9, FID.ARBITRARY_1, 1, FS.HALT)),
                    # Copy the end conveyor location switch.
                    EF().add(EC.darken(4)).add(EC.fade_screen())
                    .add(get_command(bytes.fromhex("E1FA08183E")))  # change loc
                ),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string(
                        "{Robo} must be recruited to enter.{null}"
                    )
                )).add(EC.call_obj_function(9, FID.ARBITRARY_1, 1, FS.HALT))
            ).add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )
        script.set_function(8, FID.ACTIVATE, new_computer_func)


"""Openworld Laruba Ruins"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Laruba Ruins"""
    loc_id = ctenums.LocID.LARUBA_RUINS

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Laruba Ruins Event.
        - Give Ayla a normal startup
        - Add dreamstone turn-in to the chief.
        - Remove storyline lock on the name change/rock Nu
        - Remove scene of the girl saying Kino is taken
        """

        # Ayla normal startup, delete the storyline check
        pos = script.get_function_start(6, FID.STARTUP)
        script.delete_jump_block(pos)

        # Remove condition to hide Nu and the Zzz
        for obj_id in (0xD, 0xE):
            pos = script.get_function_start(obj_id, FID.STARTUP)
            script.delete_jump_block(pos)

        cls.remove_intro_scenes(script)
        cls.modify_chief(script)

    @classmethod
    def remove_intro_scenes(cls, script: Event):
        """
        Change the scenes that can play when first entering Laruba
        - Remove the girl who says Kino has been taken
        - Remove the scene of Ayla arguing with the chief.  This one will be put back
          by the recruit code possibly as a way to scout the recruit.
        """

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x8E))
        script.delete_jump_block(pos)

    @classmethod
    def modify_chief(cls, script: Event):
        """
        Add a dreamstone check to the chief.  Remove storyline checks/setting.
        """
        chief_obj = 0x8
        pos = script.get_object_start(chief_obj)
        script.delete_commands(pos, 1)  # Remove if storyline < 0xAB

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x8E))
        script.delete_commands(pos, 1)  # This changes his init facing

        new_activate = (
            EF().add(EC.set_own_facing_pc(0))
            .add_if_else(
                EC.if_flag(memory.Flags.HAS_DACYTL_PERMISSION),
                # If has permission, give a text reminder.
                EF().add(EC.auto_text_box(
                    script.add_py_string("OLD MAN: Use Dactyl!  Beat Reptites!{null}")
                )),
                # Else check for dreamstone
                EF().add_if_else(
                    EC.if_has_item(ctenums.ItemID.DREAMSTONE),
                    # If has dreamstone, give text and set flag.
                    EF().add(EC.set_explore_mode(False))
                    .add(EC.auto_text_box(
                        script.add_py_string(
                            "OLD MAN: ...OK.{line break}"
                            "Will call for Dactyl.  Friend may still{line break}"
                            "be at summit.  Careful, {pc1}!{null}"
                        )
                    ))
                    .add(EC.assign_val_to_mem(0x80, memory.Memory.DACTYL_STATUS, 1))
                    .add(EC.assign_val_to_mem(0x0218, memory.Memory.DACTYL_X_COORD_LO, 2))
                    .add(EC.assign_val_to_mem(0x0128, memory.Memory.DACTYL_Y_COORD_LO, 2))
                    .add(EC.set_flag(memory.Flags.HAS_DACYTL_PERMISSION))
                    .add(EC.set_explore_mode(True)),
                    # Else, tell the player to bring dreamstone
                    EF()
                    .add(EC.auto_text_box(
                        script.add_py_string(
                            "OLD MAN: Bring Dreamstone if want{line break}"
                            "dactyl!{null}"
                        )
                    ))
                )
            ).add(EC.return_cmd())
        )

        script.set_function(chief_obj, FID.ACTIVATE, new_activate)
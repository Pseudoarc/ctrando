"""Openworld Arris Dome Food Storage"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Dome Food Storage"""
    loc_id = ctenums.LocID.ARRIS_DOME_FOOD_LOCKER
    pc_id_start = 0x7F0214

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Food Storage Event.
        - Remove intro scene.
        - Put the Seed on the dead guy instead of in the intro scene.
        """

        # Remove the scene
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.OBTAINED_ARRIS_FOOD_ITEM)
        )
        end = script.get_function_end(0, FID.STARTUP)
        script.delete_commands_range(pos, end)

        # Add it to dead guy
        dead_guy_obj = 8
        pos = script.get_function_start(dead_guy_obj, FID.ACTIVATE)
        pos = script.find_exact_command(EC.return_cmd(), pos)

        script.insert_commands(
            EF().add_if(
                EC.if_not_flag(memory.Flags.OBTAINED_ARRIS_FOOD_ITEM),
                EF().add(EC.assign_val_to_mem(ctenums.ItemID.SEED, 0x7F0200, 1))
                .add(EC.add_item(ctenums.ItemID.SEED))
                .add(EC.auto_text_box(
                    script.add_py_string(
                        "{line break}Got 1 {item}!{line break}{itemdesc}{null}"
                    )))
                .add(EC.set_flag(memory.Flags.OBTAINED_ARRIS_FOOD_ITEM))
            ).get_bytearray(), pos
        )
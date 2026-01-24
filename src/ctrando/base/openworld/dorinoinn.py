"""Openworld Dorino Inn"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF


class EventMod(locationevent.LocEventMod):
    """EventMod for Dorino Inn"""
    loc_id = ctenums.LocID.DORINO_INN

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Choras Inn (600) for an Open World.
        - Exploremode after partyfollows
        - Modify the Marle PowerMeal check
        """

        dummy_item_obj_id = script.append_empty_object()
        script.dummy_object_out(dummy_item_obj_id)
        got_item_str_id = owu.add_default_treasure_string(script)

        add_item_func = (
            EF()
            .add_if(
                EC.if_pc_recruited(ctenums.CharID.MARLE),
                EF()
                .add_if_else(
                    EC.if_not_flag(memory.Flags.OBTAINED_DORINO_INN_POWERMEAL),
                    # Give the unique item
                    EF()
                    .add(EC.assign_val_to_mem(ctenums.ItemID.POWER_MEAL, 0x7F0200, 1))
                    .add(EC.add_item_memory(0x7F0200))
                    .add(EC.auto_text_box(got_item_str_id))
                    .add(EC.set_flag(memory.Flags.OBTAINED_DORINO_INN_POWERMEAL)),
                    # Give the generic powermeal
                    EF()
                    .add_if(
                        EC.if_pc_active(ctenums.CharID.MARLE),
                        EF()
                        .add_if_else(
                            EC.if_has_item(ctenums.ItemID.POWER_MEAL),
                            EF(),
                            EF()
                            .add(EC.assign_val_to_mem(ctenums.ItemID.POWER_MEAL, 0x7F0200, 1))
                            .add(EC.add_item_memory(0x7F0200))
                            .add(EC.auto_text_box(got_item_str_id))
                        )
                    )
                )
            )
            .add(EC.return_cmd())
        )
        script.set_function(dummy_item_obj_id, FID.ARBITRARY_0, add_item_func)

        darken_pos = script.find_exact_command(
            EC.darken(0x02),
            script.get_function_start(0x17, FID.ARBITRARY_0)
        )
        item_pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE), darken_pos
        )
        script.delete_jump_block(item_pos)
        script.insert_commands(
            EC.call_obj_function(dummy_item_obj_id, FID.ARBITRARY_0, 4, FS.HALT)
            .to_bytearray(), darken_pos
        )

        owu.add_exploremode_to_partyfollows(script)


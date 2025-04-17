"""Update Millennial Fair for an open world."""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP


class EventMod(locationevent.LocEventMod):
    """EventMod for Millennial Fair"""
    loc_id = ctenums.LocID.MILLENNIAL_FAIR
    melchior_obj = 0x0E
    armor_shop_obj = 0x10
    item_shop_obj = 0x18

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Modify Millennial Fair Event

        - Fix Melchior: No pendant selling.  No Flag Setting.  No leaving.
        - Remove Lucca's device set up notifications.
        """
        cls.update_melchior(script)
        cls.fix_shops(script)
        cls.remove_lucca_device(script)
        cls.remove_trial_flashback(script)

    @classmethod
    def update_melchior(cls, script: locationevent.LocationEvent):
        """
        Make the following changes to fair Melchior:
        - No Flags updates when selling pendant because the whole selling
          dialogue is gone.
        - Make Melchior stay at the fair all game.  The lady next to him too.
        """

        start = script.get_function_start(cls.melchior_obj, FID.STARTUP)
        end = script.get_function_start(cls.melchior_obj+1, FID.STARTUP)

        # Remove the part that makes Melchior leave after storyline 0x51
        leave_cmd = EC.if_mem_op_value(
            memory.Memory.STORYLINE_COUNTER, OP.GREATER_OR_EQUAL, 0x51, 1, 0
        )
        pos = script.find_exact_command(leave_cmd, start, end)
        script.delete_jump_block(pos)

        # Keep the lady beside him too
        pos_lady = script.find_exact_command(
            leave_cmd,
            script.get_function_start(0x15, FID.STARTUP)
        )
        script.delete_jump_block(pos_lady)

        # Change Melchior to immediate shop + parting text
        store_cmd = EC.if_result_equals(0, 0)
        pos = script.find_exact_command(store_cmd, pos, end)

        store_block = script.get_jump_block(pos)
        store_block.delete_at_index(-1)  # Remove trailing jump

        script.set_function(cls.melchior_obj, FID.ACTIVATE, store_block)

    @classmethod
    def fix_shops(cls, script: locationevent.LocationEvent):
        """
        Make the shops stick around regardless of storyline counter.
        """

        leave_cmd = EC.if_mem_op_value(
            memory.Memory.STORYLINE_COUNTER, OP.GREATER_OR_EQUAL, 0x27, 1, 0
        )

        for obj_id in (cls.item_shop_obj, cls.armor_shop_obj):
            start, end = script.get_function_bounds(obj_id, FID.STARTUP)
            pos = script.find_exact_command(leave_cmd, start, end)
            script.delete_jump_block(pos)

    @classmethod
    def remove_lucca_device(cls, script: locationevent.LocationEvent):
        """Remove notifications that Lucca's device is set up."""
        npc_objs = (cls.armor_shop_obj, 0x11, cls.item_shop_obj)
        notify_cmd = EC.if_mem_op_value(
            memory.Memory.STORYLINE_COUNTER, OP.LESS_THAN, 0xC, 1, 0
        )

        for obj_id in npc_objs:
            start, end = script.get_function_bounds(obj_id, FID.ACTIVATE)
            pos = script.find_exact_command(notify_cmd, start, end)
            script.delete_jump_block(pos)

        # wrapped in an if marle active
        odd_obj = 0x16
        notify_cmd = EC.check_active_pc(ctenums.CharID.MARLE, 0)
        start, end = script.get_function_bounds(odd_obj, FID.ACTIVATE)
        pos = script.find_exact_command(notify_cmd, start, end)
        script.delete_jump_block(pos)

    @classmethod
    def remove_trial_flashback(cls, script: locationevent.LocationEvent):
        """Remove flash back of Crono selling the pendant"""
        flashback_cmd = EC.if_mem_op_value(
            0x7F0059,  # memory.Memory.CRONO_TRIAL_COUNTER
            OP.EQUALS, 6, 1, 0)

        pos = script.find_exact_command(
            flashback_cmd,
            script.get_function_start(1, FID.STARTUP)
        )
        script.delete_jump_block(pos)

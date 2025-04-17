"""Openworld West Cape"""

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
    """EventMod for West Cape"""
    loc_id = ctenums.LocID.WEST_CAPE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify West Cape for an Open World.
        - Check for Toma's Pop instead of the Toma item flag.
        - Modify exploremode for the speed tab.
        - Add a cutscene skip for showing Giant's Claw.
        """

        tombstone_obj_id = 8
        pos = script.get_function_start(tombstone_obj_id, FID.ACTIVATE)
        script.delete_commands(pos, 1)  # ExploreMode Off

        pos = script.find_exact_command(EC.auto_text_box(1), pos)
        script.insert_commands(EC.set_explore_mode(False).to_bytearray(), pos)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.OBTAINED_TOMA_ITEM), pos
        )
        script.replace_jump_cmd(
            pos, EC.if_has_item(ctenums.ItemID.TOMAS_POP)
        )

        # Notably, there's a check for whether you've already done Claw which
        # also ignores the pop pour.  Remove for entrance rando.
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.RECOVERED_RAINBOW_SHELL),
            pos
        )
        script.delete_jump_block(pos)


        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.HAS_POURED_TOMAS_POP)
        )

        cls.add_cutscene_skip(script)

        owu.update_add_item(
            script, script.get_function_start(8, FID.ACTIVATE)
        )

    @classmethod
    def add_cutscene_skip(cls, script: Event):
        """
        Add a choice to skip the scene where the Giant's Claw is shown.
        """
        toma_obj = 9

        flag_cmd = EC.set_flag(memory.Flags.TOMA_SHOWING_GIANTS_CLAW)
        block_st = script.find_exact_command(
            flag_cmd, script.get_function_start(toma_obj, FID.ACTIVATE))
        block_end = script.find_exact_command(EC.return_cmd(), block_st)
        
        warp_func = EF.from_bytearray(script.data[block_st:block_end])
        script.delete_commands_range(block_st, block_end)  # Leave the return

        string_id = script.add_py_string(
            "TOMA: You know where that is, right?{line break}"
            "   Yes{line break}"
            "   No{null}"
        )

        warp_choice_func = (
            EF()
            .add(EC.decision_box(string_id, 1, 2))
            .add_if(EC.if_result_equals(2, 1), warp_func)
        )
        script.insert_commands(warp_choice_func.get_bytearray(), block_st)

        # Now the function will return if we say we know where the claw is.
        # Go back to the caller, Obj8, Activate and call Toma's exit.
        st = script.get_function_start(8, 1)
        end = script.get_function_end(8, 1)
        orig_call_cmd = EC.call_obj_function(9, FID.TOUCH, 6, FS.HALT)
        extra_call_cmd = EC.call_obj_function(9, FID.ACTIVATE, 6, FS.HALT)
        
        # Inserting at the end of a block is always weird.  Do the insert first
        # so that the if bounds don't shorten.
        pos = script.find_exact_command(orig_call_cmd, st, end)
        new_calls = EF().add(orig_call_cmd).add(extra_call_cmd)
        script.insert_commands(new_calls.get_bytearray(), pos)
        
        pos += len(new_calls)
        script.delete_commands(pos, 1)
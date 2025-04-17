"""Openworld Arris Auxiliary Console"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Auxiliary Console"""
    loc_id = ctenums.LocID.ARRIS_DOME_AUXILIARY_CONSOLE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Auxiliary Console Event.
        - Fix the password required text to not have Lucca's name.
        - Insert an ExploreMode On command after inputting the password.
        """

        script.strings[0] = ctstrings.CTString.from_str(
            "Password Required.{null}"
        )

        # Each computer terminal has two partyfollows which need to be followed
        # with setting exploremode on.
        ins_block = EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
        for obj_id in (8, 9):
            pos = script.get_function_start(obj_id, FID.ACTIVATE)
            for _ in range(2):
                pos = script.find_exact_command(EC.party_follow(), pos)

                script.insert_commands(ins_block.get_bytearray(), pos)
                pos += len(ins_block)
                script.delete_commands(pos, 1)

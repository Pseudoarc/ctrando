"""Openworld Arris Lower Commons"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Dome Lower Commons"""
    loc_id = ctenums.LocID.ARRIS_DOME_LOWER_COMMONS
    temp_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Auxiliary Console Event.
        - Insert an ExploreMode On command after inputting the password.
        - Change the charged pendant storyline trigger to the correct check
        """

        # The computer terminal has two partyfollows which need to be followed
        # with setting exploremode on.
        ins_block = EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
        pos = script.get_function_start(8, FID.ACTIVATE)
        for _ in range(2):
            pos = script.find_exact_command(EC.party_follow(), pos)

            script.insert_commands(ins_block.get_bytearray(), pos)
            pos += len(ins_block)
            script.delete_commands(pos, 1)

        # Change the Pendant trigger
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xAB),
            script.get_function_start(9, FID.ACTIVATE)
        )
        owu.modify_if_not_charge(script, pos, cls.temp_addr)
        # script.replace_jump_cmd(
        #     pos, EC.if_not_flag(memory.Flags.PENDANT_CHARGED)
        # )
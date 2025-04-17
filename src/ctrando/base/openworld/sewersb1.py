"""Openworld Sewers B1"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Sewers B1"""
    loc_id = ctenums.LocID.SEWERS_B1
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Sewers B1 Event.
        - Pre-set flags to avoid frog and scouter scenes.
        - For now, remove the forced nereid fight at the start.
        - Shorten the Krawlie scene
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.VIEWED_FIRST_BOSS_UNDERLING_SCENE))
            .add(EC.set_flag(memory.Flags.VIEWED_SEWERS_INTRO_SCENE))
            .add(EC.set_flag(memory.Flags.VIEWED_SEWERS_B2_SCENE))
            .add(EC.set_flag(memory.Flags.VIEWED_SECOND_BOSS_UNDERLING_SCENE))
            .add(EC.set_flag(memory.Flags.FOUGHT_SEWERS_B1_ENTRANCE_NEREID_BATTLE))
            .get_bytearray(), pos
        )

        pos, cmd = script.find_command(
            [0xD8],
            script.get_function_start(0x22, FID.ACTIVATE)
        )
        script.data[pos + 2] |= 0x80
        pos += len(cmd)

        script.insert_commands(
            EF()
            .add(EC.party_follow())
            .add(EC.set_explore_mode(True)).get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.set_explore_mode(False),
            script.get_function_start(0x23, FID.ACTIVATE)
        )
        pos += 2

        script.delete_commands(pos, 4)

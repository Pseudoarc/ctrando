"""Openworld Ocean Palace Regal Antechamber"""

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
    """EventMod for Ocean Palace Regal Antechamber"""
    loc_id = ctenums.LocID.OCEAN_PALACE_REGAL_ANTECHAMBER

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Western Regal Antechamber Event.
        - Remove text from Dalton.  Unlike Jets let's keep him here for now.  We'll
          have to see whether boss rando will conflict.
        - Replace storyline checking and setting with flags.
        - Possibly give Dalton spoiler text for the Golem Boss spot.
        """

        cls.modify_battle_scenes(script)
        cls.modify_storyline_triggers(script)

    @classmethod
    def modify_battle_scenes(cls, script: Event):
        """
        Remove dialog from Dalton.  Set a flag instead of storyline.
        """

        pos, _ = script.find_command(
            [0xC2], script.get_object_start(0xC))
        # script.delete_commands(pos, 1)
        # TODO: game is fine with deleting, but TF hangs.  Why?
        script.data[pos:pos+2] = EC.generic_command(0xAD, 4).to_bytearray()

        pos = script.get_function_start(0xE, FID.ARBITRARY_0)
        for _ in range(6):
            pos, __ = script.find_command([0xC2, 0xBB], pos)
            script.data[pos:pos+2] = EC.generic_command(0xAD, 0x4).to_bytearray()

        pos = script.find_exact_command(EC.set_storyline_counter(0xC9), pos)
        script.replace_command_at_pos(
            pos, EC.set_flag(memory.Flags.OCEAN_PALACE_TWIN_BOSS_DEFEATED))

    @classmethod
    def modify_storyline_triggers(cls, script: Event):
        """
        Change checking of the storyline counter to use a flag.  The setting was
        handled by modify_battle_scenes.
        """

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xC9))
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.OCEAN_PALACE_TWIN_BOSS_DEFEATED))

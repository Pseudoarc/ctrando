"""Openworld Guardia Queen's Chamber 600"""
from typing import Optional

from ctrando.base import openworldutils as utils
from ctrando.common import ctenums, memory
from ctrando.common.memory import Flags
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Queen's Chamber 600"""
    loc_id = ctenums.LocID.QUEENS_ROOM_600

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Guardia Throneroom 600 Event.
        - Set some initial flags for guard/attendant position
        - Make the PC startups be normal.
        - Change storyline to flags.
        """

        # Remove commands that make the screen green when Marle disappears.
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.MARLE_DISAPPEARED),
            script.get_function_start(0, FID.ACTIVATE)
        )
        script.delete_jump_block(pos)

        cls.set_initial_flags(script)
        cls.modify_pc_objects(script)
        cls.remove_unused_objects(script)
        cls.replace_storyline_triggers(script)

        # Remove an object used by the recruitment
        return_obj = 0x14
        pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(return_obj)) + 1
        script.insert_commands(
            EF().add(EC.remove_object(return_obj))
            .add(EC.remove_object(return_obj+1))
            .add(EC.remove_object(return_obj+2))
            .get_bytearray(), pos
        )



    @classmethod
    def modify_pc_objects(cls, script: Event):
        """
        Remove special startup from Marle.
        """

        normal_startup = (
            EF().add(EC.load_pc_in_party(ctenums.CharID.MARLE))
            .add(EC.return_cmd())
            .add(EC.set_controllable_infinite())
        )

        script.set_function(2, FID.STARTUP, normal_startup)

    @classmethod
    def set_initial_flags(cls, script: Event):
        """
        Set flags so that the NPCs go in the right spot.
        """

        pos = script.get_object_start(0)
        block = (
            EF().add(EC.set_flag(Flags.MARLE_DISMISS_ATTENDANTS))
            .add(EC.set_flag(Flags.QUEEN_600_GUARD_MOVED))
        )
        script.insert_commands(block.get_bytearray(), pos)

    @classmethod
    def remove_unused_objects(cls, script: Event):
        """
        Remove objects related to Nadia vanishing.
        """

        for obj_id in range(0x17, 0x13, -1):
            script.remove_object(obj_id)

    @classmethod
    def replace_storyline_triggers(cls, script: Event):
        """
        Replace storyline checks with flag checks.
        """

        # 0x10 <-> Marle Disappears -- Should always be true
        # 0x1C <-> Has defeated Manoria boss
        # 0x21 <-> Marle Has Reappeared (recruit gained)
        # 0x54 <-> ??? (Vanilla, after heckran cave)
        #  - Some NPCs vanish after this storyline point.  Can just ignore.

        flag_dict: dict[int, Optional[memory.Flags]] = {
            0x10: None,
            0x1C: memory.Flags.MANORIA_BOSS_DEFEATED,
            0x21: memory.Flags.CASTLE_RECRUIT_OBTAINED,
            0x54: None
        }

        utils.storyline_to_flag(script, flag_dict)

    @classmethod
    def remove_dialogue(cls, script: Event):
        """
        Remove extra dialogue from the return cutscene.  AFTER REMOVAL
        """

        # After object removal, the return object is 0x14

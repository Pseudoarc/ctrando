"""Openworld Lair Ruins Portal"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Lair Ruins Portal"""
    loc_id = ctenums.LocID.LAIR_RUINS_PORTAL
    temp_addr = 0x7F0220
    can_eot_addr = 0x7F0222

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Lair Ruins Portal Event.
        - Remove the cutscenes.
        - Add an exploremode on.
        """

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0xA8)
        )
        script.delete_jump_block(pos)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.VIEWING_KEEPERS_FLASHBACK), pos
        )
        script.delete_jump_block(pos)

        end = script.find_exact_command(EC.end_cmd())
        script.delete_commands_range(pos, end)

        script.insert_commands(
            EC.set_explore_mode(True).to_bytearray(), pos
        )

        cls.modify_portal_activation(script)

    @classmethod
    def modify_portal_activation(cls, script: Event):
        """
        Add the standard EoT check to the portal activation.
        Award Dark Ages time gauge access.
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            owu.get_can_eot_func(cls.temp_addr, cls.can_eot_addr).get_bytearray(),
            pos
        )

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_VIEWED_DARKAGES_PORTAL_FIRST_SCENE), pos
        )
        script.replace_jump_cmd(
            pos, EC.if_mem_op_value(cls.can_eot_addr, OP.EQUALS, 1)
        )

        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.HAS_LAIR_RUINS_PORTAL))
            .add(EC.set_flag(memory.Flags.HAS_DARK_AGES_PORTAL))
            .add(EC.set_flag(memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS))
            .get_bytearray(),
            pos
        )
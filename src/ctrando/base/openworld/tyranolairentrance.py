"""Openworld Tyrano Lair Entrance"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Tyrano Lair Entrance"""
    loc_id = ctenums.LocID.TYRANO_LAIR_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tyrano Lair Entrance Event.  We're pretending like Kino has already
        been rescued and the door is open.
        - Set the left skull to be always open
        """

        # pos = script.get_object_start(0)
        # script.insert_commands(
        #     EC.set_flag(memory.Flags.TYRANO_LAIR_ENTRANCE_SKULL_OPEN).to_bytearray(),
        #     pos
        # )
        skull_obj = script.append_empty_object()

        _, copy_cmd = script.find_command([0xE4], script.get_function_start(0, FID.ACTIVATE))
        copy_cmd.command = 0xE5

        script.set_function(
            skull_obj, FID.STARTUP,
            EF()
            .add_if(
                EC.if_not_flag(memory.Flags.TYRANO_LAIR_ENTRANCE_SKULL_OPEN),
                EF()
                .add(EC.load_npc(ctenums.NpcID.GIANT_BLUE_STAR))
                .add(EC.set_object_coordinates_tile(0x32, 0x2E))
            )
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )
        script.set_function(
            skull_obj, FID.ACTIVATE,
            EF()
            .add_if(
                EC.if_flag(memory.Flags.TYRANO_LAIR_ENTRANCE_SKULL_OPEN),
                EF().add(EC.return_cmd())
            )
            .add_if(
                EC.if_pc_recruited(ctenums.CharID.AYLA),
                EF()
                .add(EC.set_explore_mode(False))
                .add(EC.play_sound(0xCD))
                .add(copy_cmd)
                .add(EC.set_flag(memory.Flags.TYRANO_LAIR_ENTRANCE_SKULL_OPEN))
                .add(EC.remove_object(skull_obj))
                .add(EC.set_explore_mode(True))
                .add(EC.return_cmd())
            )
            .add(EC.auto_text_box(
                script.add_py_string("Only {ayla} can open the skull. {null}")
            ))
            .add(EC.return_cmd())
        )
        script.set_function(
            skull_obj, FID.TOUCH, EF().add(EC.return_cmd())
        )

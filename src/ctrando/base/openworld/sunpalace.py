"""Openworld Sun Palace"""

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
    """EventMod for Sun Palace"""
    loc_id = ctenums.LocID.SUN_PALACE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sun Palace for an Open World.
        - Replace a potentially buggy check for SoS defeated.
        - Remove some dialog and pause when the KI is picked up.
        """

        # The check of 0x7F0138 > 0 will fail in rando because other flags, such
        # as Sun Stone checks may get set prior to the Sun Palace.
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F013A, OP.GREATER_THAN, 0)
        )
        script.replace_jump_cmd(
            pos, EC.if_flag(memory.Flags.SUN_PALACE_BOSS_DEFEATED)
        )

        # Replace the item pickup script
        pos = script.get_function_start(0x11, FID.ACTIVATE)
        pos = script.find_exact_command(EC.if_pc_active(ctenums.CharID.LUCCA), pos)
        end = script.find_exact_command(EC.set_explore_mode(True), pos)

        script.delete_commands_range(pos, end)
        owu.insert_add_item_block(
            script, pos, ctenums.ItemID.MOON_STONE,
            memory.Flags.SUN_PALACE_ITEM_OBTAINED
        )

        script.insert_commands(
            EF().add(EC.set_own_drawing_status(False))
            .add(EC.play_song(0x3D)).get_bytearray(), pos
        )

        pos = script.find_exact_command(EC.set_explore_mode(True), pos) + 2
        script.insert_commands(EC.generic_command(0xEE).to_bytearray(), pos)






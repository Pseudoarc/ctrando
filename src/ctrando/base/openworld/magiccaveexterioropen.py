"""Openworld Magic Cave Exterior (After Opening)"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Magic Cave Exterior"""
    loc_id = ctenums.LocID.MAGIC_CAVE_EXTERIOR_OPEN

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Magic Cave Exterior Event.
        - Trigger Masamune cutscene with Frog + Masa
        - Shorten the cutscene by removing dialogue and flashbacks.
        """

        temp_addr = 0x7F0300
        has_masa_addr = 0x7F0210
        has_masa_func = owu.get_has_equipment_func(
            ctenums.ItemID.MASAMUNE_1, has_masa_addr, temp_addr
        )

        flag_block = (
            EF()

            .add_if(
                EC.if_not_flag(memory.Flags.OW_MAGIC_CAVE_OPEN),
                EF()
                .add_if(
                    EC.if_pc_recruited(ctenums.CharID.FROG),
                    has_masa_func
                    .add_if(
                        EC.if_mem_op_value(has_masa_addr, OP.EQUALS, 1),
                        EF().add(EC.set_flag(memory.Flags.OW_MAGIC_CAVE_OPEN))
                    )
                )
            )
        )

        pos = script.get_object_start(0)
        script.insert_commands(flag_block.get_bytearray(), pos)

        pos  = script.find_exact_command(EC.end_cmd(), pos)
        script.insert_commands(
            EF().add_if(
                EC.if_not_flag(memory.Flags.OW_MAGIC_CAVE_OPEN),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string(
                        "Bring {frog} and the Masamune to{line break}"
                        "open the mountain.{null}"
                    )
                ))
            ).get_bytearray(), pos
        )

        copy_tiles = script.get_function(0, FID.ACTIVATE)
        copy_tiles = (
            EF().add_if_else(
                EC.if_flag(memory.Flags.OW_MAGIC_CAVE_OPEN),
                copy_tiles,
                EF().add(
                    EC.copy_tiles(0x0, 0xA, 0xF, 0xC,
                                  0, 0, True, True)
                )
            )
        )

        script.set_function(0, FID.ACTIVATE, copy_tiles)

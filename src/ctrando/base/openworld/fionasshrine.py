"""Openworld Fiona's Shrine"""

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
    """EventMod for Fiona's Shrine"""
    loc_id = ctenums.LocID.FIONAS_SHRINE
    temp_epoch_status = 0x7F0220
    temp_pc1_addr = 0x7F0222

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Fiona's Shrine for an Open World.
        - Put a Lucca lock on reactivating Robo.
        - Remove dialog when reactivating Robo.
        - Modify the party manipulation before the forest scene
        - Hide Robo before Robo has agreed to help Fiona (only matters for entrance rando)
        """

        # Wrecked Robo is object 08
        pos = script.get_function_start(8, FID.STARTUP)
        script.insert_commands(
            EF()
            .add_if(
                EC.if_not_flag(memory.Flags.ROBO_HELPS_FIONA),
                EF()
                .add(EC.set_own_drawing_status(False))
            ).get_bytearray(),
            pos
        )

        pos = script.get_function_start(8, FID.ACTIVATE)
        script.insert_commands(
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1,
                                      cls.temp_pc1_addr, 1))
            .add_if(
                EC.if_mem_op_value(cls.temp_pc1_addr, OP.NOT_EQUALS,
                                   ctenums.CharID.LUCCA),
                EF().add(EC.auto_text_box(
                    script.add_py_string(
                        "{Lucca} must fix Robo!{null}"
                    )
                )).add(EC.return_cmd())
            ).get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.add_pc_to_reserve(ctenums.CharID.ROBO), pos
        )
        script.delete_commands(pos, 1)

        pos = script.get_function_start(8, FID.ARBITRARY_1)
        for _ in range(7):
            pos, cmd = script.find_command([0xBC, 0xBA, 0xBD], pos)
            if cmd.command == 0xBC:
                script.data[pos] = 0xBA  # 1 -> 0.5
            elif cmd.command == 0xBA:
                script.data[pos] = 0xB9  # 0.5 -> 0.25
            else:
                cmd.command = 0xBC  # 2 --> 1

            pos += 1

        script.delete_commands(pos, 1)  # remove text

        pos = script.find_exact_command(
            EC.if_pc_recruited(ctenums.CharID.CRONO), pos
        )
        end, _ = script.find_command([0xE1], pos)
        script.delete_commands_range(pos, end)
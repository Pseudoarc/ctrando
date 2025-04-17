"""Openworld Apocalypse Lavos"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    Operation as OP,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Apocalypse Lavos"""

    loc_id = ctenums.LocID.APOLCALYPSE_LAVOS
    pc1_addr = 0x7F0214
    pc2_addr = 0x7F0216
    pc3_addr = 0x7F0218
    choose_fight_addr = 0x7F0232
    temp_pc_addr = 0x7F0234


    @classmethod
    def modify(cls, script: Event):
        """
        Modify Apocalypse Lavos for an Open World.
        - Skip the Lavos emerging cutscene.
        - Remove dialog except for the choice to fight or not.
        - Allow the scene to proceed with a single character.
        """

        owu.add_exploremode_to_partyfollows(script)

        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_SEEN_LAVOS_APOCALYPSE_SCENE).to_bytearray(),
            pos,
        )

        # The prompt to fight or not is Obj09, Arb2
        pos = script.get_function_start(9, FID.ARBITRARY_2)
        end = script.find_exact_command(
            EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, 6), pos)

        script.delete_commands_range(pos, end)
        script.insert_commands(
            EF()
            .add(EC.assign_mem_to_mem(cls.pc1_addr, cls.temp_pc_addr, 1))
            .add_if(
                EC.if_mem_op_value(cls.temp_pc_addr, OP.EQUALS, 0),
                EF()
                .add(EC.decision_box(
                    script.add_py_string(
                        "What does {crono} choose? {line break}"
                        "  Fight! {line break}"
                        "  Run Away.{null}"
                    ), 1, 2
                ))
                .add_if(
                    EC.if_result_equals(1),
                    EF().add(EC.assign_val_to_mem(1, cls.choose_fight_addr, 1))
                )
            ).get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, 6), pos
        )
        script.replace_jump_cmd(
            pos, EC.if_mem_op_value(cls.temp_pc_addr, OP.EQUALS, 6)
        )
"""Openworld Flying Epoch"""
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
    """EventMod for Flying Epoch"""

    loc_id = ctenums.LocID.FLYING_EPOCH
    choose_fight_addr = 0x7F0216

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Flying Epoch for an Open World.
        - Skip the Lavos emerging cutscene.
        - Remove dialog except for the choice to fight or not.
        - Allow the scene to proceed with solo Crono
        """

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999),
            script.get_function_start(0xA, FID.ARBITRARY_1)
        )
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999).to_bytearray(),
            pos
        )

        pos = script.find_exact_command(EC.set_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999),
                                        script.get_function_start(0x11, FID.ARBITRARY_3))

        crono_choice_ef = (
            EF()
            .add_if(
                EC.if_mem_op_value(0x7F0212, OP.GREATER_OR_EQUAL, 0x80),
                EF().add(EC.decision_box(
                    script.add_py_string(
                        "What does {pc1} choose? {line break}"
                        "   Fight! {line break}"
                        "   Run Away.{null}"
                    ), 1, 2)
                ).add_if(
                    EC.if_result_equals(1),
                    EF().add(EC.assign_val_to_mem(1, cls.choose_fight_addr, 1))
                )
            )
        )
        script.insert_commands(crono_choice_ef.get_bytearray(), pos)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.OBTAINED_EPOCH_FLIGHT), pos
        )
        script.delete_jump_block(pos)
        script.insert_commands(EC.set_flag(memory.Flags.LAVOS_SHELL_DEFEATED).to_bytearray(), pos)

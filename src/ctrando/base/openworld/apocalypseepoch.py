"""Openworld Apocalypse Epoch"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Apocalypse Epoch"""

    loc_id = ctenums.LocID.APOCALYPSE_EPOCH
    choose_fight_addr = 0x7F0216

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Apocalypse Epoch for an Open World.
        - Skip the Lavos emerging cutscene.
        - Remove dialog except for the choice to fight or not.
        - Fix the issue with solo Crono on this map.
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999).to_bytearray(),
            pos
        )

        pos = script.find_exact_command(EC.set_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999),
                                        script.get_function_start(0x9, FID.ARBITRARY_2))

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

        pos = script.find_exact_command(EC.assign_val_to_mem(0x02, memory.Memory.LAVOS_STATUS, 1), pos)
        repl_block = (
            EF()
            .add_if(
                EC.if_flag(memory.Flags.LAVOS_SHELL_DEFEATED),
                EF()
                .add(EC.reset_bit(0x7F00AA, 0x04))
                .add(EC.change_location(ctenums.LocID.LAVOS_TUNNEL, 0x07, 0x3a, 0, 0, False))
                .add(EC.return_cmd())
            )
            .add(EC.assign_val_to_mem(4, memory.Memory.LAVOS_STATUS, 1))
            # .add(EC.assign_val_to_mem(8, memory.Memory.FLYING_EPOCH_CUTSCENE_COUNTER, 1))
            .add(EC.set_bit(0x7F00AA, 0x04))
            .add(EC.reset_bit(0x7F00AA, 0x08))
        )
        script.delete_commands(pos, 1)
        script.insert_commands(repl_block.get_bytearray(), pos)


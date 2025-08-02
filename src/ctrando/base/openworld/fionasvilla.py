"""Openworld Fiona's Villa"""

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
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Fiona's Villa"""
    loc_id = ctenums.LocID.FIONAS_VILLA
    temp_epoch_status = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Fiona's Villa for an Open World.
        - Remove some dialog (and the decision box) when turning in the quest.
        - Don't actually remove Robo from the party.
        - Only move the Epoch if flight is obtained.
        """
        cls.modify_quest_turnin(script)

    @classmethod
    def modify_quest_turnin(cls, script: Event):
        """
        Don't remove Robo from the party.  Only move the Epoch if flight is available.
        """

        # Turn-in is in Obj08 (Fiona), Activate
        pos = script.get_function_start(8, FID.ACTIVATE)
        pos, cmd = script.find_command([0xC0], pos)

        str_ind = cmd.args[0]
        script.strings[str_ind] = ctstrings.CTString.from_str(
            "{Robo}: You can come for me when{line break}"
            "the job is done.{null}"
        )
        script.replace_command_at_pos(pos, EC.auto_text_box(str_ind))

        pos += 2  # Should skip to the check result command after.
        script.delete_commands(pos, 1)

        # Remove all of the party manipulation the game does.
        pos = script.find_exact_command(
            EC.remove_pc_from_party(ctenums.CharID.ROBO), pos
        )
        end = script.find_exact_command(EC.darken(2), pos)
        script.delete_commands_range(pos, end)

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xD2), pos
        )

        upgrade_bit = memory.Flags.EPOCH_CAN_FLY.value.bit
        upgrade_bit = 0xFF ^ upgrade_bit
        # This if being True will cause the Epoch move to be skipped
        script.replace_jump_cmd(
            pos, EC.if_mem_op_value(cls.temp_epoch_status, OP.EQUALS, 0)
        )
        script.insert_commands(
            EF().add(EC.assign_mem_to_mem(memory.Memory.EPOCH_STATUS,
                                          cls.temp_epoch_status, 1))
            .add(EC.set_reset_bits(cls.temp_epoch_status, upgrade_bit, False))
            .get_bytearray(), pos
        )


"""Openworld Special Purpose Area"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Special Purpose Area"""
    loc_id = ctenums.LocID.SPECIAL_PURPOSE_AREA

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Special Purpose Area Event.
        - Remove the character lock
        - Change the string to 1st PC.
        """

        # for ind, string in enumerate(script.strings):
        #     py_str = ctstrings.CTString.ct_bytes_to_ascii(string)
        #     print(f"{ind:02X}: {py_str}")

        wakeup_str = script.strings[1]
        script.strings[1] = wakeup_str.replace(b'\x13', b'\x1B')

        pos = script.find_exact_command(
            EC.set_bit(memory.Memory.CHARLOCK, 0x80))
        script.delete_commands(pos, 1)

        cls.modify_ocean_palace_scene(script)

    @classmethod
    def modify_ocean_palace_scene(cls, script: Event):
        """
        Change the check for storyline == 0xCC to a flag check.
        Remove the "Crono!!" dialog and just go to the Last Village
        """

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F020C, OP.EQUALS, 0xCC),
        )
        script.replace_jump_cmd(
            pos, EC.if_flag(memory.Flags.OCEAN_PALACE_DISASTER_SCENE))
        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE),
        )
        end, _ = script.find_command([0xDF], pos)
        script.data[end] = 0xE1  # Changing type of changeloc so screen refreshes.
        script.delete_commands_range(pos, end)

        script.insert_commands(
            EF().add(EC.reset_flag(memory.Flags.OCEAN_PALACE_DISASTER_SCENE))
            .add(EC.pause(1)).get_bytearray(), pos
        )

"""Openworld Prehistoric Canyon"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Prehistoric Canyon"""
    loc_id = ctenums.LocID.PREHISTORIC_CANYON
    pc1_addr = 0x7F0220
    pc2_addr = 0x7F0222
    pc3_addr = 0x7F0224

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Prehistoric Canyon Event.
        - Shorten many pauses and remove dialog.
        - Only load sparkles when there are PCs.
        - Set the Lavos has fallen flag instead of storyline.
        - Add Epoch move
        """

        cls.modify_sparkle_scene(script)
        cls.modify_sparkles(script)

    @classmethod
    def modify_sparkle_scene(cls, script: Event):
        """
        Remove pauses and dialog.  Speed up screen scrolling.  Epoch Move.
        """

        # Ayla and Kino appear in this scene as part of an ending.  We skip over
        # that stuff.
        pos = script.find_exact_command(EC.play_song(0))

        script.insert_commands(
            EC.set_flag(memory.Flags.OW_LAVOS_HAS_FALLEN).to_bytearray(), pos
        )

        # Remove some pauses
        pos = script.find_exact_command(EC.generic_command(0xAD, 0x20), pos)
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(EC.pause(8), pos)
        script.data[pos+1] = 0x30

        pos, _ = script.find_command([0xEB], pos)
        script.delete_commands(pos, 15)  # Scream, wind song, dialog

        # Make the scroll larger in magnitude, cut it off after 1.75 seconds.
        cmd = get_command(script.data, pos)
        cmd.args[0] = 0x0800
        script.data[pos:pos + len(cmd)] = cmd.to_bytearray()
        pos += len(cmd)
        script.data[pos+1] = 0x28

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.LUCCA), pos
        )
        script.delete_commands(pos, 8)  # all char text commands

        pos, _ = script.find_command([0xE0], pos)
        script.insert_commands(
            owu.get_epoch_set_block(
                ctenums.LocID.OW_PREHISTORIC, 0x350, 0x290
            ).get_bytearray(), pos
        )

    @classmethod
    def modify_sparkles(cls, script: Event):
        """
        Load Sparkles only if PCs are active.  Remove dialog from sparkles
        """

        pos = script.find_exact_command(EC.return_cmd())
        script.insert_commands(
            EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1, cls.pc1_addr, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2, cls.pc2_addr, 1))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, cls.pc3_addr, 1))
            .get_bytearray(), pos
        )

        # Obj01 is Ayla's (PC3) object in the main script
        pos = script.find_exact_command(
            EC.return_cmd(), script.get_object_start(1)
        )
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(cls.pc3_addr, OP.EQUALS, 0x80),
                EF().add(EC.remove_object(1))
            ).get_bytearray(), pos
        )

        # Remova Ayla dialog
        for _ in range(2):
            pos, _ = script.find_command([0xC1], pos)
            script.delete_commands(pos, 1)

        # We'll say obj02 is the PC2 object
        pos = script.find_exact_command(
            EC.return_cmd(), script.get_object_start(2)
        )
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, 0x80),
                EF().add(EC.remove_object(2))
            ).get_bytearray(), pos
        )
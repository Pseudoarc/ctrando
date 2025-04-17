"""Openworld Tyrano Lair Keep"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Tyrano Lair Keep"""
    loc_id = ctenums.LocID.TYRANO_LAIR_KEEP

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tyrano Lair Keep Event.
        - Shorten pre-battle cutscene a little bit.
        - Shorten post-battle cutscene significantly.
        """

        # The pre-battle scene takes place in Obj15, Arb0
        # This function also handles up until the lavos in space scene is played.
        # After the lavos in space scene, the control picks up with Obj15, Startup.

        pos = script.get_function_start(0x15, FID.ARBITRARY_0)
        pos, _ = script.find_command([0xC2], pos)
        script.delete_commands(pos, 2)  # text + pause

        pos, _ = script.find_command([0xC2], pos)
        script.delete_commands(pos, 1)  # text

        pos, _ = script.find_command([0xC2], pos)
        script.delete_commands(pos, 1)  # text

        # Now it's after the battle
        pos, _ = script.find_command([0xC2], pos)
        script.delete_commands(pos, 6)  # text + ayla-anims

        pos = script.find_exact_command(
            EC.call_obj_function(6, FID.ARBITRARY_1, 3, FS.HALT)
        )
        script.delete_commands(pos, 6)  # text + red flash

        pos = script.find_exact_command(EC.generic_command(0xAD, 0x10), pos)
        script.data[pos+1] = 0x08  # shorten a pause
        pos += 2
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(EC.generic_command(0xAD, 0x10), pos)
        script.data[pos + 1] = 0x08  # shorten a pause
        pos += 2
        script.delete_commands(pos, 7)

        pos, _ = script.find_command([0x56], pos)
        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

        new_block = (
            EF().add(EC.generic_command(0xF1, 0x3F, 0)).add(EC.pause(0.25))
            .add(EC.generic_command(0xF1, 0)).add(EC.pause(0.25))
            .add(EC.play_song(0xD))
            .add(get_command(bytes.fromhex('E600100100')))  # scroll layers start
            .add(EC.pause(0.5))
            .add(get_command(bytes.fromhex('E600000100')))  # scroll layers end
            .add(EC.move_party(0x8B, 0x90, 0x8B, 0x91, 0x8B, 0x92))
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_obj_function(0xC, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_obj_function(0xE, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_obj_function(0xD, FID.ARBITRARY_0, 3, FS.HALT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_0, 3, FS.HALT))
            .add(EC.move_party(0x08, 0x8B, 0x0A, 0x8A, 0x0C, 0x8C))
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_2, 5, FS.CONT))
            .add(EC.call_obj_function(0xC, FID.ARBITRARY_2, 5, FS.CONT))
            .add(EC.call_obj_function(0xD, FID.ARBITRARY_1, 5, FS.CONT))
            .add(EC.call_obj_function(0xE, FID.ARBITRARY_4, 5, FS.CONT))
            .add(EC.move_party(0x0F, 0x80, 0x0F, 0x80, 0x0F, 0x80))
            .add(EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1))
            .add(EC.set_flag(memory.Flags.OW_PREHISTORY_LAVOS_FALL))
            .add(EC.fade_screen())
            .add(get_command(bytes.fromhex("DFF3030000")))  # copied change loc
        )
        script.insert_commands(new_block.get_bytearray(), pos)

        cls.normalize_pc_functions(script)

    @classmethod
    def normalize_pc_functions(cls, script: Event):
        """
        Give every PC the same functions so that they can take part in the cutscenes.
        """

        # Arb0 - set the move destination for attaching to dactyls
        func = (
            EF().add(EC.set_move_destination(True, False))
            .add(EC.return_cmd())
        )

        for pc_id in ctenums.CharID:
            obj_id = pc_id + 1
            script.set_function(obj_id, FID.ARBITRARY_0, func)


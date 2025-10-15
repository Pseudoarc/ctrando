"""Openworld Black Omen Celestial Gate"""
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

# Notes:
# Scene control checks (in order)
# - If 0xD3 < storyline < 0xD4: The vanilla Omen rising cutscene
#   - Leave this alone because it will never trigger and we might want to reuse.
# - 0x7F00DA == 2: Part of the Omen getting devoured by Lavos
#   - 0x7F00DA set to 1 after Zeal's defeat (this map).  Then passes to
#     Last Village.
#   - OW scene shows the Omen disintegrating into the ocean and the counter is
#     set to 2.  Passes back to Celestial Gate
#   - In Celestial Gate, sets a flag and goes back to overworld for more cutscene
#   - Eventually this leads to fighting Lavos1
# - If 0x7F01A8 & 0x80 (Mammon M dead)
#   - Starts the battle sequence for Zeal2


class EventMod(locationevent.LocEventMod):
    """EventMod for Black Omen Celestial Gate"""

    loc_id = ctenums.LocID.BLACK_OMEN_CELESTIAL_GATE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen Celestial Gate for an Open World.
        - Restore Exploremode after battles (panel+boss).
        """
        cls.shorten_zeal_pre_battle_scene(script)
        cls.modify_zeal_post_battle_scene(script)

    @classmethod
    def shorten_zeal_pre_battle_scene(cls, script: Event):
        """
        Remove some dialogue prior to the battle.
        """
        zeal_obj = 0x9
        pos = script.get_function_start(zeal_obj, FID.ACTIVATE)
        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.call_obj_function(8, FID.ARBITRARY_8, 6, FS.HALT), pos
        )
        script.delete_commands(pos, 5)

        for _ in range(3):
            pos, __ = script.find_command([0xBB], pos)
            script.data[pos:pos+2] = EC.generic_command(0xAD, 0x04).to_bytearray()

    @classmethod
    def modify_zeal_post_battle_scene(cls, script: Event):
        """
        Skip the cutscene and go straight to the Lavos1 fight.
        Also skip the boss gauntlet.
        """
        zeal_obj = 0x9
        pos = script.find_exact_command(
            EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1),
            script.get_function_start(zeal_obj, FID.ACTIVATE)
        )
        del_end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, del_end)

        new_end = (
            EF()
            .add(EC.assign_val_to_mem(0xA, 0x7F00DE, 1))
            .add(EC.assign_val_to_mem(4, memory.Memory.LAVOS_STATUS, 1))
            .add(EC.change_location(ctenums.LocID.LAVOS, 7, 0xA))
        )
        #
        # new_end = (
        #     EF()
        #     .add(EC.assign_val_to_mem(6, 0x7F00DA,1))
        #     .add(EC.assign_val_to_mem(4 , memory.Memory.LAVOS_STATUS, 1))
        #     .add(EC.change_location(ctenums.LocID.LAVOS, 7, 0xA))
        # )
        script.insert_commands(new_end.get_bytearray(), pos)


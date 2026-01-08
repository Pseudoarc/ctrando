"""Openworld Northern Ruins Hero's Grave"""
import math

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

# Cyrus Cutscene Notes
# Obj08, Act (tombstone)
#   - Positions party.
#   - Calls --> Obj05, Arb2 (Frog) using cont, priority 6.
# Obj05, Arb2
#   - Frog walks up to the grave and lifts his sword.
#   - Calls --> Obj08, Arb0 (tombstone) with halt, priority 6 (Frog obj stuck here)
# Obj08, Arb0
#   - (Slowly) Makes the screen blue
#   - Calls out to Obj09, Touch (Cyrus) with 6, Cont
#   - Makes the stone glow
#   - (Slowly) Makes the screen more blue and returns (unsticks Frog)
# Obj09, Touch
#   - Moves Cyrus up (slowly)
#   - Calls Obj05, Arb3 (Frog) with 6, Cont
#   - Pulses the sprite to white and back until 0x7F021A is set and returns.
# Obj05, Arb3
#   - Dialogue and Cyrus fading away
#   - Calls to ObjA, ObjB, Touch control the fadeout
#   - Calls --> Obj0C, Activate (masa) with 6, Cont
# Obj0C, Act
#   - Calls Obj0D, Obj0E, Touch to get Masa and Mune to appear.
#   - Calls --> Obj05, Arb4
# Obj05, Arb4
#   - Just some anim/text
#   - Calls --> Obj0E, Activate --> Obj0D, Act --> Obj0C, Touch --> Obj05, Arb5
#   - There's some issue here where the previous Obj0D, Obj0E Touch functions need to be complete
#     before Obj0E, Act is called.
# Obj05, Arb5
#   - Much anim/text
#   - Also handles the item add/remove



class EventMod(locationevent.LocEventMod):
    """EventMod for Northern Ruins Hero's Grave"""
    loc_id = ctenums.LocID.NORTHERN_RUINS_HEROS_GRAVE
    has_masa_addr = 0x7F0220
    temp_addr = 0x7F0222

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Northern Ruins Hero's Grave for an Open World.
        - Add a Masamune lock on the tombstone.
        - Remove most dialogue and animation from the charge up scene.
        """
        cls.add_masamune_lock(script)
        cls.modify_cyrus_scene(script)
        cls.modify_item_pickup(script)

        owu.update_add_item(script, script.get_function_start(0xF, FID.ACTIVATE))


    @classmethod
    def modify_item_pickup(cls, script: Event):
        """
        Do not remove the Masamune.  Give an item_received textbox.
        Call this after the shortening which removes all text.
        """

        pos = script.find_exact_command(
            EC.assign_mem_to_mem(0x7E2769, 0x7F021C, 1),
            script.get_function_start(5, FID.ARBITRARY_5)
        )
        script.delete_commands(pos, 4)

        got_item_str_id = owu.add_default_treasure_string(script)
        item_func = owu.get_add_item_block_function(
            ctenums.ItemID.MASAMUNE_2, None, got_item_str_id
        )
        item_func.add(EC.set_flag(memory.Flags.NORTHERN_RUINS_BASEMENT_SENTRIES_CLEARED))
        script.insert_commands(item_func.get_bytearray(), pos)

    @classmethod
    def add_masamune_lock(cls, script: Event):
        """
        Require the Masamune to get the Cyrus cutscene.
        """
        has_masa_fn = owu.get_has_equipment_func(
            ctenums.ItemID.MASAMUNE_1, cls.has_masa_addr, cls.temp_addr
        )
        pos = script.get_object_start(0)
        script.insert_commands(has_masa_fn.get_bytearray(), pos)

        pos = script.get_function_start(8, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.FROG)
        )
        script.wrap_jump_cmd(
            pos, EC.if_mem_op_value(cls.has_masa_addr, OP.EQUALS, 1)
        )

    @classmethod
    def speed_up_masa_mune_powering(cls, script: Event):
        """
        Speed up Masa and Mune's part where they split from the sword and recombine.
        """
        for obj_id in (0xD, 0xE):
            pos = script.get_function_start(obj_id, FID.TOUCH)
            pos = script.find_exact_command(EC.set_move_speed(8), pos)
            script.data[pos+1] = 0x18
            pos, _ = script.find_command([0x9C], pos)
            script.data[pos+2] //= 3

            pos, _ = script.find_command([0x88], pos)
            script.data[pos+4] = 2

            pos = script.get_function_start(obj_id, FID.ACTIVATE)
            owu.remove_next_dialogue_command(script, pos)

    @classmethod
    def speed_up_masamune_spinning(cls, script: Event):
        """
        Speed up the part of the scene where the masamune rises up and spins.
        """
        pos = script.get_function_start(0xC, FID.ACTIVATE)
        pos = script.find_exact_command(EC.set_move_speed(8), pos)
        script.data[pos+1] = 0x10

        pos, _ = script.find_command([0x9C], pos)
        script.data[pos+2] //= 2  # may need to fudge this

        pos, _ = script.find_command([0x88], pos)
        script.data[pos + 4] //= 2

        pos = script.find_exact_command(EC.generic_command(0xAD, 0x30), pos)
        script.data[pos+1] = 18

        pos, cmd = script.find_command([0xBB], pos)
        script.data[pos : pos + len(cmd)] = EC.generic_command(0xAD, 1).to_bytearray()

        pos = script.find_exact_command(EC.generic_command(0xAD, 0x80), pos)
        script.data[pos + 1] = 0x20

        pos, cmd = script.find_command([0xBB], pos)
        script.data[pos : pos + len(cmd)] = EC.generic_command(0xAD, 1).to_bytearray()

        pos, _ = script.find_command([0x9C], pos)
        script.data[pos + 2] //= 2  # may need to fudge this

    @classmethod
    def speed_up_cyrus_appearing(cls, script: Event):
        """
        Speed up the time it takes for the screen to turn blue and cyrus to float up.
        """
        pos = script.get_function_start(8, FID.ARBITRARY_0)

        scale_factor = 3
        # Weird MemCpy88 command
        pos, _ = script.find_command([0x88], pos)
        script.data[pos+4] //= scale_factor

        # Color Addition command
        pos, cmd = script.find_command([0x2E], pos)
        script.data[pos+5] //= scale_factor

        pos += len(cmd)  # To a pause
        script.data[pos+1] //= scale_factor

        # Weird MemCpy88 command
        pos, _ = script.find_command([0x88], pos)
        script.data[pos + 4] //= scale_factor

        # Color Addition command
        pos, _ = script.find_command([0x2E], pos)
        script.data[pos + 5] //= scale_factor

        # Now increase Cyrus's float speed
        pos = script.find_exact_command(
            EC.set_move_speed(0xA),
            script.get_function_start(9, FID.TOUCH)
        )
        script.data[pos+1] *= scale_factor

        pos, _ = script.find_command([0x9C], pos)  # Vec move

        script.data[pos+2] //= (scale_factor)
        script.data[pos+2] -= 0xB  # manually computed fudge factor

    @classmethod
    def modify_cyrus_scene(cls, script: Event):
        """
        Remove dialogue and some non-essential bits of the Cyrus ghost scene.
        Do not remove Masa1 from inventory.
        """

        # pos = script.find_exact_command(
        #     EC.load_npc(0x96), script.get_function_start(0xA, FID.STARTUP)
        # )
        # # script.data[pos+1] = 0xB1
        # pos += 2
        # script.delete_commands(pos, 1)
        #
        # pos = script.find_exact_command(
        #     EC.load_npc(0x96), script.get_function_start(0xB, FID.STARTUP)
        # )
        # # script.data[pos + 1] = 0xB1
        # pos += 2
        # script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.set_move_speed(6),
            script.get_function_start(0xA, FID.ACTIVATE)
        )
        scale_factor = 8 / 3
        script.data[pos+1] = int(script.data[pos+1]*scale_factor) - 2
        pos, cmd = script.find_command([0x92], pos)
        pos += 2
        mag = script.data[pos]
        mag = math.floor(mag/scale_factor)
        script.data[pos] = mag
        def shorten_scene(
                script: Event, start: int, end: int,
                is_pc_obj: bool = True):
            pos = start

            pause_repl_dict: dict[int, int] = {
                0xBD: 0xBA,
                0xBC: 0xB9
            }

            while pos < end:
                cmd = get_command(script.data, pos)
                if cmd.command in (0xBB, 0xC1, 0xC2):
                    pause_duration = 8 if is_pc_obj else 2
                    script.data[pos: pos+len(cmd)] = \
                        EC.generic_command(0xAD, pause_duration).to_bytearray()
                elif cmd.command == 0xAD:
                    pause_duration = script.data[pos+1]
                    # print(f'{pause_duration:02X}', end=" --> ")
                    if pause_duration >= 0x10:
                        pause_duration = 0x10*round(math.log2(pause_duration/0x10))
                    # print(f'{pause_duration:02X}', end = ': ')
                    script.data[pos+1] = pause_duration
                    cmd = get_command(script.data, pos)
                    # print(cmd)
                elif cmd.command in pause_repl_dict:
                    repl_cmd_id = pause_repl_dict[cmd.command]
                    script.data[pos] = repl_cmd_id
                elif cmd.command == 0xEB:
                    script.data[pos+1] //= 2
                pos += len(cmd)


        pos = script.get_function_start(5, FID.ARBITRARY_2)
        end = script.get_object_start(6)
        shorten_scene(script, pos, end, True)

        pos = script.get_object_start(0xC)
        end = script.get_object_start(0xF)
        #shorten_scene(script, pos, end, False)

        pos = script.find_exact_command(
            EC.return_cmd(), script.get_function_start(0, FID.ARBITRARY_0)
        )
        script.insert_commands(
            EC.set_explore_mode(True).to_bytearray(), pos
        )

        cls.speed_up_cyrus_appearing(script)
        cls.speed_up_masamune_spinning(script)
        cls.speed_up_masa_mune_powering(script)
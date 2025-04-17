"""Openworld Blackbird Cell"""
import typing

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    Facing,
    get_command,
    get_offset
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Blackbird Cell"""
    loc_id = ctenums.LocID.BLACKBIRD_CELL
    pc1_addr = 0x7F020E
    pc2_addr = 0x7F0210
    pc3_addr = 0x7F0212
    temp_addr = 0x7F0240
    pc1_helm_addr = 0x7F0218
    pc1_armor_addr = 0x7F0219
    pc1_weapon_addr = 0x7F021A
    pc1_accessory_addr = 0x7F021B
    pc2_helm_addr = 0x7F021C
    pc2_armor_addr = 0x7F021D
    pc2_weapon_addr = 0x7F021E
    pc2_accessory_addr = 0x7F021F
    pc3_helm_addr = 0x7F0220
    pc3_armor_addr = 0x7F0221
    pc3_weapon_addr = 0x7F0222
    pc3_accessory_addr = 0x7F0223
    duct_check_addr = 0x7F0228
    gold_lo = 0x7F0224  # and next byte
    gold_hi = 0x7F0226

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Blackbird Cell for an Open World.
        - Update the equipment removal if Crono and Magus are in the party.
        - Update the equipment removal to use the new flag scheme.
        - Modify pretending to be sick so that the first character acts sick.
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.BLACKBIRD_NOTICED_DUCTS).to_bytearray(), pos
        )

        owu.add_exploremode_to_partyfollows(script)
        cls.add_duct_sparkle(script)
        cls.modify_equipment_removal(script)
        cls.modify_sick_scene(script)
        cls.modify_duct_calls(script)

        # Do this last to not mess up the object indices
        cls.normalize_pc_objects(script)

    @classmethod
    def add_duct_sparkle(cls, script: Event):
        """
        Add a sparkle by the duct activation so that the player knows they can
        interact with it.
        """
        duct_obj = 0xB
        pos = script.get_object_start(duct_obj)
        script.insert_commands(
            EF().add(EC.load_npc(0x70))
            .add(EC.play_animation(2))
            .add(EC.generic_command(0x84, 0))  # solidity
            .get_bytearray(), pos
        )

    @classmethod
    def modify_equipment_removal(cls, script: Event):
        """
        Add entries for Crono and Magus in the equipment removal
        """

        # Put the imprisoned PC ids in the right memory.
        write_prison_pc_block = (
            EF()
            .add(EC.assign_mem_to_mem(
                cls.pc1_addr, memory.Memory.BLACKBIRD_IMPRISONED_PC1, 1))
            .add(EC.assign_mem_to_mem(
                cls.pc2_addr, memory.Memory.BLACKBIRD_IMPRISONED_PC2, 1))
            .add(EC.assign_mem_to_mem(
                cls.pc3_addr, memory.Memory.BLACKBIRD_IMPRISONED_PC3, 1))
        )

        # Put the stolen gear in the right memory.
        gear_remove_block = EF()
        for pc_id in ctenums.CharID:
            helm_addr = 0x7E2627 + 0x50*pc_id
            weapon_addr = helm_addr + 2

            # Note, moving two bytes copies two pieces of gear.
            gear_remove_block.add_if(
                EC.if_mem_op_value(cls.pc1_addr, OP.EQUALS, pc_id),
                EF()
                .add(EC.assign_mem_to_mem(helm_addr, cls.pc1_helm_addr, 2))
                .add(EC.assign_mem_to_mem(weapon_addr, cls.pc1_weapon_addr, 2))
            ).add_if(
                EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, pc_id),
                EF()
                .add(EC.assign_mem_to_mem(helm_addr, cls.pc2_helm_addr, 2))
                .add(EC.assign_mem_to_mem(weapon_addr, cls.pc2_weapon_addr, 2))
            ).add_if(
                EC.if_mem_op_value(cls.pc3_addr, OP.EQUALS, pc_id),
                EF()
                .add(EC.assign_mem_to_mem(helm_addr, cls.pc3_helm_addr, 2))
                .add(EC.assign_mem_to_mem(weapon_addr, cls.pc3_weapon_addr, 2))
            )

        (
            gear_remove_block
            .add(EC.assign_mem_to_mem(
                cls.pc1_helm_addr, memory.Memory.BLACKBIRD_PC1_STOLEN_HELM, 2))
            .add(EC.assign_mem_to_mem(
                cls.pc1_weapon_addr, memory.Memory.BLACKBIRD_PC1_STOLEN_WEAPON, 2))
            .add(EC.assign_mem_to_mem(
                cls.pc2_helm_addr, memory.Memory.BLACKBIRD_PC2_STOLEN_HELM, 2))
            .add(EC.assign_mem_to_mem(
                cls.pc2_weapon_addr, memory.Memory.BLACKBIRD_PC2_STOLEN_WEAPON, 2))
            .add(EC.assign_mem_to_mem(
                cls.pc3_helm_addr, memory.Memory.BLACKBIRD_PC3_STOLEN_HELM, 2))
            .add(EC.assign_mem_to_mem(
                cls.pc3_weapon_addr, memory.Memory.BLACKBIRD_PC3_STOLEN_WEAPON, 2))
        )

        # Lock the PCs that are in jail.  Also set their equip-lock bit (not Ayla)
        char_lock_fn = EF()
        for pc_id in ctenums.CharID:
            pc_block = (
                EF()
                .add(EC.set_bit(memory.Memory.CHARLOCK, 0x80 >> pc_id))
                .add(EC.equip_item_to_pc(pc_id, ctenums.ItemID.NONE))
            )
            if pc_id == ctenums.CharID.AYLA:
                pc_block.add(EC.set_flag(memory.Flags.CAN_FIGHT_ON_BLACKBIRD))

            char_lock_fn.add_if(
                EC.if_pc_active(pc_id), pc_block
            )

        gold_removal_block = (
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.GOLD_LO, cls.gold_lo, 2))
            .add(EC.assign_mem_to_mem(memory.Memory.GOLD_HI, cls.gold_hi, 1))
            .add(EC.assign_mem_to_mem(cls.gold_lo, memory.Memory.BLACKBIRD_STOLEN_GOLD_LO, 2))
            .add(EC.assign_mem_to_mem(cls.gold_hi, memory.Memory.BLACKBIRD_STOLEN_GOLD_HI, 1))
            .add(EC.assign_val_to_mem(0, memory.Memory.GOLD_LO, 2))
            .add(EC.assign_val_to_mem(0, memory.Memory.GOLD_HI, 1))
        )
        
        # The charlock bits exactly match the gear locked bits except for Ayla
        # Note that DC only has to change the bit resetting for multiple Aylas.
        (
            char_lock_fn.add(EC.assign_mem_to_mem(memory.Memory.CHARLOCK, cls.temp_addr, 1))
            .add(EC.reset_bit(cls.temp_addr, 0x80 >> ctenums.CharID.AYLA))
            .add(EC.assign_mem_to_mem(cls.temp_addr, memory.Memory.BLACKBIRD_GEAR_STATUS, 1))
        )

        new_gear_removal_func = (
            EF()
            .append(write_prison_pc_block)
            .append(gear_remove_block)
            .append(char_lock_fn)
            .append(gold_removal_block)
            .add(EC.set_flag(memory.Flags.BLACKBIRD_GEAR_TAKEN))
            .add(EC.set_flag(memory.Flags.BLACKBIRD_ITEMS_TAKEN))
            .add(EC.set_flag(memory.Flags.BLACKBIRD_SEEN_EXTERIOR))
        )

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE)
        )
        end = script.find_exact_command(EC.set_storyline_counter(0xCF), pos) + 2
        script.delete_commands_range(pos, end)

        script.insert_commands(
            new_gear_removal_func.get_bytearray(), pos
        )

    @classmethod
    def normalize_pc_objects(cls, script: Event):
        """
        Allow every PC to be in the location.
        - Add objects for Crono and Magus to the scene.
        - Give everyone an ArbB for the sick scene, and put everyone's ArbC as the
          duct function.
        - Make everyone's duct function use the same temporary address
        - Change the duct functions.
        """
        generic_arbB = (
            EF().add(EC.set_own_facing('down'))
            .add(EC.loop_animation(0x21, 1))
            .add(EC.static_animation(0x60))
            .add(EC.pause(1))
            .add(EC.reset_animation())
            .add(EC.return_cmd())
        )
        marle_arbB = script.get_function(1, FID.ARBITRARY_B)

        script.set_function(1, FID.ARBITRARY_B, generic_arbB)
        script.set_function(1, FID.ARBITRARY_C, marle_arbB)

        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 6)
        owu.insert_pc_object(script, ctenums.CharID.CRONO, 1, 1)

        # Fix Crono Static Anim
        pos = script.get_function_start(1, FID.ARBITRARY_C)
        for _ in range(2):
            pos = script.find_exact_command(EC.static_animation(0x5D), pos)
            script.data[pos+1] = 107

        # Fix Magus Static Anim
        pos = script.get_function_start(7, FID.ARBITRARY_C)
        for _ in range(2):
            pos = script.find_exact_command(EC.static_animation(0x5D), pos)
            script.data[pos+1] = 90

        # There are some checks for something == 1 in Marle's object.
        # We need to replace them with 0 and 6 for Crono and Magus.
        for obj_id in (1, 7):
            pc_id = ctenums.CharID(obj_id-1)
            pos = script.find_exact_command(EC.play_animation(8),
                                            script.get_object_start(obj_id))
            for _ in range(3):
                pos, cmd = script.find_command([0x12], pos)
                script.data[pos+2] = pc_id
                pos += len(cmd)

            pos = script.get_function_start(obj_id, FID.ARBITRARY_2)
            for _ in range(2):
                pos, cmd = script.find_command([0x12], pos)
                script.data[pos+2] = pc_id
                pos += len(cmd)

        # Have everyone's ArbC (duct function) use the same up/down check.
        # Only need to alter Lucca, Robo, Frog, Ayla because Crono and Magus have
        # copied Marle who used 0x7F0220.

        for obj_id in range(3, 7):
            pos = script.get_function_start(obj_id, FID.ARBITRARY_C)
            for _ in range(2):
                pos, cmd = script.find_command([0x12], pos)
                script.data[pos+1] = get_offset(cls.duct_check_addr)
                pos += len(cmd)

    @classmethod
    def modify_duct_calls(cls, script: Event):
        """
        Change the duct function to use the functions as modified by
        normalize_pc_objects (all ArbC, all 0x7F0220 check for up/down).
        """

        # Duct calls are in Obj0B, Startup (coming down) and activate (going up)
        new_down_block = (
            EF().add(EC.assign_val_to_mem(1, cls.duct_check_addr, 1))
            .add_if_else(
                EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, 0x80),
                EF()
                .add(EC.call_pc_function(0, FID.ARBITRARY_C, 4, FS.HALT)),
                EF()
                .add_if_else(
                    EC.if_mem_op_value(cls.pc3_addr, OP.EQUALS, 0x80),
                    EF()
                    .add(EC.call_pc_function(0, FID.ARBITRARY_C, 4, FS.SYNC))
                    .add(EC.generic_command(0xAD, 5))
                    .add(EC.call_pc_function(1, FID.ARBITRARY_C, 4, FS.HALT)),
                    EF()
                    .add(EC.call_pc_function(0, FID.ARBITRARY_C, 4, FS.SYNC))
                    .add(EC.generic_command(0xAD, 5))
                    .add(EC.call_pc_function(1, FID.ARBITRARY_C, 4, FS.CONT))
                    .add(EC.generic_command(0xAD, 5))
                    .add(EC.call_pc_function(2, FID.ARBITRARY_C, 4, FS.HALT))
                )
            )
        )

        new_up_block = (
            EF().add(EC.assign_val_to_mem(0, cls.duct_check_addr, 1))
            .add(EC.call_pc_function(0, FID.ARBITRARY_C, 4, FS.HALT))
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.pc1_addr, OP.EQUALS, 1),
            script.get_function_start(0xB, FID.STARTUP)
        )
        end = script.find_exact_command(
            EC.reset_flag(memory.Flags.BLACKBIRD_COMING_DOWN_DUCT), pos
        )
        script.delete_commands_range(pos, end)
        script.insert_commands(new_down_block.get_bytearray(), pos)

        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.pc1_addr, OP.EQUALS, 1),
            script.get_function_start(0xB, FID.ACTIVATE),
        )
        end, _ = script.find_command([0xE0], pos)
        script.delete_commands_range(pos, end)
        script.insert_commands(new_up_block.get_bytearray(), pos)

    @classmethod
    def modify_sick_scene(cls, script: Event):
        """
        Give a generic function for the first PC to play sick and call it when
        the party doesn't support one of the existing functions.
        """

        # OK this one is annoying.
        # Usually it's the third PC who does the sick scene.  However, Marle never
        # pretends to be sick.  If Marle is PC3, then the duty passes to PC2.

        # We are going to switch it up so that PC1 always does the scene because
        # that's the only PC that we know we'll have.  The dialog also involves both
        # the lead PC and the PC who acts sick, so instead we're just going to have
        # a generic prompt.

        generic_sick_func = (
            EF().add(EC.move_party(0x18, 0x87,
                                   0x96, 0x89,
                                   0x9A, 0x09))
            .add(EC.call_pc_function(0, FID.ARBITRARY_7, 4, FS.HALT))
            .add(EC.play_sound(0x66))
            .add(EC.generic_command(0xAD, 3))
            .add(EC.play_sound(0x53))
            .add(EC.text_box(0x31, False))
            .add(EC.call_obj_function(7, FID.ARBITRARY_0, 4, FS.HALT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_8, 4, FS.HALT))
            .add(get_command(bytes.fromhex("F16F00")))  # Color
            .add(EC.play_sound(0x8B))
            .add(get_command(bytes.fromhex("F1E000")))  # Color
            .add(get_command(bytes.fromhex("F100")))  # Color
            .add(EC.pause(0.625))
            .add(EC.call_obj_function(7, FID.ARBITRARY_1, 4, FS.HALT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_B, 4, FS.HALT))
            .add(EC.assign_val_to_mem(0, 0x7F020C, 1))
            .add(EC.party_follow()).add(EC.set_explore_mode(True))
            .add(EC.set_flag(memory.Flags.BLACKBIRD_PLAYED_SICK))
            .add(EC.return_cmd())
        )

        script.set_function(8, FID.ARBITRARY_4, generic_sick_func)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.BLACKBIRD_SEEN_EXTERIOR),
            script.get_function_start(8, FID.TOUCH)
        )

        new_block = (
            EF().add(EC.decision_box(
                script.add_py_string(
                    "Act Sick?{line break}"
                    "   Yes.{line break}"
                    "   No.{null}",
                ), 1, 2
            )).add_if(
                EC.if_result_equals(2),
                EF().add(EC.assign_val_to_mem(0, 0x7F020C, 1))
                .add(EC.party_follow()).add(EC.set_explore_mode(True))
                .add(EC.return_cmd())
            ).add(EC.get_result(cls.pc1_addr))
            .add_if(
                EC.if_result_equals(ctenums.CharID.LUCCA),
                EF()
                .add(EC.call_obj_function(8, FID.ARBITRARY_0, 4, FS.HALT))
                .add(EC.return_cmd())
            ).add_if(
                EC.if_result_equals(ctenums.CharID.ROBO),
                EF()
                .add(EC.call_obj_function(8, FID.ARBITRARY_1, 4, FS.HALT))
                .add(EC.return_cmd())
            ).add_if(
                EC.if_result_equals(ctenums.CharID.FROG),
                EF()
                .add(EC.call_obj_function(8, FID.ARBITRARY_2, 4, FS.HALT))
                .add(EC.return_cmd())
            ).add_if(
                EC.if_result_equals(ctenums.CharID.AYLA),
                EF()
                .add(EC.call_obj_function(8, FID.ARBITRARY_1, 4, FS.HALT))
                .add(EC.return_cmd())
            ).add(EC.call_obj_function(8, FID.ARBITRARY_4, 4, FS.HALT))
            .add(EC.return_cmd())
        )

        pos, cmd = script.find_command([0xD9], pos)
        pos += len(cmd)

        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

        # There are extra commands after the first command because spaghetti code.
        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block) + 1
        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

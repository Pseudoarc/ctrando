"""Openworld Lab 32 West"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Lab 32 West"""
    loc_id = ctenums.LocID.LAB_32_WEST
    scorekeeper_obj = 0xE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Lab 32 West Event.
        - Pre-set a flag to skip the Johnny entrance scene.
        - Pre-set the has raced flag so that foot access is still possible.
        - TODO: Set up a warp between lab endpoints if the race has been won
        """

        # The break command we find is within an if has bike key block.
        # We set the flag to skip the Johnny cutscene here.
        pos = script.find_exact_command(EC.break_cmd())
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.HAS_MET_JOHNNY))
            .add(EC.set_flag(memory.Flags.HAS_ATTEMPTED_JOHNNY_RACE))
            .get_bytearray(), pos
        )

        cls.update_scorekeeper_object(script, cls.scorekeeper_obj)

    # For the RX-XR Object:
    # Activate: Change Modes/High Scores - No changes needed
    # Arb0: Initial greeting - No changes needed
    # Arb1: High score check - No changes needed
    # Arb2: Check 2300+, 2000+, and 1500+ (tab)
    # Arb3: Just Check 1500+ (tab)
    # Arb4: Just Check 1300+
    # Arb5: Just Check 777 scores - Probably no change
    # Arb6: Just check other XXX scores - Probably no change

    # You can get the 1500+ (tab) reward once.
    # You can get at most one of the other threshold rewards in a race
    # You can get

    @classmethod
    def find_tier_str_ids(cls, script: Event) -> tuple[int, int, int, int]:
        """Returns key item, low, mid, high string ids"""
        tier_1300_id = tier_1500_id = tier_2000_id = tier_2300_id = -1
        for ind, ct_str in enumerate(script.strings):
            py_str = ctstrings.CTString.ct_bytes_to_ascii(ct_str)

            if "Unbelievable!" in py_str:
                tier_1500_id = ind
            if "Beautiful!" in py_str:
                tier_1300_id = ind
            if "anaconda!" in py_str:
                tier_2000_id = ind
            if "shut me down" in py_str:
                tier_2300_id = ind

        ret_tuple = (tier_1500_id, tier_1300_id, tier_2000_id, tier_2300_id)
        if any((x<0 for x in ret_tuple)):
            raise ValueError

        return ret_tuple


    @classmethod
    def update_scorekeeper_object(
            cls, script: Event,
            object_id: int,
            temp_counter_addr: int = 0x7F0236,
            temp_score_addr: int = 0x7F0238,
            temp_status_addr: int = 0x7F023A
    ):

        key_id, low_id, mid_id, high_id = cls.find_tier_str_ids(script)

        low_str = ctstrings.CTString.ct_bytes_to_ascii(script.strings[low_id])
        ind = low_str.find("{full break}")
        low_str = low_str[:ind] + "{null}"
        script.strings[low_id] = ctstrings.CTString.from_str(low_str, True)

        got_item_id = owu.add_default_treasure_string(script)

        score_addr = 0x7E0382
        high_mid_fn = (
            EF()
            .add_if(
                EC.if_mem_op_value(temp_score_addr, OP.GREATER_OR_EQUAL, 2300, 2),
                EF()
                .add(EC.increment_mem(temp_status_addr))
                .add(EC.auto_text_box(high_id))
                .add(EC.assign_val_to_mem(5, temp_counter_addr, 1))
                .set_label("high_loop")
                .add_if(
                    EC.if_mem_op_value(temp_counter_addr, OP.GREATER_THAN, 0),
                    EF()
                    .add(EC.play_sound(0xB0))
                    .add(EC.add_item(ctenums.ItemID.FULL_ETHER))
                    .add(EC.decrement_mem(temp_counter_addr))
                    .jump_to_label(EC.jump_back(), "high_loop")
                )
                .add(EC.auto_text_box(script.add_py_string("{line break}     Got 5 Full Ethers!{null}")))
                .jump_to_label(EC.jump_forward(), "tab_check")
            )
            .add_if(
                EC.if_mem_op_value(temp_score_addr, OP.GREATER_OR_EQUAL, 2000, 2),
                EF()
                .add(EC.increment_mem(temp_status_addr))
                .add(EC.auto_text_box(mid_id))
                .add(EC.assign_val_to_mem(5, temp_counter_addr, 1))
                .set_label("mid_loop")
                .add_if(
                    EC.if_mem_op_value(temp_counter_addr, OP.GREATER_THAN, 0),
                    EF()
                    .add(EC.play_sound(0xB0))
                    .add(EC.add_item(ctenums.ItemID.ETHER))
                    .add(EC.decrement_mem(temp_counter_addr))
                    .jump_to_label(EC.jump_back(), "mid_loop")
                )
                .add(EC.auto_text_box(script.add_py_string("{line break}     Got 5 Ethers!{null}")))
            )
            .set_label("tab_check")
            .add_if(
                EC.if_mem_op_value(temp_score_addr, OP.GREATER_OR_EQUAL, 1500, 2),
                EF()
                .add_if(
                    EC.if_not_flag(memory.Flags.OBTAINED_JOHNNY_RACE_POWER_TAB),
                    EF()
                    .add_if(
                        EC.if_mem_op_value(temp_status_addr, OP.EQUALS, 0),
                        EF()
                        .add(EC.increment_mem(temp_status_addr))
                        .add(EC.auto_text_box(key_id))
                    )
                    .add(EC.assign_val_to_mem(ctenums.ItemID.POWER_TAB, 0x7F0200, 1))
                    .add(EC.add_item_memory(0x7F0200))
                    .add(EC.auto_text_box(got_item_id))
                    .add(EC.set_flag(memory.Flags.OBTAINED_JOHNNY_RACE_POWER_TAB))
                )
            )
            .add(EC.return_cmd())
        )

        script.set_function(object_id, FID.ARBITRARY_2, high_mid_fn)

        low_fn = (
            EF()
            .add_if(
                EC.if_mem_op_value(temp_score_addr, OP.GREATER_OR_EQUAL, 1300, 2),
                EF()
                .add(EC.increment_mem(temp_status_addr))
                .add(EC.auto_text_box(low_id))
                .add(EC.assign_val_to_mem(5, temp_counter_addr, 1))
                .set_label("low_loop")
                .add_if(
                    EC.if_mem_op_value(temp_counter_addr, OP.GREATER_THAN, 0),
                    EF()
                    .add(EC.play_sound(0xB0))
                    .add(EC.add_item(ctenums.ItemID.MID_TONIC))
                    .add(EC.decrement_mem(temp_counter_addr))
                    .jump_to_label(EC.jump_back(), "low_loop")
                )
                .add(EC.auto_text_box(script.add_py_string("{line break}     Got 5 Mid Tonics!{null}")))
            )
            .add(EC.return_cmd())
        )
        script.set_function(object_id, FID.ARBITRARY_4, low_fn)

        find_cmd = EC.if_flag(memory.Flags.HAS_MET_RX_XR)
        pos = script.find_exact_command(find_cmd) + len(find_cmd)

        script.insert_commands(
            EC.assign_mem_to_mem(score_addr, temp_score_addr, 2)
            .to_bytearray(),
            pos
        )

        pos, _ = script.find_command([0x12], pos)  # Check 0x80 of race status
        script.delete_jump_block(pos)
        script.insert_commands(
            EC.call_obj_function(object_id, FID.ARBITRARY_2, 1, FS.HALT)
            .to_bytearray(),
            pos
        )

        del_pos, _ = script.find_command([0x16], pos)  # Check power tab
        del_end, _ = script.find_command([0x67], del_pos)
        script.delete_commands_range(del_pos, del_end)
        script.insert_commands(
            EF()
            .add_if(
                EC.if_mem_op_value(temp_status_addr, OP.EQUALS, 0),
                EF()
                .add(EC.call_obj_function(object_id, FID.ARBITRARY_4, 1, FS.HALT))
            ).get_bytearray(),
            del_pos
        )

        # print(script.get_function(0, FID.STARTUP))
        # input()


    @classmethod
    def assign_key_threshold(cls, script: Event, obj_id: int, threshold: int):
        pos = script.get_function_start(obj_id, FID.ARBITRARY_2)

        pos, cmd = script.find_command([0x13], pos)
        pos += len(cmd)
        pos, cmd = script.find_command([0x13], pos)
        pos += len(cmd)
        pos, cmd = script.find_command([0x13], pos)

        script.data[pos+2: pos+4] = threshold.to_bytes(2, "little")


    @classmethod
    def assign_tier_reward(
            cls, script: Event, obj_id: int,
            tier: int, threshold: int, item: ctenums.ItemID, amount: int):
        """
        Change the race reward for a given tier.  Param obj_id is the RX-XR object.
        Currently only works from vanilla values (explicit number checks)
        """
        key_id, low_id, mid_id, high_id = cls.find_tier_str_ids(script)

        if tier == 0:
            py_str = ctstrings.CTString.ct_bytes_to_ascii(script.strings[low_id])
            py_str = py_str.replace("1300", str(threshold))
            script.strings[low_id] = ctstrings.CTString.from_str(py_str, True)

            pos, cmd = script.find_command(
                [0x13], script.get_function_start(obj_id, FID.ARBITRARY_4)
            )
            script.data[pos+2: pos+4] = int.to_bytes(threshold, 2, "little")

        elif tier == 1:
            py_str = ctstrings.CTString.ct_bytes_to_ascii(script.strings[mid_id])
            py_str = py_str.replace("2000", str(threshold))
            script.strings[mid_id] = ctstrings.CTString.from_str(py_str, True)

            pos, cmd = script.find_command(
                [0x13], script.get_function_start(obj_id, FID.ARBITRARY_2)
            )
            pos += len(cmd)
            pos, cmd = script.find_command([0x13], pos)

            script.data[pos + 2: pos + 4] = int.to_bytes(threshold, 2, "little")

        elif tier == 2:
            py_str = ctstrings.CTString.ct_bytes_to_ascii(script.strings[high_id])
            py_str = py_str.replace("2300", str(threshold))
            script.strings[high_id] = ctstrings.CTString.from_str(py_str, True)

            pos, cmd = script.find_command(
                [0x13], script.get_function_start(obj_id, FID.ARBITRARY_2)
            )
        else:
            raise ValueError

        script.data[pos + 2: pos + 4] = int.to_bytes(threshold, 2, "little")

        pos, cmd = script.find_command([0x4F], pos)
        script.data[pos + 1] = amount

        pos, _ = script.find_command([0xCA], pos)
        script.data[pos + 1] = item

        new_str = f"{{line break}}       Got {amount}x {{item}}!{{null}}"
        pos, cmd = script.find_command([0xBB], pos)
        str_id = cmd.args[0]

        script.strings[str_id] = ctstrings.CTString.from_str(new_str, True)
        script.insert_commands(
            EC.assign_val_to_mem(item, 0x7F0200, 1).to_bytearray(),
            pos
        )




"""
This module provides data types for manipulating spots in the game which can
give a reward.  It also provides an association of ctenums.TreasureID to the
appropriate treasure objects.
"""
import typing

from ctrando.base.openworld import iokatradingpost
from ctrando.common import byteops, ctenums, ctrom, cttypes as ctt, memory
from ctrando.locations import locationevent, eventcommand
from ctrando.strings import ctstrings

from ctrando.locations.scriptmanager import ScriptManager, LocationEvent
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF

class Gold(int):
    def __init__(self, *args, **kwargs):
        int.__init__(self)

        if self % 2 != 0:
            raise ValueError("Gold values must be even.")

        if self not in range(0, 2**16):
            raise ValueError("Gold must be in range(0, 65353)")


RewardType = typing.Union[ctenums.ItemID, Gold]


class _RewardSpotBase(typing.Protocol):
    def write_to_ct_rom(self, ct_rom: ctrom.CTRom,
                        script_manager: typing.Optional[ScriptManager] = None):
        """Write this RewardSpot to the given state."""

    def read_reward_from_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None

    ) -> RewardType:
        """Read the reward currently held in this spot"""


class RewardSpotProperty(_RewardSpotBase, typing.Protocol):
    @property
    def reward(self) -> RewardType:
        pass

    @reward.setter
    def reward(self, new_reward: RewardType):
        pass


class RewardSpotField(_RewardSpotBase, typing.Protocol):
    reward: RewardType


type RewardSpot = RewardSpotProperty | RewardSpotField


class ChestRW(ctt.RomRW):
    def __init__(self, ptr_to_ptr_table: int = 0x00A751):
        self.ptr_to_ptr_table = ptr_to_ptr_table

    def get_data_start(self, ct_rom: ctrom.CTRom) -> int:
        ct_rom.seek(self.ptr_to_ptr_table)

        ptr_table_st = int.from_bytes(ct_rom.read(3), "little")
        ptr_table_st = byteops.to_file_ptr(ptr_table_st)

        bank = ptr_table_st & 0xFF0000

        ct_rom.seek(ptr_table_st)
        first_ptr = int.from_bytes(ct_rom.read(2), "little") + bank

        return first_ptr

    def read_data_from_ctrom(
        self,
        ct_rom: ctrom.CTRom,
        num_bytes: int,
        record_num: int = 0,
        data_start: typing.Optional[int] = None,
    ) -> bytearray:
        if data_start is None:
            data_start = self.get_data_start(ct_rom)

        ct_rom.seek(data_start + num_bytes * record_num)
        return bytearray(ct_rom.read(num_bytes))

    def write_data_to_ct_rom(
        self,
        ct_rom: ctrom.CTRom,
        data: typing.ByteString,
        record_num: int = 0,
        data_start: typing.Optional[int] = None,
    ):
        """
        Write data to a ctrom.CTRom.  If the target data is arranged in
        records of length len(data), write to record number record_num.
        """
        if data_start is None:
            data_start = self.get_data_start(ct_rom)

        ct_rom.seek(data_start + len(data) * record_num)
        ct_rom.write(data)

    def free_data_on_ct_rom(
        self,
        ct_rom: ctrom.CTRom,
        num_bytes: int,
        record_num: int = 0,
        start_addr: typing.Optional[int] = None,
        data_start: typing.Optional[int] = None,
    ):
        """
        Mark the data on the ROM that would be read/written as free
        """
        space_man = ct_rom.space_manager

        if data_start is None:
            data_start = self.get_data_start(ct_rom)

        start = data_start + num_bytes * record_num
        end = start + num_bytes

        space_man.mark_block((start, end), ctrom.freespace.FSWriteType.MARK_FREE)


class ChestTreasureData(ctt.BinaryData):
    """
    This class represents the data on the rom for a treasure chest.
    """

    SIZE = 4
    ROM_RW = ChestRW(0x00A751)

    x_coord = ctt.byte_prop(0)
    y_coord = ctt.byte_prop(1)
    has_gold = ctt.bytes_prop(2, 2, 0x8000)

    @property
    def gold(self) -> Gold:
        if not self.has_gold:
            raise ValueError("Chest data is not set to contain gold")

        return Gold(byteops.get_masked_range(self, 2, 2, 0x7FFF) * 2)

    @gold.setter
    def gold(self, gold_amt: int):
        if gold_amt < 0:
            raise ValueError("Gold must be non-negative.")

        if gold_amt > 0xFFFE:
            raise ValueError("Gold must be at most 0xFFFE = 65534")

        self.has_gold = True
        byteops.set_masked_range(self, 2, 2, 0x7FFF, gold_amt // 2)

    _is_empty = ctt.bytes_prop(2, 2, 0x4000)

    @property
    def is_empty(self) -> bool:
        if self.has_gold:
            return False

        return self._is_empty

    @is_empty.setter
    def is_empty(self, val: bool):
        if not val:
            if self.has_gold:
                self.has_gold = False
        else:
            self.has_gold = False
            self.reward = ctenums.ItemID.MOP

        self._is_empty = val

    _held_item = ctt.bytes_prop(2, 2, 0x3FFF, ret_type=ctenums.ItemID)

    @property
    def held_item(self) -> ctenums.ItemID:
        if self.has_gold:
            raise ValueError("Chest data is set to contain gold.")

        return ctenums.ItemID(self._held_item)

    @held_item.setter
    def held_item(self, item: ctenums.ItemID):
        item = ctenums.ItemID(item)
        if item == ctenums.ItemID.NONE:
            self._is_empty = True
            self.has_gold = False
            self._held_item = ctenums.ItemID.NONE

        self.has_gold = False
        self._is_empty = False
        self._held_item = item

    @property
    def loc_pointer(self) -> typing.Optional[ctenums.LocID]:
        if self.x_coord == 0 and self.y_coord == 0:
            loc_id = int.from_bytes(self[2:4], "little")
            return ctenums.LocID(loc_id)

        return None

    @loc_pointer.setter
    def loc_pointer(self, loc_id: ctenums.LocID):
        self.x_coord = 0
        self.y_coord = 0
        self[2:4] = int.to_bytes(int(loc_id), 2, "little")

    def is_copying_location(self) -> bool:
        return self.x_coord == self.y_coord == 0

    @property
    def reward(self) -> RewardType:
        if self.is_empty:
            return ctenums.ItemID.NONE

        if self.has_gold:
            return self.gold

        return self._held_item

    @reward.setter
    def reward(self, val: RewardType):
        if isinstance(val, ctenums.ItemID):
            self.held_item = val
        else:
            self.gold = val

    @property
    def copy_location(self) -> ctenums.LocID:
        if self.x_coord != 0 or self.y_coord != 0:
            raise ValueError("X and Y coordinates are nonzero")

        return ctenums.LocID(int.from_bytes(self[2:4], "little"))

    @copy_location.setter
    def copy_location(self, loc_id: ctenums.LocID):
        self.x_coord = 0
        self.y_coord = 0

        self[2:4] = int.to_bytes(loc_id, 2, "little")


class ChestTreasure:
    """
    A class which represents a treasure chest.  Implements RewardSpot.
    """

    def __init__(self, chest_index: int, reward: RewardType = ctenums.ItemID.MOP):
        self.reward = reward
        self.chest_index = chest_index

    def write_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None):
        self.write_to_ctrom(ct_rom)

    def read_reward_from_ct_rom(self, ct_rom, script_manager) -> RewardType:
        chest_data = ChestTreasureData.read_from_ctrom(ct_rom, self.chest_index)

        if chest_data.is_copying_location():
            raise ValueError

        if chest_data.has_gold:
            return chest_data.gold
        else:
            return chest_data.held_item

    def write_to_ctrom(
        self, ct_rom: ctrom.CTRom, data_start: typing.Optional[int] = None
    ):
        chest_rw = ChestRW(0x00A751)
        if data_start is None:
            data_start = chest_rw.get_data_start(ct_rom)

        # Read that current chest on the rom and just update the reward part
        current_data = ChestTreasureData(
            chest_rw.read_data_from_ctrom(
                ct_rom, ChestTreasureData.SIZE, self.chest_index, data_start
            )
        )
        current_data.reward = self.reward
        if current_data.reward == ctenums.ItemID.NONE:
            current_data.is_empty = True

        chest_rw.write_data_to_ct_rom(
            ct_rom, current_data, self.chest_index, data_start
        )


class ScriptTreasure:
    """
    A class for writing rewards to places in a script where a reward can be
    gained.
    """

    def __init__(
        self,
        location: ctenums.LocID,
        object_id: int,
        function_id: int,
        reward: RewardType = ctenums.ItemID.MOP,
        item_num: int = 0,
    ):
        self.reward = reward
        self.location = location
        self.object_id = object_id
        self.function_id = function_id
        self.item_num = item_num

    def __repr__(self):
        x = (
            f"{type(self).__name__}(location={self.location}, "
            + f"object_id={self.object_id}, function_id={self.function_id},  "
            + f"reward={self.reward}, "
            f"item_num={self.item_num})"
        )
        return x

    @staticmethod
    def update_get_reward_text(
        script: locationevent.LocationEvent,
        start: int,
        end: int,
        reward: RewardType,
        orig_gold_amt: typing.Optional[int] = None,
    ):
        if isinstance(reward, ctenums.ItemID):
            if reward == ctenums.ItemID.NONE:
                repl_str = "Nothing"
            else:
                repl_str = "{item}!{line break}{itemdesc}"
        else:
            repl_str = f"{reward} G"

        pos: typing.Optional[int] = start
        text_cmds = [0xBB, 0xC1, 0xC2]
        while True:
            pos, cmd = script.find_command_opt(text_cmds, pos, end)

            if pos is None:
                raise locationevent.CommandNotFoundException(
                    "Unable to find reward string."
                )

            str_ind = cmd.args[-1]
            string = script.strings[str_ind]
            py_string = ctstrings.CTString.ct_bytes_to_ascii(string)

            orig_str = None
            if "{item}!{line break}{itemdesc}" in py_string:
                orig_str = "{item}!{line break}{itemdesc}"
            elif "{item}!" in py_string:
                orig_str = "{item}!"
            elif "{item}" in py_string:
                orig_str = "{item}"
                repl_str = repl_str.replace("!{line break}{itemdesc}", "")
            elif f"{orig_gold_amt}G" in py_string:
                orig_str = f"{orig_gold_amt}G!"
            elif f"{orig_gold_amt} G" in py_string:
                orig_str = f"{orig_gold_amt} G!"

            if orig_str is not None:
                new_str = py_string.replace(orig_str, repl_str)
                if "{item}" not in repl_str or orig_str == "{item}":
                    new_str = new_str.replace("{itemdesc}", "")
                new_ind = script.add_py_string(new_str)
                script.data[pos + 1] = new_ind
                # print(orig_str, new_str)
                # print(py_string)
                # input()
                break

            pos += len(cmd)

    def _get_search_start_end(self, script: LocationEvent):
        fn_start = script.get_function_start(self.object_id, self.function_id)
        fn_end = script.get_function_end(self.object_id, self.function_id)

        return fn_start, fn_end



    def write_to_ct_rom(self, ct_rom: ctrom.CTRom,
                        script_manager: typing.Optional[ScriptManager] = None):
        """
        Insert the desired reward into the event script in the state
        """
        script = script_manager[self.location]
        fn_start, fn_end = self._get_search_start_end(script)

        pos: typing.Optional[int] = fn_start
        num_mem_set_cmds_found = 0
        mem_set_pos: typing.Optional[int] = None

        num_add_rwd_cmds_found = 0
        add_rwd_pos: typing.Optional[int] = None

        while True:
            # Commands:
            #   0x4F - Set script memory.  Look for setting 0x7F0200 (item)
            #   0xC7 - Add item from memory.
            #   0xCA - Add item.
            #   0xCD - Add gold.

            # Loop until we reach the appropriate number of set memory and
            # add gold/item commands
            pos, cmd = script.find_command_opt([0x4F, 0xCA, 0xCD, 0xC7], pos, fn_end)

            if pos is None:
                # print(self)
                # print(num_mem_set_cmds_found, num_add_rwd_cmds_found)
                raise locationevent.CommandNotFoundException(
                    f"{self.location}: " "Failed to find item setting commands."
                )

            if cmd.command == 0x4F:
                # Writing to 0x7F0200 is means the last argument is 0
                if cmd.args[-1] == 0:
                    num_mem_set_cmds_found += 1
                    if num_mem_set_cmds_found == self.item_num + 1:
                        mem_set_pos = pos
            elif cmd.command in (0xCA, 0xCD, 0xC7):
                num_add_rwd_cmds_found += 1
                if num_add_rwd_cmds_found == self.item_num + 1:
                    add_rwd_pos = pos

            if add_rwd_pos is not None and script.data[add_rwd_pos] == 0xCD:
                break
            if mem_set_pos is not None and add_rwd_pos is not None:
                break

            pos += len(cmd)

        if script.data[add_rwd_pos] == 0xCD:
            add_gold_cmd = eventcommand.get_command(script.data, add_rwd_pos)
            added_gold = add_gold_cmd.args[-1]
        else:
            added_gold = None

        # print(self.location, self.object_id, self.function_id)
        ScriptTreasure.update_get_reward_text(
            script, mem_set_pos, fn_end, self.reward, added_gold
        )

        if isinstance(self.reward, ctenums.ItemID):
            # Update the mem_set and add_rwd locations
            script.data[mem_set_pos + 1] = int(self.reward)
            if script.data[add_rwd_pos] == 0xCD:
                script.insert_commands(
                    EC.add_item_memory(0x7F0200).to_bytearray(), add_rwd_pos
                )
                script.delete_commands(add_rwd_pos+2, 1)
            elif script.data[add_rwd_pos] != 0xC7:
                script.data[add_rwd_pos + 1] = int(self.reward)

        else:  # The reward is gold
            add_gold_cmd = EC.add_gold(self.reward)

            # Note, we do insert then add because of weirdness if this happens
            # to be at the end of an if-block.
            script.insert_commands(add_gold_cmd.to_bytearray(), add_rwd_pos)
            script.delete_commands(add_rwd_pos + len(add_gold_cmd), 1)

            # Also note, we keep the mem set command intact in case we ever
            # want to use this method to set this ScriptTreasure another time.

    def read_reward_from_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None
    ) -> RewardType:
        script = script_manager[self.location]

        pos = script.get_function_start(self.object_id, self.function_id)

        num_mem_set_cmds_found = 0
        mem_set_pos: typing.Optional[int] = None

        num_add_rwd_cmds_found = 0
        add_rwd_pos: typing.Optional[int] = None

        while True:
            pos, cmd = script.find_command_opt([0x4F, 0xCA, 0xCD, 0xC7], pos)

            if pos is None:
                raise locationevent.CommandNotFoundException

            if cmd.command == 0x4F and cmd.args[-1] == 0:
                num_mem_set_cmds_found += 1
                if num_mem_set_cmds_found == self.item_num + 1:
                    mem_set_pos = pos
            elif cmd.command in (0xCA, 0xCD, 0xC7):
                num_add_rwd_cmds_found += 1
                if num_add_rwd_cmds_found == self.item_num + 1:
                    add_rwd_pos = pos

            if mem_set_pos is not None and add_rwd_pos is not None:
                break

            pos += len(cmd)

        add_rwd_cmd_id = script.data[add_rwd_pos]
        if add_rwd_cmd_id == 0xC7:  # Item from mem
            item_id = script.data[mem_set_pos + 1]
            return ctenums.ItemID(item_id)
        elif add_rwd_cmd_id == 0xCA:  # Add Item
            item_id = script.data[add_rwd_pos + 1]
            return ctenums.ItemID(item_id)
        else:  # Add Gold, 0xCD
            gold_amt = int.from_bytes(script.data[add_rwd_pos + 1 : add_rwd_pos + 3])
            return Gold(gold_amt)


class SpriteScriptTreasure(ScriptTreasure):
    """ScriptTreasure that gets drawn on screen."""

    _item_id_sprite_dict: dict[ctenums.ItemID, ctenums.NpcID] = {
        ctenums.ItemID.DREAMSTONE: ctenums.NpcID.DREAMSTONE,
        ctenums.ItemID.GATE_KEY: ctenums.NpcID.GATE_KEY,
        ctenums.ItemID.TOMAS_POP: ctenums.NpcID.SODA_CAN,
        ctenums.ItemID.PENDANT: ctenums.NpcID.PENDANT,
        ctenums.ItemID.PENDANT_CHARGE: ctenums.NpcID.PENDANT,
        ctenums.ItemID.RUBY_KNIFE: ctenums.NpcID.RED_KNIFE,
        ctenums.ItemID.BENT_HILT: ctenums.NpcID.BROKEN_BLADE,
        ctenums.ItemID.BENT_SWORD: ctenums.NpcID.BROKEN_BLADE,
        ctenums.ItemID.MASAMUNE_1: ctenums.NpcID.MASAMUNE_SPINNING,
        ctenums.ItemID.MOON_STONE: ctenums.NpcID.MOONSTONE,
        ctenums.ItemID.SUN_STONE: ctenums.NpcID.MOONSTONE,
        ctenums.ItemID.RAINBOW_SHELL: ctenums.NpcID.RAINBOW_SHELL,
        ctenums.ItemID.C_TRIGGER: ctenums.NpcID.C_TRIGGER,
        ctenums.ItemID.JETSOFTIME: ctenums.NpcID.FLYING_EPOCH_OW,
        ctenums.ItemID.SEED: ctenums.NpcID.POTTED_PLANT
    }
    def __init__(
            self,
            location: ctenums.LocID,
            object_id: int,
            function_id: int,
            reward: RewardType = ctenums.ItemID.MOP,
            item_num: int = 0,
            sprite_object_id: typing.Optional[int] = None
    ):
        if sprite_object_id is None:
            sprite_object_id = object_id

        ScriptTreasure.__init__(self, location, object_id, function_id,
                                reward, item_num)
        self.sprite_object_id = sprite_object_id

    def write_to_ct_rom(self, ct_rom: ctrom.CTRom,
                        script_manager: typing.Optional[ScriptManager] = None):
        ScriptTreasure.write_to_ct_rom(self, ct_rom, script_manager)

        script = script_manager[self.location]

        pos, end = script.get_function_bounds(self.sprite_object_id,
                                              FID.STARTUP)

        new_npc_id = self._item_id_sprite_dict.get(
            self.reward, ctenums.NpcID.GIANT_BLUE_STAR
        )

        pos, _ = script.find_command(
            [EC.load_npc(0).command], pos, end
        )
        script.replace_command_at_pos(
            pos, EC.load_npc(new_npc_id)
        )


class MasaMuneTreasure(ScriptTreasure):
    """
    Treasure type for setting the Cave of Masamune key item.
    Needs to change the "Are you here for {item}" prompt as well.
    """
    def __init__(
            self,
            location: ctenums.LocID,
            object_id: int,
            function_id: int,
            reward: RewardType = ctenums.ItemID.MOP,
            item_num=0,
            text_object_id: int = 0x0D,
            text_function_id: int = FID.ARBITRARY_0,
    ):
        ScriptTreasure.__init__(self, location, object_id, function_id, reward, item_num)
        self.text_object_id = text_object_id
        self.text_function_id = text_function_id


    def write_to_ct_rom(self, ct_rom: ctrom.CTRom,
                        script_manager: typing.Optional[ScriptManager] = None):
        ScriptTreasure.write_to_ct_rom(self, ct_rom, script_manager)
        self.write_item_to_decbox(script_manager)

    def write_item_to_decbox(
            self,
            script_manager: ScriptManager
    ):
        script = script_manager[ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE]
        pos, _ = script.find_command(
            [0xC0],
            script.get_function_start(self.text_object_id, self.text_function_id)
        )
        str_ind = script.data[pos+1]

        if isinstance(self.reward, ctenums.ItemID):
            script.insert_commands(
                EC.assign_val_to_mem(self.reward, 0x7F0200, 1).to_bytearray(), pos
            )
            repl_str = "{item}"
        else:
            repl_str = f"{int(self.reward)}G"

        dec_str = ctstrings.CTString.ct_bytes_to_ascii(script.strings[str_ind]).replace("Masamune", repl_str)
        script.strings[str_ind] = ctstrings.CTString.from_str(dec_str, True)


class BekklerTreasure(ScriptTreasure):
    """
    Treasure type for setting the Bekkler key item.  Needs extra work because
    the check is split over two locations.
    """

    def __init__(
        self,
        location: ctenums.LocID,
        object_id: int,
        function_id: int,
        held_item: ctenums.ItemID = ctenums.ItemID.MOP,
        item_num=0,
        bekkler_location: ctenums.LocID = ctenums.LocID.BEKKLERS_LAB,
        bekkler_object_id: int = 0x0B,
        bekkler_function_id: int = 0x01,
    ):
        ScriptTreasure.__init__(
            self, location, object_id, function_id, held_item, item_num
        )

        self.bekkler_location = bekkler_location
        self.bekkler_object_id = bekkler_object_id
        self.bekkler_function_id = bekkler_function_id

    def write_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None):
        ScriptTreasure.write_to_ct_rom(self, ct_rom, script_manager)
        self.write_bekkler_name_to_script(script_manager)

    def write_bekkler_name_to_script(self, script_manager: ScriptManager):
        script = script_manager[self.bekkler_location]

        st = script.get_function_start(self.bekkler_object_id, self.bekkler_function_id)
        end = script.get_function_end(self.bekkler_object_id, self.bekkler_function_id)

        pos, _ = script.find_command([0x4F], st, end)

        if isinstance(self.reward, ctenums.ItemID):
            script.data[pos + 1] = int(self.reward)
        else:
            pos, cmd = script.find_command([0xC0])
            str_ind = cmd.args[-1]
            py_str = ctstrings.CTString.ct_bytes_to_ascii(script.strings[str_ind])
            py_str = py_str.replace("{item}", "wad of cash")
            script.strings[str_ind] = ctstrings.CTString.from_str(py_str)


class PrismShardTreasure(ScriptTreasure):
    def write_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None):
        """Also set the name spoiler in obj9, touch"""
        ScriptTreasure.write_to_ct_rom(self, ct_rom, script_manager)

        script = script_manager[ctenums.LocID.GUARDIA_REAR_STORAGE]

        pos, _ = script.find_command(
            [0x4F], script.get_function_start(9, 2)  # val to mem,
        )

        if isinstance(self.reward, ctenums.ItemID):
            hook_cmd = EC.assign_val_to_mem(self.reward, 0x7F0200, 1)
            script.data[pos : pos + len(hook_cmd)] = hook_cmd.to_bytearray()

        pos, cmd = script.find_command([0xC0], pos)  # spoiler DecBox

        str_ind = cmd.args[0]
        string = script.strings[str_ind]
        py_string = ctstrings.CTString.ct_bytes_to_ascii(string)

        if not isinstance(self.reward, ctenums.ItemID):
            reward_str = f"{int(self.reward)}G"
            py_string = py_string.replace("{item}", reward_str)
            script.strings[str_ind] = ctstrings.CTString.from_str(py_string)


class ChargeableTreasure(ScriptTreasure):
    """A ScriptTreasure which can be charged by the pendant."""

    def write_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None):
        ScriptTreasure.write_to_ct_rom(self, ct_rom, script_manager)

        script = script_manager[self.location]
        pos, _ = script.find_command(
            [0xC0], script.get_function_start(self.object_id, self.function_id)
        )
        str_id = script.data[pos + 1]
        item_str = str(self.reward)
        new_str_id = script.add_py_string(
            f"A {item_str} is reacting to the pendant.{{linebreak+0}}"
            "Take it out?{line break}"
            "   Yes.{line break}"
            "   No.{null}"
        )
        script.data[pos+1] = new_str_id


class SplitChargeableTreasure:
    """
    Class for a RewardSpot that is chargeable and also the charged
    spot is on a different map (e.g. Truce Inn).
    """

    def __init__(
        self,
        location: ctenums.LocID,
        object_id: int,
        function_id: FID,
        charge_location: ctenums.LocID,
        charge_object_id: int,
        charge_function_id: FID,
        charge_item_num: int = 1,
        reward: RewardType = ctenums.ItemID.MOP,
    ):
        self.base_loc_spot = ChargeableTreasure(
            location, object_id, function_id, reward=reward
        )
        self.charge_loc_base_spot = ScriptTreasure(
            charge_location,
            charge_object_id,
            charge_function_id,
            reward=reward,
            item_num=charge_item_num,
        )

    @property
    def reward(self) -> RewardType:
        """Gets reward in base location"""
        return self.base_loc_spot.reward

    @reward.setter
    def reward(self, new_reward: RewardType):
        """Sets base reward in base and charge location."""
        self.base_loc_spot.reward = new_reward
        self.charge_loc_base_spot.reward = new_reward

    def write_to_ct_rom(self, ct_rom: ctrom.CTRom,
                        script_manager: typing.Optional[ScriptManager] = None):
        """Sets base reward in base and charge location."""
        self.base_loc_spot.write_to_ct_rom(ct_rom, script_manager)
        self.charge_loc_base_spot.write_to_ct_rom(ct_rom, script_manager)

    def read_reward_from_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None
    ) -> RewardType:
        """Read reward from ct_rom"""
        base_reward = self.base_loc_spot.read_reward_from_ct_rom(ct_rom, script_manager)
        charge_spot_base_reward = self.charge_loc_base_spot.read_reward_from_ct_rom(
            ct_rom, script_manager
        )

        if base_reward != charge_spot_base_reward:
            raise ValueError

        return base_reward


class HuntingRangeNuTreasure(ScriptTreasure):
    """Special Case for the Nu's reward in the hunting grounds."""

    def write_to_ct_rom(self, ct_rom: ctrom.CTRom,
                        script_manager: typing.Optional[ScriptManager] = None):
        script = script_manager[self.location]

        for object_id in range(self.object_id, self.object_id + 3):
            fn_start = script.get_function_start(object_id, self.function_id)
            fn_end = script.get_function_end(object_id, self.function_id)

            pos = script.find_exact_command(
                EC.if_flag(memory.Flags.HUNTING_RANGE_NU_REWARD),
                fn_start, fn_end
            )
            cmd = locationevent.get_command(script.data, pos)
            skip_len = cmd.args[-1]
            pos += len(cmd) + skip_len - 1

            if isinstance(self.reward, ctenums.ItemID):
                script.data[pos+1] = self.reward
            else:
                new_block = (
                    EF().add(EC.add_gold(self.reward))
                    .add(EC.auto_text_box(
                        script.add_py_string(
                            "{line break}"
                            f"Got {self.reward}G!{{null}}"
                        )
                    ))
                )
                script.insert_commands(new_block.get_bytearray(), pos)
                pos += len(new_block)
                script.delete_commands(pos, 3)

    def read_reward_from_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None
    ) -> RewardType:
        script = script_manager[self.location]

        fn_start = script.get_function_start(self.object_id, self.function_id)
        fn_end = script.get_function_end(self.object_id, self.function_id)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HUNTING_RANGE_NU_REWARD),
            fn_start, fn_end
        )

        reward_pos, cmd = script.find_command_opt([0x4F], pos, fn_end)

        if reward_pos is not None:
            return ctenums.ItemID(cmd.args[0])
        else:
            reward_pos, cmd = script.find_command([0xCD])
            return Gold(cmd.args[0])


class JohnnyRacePart(ScriptTreasure):

    def _get_search_start_end(self, script: LocationEvent):
        fn_start, fn_end = ScriptTreasure._get_search_start_end(self, script)

        fn_start = script.find_exact_command(
            EC.if_not_flag(memory.Flags.OBTAINED_JOHNNY_RACE_POWER_TAB),
            fn_start, fn_end
        )

        return fn_start, fn_end


class JohnnyRaceKeyItemTreasure:
    def __init__(
            self,
            west_spot: JohnnyRacePart,
            east_spot: JohnnyRacePart,
            reward: RewardType = ctenums.ItemID.MOP
    ):
        self.reward = reward
        self.west_spot = west_spot
        self.east_spot = east_spot

    def write_to_ct_rom(self, ct_rom: ctrom.CTRom,
                        script_manager: typing.Optional[ScriptManager] = None):
        if script_manager is None:
            raise ValueError

        self.west_spot.write_to_ct_rom(ct_rom, script_manager)
        self.east_spot.write_to_ct_rom(ct_rom, script_manager)

    def read_reward_from_ct_rom(
            self, ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None
    ):
        if script_manager is None:
            raise ValueError

        item_16 = self.west_spot.read_reward_from_ct_rom(ct_rom, script_manager)
        item_32 = self.east_spot.read_reward_from_ct_rom(ct_rom, script_manager)

        if item_16 != item_32:
            raise ValueError

        return item_16



class TradingPostTreasure:
    def __init__(
            self,
            selection_index: int,
            is_base_item: bool,
            reward: RewardType = ctenums.ItemID.MOP
    ):
        self.selection_index = selection_index
        self.is_base_item = is_base_item
        self.reward = reward


    def _get_reward_cmd(self) -> EC:
        if not isinstance(self.reward, ctenums.ItemID):
            raise TypeError("Reward must be an item.")

        return EC.assign_val_to_mem(self.reward, 0x7F0200, 1)


    def _get_script_and_pos(self, script_manager: ScriptManager) -> tuple[LocationEvent, int]:
        loc_id = ctenums.LocID.IOKA_TRADING_POST
        obj_id, func_id = 0xC, FID.ARBITRARY_1
        selection_addr = iokatradingpost.EventMod.trade_selection

        if not isinstance(self.reward, ctenums.ItemID):
            raise TypeError("Trading Post must have items.")

        script = script_manager[loc_id]
        pos = script.get_function_start(obj_id, func_id)
        pos = script.find_exact_command(
            EC.if_mem_op_value(selection_addr, OP.EQUALS, self.selection_index),
            pos
        )
        new_cmd = self._get_reward_cmd()

        pos, cmd = script.find_command([new_cmd.command], pos)
        if not self.is_base_item:
            pos += len(cmd)
            pos, cmd = script.find_command([new_cmd.command], pos)

        return script, pos

    def write_to_ct_rom(self, ct_rom, script_manager: typing.Optional[ScriptManager]):
        if script_manager is None:
            raise ValueError

        script, pos = self._get_script_and_pos(script_manager)
        new_cmd = self._get_reward_cmd()

        script.data[pos: pos + len(new_cmd)] = new_cmd.to_bytearray()

    def read_reward_from_ct_rom(
            self,
            ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None
    ) -> RewardType:
        if script_manager is None:
            raise ValueError

        script, pos = self._get_script_and_pos(script_manager)
        cmd = get_command(script.data, pos)

        return ctenums.ItemID(cmd.args[0])


class TradingPostSpecialTreasure:
    def __init__(self, reward: RewardType = ctenums.ItemID.MOP):
        self.reward = reward

    def _get_reward_cmd(self) -> EC:
        if not isinstance(self.reward, ctenums.ItemID):
            raise TypeError("Reward must be an item.")

        return EC.assign_val_to_mem(self.reward, 0x7F0200, 1)

    def _get_script_and_pos(self, script_manager: ScriptManager) -> tuple[LocationEvent, int]:
        loc_id = ctenums.LocID.IOKA_TRADING_POST
        obj_id, func_id = 0xC, FID.ARBITRARY_2

        if not isinstance(self.reward, ctenums.ItemID):
            raise TypeError("Trading Post must have items.")

        script = script_manager[loc_id]
        new_cmd = self._get_reward_cmd()

        pos = script.find_exact_command(
            EC.play_sound(0xB0), script.get_function_start(obj_id, func_id)
        )
        pos, _ = script.find_command([new_cmd.command], pos)

        return script, pos

    def read_reward_from_ct_rom(
            self,
            ct_rom: ctrom.CTRom,
            script_manager: typing.Optional[ScriptManager] = None
    ) -> RewardType:

        script, pos = self._get_script_and_pos(script_manager)
        cmd = get_command(script.data, pos)
        return cmd.args[0]

    def write_to_ct_rom(self, ct_rom, script_manager: typing.Optional[ScriptManager]):
        if script_manager is None:
            raise ValueError

        script, pos = self._get_script_and_pos(script_manager)
        new_cmd = self._get_reward_cmd()
        script.data[pos: pos + len(new_cmd)] = new_cmd.to_bytearray()

        pos, _ = script.find_command([new_cmd.command],
                                  script.get_function_start(8, FID.ACTIVATE))
        script.data[pos: pos + len(new_cmd)] = new_cmd.to_bytearray()



def get_base_treasure_dict() -> dict[ctenums.TreasureID, RewardSpot]:
    """
    Return a dictionary of all possible TreasureIDs to their corresponding
    treasure objects.
    """
    LocID = ctenums.LocID
    TID = ctenums.TreasureID

    ret_dict: dict[TID, RewardSpot] = {
        TID.TRUCE_MAYOR_1F: ChestTreasure(0x02),
        TID.TRUCE_MAYOR_2F: ChestTreasure(0x03),
        TID.KINGS_ROOM_1000: ChestTreasure(0x04),
        TID.QUEENS_ROOM_1000: ChestTreasure(0x05),
        TID.GUARDIA_BASEMENT_1: ChestTreasure(0x06),
        TID.GUARDIA_BASEMENT_2: ChestTreasure(0x07),
        TID.GUARDIA_BASEMENT_3: ChestTreasure(0x08),
        # non-cs
        TID.GUARDIA_JAIL_FRITZ_STORAGE: ChestTreasure(0x09),
        # end non-cs
        TID.FOREST_RUINS: ChestTreasure(0x0A),
        TID.HECKRAN_CAVE_SIDETRACK: ChestTreasure(0x0B),
        TID.HECKRAN_CAVE_ENTRANCE: ChestTreasure(0x0C),
        TID.HECKRAN_CAVE_1: ChestTreasure(0x0D),
        TID.HECKRAN_CAVE_2: ChestTreasure(0x0E),
        TID.PORRE_MAYOR_2F: ChestTreasure(0x0F),
        # non-cs
        TID.GUARDIA_JAIL_CELL: ChestTreasure(0x10),
        TID.GUARDIA_JAIL_OMNICRONE_1: ChestTreasure(0x11),
        TID.GUARDIA_JAIL_OMNICRONE_2: ChestTreasure(0x12),
        TID.GUARDIA_JAIL_OMNICRONE_3: ChestTreasure(0x13),
        TID.GUARDIA_JAIL_HOLE_1: ChestTreasure(0x14),
        TID.GUARDIA_JAIL_HOLE_2: ChestTreasure(0x15),
        TID.GUARDIA_JAIL_OUTER_WALL: ChestTreasure(0x16),
        TID.GUARDIA_JAIL_OMNICRONE_4: ChestTreasure(0x17),
        TID.GUARDIA_JAIL_FRITZ: ChestTreasure(0x18),
        # end non-cs
        # This is the "copy tyrano lair" chest data
        # TID.GIANTS_CLAW_KINO_CELL: ChestTreasure(0x19),
        TID.GIANTS_CLAW_TRAPS: ChestTreasure(0x1A),
        TID.TRUCE_CANYON_1: ChestTreasure(0x1B),
        TID.TRUCE_CANYON_2: ChestTreasure(0x1C),
        TID.KINGS_ROOM_600: ChestTreasure(0x1D),
        TID.QUEENS_ROOM_600: ChestTreasure(0x1E),
        TID.ROYAL_KITCHEN: ChestTreasure(0x1F),
        # non-cs
        TID.MAGUS_CASTLE_RIGHT_HALL: ChestTreasure(0x20),
        # end non-cs
        TID.MANORIA_CATHEDRAL_1: ChestTreasure(0x21),
        TID.MANORIA_CATHEDRAL_2: ChestTreasure(0x22),
        TID.MANORIA_CATHEDRAL_3: ChestTreasure(0x23),
        TID.MANORIA_INTERIOR_1: ChestTreasure(0x24),
        TID.MANORIA_INTERIOR_2: ChestTreasure(0x25),
        TID.MANORIA_INTERIOR_3: ChestTreasure(0x26),
        TID.MANORIA_INTERIOR_4: ChestTreasure(0x27),
        TID.CURSED_WOODS_1: ChestTreasure(0x28),
        TID.CURSED_WOODS_2: ChestTreasure(0x29),
        TID.FROGS_BURROW_RIGHT: ChestTreasure(0x2A),
        TID.DENADORO_MTS_SCREEN2_1: ChestTreasure(0x2B),
        TID.DENADORO_MTS_SCREEN2_2: ChestTreasure(0x2C),
        TID.DENADORO_MTS_SCREEN2_3: ChestTreasure(0x2D),
        TID.DENADORO_MTS_FINAL_1: ChestTreasure(0x2E),
        TID.DENADORO_MTS_FINAL_2: ChestTreasure(0x2F),
        TID.DENADORO_MTS_FINAL_3: ChestTreasure(0x30),
        TID.DENADORO_MTS_WATERFALL_TOP_1: ChestTreasure(0x31),
        TID.DENADORO_MTS_WATERFALL_TOP_2: ChestTreasure(0x32),
        TID.DENADORO_MTS_WATERFALL_TOP_3: ChestTreasure(0x33),
        TID.DENADORO_MTS_WATERFALL_TOP_4: ChestTreasure(0x34),
        TID.DENADORO_MTS_WATERFALL_TOP_5: ChestTreasure(0x35),
        TID.DENADORO_MTS_ENTRANCE_1: ChestTreasure(0x36),
        TID.DENADORO_MTS_ENTRANCE_2: ChestTreasure(0x37),
        TID.DENADORO_MTS_SCREEN3_1: ChestTreasure(0x38),
        TID.DENADORO_MTS_SCREEN3_2: ChestTreasure(0x39),
        TID.DENADORO_MTS_SCREEN3_3: ChestTreasure(0x3A),
        TID.DENADORO_MTS_SCREEN3_4: ChestTreasure(0x3B),
        TID.DENADORO_MTS_AMBUSH: ChestTreasure(0x3C),
        TID.DENADORO_MTS_SAVE_PT: ChestTreasure(0x3D),
        TID.FIONAS_HOUSE_1: ChestTreasure(0x3E),
        TID.FIONAS_HOUSE_2: ChestTreasure(0x3F),
        # Block of non-Chronosanity chests
        TID.SUNKEN_DESERT_B1_NW: ChestTreasure(0x40),
        TID.SUNKEN_DESERT_B1_NE: ChestTreasure(0x41),
        TID.SUNKEN_DESERT_B1_SE: ChestTreasure(0x42),
        TID.SUNKEN_DESERT_B1_SW: ChestTreasure(0x43),
        TID.SUNKEN_DESERT_B2_NW: ChestTreasure(0x44),
        TID.SUNKEN_DESERT_B2_N: ChestTreasure(0x45),
        TID.SUNKEN_DESERT_B2_E: ChestTreasure(0x46),
        TID.SUNKEN_DESERT_B2_SE: ChestTreasure(0x47),
        TID.SUNKEN_DESERT_B2_SW: ChestTreasure(0x48),
        TID.SUNKEN_DESERT_B2_W: ChestTreasure(0x49),
        TID.SUNKEN_DESERT_B2_CENTER: ChestTreasure(0x4A),
        TID.MAGUS_CASTLE_GUILLOTINE_1: ChestTreasure(0x4B),
        TID.MAGUS_CASTLE_GUILLOTINE_2: ChestTreasure(0x4C),
        TID.MAGUS_CASTLE_SLASH_ROOM_1: ChestTreasure(0x4D),
        TID.MAGUS_CASTLE_SLASH_ROOM_2: ChestTreasure(0x4E),
        TID.MAGUS_CASTLE_STATUE_HALL: ChestTreasure(0x4F),
        # Actually inaccessible
        # TID.MAGUS_CASTLE_FOUR_KIDS: ChestTreasure(0x50),
        TID.MAGUS_CASTLE_OZZIE_1: ChestTreasure(0x51),
        TID.MAGUS_CASTLE_OZZIE_2: ChestTreasure(0x52),
        TID.MAGUS_CASTLE_ENEMY_ELEVATOR: ChestTreasure(0x53),
        # end non-CS block
        TID.OZZIES_FORT_GUILLOTINES_1: ChestTreasure(0x54),
        TID.OZZIES_FORT_GUILLOTINES_2: ChestTreasure(0x55),
        TID.OZZIES_FORT_GUILLOTINES_3: ChestTreasure(0x56),
        TID.OZZIES_FORT_GUILLOTINES_4: ChestTreasure(0x57),
        TID.OZZIES_FORT_FINAL_1: ChestTreasure(0x58),
        TID.OZZIES_FORT_FINAL_2: ChestTreasure(0x59),
        TID.GIANTS_CLAW_CAVES_1: ChestTreasure(0x5A),
        TID.GIANTS_CLAW_CAVES_2: ChestTreasure(0x5B),
        TID.GIANTS_CLAW_CAVES_3: ChestTreasure(0x5C),
        TID.GIANTS_CLAW_CAVES_4: ChestTreasure(0x5D),
        TID.GIANTS_CLAW_ROCK: ChestTreasure(0x5E),
        TID.GIANTS_CLAW_CAVES_5: ChestTreasure(0x5F),
        TID.YAKRAS_ROOM: ChestTreasure(0x60),
        TID.MANORIA_SHRINE_SIDEROOM_1: ChestTreasure(0x61),
        TID.MANORIA_SHRINE_SIDEROOM_2: ChestTreasure(0x62),
        TID.MANORIA_BROMIDE_1: ChestTreasure(0x63),
        TID.MANORIA_BROMIDE_2: ChestTreasure(0x64),
        TID.MANORIA_BROMIDE_3: ChestTreasure(0x65),
        TID.MANORIA_SHRINE_MAGUS_1: ChestTreasure(0x66),
        TID.MANORIA_SHRINE_MAGUS_2: ChestTreasure(0x67),
        TID.BANGOR_DOME_SEAL_1: ChestTreasure(0x68),
        TID.BANGOR_DOME_SEAL_2: ChestTreasure(0x69),
        TID.BANGOR_DOME_SEAL_3: ChestTreasure(0x6A),
        TID.TRANN_DOME_SEAL_1: ChestTreasure(0x6B),
        TID.TRANN_DOME_SEAL_2: ChestTreasure(0x6C),
        TID.LAB_16_1: ChestTreasure(0x6D),
        TID.LAB_16_2: ChestTreasure(0x6E),
        TID.LAB_16_3: ChestTreasure(0x6F),
        TID.LAB_16_4: ChestTreasure(0x70),
        TID.ARRIS_DOME_RATS: ChestTreasure(0x71),
        TID.ARRIS_DOME_SEAL_1: ChestTreasure(0x72),
        TID.ARRIS_DOME_SEAL_2: ChestTreasure(0x73),
        TID.ARRIS_DOME_SEAL_3: ChestTreasure(0x74),
        TID.ARRIS_DOME_SEAL_4: ChestTreasure(0x75),
        # Non-CS
        TID.REPTITE_LAIR_SECRET_B2_NE_RIGHT: ChestTreasure(0x76),
        #
        TID.LAB_32_1: ChestTreasure(0x77),
        # Non-CS
        TID.LAB_32_RACE_LOG: ChestTreasure(0x78),
        # end non-cs
        TID.FACTORY_LEFT_AUX_CONSOLE: ChestTreasure(0x79),
        TID.FACTORY_LEFT_SECURITY_RIGHT: ChestTreasure(0x7A),
        TID.FACTORY_LEFT_SECURITY_LEFT: ChestTreasure(0x7B),
        TID.FACTORY_RIGHT_FLOOR_TOP: ChestTreasure(0x7C),
        TID.FACTORY_RIGHT_FLOOR_LEFT: ChestTreasure(0x7D),
        TID.FACTORY_RIGHT_FLOOR_BOTTOM: ChestTreasure(0x7E),
        TID.FACTORY_RIGHT_FLOOR_SECRET: ChestTreasure(0x7F),
        TID.FACTORY_RIGHT_CRANE_UPPER: ChestTreasure(0x80),
        TID.FACTORY_RIGHT_CRANE_LOWER: ChestTreasure(0x81),
        TID.FACTORY_RIGHT_INFO_ARCHIVE: ChestTreasure(0x82),
        # Non-CS
        TID.FACTORY_RUINS_GENERATOR: ChestTreasure(0x83),
        # end non-cs
        TID.SEWERS_1: ChestTreasure(0x84),
        TID.SEWERS_2: ChestTreasure(0x85),
        TID.SEWERS_3: ChestTreasure(0x86),
        # Non-CS
        TID.DEATH_PEAK_SOUTH_FACE_KRAKKER: ChestTreasure(0x87),
        TID.DEATH_PEAK_SOUTH_FACE_SPAWN_SAVE: ChestTreasure(0x88),
        TID.DEATH_PEAK_SOUTH_FACE_SUMMIT: ChestTreasure(0x89),
        TID.DEATH_PEAK_FIELD: ChestTreasure(0x8A),
        # End Non-CS block
        TID.GENO_DOME_1F_1: ChestTreasure(0x8B),
        TID.GENO_DOME_1F_2: ChestTreasure(0x8C),
        TID.GENO_DOME_1F_3: ChestTreasure(0x8D),
        TID.GENO_DOME_1F_4: ChestTreasure(0x8E),
        TID.GENO_DOME_ROOM_1: ChestTreasure(0x8F),
        TID.GENO_DOME_ROOM_2: ChestTreasure(0x90),
        TID.GENO_DOME_PROTO4_1: ChestTreasure(0x91),
        TID.GENO_DOME_PROTO4_2: ChestTreasure(0x92),
        TID.FACTORY_RIGHT_DATA_CORE_1: ChestTreasure(0x93),
        TID.FACTORY_RIGHT_DATA_CORE_2: ChestTreasure(0x94),
        # Non-CS
        TID.DEATH_PEAK_KRAKKER_PARADE: ChestTreasure(0x95),
        TID.DEATH_PEAK_CAVES_LEFT: ChestTreasure(0x96),
        TID.DEATH_PEAK_CAVES_CENTER: ChestTreasure(0x97),
        TID.DEATH_PEAK_CAVES_RIGHT: ChestTreasure(0x98),
        # End Non-CS block
        TID.GENO_DOME_2F_1: ChestTreasure(0x99),
        TID.GENO_DOME_2F_2: ChestTreasure(0x9A),
        TID.GENO_DOME_2F_3: ChestTreasure(0x9B),
        TID.GENO_DOME_2F_4: ChestTreasure(0x9C),
        TID.MYSTIC_MT_STREAM: ChestTreasure(0x9D),
        TID.FOREST_MAZE_1: ChestTreasure(0x9E),
        TID.FOREST_MAZE_2: ChestTreasure(0x9F),
        TID.FOREST_MAZE_3: ChestTreasure(0xA0),
        TID.FOREST_MAZE_4: ChestTreasure(0xA1),
        TID.FOREST_MAZE_5: ChestTreasure(0xA2),
        TID.FOREST_MAZE_6: ChestTreasure(0xA3),
        TID.FOREST_MAZE_7: ChestTreasure(0xA4),
        TID.FOREST_MAZE_8: ChestTreasure(0xA5),
        TID.FOREST_MAZE_9: ChestTreasure(0xA6),
        # Non-CS
        TID.REPTITE_LAIR_SECRET_B1_SW: ChestTreasure(0xA7),
        TID.REPTITE_LAIR_SECRET_B1_NE: ChestTreasure(0xA8),
        TID.REPTITE_LAIR_SECRET_B1_SE: ChestTreasure(0xA9),
        TID.REPTITE_LAIR_SECRET_B2_SE_RIGHT: ChestTreasure(0xAA),
        TID.REPTITE_LAIR_SECRET_B2_NE_OR_SE_LEFT: ChestTreasure(0xAB),
        TID.REPTITE_LAIR_SECRET_B2_SW: ChestTreasure(0xAC),
        # End non-CS block
        TID.REPTITE_LAIR_REPTITES_1: ChestTreasure(0xAD),
        TID.REPTITE_LAIR_REPTITES_2: ChestTreasure(0xAE),
        TID.DACTYL_NEST_1: ChestTreasure(0xAF),
        TID.DACTYL_NEST_2: ChestTreasure(0xB0),
        TID.DACTYL_NEST_3: ChestTreasure(0xB1),
        # Non-CS
        TID.TYRANO_LAIR_THRONE_1: ChestTreasure(0xB2),
        TID.TYRANO_LAIR_THRONE_2: ChestTreasure(0xB3),
        # TYRANO_LAIR_THRONE: 0xB4 (Unused?)
        TID.TYRANO_LAIR_TRAPDOOR: ChestTreasure(0xB5),
        TID.TYRANO_LAIR_KINO_CELL: ChestTreasure(0xB6),
        # TYRANO_LAIR Unused? : 0xB7
        TID.TYRANO_LAIR_MAZE_1: ChestTreasure(0xB8),
        TID.TYRANO_LAIR_MAZE_2: ChestTreasure(0xB9),
        TID.TYRANO_LAIR_MAZE_3: ChestTreasure(0xBA),
        TID.TYRANO_LAIR_MAZE_4: ChestTreasure(0xBB),
        # 0xBC - 0xCF - BLACK_OMEN
        TID.BLACK_OMEN_AUX_COMMAND_MID: ChestTreasure(0xBC),
        TID.BLACK_OMEN_AUX_COMMAND_NE: ChestTreasure(0xBD),
        TID.BLACK_OMEN_GRAND_HALL: ChestTreasure(0xBE),
        TID.BLACK_OMEN_NU_HALL_NW: ChestTreasure(0xBF),
        TID.BLACK_OMEN_NU_HALL_W: ChestTreasure(0xC0),
        TID.BLACK_OMEN_NU_HALL_SW: ChestTreasure(0xC1),
        TID.BLACK_OMEN_NU_HALL_NE: ChestTreasure(0xC2),
        TID.BLACK_OMEN_NU_HALL_E: ChestTreasure(0xC3),
        TID.BLACK_OMEN_NU_HALL_SE: ChestTreasure(0xC4),
        TID.BLACK_OMEN_ROYAL_PATH: ChestTreasure(0xC5),
        TID.BLACK_OMEN_RUMINATOR_PARADE: ChestTreasure(0xC6),
        TID.BLACK_OMEN_EYEBALL_HALL: ChestTreasure(0xC7),
        TID.BLACK_OMEN_TUBSTER_FLY: ChestTreasure(0xC8),
        TID.BLACK_OMEN_MARTELLO: ChestTreasure(0xC9),
        TID.BLACK_OMEN_ALIEN_SW: ChestTreasure(0xCA),
        TID.BLACK_OMEN_ALIEN_NE: ChestTreasure(0xCB),
        TID.BLACK_OMEN_ALIEN_NW: ChestTreasure(0xCC),
        TID.BLACK_OMEN_TERRA_W: ChestTreasure(0xCD),
        TID.BLACK_OMEN_TERRA_ROCK: ChestTreasure(0xCE),
        TID.BLACK_OMEN_TERRA_NE: ChestTreasure(0xCF),
        # end non-cs
        TID.ARRIS_DOME_FOOD_STORE: ChestTreasure(0xD0),
        TID.MT_WOE_2ND_SCREEN_1: ChestTreasure(0xD1),
        TID.MT_WOE_2ND_SCREEN_2: ChestTreasure(0xD2),
        TID.MT_WOE_2ND_SCREEN_3: ChestTreasure(0xD3),
        TID.MT_WOE_2ND_SCREEN_4: ChestTreasure(0xD4),
        TID.MT_WOE_2ND_SCREEN_5: ChestTreasure(0xD5),
        TID.MT_WOE_3RD_SCREEN_1: ChestTreasure(0xD6),
        TID.MT_WOE_3RD_SCREEN_2: ChestTreasure(0xD7),
        TID.MT_WOE_3RD_SCREEN_3: ChestTreasure(0xD8),
        TID.MT_WOE_3RD_SCREEN_4: ChestTreasure(0xD9),
        TID.MT_WOE_3RD_SCREEN_5: ChestTreasure(0xDA),
        TID.MT_WOE_1ST_SCREEN: ChestTreasure(0xDB),
        TID.MT_WOE_FINAL_1: ChestTreasure(0xDC),
        TID.MT_WOE_FINAL_2: ChestTreasure(0xDD),
        # Non-cs
        TID.OCEAN_PALACE_MAIN_S: ChestTreasure(0xDE),
        TID.OCEAN_PALACE_MAIN_N: ChestTreasure(0xDF),
        TID.OCEAN_PALACE_W_ROOM: ChestTreasure(0xE0),
        TID.OCEAN_PALACE_E_ROOM: ChestTreasure(0xE1),
        TID.OCEAN_PALACE_SWITCH_NW: ChestTreasure(0xE2),
        TID.OCEAN_PALACE_SWITCH_SW: ChestTreasure(0xE3),
        TID.OCEAN_PALACE_SWITCH_NE: ChestTreasure(0xE4),
        TID.OCEAN_PALACE_SWITCH_SECRET: ChestTreasure(0xE5),
        TID.OCEAN_PALACE_FINAL: ChestTreasure(0xE6),
        # end non-cs
        # FACTORY_RUINS_UNUSED: 0xE7
        TID.GUARDIA_TREASURY_1: ChestTreasure(0xE8),
        TID.GUARDIA_TREASURY_2: ChestTreasure(0xE9),
        TID.GUARDIA_TREASURY_3: ChestTreasure(0xEA),
        TID.QUEENS_TOWER_600: ChestTreasure(0xEB),
        # Non-cs block
        TID.MAGUS_CASTLE_LEFT_HALL: ChestTreasure(0xEC),
        TID.MAGUS_CASTLE_UNSKIPPABLES: ChestTreasure(0xED),
        TID.MAGUS_CASTLE_PIT_E: ChestTreasure(0xEE),
        TID.MAGUS_CASTLE_PIT_NE: ChestTreasure(0xEF),
        TID.MAGUS_CASTLE_PIT_NW: ChestTreasure(0xF0),
        TID.MAGUS_CASTLE_PIT_W: ChestTreasure(0xF1),
        # end non-cs
        TID.KINGS_TOWER_600: ChestTreasure(0xF2),
        TID.KINGS_TOWER_1000: ChestTreasure(0xF3),
        TID.QUEENS_TOWER_1000: ChestTreasure(0xF4),
        TID.GUARDIA_COURT_TOWER: ChestTreasure(0xF5),
        TID.PRISON_TOWER_1000: ChestTreasure(0xF6),
        # GIANTS_CLAW_MAZE Unused: 0xF7
        # DEATH_PEAK_CLIFF Unused: 0xF8
        # Script Chests:
        # Weirdness with Northern Ruins.
        # There's a variable set, only for these
        # locations indicating whether you're in the
        #   0x7F10A3 & 0x10 ->  600
        #   0x7F10A3 & 0x20 -> 1000
        TID.NORTHERN_RUINS_BASEMENT_600: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_BASEMENT,
            object_id=0x08,
            function_id=0x01,
            item_num=1,
        ),
        # Frog locked one
        TID.NORTHERN_RUINS_BASEMENT_1000: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_BASEMENT,
            object_id=0x08,
            function_id=0x01,
            item_num=0,
        ),
        TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_ANTECHAMBER,
            object_id=0x08,
            function_id=0x01,
            item_num=0,
        ),
        TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_ANTECHAMBER,
            object_id=0x08,
            function_id=0x01,
            item_num=1,
        ),
        TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_ANTECHAMBER,
            object_id=0x10,
            function_id=0x01,
            item_num=0,
        ),
        TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600: ChargeableTreasure(
            location=LocID.NORTHERN_RUINS_ANTECHAMBER,
            object_id=0x10,
            function_id=0x01,
            item_num=1,
        ),
        TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_BACK_ROOM,
            object_id=0x10,
            function_id=0x01,
            item_num=0,
        ),
        TID.NORTHERN_RUINS_BACK_LEFT_SEALED_600: ChargeableTreasure(
            location=LocID.NORTHERN_RUINS_BACK_ROOM,
            object_id=0x10,
            function_id=0x01,
            item_num=1,
        ),
        TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_BACK_ROOM,
            object_id=0x11,
            function_id=0x01,
            item_num=0,
        ),
        TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600: ChargeableTreasure(
            location=LocID.NORTHERN_RUINS_BACK_ROOM,
            object_id=0x11,
            function_id=0x01,
            item_num=1,
        ),
        TID.TRUCE_INN_SEALED_600: SplitChargeableTreasure(
            LocID.TRUCE_INN_600_2F, 0x0C, FID.ACTIVATE,
            charge_location=LocID.TRUCE_INN_1000,
            charge_object_id=0x11,
            charge_function_id=FID.ACTIVATE,
        ),
        TID.TRUCE_INN_SEALED_1000: ScriptTreasure(
            location=LocID.TRUCE_INN_1000, object_id=0x11, function_id=0x01
        ),
        TID.PYRAMID_LEFT: ScriptTreasure(
            location=LocID.FOREST_RUINS, object_id=0x13, function_id=0x01
        ),
        TID.PYRAMID_RIGHT: ScriptTreasure(
            location=LocID.FOREST_RUINS, object_id=0x14, function_id=0x01
        ),
        TID.PORRE_ELDER_SEALED_1: SplitChargeableTreasure(
            LocID.PORRE_ELDER, 0x0D, FID.ACTIVATE,
            charge_location=LocID.PORRE_MAYOR_2F,
            charge_object_id=0x9,
            charge_function_id=FID.ACTIVATE
        ),
        TID.PORRE_ELDER_SEALED_2: SplitChargeableTreasure(
            LocID.PORRE_ELDER, 0x0E, FID.ACTIVATE,
            charge_location=LocID.PORRE_MAYOR_2F,
            charge_object_id=0xA,
            charge_function_id=FID.ACTIVATE
        ),
        TID.PORRE_MAYOR_SEALED_1: ScriptTreasure(
            location=LocID.PORRE_MAYOR_2F, object_id=0x09, function_id=0x01
        ),
        TID.PORRE_MAYOR_SEALED_2: ScriptTreasure(
            location=LocID.PORRE_MAYOR_2F, object_id=0x0A, function_id=0x01
        ),
        TID.GUARDIA_CASTLE_SEALED_600: SplitChargeableTreasure(
            LocID.GUARDIA_KINGS_TOWER_600, 0x08, FID.ACTIVATE,
            charge_location=LocID.GUARDIA_KINGS_TOWER_1000,
            charge_object_id=0x8,
            charge_function_id=FID.ACTIVATE
        ),
        TID.GUARDIA_FOREST_SEALED_600: ScriptTreasure(
            location=LocID.GUARDIA_FOREST_600,
            object_id=0x3E - 6,  # removed some objects from forest
            function_id=0x01,
        ),
        TID.GUARDIA_FOREST_SEALED_1000: ScriptTreasure(
            location=LocID.GUARDIA_FOREST_DEAD_END, object_id=0x12, function_id=0x01
        ),
        TID.GUARDIA_CASTLE_SEALED_1000: ScriptTreasure(
            location=LocID.GUARDIA_KINGS_TOWER_1000, object_id=0x08, function_id=0x01
        ),
        TID.HECKRAN_SEALED_1: ScriptTreasure(
            location=LocID.HECKRAN_CAVE_PASSAGEWAYS,
            object_id=0x0C,
            function_id=0x01,
            item_num=0,
        ),
        TID.HECKRAN_SEALED_2: ScriptTreasure(
            location=LocID.HECKRAN_CAVE_PASSAGEWAYS,
            object_id=0x0C,
            function_id=0x01,
            item_num=1,
        ),
        TID.MAGIC_CAVE_SEALED: ScriptTreasure(
            location=LocID.MAGIC_CAVE_INTERIOR, object_id=0x19, function_id=0x01
        ),
        # Key Items
        TID.REPTITE_LAIR_KEY: SpriteScriptTreasure(
            LocID.REPTITE_LAIR_AZALA_ROOM, object_id=0x00, function_id=0x00,
            sprite_object_id=0xC
        ),
        TID.MELCHIOR_RAINBOW_SHELL: ScriptTreasure(
            LocID.GUARDIA_REAR_STORAGE, 0x17, FID.ACTIVATE, item_num=0
        ),
        TID.MELCHIOR_SUNSTONE_RAINBOW: ScriptTreasure(
            LocID.GUARDIA_REAR_STORAGE, 0x17, FID.ACTIVATE, item_num=1
        ),
        TID.MELCHIOR_SUNSTONE_SPECS: ScriptTreasure(
            LocID.GUARDIA_REAR_STORAGE, 0x17, FID.ACTIVATE, item_num=2
        ),
        TID.FROGS_BURROW_LEFT: ScriptTreasure(
            location=LocID.FROGS_BURROW, object_id=0x0A, function_id=0x01
        ),
        TID.MT_WOE_KEY: ScriptTreasure(
            location=LocID.MT_WOE_SUMMIT, object_id=0x08, function_id=0x01
        ),
        TID.FIONA_KEY: ScriptTreasure(LocID.FIONA_FOREST, 0x01, FID.ARBITRARY_4),
        TID.ARRIS_DOME_DOAN_KEY: ScriptTreasure(
            location=LocID.ARRIS_DOME, object_id=0x0F, function_id=0x2
        ),
        TID.SUN_PALACE_KEY: ScriptTreasure(
            location=LocID.SUN_PALACE, object_id=0x11, function_id=0x01
        ),
        TID.GENO_DOME_BOSS_1: ScriptTreasure(
            location=LocID.GENO_DOME_MAINFRAME,
            object_id=0x00,
            function_id=FID.ARBITRARY_3,
            item_num=0,
        ),
        TID.GENO_DOME_BOSS_2: ScriptTreasure(
            location=LocID.GENO_DOME_MAINFRAME,
            object_id=0x00,
            function_id=FID.ARBITRARY_3,
            item_num=1,
        ),
        TID.GIANTS_CLAW_KEY: ScriptTreasure(
            location=LocID.GIANTS_CLAW_TYRANO, object_id=0x01, function_id=FID.STARTUP
        ),
        TID.KINGS_TRIAL_KEY: PrismShardTreasure(
            location=LocID.GUARDIA_REAR_STORAGE, object_id=0x02, function_id=0x03
        ),
        TID.ZENAN_BRIDGE_CHEF: ScriptTreasure(
            LocID.GUARDIA_THRONEROOM_600, 0x0F, FID.STARTUP
        ),
        TID.ZENAN_BRIDGE_CHEF_TAB: ScriptTreasure(
            LocID.GUARDIA_THRONEROOM_600, 0x0F, FID.STARTUP, item_num=1
        ),
        TID.ZENAN_BRIDGE_CAPTAIN: ScriptTreasure(
            LocID.ZENAN_BRIDGE_BOSS, object_id=0x1, function_id=FID.STARTUP
        ),
        TID.SNAIL_STOP_KEY: ScriptTreasure(
            LocID.SNAIL_STOP, object_id=0x09, function_id=0x01
        ),
        TID.LAZY_CARPENTER: ScriptTreasure(
            LocID.CHORAS_CARPENTER_1000, object_id=0x08, function_id=0x01
        ),
        TID.TABAN_GIFT_VEST: ScriptTreasure(
            LocID.LUCCAS_WORKSHOP, object_id=0x08, function_id=0x01, item_num=2
        ),
        TID.DENADORO_MTS_KEY: MasaMuneTreasure(
            location=LocID.DENADORO_CAVE_OF_MASAMUNE,
            object_id=0x0A,
            function_id=FID.TOUCH,
        ),
        # Other Script Treasures
        TID.TABAN_GIFT_HELM: ScriptTreasure(
            LocID.LUCCAS_WORKSHOP, object_id=0x08, function_id=0x01, item_num=1
        ),
        TID.TABAN_GIFT_SUIT: ScriptTreasure(
            LocID.LUCCAS_WORKSHOP, object_id=0x08, function_id=0x01, item_num=0
        ),
        # TID.TRADING_POST_RANGED_WEAPON: ScriptTreasure(
        #     location=LocID.IOKA_TRADING_POST,
        #     object_id=0x0C,
        #     function_id=0x04,
        #     item_num=0,
        # ),
        # TID.TRADING_POST_ACCESSORY: ScriptTreasure(
        #     location=LocID.IOKA_TRADING_POST,
        #     object_id=0x0C,
        #     function_id=0x04,
        #     item_num=1,
        # ),
        # TID.TRADING_POST_TAB: ScriptTreasure(
        #     location=LocID.IOKA_TRADING_POST,
        #     object_id=0x0C,
        #     function_id=0x04,
        #     item_num=2,
        # ),
        # TID.TRADING_POST_MELEE_WEAPON: ScriptTreasure(
        #     location=LocID.IOKA_TRADING_POST,
        #     object_id=0x0C,
        #     function_id=0x04,
        #     item_num=3,
        # ),
        # TID.TRADING_POST_ARMOR: ScriptTreasure(
        #     location=LocID.IOKA_TRADING_POST,
        #     object_id=0x0C,
        #     function_id=0x04,
        #     item_num=4,
        # ),
        # TID.TRADING_POST_HELM: ScriptTreasure(
        #     location=LocID.IOKA_TRADING_POST,
        #     object_id=0x0C,
        #     function_id=0x04,
        #     item_num=5,
        # ),
        TID.JERKY_GIFT: ScriptTreasure(
            location=LocID.PORRE_MAYOR_1F, object_id=0x08, function_id=0x01, item_num=0
        ),
        TID.DENADORO_ROCK: ScriptTreasure(
            location=LocID.DENADORO_CAVE_OF_MASAMUNE_EXTERIOR,
            object_id=0x04,
            function_id=FID.ARBITRARY_3,
        ),
        TID.LARUBA_ROCK: ScriptTreasure(
            location=LocID.LARUBA_RUINS, object_id=0x0D, function_id=0x01
        ),
        TID.KAJAR_ROCK: ScriptTreasure(
            location=LocID.KAJAR_ROCK_ROOM, object_id=0x08, function_id=0x01
        ),
        TID.BEKKLER_KEY: BekklerTreasure(
            location=LocID.CRONOS_ROOM,
            object_id=0x13,
            function_id=1,
            item_num=0,
            bekkler_location=LocID.BEKKLERS_LAB,
            bekkler_object_id=0xB,
            bekkler_function_id=1,
        ),
        TID.CYRUS_GRAVE_KEY: ScriptTreasure(
            location=LocID.NORTHERN_RUINS_HEROS_GRAVE,
            object_id=5,
            function_id=FID.ARBITRARY_5,
            item_num=0,
        ),
        TID.SUN_KEEP_2300: ScriptTreasure(LocID.SUN_KEEP_2300, 8, 1),
        TID.ARRIS_DOME_FOOD_LOCKER_KEY: ScriptTreasure(
            LocID.ARRIS_DOME_FOOD_LOCKER, 8, FID.ACTIVATE
        ),
        TID.LUCCA_WONDERSHOT: ScriptTreasure(
            LocID.LUCCAS_WORKSHOP, 3, FID.ARBITRARY_1, item_num=0
        ),
        TID.TABAN_SUNSHADES: ScriptTreasure(
            LocID.LUCCAS_WORKSHOP, 3, FID.ARBITRARY_1, item_num=1
        ),
        TID.TATA_REWARD: ScriptTreasure(LocID.TATAS_HOUSE_1F, 9, FID.ACTIVATE),
        TID.TOMA_REWARD: ScriptTreasure(LocID.CHORAS_CAFE, 0xD, FID.ACTIVATE),
        TID.MELCHIOR_FORGE_MASA: ScriptTreasure(
            LocID.MELCHIORS_KITCHEN, 8, FID.ACTIVATE
        ),
        TID.EOT_GASPAR_REWARD: ScriptTreasure(
            LocID.END_OF_TIME, 0x1C, FID.ACTIVATE
        ),
        TID.FAIR_PENDANT: SpriteScriptTreasure(
            LocID.LEENE_SQUARE, 0xF, FID.ACTIVATE
        ),
        TID.HUNTING_RANGE_NU_REWARD: HuntingRangeNuTreasure(
            LocID.HUNTING_RANGE, 4, FID.STARTUP
        ),
        TID.ZEAL_MAMMON_MACHINE: ScriptTreasure(
            LocID.ZEAL_PALACE_HALL_OF_MAMMON, 0x10, FID.ACTIVATE
        ),
        TID.MAGUS_CASTLE_FOUR_KIDS: ScriptTreasure(
            LocID.MAGUS_CASTLE_HALL_DECEIT, 9, FID.ACTIVATE
        ),
        TID.MAGUS_CASTLE_SLASH_SWORD_FLOOR: ScriptTreasure(
            LocID.MAGUS_CASTLE_SLASH, 0xA, FID.ACTIVATE
        ),
        TID.GUARDIA_PRISON_LUNCH_BAG: ScriptTreasure(
            LocID.PRISON_CELLS, 0x29,FID.ACTIVATE
        ),
        # Tabs later if they're going to be randomized
        TID.DORINO_BROMIDE_MAGIC_TAB: ScriptTreasure(
            location=LocID.DORINO_PERVERT_RESIDENCE,
            object_id=0xC,
            function_id=FID.ACTIVATE,
        ),
        TID.GUARDIA_FOREST_POWER_TAB_600: ScriptTreasure(
            location=LocID.GUARDIA_FOREST_600,
            object_id=0x3F - 6,  # Removed objects vs vanilla
            function_id=FID.ACTIVATE,
        ),
        TID.GUARDIA_FOREST_POWER_TAB_1000: ScriptTreasure(
            location=LocID.GUARDIA_FOREST_1000, object_id=0x29, function_id=FID.ACTIVATE
        ),
        TID.MANORIA_CONFINEMENT_POWER_TAB: ScriptTreasure(
            location=LocID.MANORIA_CONFINEMENT, object_id=0xA, function_id=FID.ACTIVATE
        ),
        TID.PORRE_MARKET_600_POWER_TAB: ScriptTreasure(
            location=LocID.PORRE_MARKET_600, object_id=0xC, function_id=FID.ACTIVATE
        ),
        TID.DENADORO_MTS_SPEED_TAB: ScriptTreasure(
            location=LocID.DENADORO_WEST_FACE, object_id=9, function_id=FID.ACTIVATE
        ),
        TID.TOMAS_GRAVE_SPEED_TAB: ScriptTreasure(
            location=LocID.WEST_CAPE, object_id=8, function_id=FID.ACTIVATE
        ),
        TID.GIANTS_CLAW_CAVERNS_POWER_TAB: ScriptTreasure(
            location=LocID.GIANTS_CLAW_CAVERNS, object_id=0xD, function_id=FID.ACTIVATE
        ),
        TID.GIANTS_CLAW_ENTRANCE_POWER_TAB: ScriptTreasure(
            location=LocID.GIANTS_CLAW_LAIR_ENTRANCE,
            object_id=0xB,
            function_id=FID.ACTIVATE,
        ),
        TID.GIANTS_CLAW_TRAPS_POWER_TAB: ScriptTreasure(
            location=LocID.ANCIENT_TYRANO_LAIR_TRAPS,
            object_id=0x15,
            function_id=FID.ACTIVATE,
        ),
        TID.SUN_KEEP_600_POWER_TAB: ScriptTreasure(
            location=LocID.SUN_KEEP_600, object_id=0xA, function_id=FID.ACTIVATE
        ),
        TID.MEDINA_ELDER_SPEED_TAB: ScriptTreasure(
            location=LocID.MEDINA_ELDER_1F, object_id=0xC, function_id=FID.ACTIVATE
        ),
        TID.MEDINA_ELDER_MAGIC_TAB: ScriptTreasure(
            location=LocID.MEDINA_ELDER_2F, object_id=9, function_id=FID.ACTIVATE
        ),
        TID.MAGUS_CASTLE_FLEA_MAGIC_TAB: ScriptTreasure(
            location=LocID.MAGUS_CASTLE_FLEA, object_id=0xD, function_id=FID.ACTIVATE
        ),
        TID.MAGUS_CASTLE_DUNGEONS_MAGIC_TAB: ScriptTreasure(
            LocID.MAGUS_CASTLE_DUNGEON, 8, FID.ACTIVATE
        ),
        TID.TRANN_DOME_SEALED_MAGIC_TAB: ScriptTreasure(
            LocID.TRANN_DOME_SEALED_ROOM, 8, FID.ACTIVATE
        ),
        TID.ARRIS_DOME_SEALED_POWER_TAB: ScriptTreasure(
            LocID.ARRIS_DOME_SEALED_ROOM, 8, FID.ACTIVATE
        ),
        TID.DEATH_PEAK_POWER_TAB: ScriptTreasure(
            LocID.DEATH_PEAK_ENTRANCE, 0xA, FID.ACTIVATE
        ),
        TID.BLACKBIRD_DUCTS_MAGIC_TAB: ScriptTreasure(
            LocID.BLACKBIRD_DUCTS, 9, FID.ACTIVATE
        ),
        TID.KEEPERS_DOME_MAGIC_TAB: ScriptTreasure(
            LocID.KEEPERS_DOME_CORRIDOR, 0x12, FID.ACTIVATE
        ),
        TID.GENO_DOME_ATROPOS_MAGIC_TAB: ScriptTreasure(
            LocID.GENO_DOME_MAINFRAME, 0x26, FID.ACTIVATE
        ),
        TID.GENO_DOME_CORRIDOR_POWER_TAB: ScriptTreasure(
            LocID.GENO_DOME_LONG_CORRIDOR, 8, FID.ACTIVATE
        ),
        TID.GENO_DOME_LABS_MAGIC_TAB: ScriptTreasure(
            LocID.GENO_DOME_LABS, 0x30, FID.ACTIVATE
        ),
        TID.GENO_DOME_LABS_SPEED_TAB: ScriptTreasure(
            LocID.GENO_DOME_LABS, 0x32, FID.ACTIVATE
        ),
        TID.ENHASA_NU_BATTLE_MAGIC_TAB: ScriptTreasure(
            LocID.ENHASA_NU_ROOM, 0x8, FID.ACTIVATE, item_num=0
        ),
        TID.ENHASA_NU_BATTLE_SPEED_TAB: ScriptTreasure(
            LocID.ENHASA_NU_ROOM, 0x8, FID.ACTIVATE, item_num=1
        ),
        TID.KAJAR_SPEED_TAB: ScriptTreasure(LocID.KAJAR_MAGIC_LAB, 8, FID.ACTIVATE),
        TID.KAJAR_NU_SCRATCH_MAGIC_TAB: ScriptTreasure(
            LocID.KAJAR_MAGIC_LAB, 0x11, FID.ACTIVATE
        ),
        TID.LAST_VILLAGE_NU_SHOP_MAGIC_TAB: ScriptTreasure(
            LocID.LAST_VILLAGE_SHOP,0xA, FID.ACTIVATE
        ),
        TID.SUNKEN_DESERT_POWER_TAB: ScriptTreasure(
            LocID.SUNKEN_DESERT_PARASITES, 0xD, FID.ACTIVATE
        ),
        TID.MOUNTAINS_RE_NICE_MAGIC_TAB: ScriptTreasure(
            LocID.DENADORO_MTN_VISTA, 0xD, FID.ACTIVATE
        ),
        TID.BEAST_NEST_POWER_TAB: ScriptTreasure(
            LocID.BEAST_NEST, 9, FID.ACTIVATE
        ),
        TID.MT_WOE_MAGIC_TAB: ScriptTreasure(
            LocID.MT_WOE_UPPER_EASTERN_FACE, 9, FID.ACTIVATE
        ),
        TID.OCEAN_PALACE_ELEVATOR_MAGIC_TAB: ScriptTreasure(
            LocID.OCEAN_PALACE_EASTERN_ACCESS_LIFT, 8, FID.ACTIVATE
        ),
        TID.OZZIES_FORT_GUILLOTINES_TAB: ScriptTreasure(
            LocID.OZZIES_FORT_GUILLOTINE, 0xD, FID.ACTIVATE
        ),
        TID.PROTO_DOME_PORTAL_TAB: ScriptTreasure(
            LocID.PROTO_DOME_PORTAL, 0xD, FID.ACTIVATE
        ),
        TID.NORTHERN_RUINS_HEROS_GRAVE_MAGIC_TAB: ScriptTreasure(
            LocID.NORTHERN_RUINS_HEROS_GRAVE, 0xF, FID.ACTIVATE
        ),
        TID.NORTHERN_RUINS_LANDING_POWER_TAB: ScriptTreasure(
            LocID.NORTHERN_RUINS_LANDING, 8, FID.ACTIVATE
        ),
        TID.CRONOS_MOM: ScriptTreasure(
            LocID.CRONOS_KITCHEN, 0xF, FID.TOUCH
        ),
        TID.TRUCE_MAYOR_2F_OLD_MAN: ScriptTreasure(
            LocID.TRUCE_MAYOR_2F, 8, FID.ACTIVATE
        ),
        TID.IOKA_SWEETWATER_TONIC: ScriptTreasure(
            LocID.IOKA_SWEETWATER_HUT, 8, FID.ACTIVATE
        ),
        TID.DORINO_INN_POWERMEAL: ScriptTreasure(
            LocID.DORINO_INN, 0x1B, FID.ARBITRARY_0
        ),
        TID.YAKRA_KEY_CHEST: ScriptTreasure(
            LocID.GUARDIA_LAWGIVERS_TOWER, 0x08, FID.ACTIVATE,
        ),
        TID.COURTROOM_YAKRA_KEY: ScriptTreasure(
            LocID.KINGS_TRIAL, 0x19, FID.ACTIVATE
        ),
        TID.JOHNNY_RACE_POWER_TAB: JohnnyRaceKeyItemTreasure(
            JohnnyRacePart(
                ctenums.LocID.LAB_32_WEST, 0xE, FID.ARBITRARY_2,
            ),
            JohnnyRacePart(
                ctenums.LocID.LAB_32_EAST, 0x0A, FID.ARBITRARY_2
            )
        ),
        TID.TRADING_POST_PETAL_FANG_BASE: TradingPostTreasure(3, True),
        TID.TRADING_POST_PETAL_FANG_UPGRADE: TradingPostTreasure(3, False),
        TID.TRADING_POST_PETAL_HORN_BASE: TradingPostTreasure(5, True),
        TID.TRADING_POST_PETAL_HORN_UPGRADE: TradingPostTreasure(5, False),
        TID.TRADING_POST_PETAL_FEATHER_BASE: TradingPostTreasure(9, True),
        TID.TRADING_POST_PETAL_FEATHER_UPGRADE: TradingPostTreasure(9, False),
        TID.TRADING_POST_FANG_HORN_BASE: TradingPostTreasure(6, True),
        TID.TRADING_POST_FANG_HORN_UPGRADE: TradingPostTreasure(6, False),
        TID.TRADING_POST_FANG_FEATHER_BASE: TradingPostTreasure(0xA, True),
        TID.TRADING_POST_FANG_FEATHER_UPGRADE: TradingPostTreasure(0xA, False),
        TID.TRADING_POST_HORN_FEATHER_BASE: TradingPostTreasure(0xC, True),
        TID.TRADING_POST_HORN_FEATHER_UPGRADE: TradingPostTreasure(0xC, False),
        TID.TRADING_POST_SPECIAL: TradingPostSpecialTreasure(),
    }

    return ret_dict


_treasure_count_dict: dict[ctenums.LocID, int] = {
    ctenums.LocID.LOAD_SCREEN: 1,
    ctenums.LocID.TRUCE_INN_1000: 1,
    ctenums.LocID.TRUCE_MAYOR_1F: 1,
    ctenums.LocID.TRUCE_MAYOR_2F: 1,
    ctenums.LocID.KINGS_CHAMBER_1000: 1,
    ctenums.LocID.QUEENS_ROOM_1000: 1,
    ctenums.LocID.GUARDIA_BASEMENT: 3,
    ctenums.LocID.PRISON_TORTURE_STORAGE_ROOM: 1,
    ctenums.LocID.FOREST_RUINS: 1,
    ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS: 1,
    ctenums.LocID.HECKRAN_CAVE_ENTRANCE: 1,
    ctenums.LocID.HECKRAN_CAVE_UNDERGROUND_RIVER: 2,
    ctenums.LocID.PORRE_MAYOR_2F: 1,
    ctenums.LocID.PRISON_CELLS: 8,
    ctenums.LocID.PRISON_STAIRWELLS: 1,
    ctenums.LocID.ANCIENT_TYRANO_LAIR: 1,
    ctenums.LocID.ANCIENT_TYRANO_LAIR_TRAPS: 1,
    ctenums.LocID.TRUCE_CANYON: 2,
    ctenums.LocID.KINGS_CHAMBER_600: 1,
    ctenums.LocID.QUEENS_ROOM_600: 1,
    ctenums.LocID.GUARDIA_KITCHEN_600: 1,
    ctenums.LocID.MAGUS_CASTLE_DOPPLEGANGER_CORRIDOR: 1,
    ctenums.LocID.MANORIA_MAIN_HALL: 3,
    ctenums.LocID.MANORIA_HEADQUARTERS: 4,
    ctenums.LocID.CURSED_WOODS: 2,
    ctenums.LocID.FROGS_BURROW: 1,
    ctenums.LocID.DENADORO_SOUTH_FACE: 3,
    ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE_EXTERIOR: 3,
    ctenums.LocID.DENADORO_NORTH_FACE: 5,
    ctenums.LocID.DENADORO_ENTRANCE: 2,
    ctenums.LocID.DENADORO_LOWER_EAST_FACE: 4,
    ctenums.LocID.DENADORO_UPPER_EAST_FACE: 1,
    ctenums.LocID.DENADORO_WEST_FACE: 1,
    ctenums.LocID.FIONAS_VILLA: 2,
    ctenums.LocID.SUNKEN_DESERT_PARASITES: 4,
    ctenums.LocID.SUNKEN_DESERT_DEVOURER: 7,
    ctenums.LocID.MAGUS_CASTLE_GUILLOTINES: 2,
    ctenums.LocID.MAGUS_CASTLE_SLASH: 2,
    ctenums.LocID.MAGUS_CASTLE_HALL_AGGRESSION: 1,
    ctenums.LocID.MAGUS_CASTLE_HALL_DECEIT: 1,
    ctenums.LocID.MAGUS_CASTLE_OZZIE: 2,
    ctenums.LocID.MAGUS_CASTLE_HALL_APPREHENSION: 1,
    ctenums.LocID.OZZIES_FORT_GUILLOTINE: 4,
    ctenums.LocID.OZZIES_FORT_LAST_STAND: 2,
    ctenums.LocID.GIANTS_CLAW_ENTRANCE: 2,
    ctenums.LocID.GIANTS_CLAW_CAVERNS: 4,
    ctenums.LocID.MANORIA_COMMAND: 1,
    ctenums.LocID.MANORIA_SHRINE_ANTECHAMBER: 2,
    ctenums.LocID.MANORIA_STORAGE: 3,
    ctenums.LocID.MANORIA_SHRINE: 2,
    ctenums.LocID.BANGOR_DOME_SEALED_ROOM: 3,
    ctenums.LocID.TRANN_DOME_SEALED_ROOM: 2,
    ctenums.LocID.LAB_16_WEST: 3,
    ctenums.LocID.LAB_16_EAST: 1,
    ctenums.LocID.ARRIS_DOME_INFESTATION: 1,
    ctenums.LocID.ARRIS_DOME_SEALED_ROOM: 4,
    ctenums.LocID.REPTITE_LAIR_2F: 1,
    ctenums.LocID.LAB_32_WEST: 1,
    ctenums.LocID.LAB_32: 1,
    ctenums.LocID.FACTORY_RUINS_AUXILIARY_CONSOLE: 1,
    ctenums.LocID.FACTORY_RUINS_SECURITY_CENTER: 2,
    ctenums.LocID.FACTORY_RUINS_CRANE_ROOM: 4,
    ctenums.LocID.FACTORY_RUINS_CRANE_CONTROL: 2,
    ctenums.LocID.FACTORY_RUINS_INFO_ARCHIVE: 1,
    ctenums.LocID.FACTORY_RUINS_POWER_CORE: 1,
    ctenums.LocID.SEWERS_B1: 3,
    ctenums.LocID.DEATH_PEAK_SOUTH_FACE: 3,
    ctenums.LocID.DEATH_PEAK_SOUTHEAST_FACE: 1,
    ctenums.LocID.GENO_DOME_LABS: 4,
    ctenums.LocID.GENO_DOME_STORAGE: 2,
    ctenums.LocID.GENO_DOME_ROBOT_HUB: 2,
    ctenums.LocID.FACTORY_RUINS_DATA_CORE: 2,
    ctenums.LocID.DEATH_PEAK_NORTHWEST_FACE: 1,
    ctenums.LocID.DEATH_PEAK_CAVE: 3,
    ctenums.LocID.GENO_DOME_MAINFRAME: 4,
    ctenums.LocID.MYSTIC_MTN_GULCH: 1,
    ctenums.LocID.FOREST_MAZE: 9,
    ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B1: 3,
    ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B2: 3,
    ctenums.LocID.REPTITE_LAIR_COMMONS: 2,
    ctenums.LocID.DACTYL_NEST_LOWER: 2,
    ctenums.LocID.DACTYL_NEST_UPPER: 1,
    ctenums.LocID.GIANTS_CLAW_LAIR_THRONEROOM: 2,
    ctenums.LocID.TYRANO_LAIR_THRONEROOM: 1,
    ctenums.LocID.TYRANO_LAIR_ANTECHAMBERS: 2,
    ctenums.LocID.TYRANO_LAIR_STORAGE: 1,
    ctenums.LocID.TYRANO_LAIR_ROOM_OF_VERTIGO: 4,
    ctenums.LocID.BLACK_OMEN_47F_AUX_COMMAND: 2,
    ctenums.LocID.BLACK_OMEN_47F_GRAND_HALL: 1,
    ctenums.LocID.BLACK_OMEN_47F_EMPORIUM: 6,
    ctenums.LocID.BLACK_OMEN_47F_ROYAL_PATH: 1,
    ctenums.LocID.BLACK_OMEN_47F_ROYAL_BALLROOM: 1,
    ctenums.LocID.BLACK_OMEN_47F_ROYAL_ASSEMBLY: 1,
    ctenums.LocID.BLACK_OMEN_47F_ROYAL_PROMENADE: 2,
    ctenums.LocID.BLACK_OMEN_63F_DIVINE_ESPLENADE: 3,
    ctenums.LocID.BLACK_OMEN_TERRA_MUTANT: 3,
    ctenums.LocID.ARRIS_DOME_FOOD_LOCKER: 1,
    ctenums.LocID.MT_WOE_WESTERN_FACE: 5,
    ctenums.LocID.MT_WOE_LOWER_EASTERN_FACE: 5,
    ctenums.LocID.MT_WOE_MIDDLE_EASTERN_FACE: 1,
    ctenums.LocID.MT_WOE_UPPER_EASTERN_FACE: 2,
    ctenums.LocID.OCEAN_PALACE_PIAZZA: 2,
    ctenums.LocID.OCEAN_PALACE_SIDE_ROOMS: 2,
    ctenums.LocID.OCEAN_PALACE_FORWARD_AREA: 4,
    ctenums.LocID.OCEAN_PALACE_SECURITY_ESPLANADE: 1,
    ctenums.LocID.FACTORY_RUINS_ROBOT_STORAGE: 1,
    ctenums.LocID.GUARDIA_REAR_STORAGE: 3,
    ctenums.LocID.GUARDIA_QUEENS_TOWER_600: 1,
    ctenums.LocID.MAGUS_CASTLE_CORRIDOR_OF_COMBAT: 1,
    ctenums.LocID.MAGUS_CASTLE_HALL_OF_AMBUSH: 1,
    ctenums.LocID.MAGUS_CASTLE_DUNGEON: 4,
    ctenums.LocID.GUARDIA_KINGS_TOWER_600: 1,
    ctenums.LocID.GUARDIA_KINGS_TOWER_1000: 1,
    ctenums.LocID.GUARDIA_QUEENS_TOWER_1000: 1,
    ctenums.LocID.GUARDIA_LAWGIVERS_TOWER: 1,
    ctenums.LocID.GUARDIA_PRISON_TOWER: 1,
    ctenums.LocID.ANCIENT_TYRANO_LAIR_VERTIGO: 1,
    ctenums.LocID.DEATH_PEAK_GUARDIAN_SPAWN: 1,
}

_chest_id_loc_id_dict: dict[int, ctenums.LocID] = {}
_temp = 0
for _loc_id in sorted(_treasure_count_dict.keys()):
    for _ in range(_treasure_count_dict[_loc_id]):
        _chest_id_loc_id_dict[_temp] = _loc_id
        _temp += 1
del _temp
del _loc_id


def get_chest_loc_id(chest_id: int) -> ctenums.LocID:
    """
    Returns the location in which a treasure chest lives
    """
    return _chest_id_loc_id_dict[chest_id]


def get_treasure_count_dict() -> dict[ctenums.LocID, int]:
    """
    Return a dict with a count of each location's treasure chests.
    """

    return {loc_id: _treasure_count_dict.get(loc_id, 0) for loc_id in ctenums.LocID}


def get_vanilla_assignment() -> dict[ctenums.TreasureID, RewardType]:
    return {
        ctenums.TreasureID.TRUCE_MAYOR_1F: ctenums.ItemID.TONIC,
        ctenums.TreasureID.TRUCE_MAYOR_2F: Gold(100),
        ctenums.TreasureID.KINGS_ROOM_1000: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.QUEENS_ROOM_1000: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.GUARDIA_BASEMENT_1: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.GUARDIA_BASEMENT_2: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.GUARDIA_BASEMENT_3: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.GUARDIA_JAIL_FRITZ_STORAGE: ctenums.ItemID.BRONZEMAIL,
        ctenums.TreasureID.FOREST_RUINS: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.HECKRAN_CAVE_SIDETRACK: ctenums.ItemID.MAGICSCARF,
        ctenums.TreasureID.HECKRAN_CAVE_ENTRANCE: ctenums.ItemID.ETHER,
        ctenums.TreasureID.HECKRAN_CAVE_1: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.HECKRAN_CAVE_2: ctenums.ItemID.ETHER,
        ctenums.TreasureID.PORRE_MAYOR_2F: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.GUARDIA_JAIL_CELL: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.GUARDIA_JAIL_OMNICRONE_1: ctenums.ItemID.ETHER,
        ctenums.TreasureID.GUARDIA_JAIL_OMNICRONE_2: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.GUARDIA_JAIL_OMNICRONE_3: ctenums.ItemID.ETHER,
        ctenums.TreasureID.GUARDIA_JAIL_HOLE_1: Gold(1500),
        ctenums.TreasureID.GUARDIA_JAIL_HOLE_2: ctenums.ItemID.LODE_SWORD,
        ctenums.TreasureID.GUARDIA_JAIL_OUTER_WALL: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.GUARDIA_JAIL_OMNICRONE_4: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.GUARDIA_JAIL_FRITZ: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.GIANTS_CLAW_TRAPS: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.TRUCE_CANYON_1: ctenums.ItemID.TONIC,
        ctenums.TreasureID.TRUCE_CANYON_2: ctenums.ItemID.POWERGLOVE,
        ctenums.TreasureID.KINGS_ROOM_600: ctenums.ItemID.BRONZEMAIL,
        ctenums.TreasureID.QUEENS_ROOM_600: ctenums.ItemID.ETHER,
        ctenums.TreasureID.ROYAL_KITCHEN: ctenums.ItemID.ETHER,
        ctenums.TreasureID.MAGUS_CASTLE_RIGHT_HALL: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.MANORIA_CATHEDRAL_1: ctenums.ItemID.STEELSABER,
        ctenums.TreasureID.MANORIA_CATHEDRAL_2: ctenums.ItemID.TONIC,
        ctenums.TreasureID.MANORIA_CATHEDRAL_3: ctenums.ItemID.REVIVE,
        ctenums.TreasureID.MANORIA_INTERIOR_1: ctenums.ItemID.TONIC,
        ctenums.TreasureID.MANORIA_INTERIOR_2: ctenums.ItemID.HEAL,
        ctenums.TreasureID.MANORIA_INTERIOR_3: ctenums.ItemID.IRON_SWORD,
        ctenums.TreasureID.MANORIA_INTERIOR_4: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.CURSED_WOODS_1: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.CURSED_WOODS_2: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.FROGS_BURROW_RIGHT: ctenums.ItemID.MAGICSCARF,
        ctenums.TreasureID.DENADORO_MTS_SCREEN2_1: Gold(500),
        ctenums.TreasureID.DENADORO_MTS_SCREEN2_2: ctenums.ItemID.ETHER,
        ctenums.TreasureID.DENADORO_MTS_SCREEN2_3: ctenums.ItemID.MIRAGEHAND,
        ctenums.TreasureID.DENADORO_MTS_FINAL_1: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.DENADORO_MTS_FINAL_2: ctenums.ItemID.GOLD_SUIT,
        ctenums.TreasureID.DENADORO_MTS_FINAL_3: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.DENADORO_MTS_WATERFALL_TOP_1: ctenums.ItemID.SILVERSTUD,
        ctenums.TreasureID.DENADORO_MTS_WATERFALL_TOP_2: ctenums.ItemID.SILVERERNG,
        ctenums.TreasureID.DENADORO_MTS_WATERFALL_TOP_3: Gold(300),
        ctenums.TreasureID.DENADORO_MTS_WATERFALL_TOP_4: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.DENADORO_MTS_WATERFALL_TOP_5: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.DENADORO_MTS_ENTRANCE_1: ctenums.ItemID.REVIVE,
        ctenums.TreasureID.DENADORO_MTS_ENTRANCE_2: Gold(300),
        ctenums.TreasureID.DENADORO_MTS_SCREEN3_1: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.DENADORO_MTS_SCREEN3_2: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.DENADORO_MTS_SCREEN3_3: ctenums.ItemID.GOLD_HELM,
        ctenums.TreasureID.DENADORO_MTS_SCREEN3_4: ctenums.ItemID.REVIVE,
        ctenums.TreasureID.DENADORO_MTS_AMBUSH: Gold(600),
        ctenums.TreasureID.DENADORO_MTS_SAVE_PT: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.FIONAS_HOUSE_1: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.FIONAS_HOUSE_2: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.SUNKEN_DESERT_B1_NW: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.SUNKEN_DESERT_B1_NE: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.SUNKEN_DESERT_B1_SE: ctenums.ItemID.AEON_SUIT,
        ctenums.TreasureID.SUNKEN_DESERT_B1_SW: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.SUNKEN_DESERT_B2_NW: ctenums.ItemID.FULL_TONIC,
        ctenums.TreasureID.SUNKEN_DESERT_B2_N: Gold(5000),
        ctenums.TreasureID.SUNKEN_DESERT_B2_E: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.SUNKEN_DESERT_B2_SE: ctenums.ItemID.AEON_HELM,
        ctenums.TreasureID.SUNKEN_DESERT_B2_SW: ctenums.ItemID.MEMORY_CAP,
        ctenums.TreasureID.SUNKEN_DESERT_B2_W: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.SUNKEN_DESERT_B2_CENTER: ctenums.ItemID.MUSCLERING,
        ctenums.TreasureID.MAGUS_CASTLE_GUILLOTINE_1: ctenums.ItemID.DARK_MAIL,
        ctenums.TreasureID.MAGUS_CASTLE_GUILLOTINE_2: ctenums.ItemID.DOOMFINGER,
        ctenums.TreasureID.MAGUS_CASTLE_SLASH_ROOM_1: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.MAGUS_CASTLE_SLASH_ROOM_2: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.MAGUS_CASTLE_STATUE_HALL: ctenums.ItemID.MIST_ROBE,
        ctenums.TreasureID.MAGUS_CASTLE_OZZIE_1: ctenums.ItemID.MIST_ROBE,
        ctenums.TreasureID.MAGUS_CASTLE_OZZIE_2: ctenums.ItemID.MAGICSCARF,
        ctenums.TreasureID.MAGUS_CASTLE_ENEMY_ELEVATOR: ctenums.ItemID.SPEED_BELT,
        ctenums.TreasureID.OZZIES_FORT_GUILLOTINES_1: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.OZZIES_FORT_GUILLOTINES_2: ctenums.ItemID.GLOOM_CAPE,
        ctenums.TreasureID.OZZIES_FORT_GUILLOTINES_3: ctenums.ItemID.GLOOM_HELM,
        ctenums.TreasureID.OZZIES_FORT_GUILLOTINES_4: ctenums.ItemID.DOOMSICKLE,
        ctenums.TreasureID.OZZIES_FORT_FINAL_1: ctenums.ItemID.DASH_RING,
        ctenums.TreasureID.OZZIES_FORT_FINAL_2: ctenums.ItemID.SIGHT_CAP,
        ctenums.TreasureID.GIANTS_CLAW_CAVES_1: ctenums.ItemID.SIGHT_CAP,
        ctenums.TreasureID.GIANTS_CLAW_CAVES_2: ctenums.ItemID.FRENZYBAND,
        ctenums.TreasureID.GIANTS_CLAW_CAVES_3: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.GIANTS_CLAW_CAVES_4: ctenums.ItemID.ZODIACCAPE,
        ctenums.TreasureID.GIANTS_CLAW_ROCK: ctenums.ItemID.BLUE_ROCK,
        ctenums.TreasureID.GIANTS_CLAW_CAVES_5: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.YAKRAS_ROOM: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.MANORIA_SHRINE_SIDEROOM_1: Gold(100),
        ctenums.TreasureID.MANORIA_SHRINE_SIDEROOM_2: ctenums.ItemID.ETHER,
        ctenums.TreasureID.MANORIA_BROMIDE_1: ctenums.ItemID.MAIDENSUIT,
        ctenums.TreasureID.MANORIA_BROMIDE_2: ctenums.ItemID.TONIC,
        ctenums.TreasureID.MANORIA_BROMIDE_3: ctenums.ItemID.ETHER,
        ctenums.TreasureID.MANORIA_SHRINE_MAGUS_1: ctenums.ItemID.SPEED_BELT,
        ctenums.TreasureID.MANORIA_SHRINE_MAGUS_2: ctenums.ItemID.DEFENDER,
        ctenums.TreasureID.BANGOR_DOME_SEAL_1: ctenums.ItemID.CHARM_TOP,
        ctenums.TreasureID.BANGOR_DOME_SEAL_2: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.BANGOR_DOME_SEAL_3: ctenums.ItemID.WALLET,
        ctenums.TreasureID.TRANN_DOME_SEAL_1: ctenums.ItemID.GOLD_STUD,
        ctenums.TreasureID.TRANN_DOME_SEAL_2: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.LAB_16_1: ctenums.ItemID.LODE_SWORD,
        ctenums.TreasureID.LAB_16_2: ctenums.ItemID.LODE_BOW,
        ctenums.TreasureID.LAB_16_3: ctenums.ItemID.BERSERKER,
        ctenums.TreasureID.LAB_16_4: ctenums.ItemID.ETHER,
        ctenums.TreasureID.ARRIS_DOME_RATS: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.ARRIS_DOME_SEAL_1: ctenums.ItemID.LUMIN_ROBE,
        ctenums.TreasureID.ARRIS_DOME_SEAL_2: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.ARRIS_DOME_SEAL_3: ctenums.ItemID.HIT_RING,
        ctenums.TreasureID.ARRIS_DOME_SEAL_4: ctenums.ItemID.GOLD_ERNG,
        ctenums.TreasureID.REPTITE_LAIR_SECRET_B2_NE_RIGHT: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.LAB_32_1: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.LAB_32_RACE_LOG: ctenums.ItemID.RACE_LOG,
        ctenums.TreasureID.FACTORY_LEFT_AUX_CONSOLE: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.FACTORY_LEFT_SECURITY_RIGHT: ctenums.ItemID.HAMMER_ARM,
        ctenums.TreasureID.FACTORY_LEFT_SECURITY_LEFT: ctenums.ItemID.TITAN_VEST,
        ctenums.TreasureID.FACTORY_RIGHT_FLOOR_TOP: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.FACTORY_RIGHT_FLOOR_LEFT: ctenums.ItemID.ROBIN_BOW,
        ctenums.TreasureID.FACTORY_RIGHT_FLOOR_BOTTOM: ctenums.ItemID.ETHER,
        ctenums.TreasureID.FACTORY_RIGHT_FLOOR_SECRET: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.FACTORY_RIGHT_CRANE_UPPER: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.FACTORY_RIGHT_CRANE_LOWER: ctenums.ItemID.ETHER,
        ctenums.TreasureID.FACTORY_RIGHT_INFO_ARCHIVE: ctenums.ItemID.BOLT_SWORD,
        ctenums.TreasureID.FACTORY_RUINS_GENERATOR: ctenums.ItemID.PLASMA_GUN,
        ctenums.TreasureID.SEWERS_1: Gold(600),
        ctenums.TreasureID.SEWERS_2: ctenums.ItemID.RAGE_BAND,
        ctenums.TreasureID.SEWERS_3: ctenums.ItemID.BOLT_SWORD,
        ctenums.TreasureID.DEATH_PEAK_SOUTH_FACE_KRAKKER: ctenums.ItemID.MAGIC_RING,
        ctenums.TreasureID.DEATH_PEAK_SOUTH_FACE_SPAWN_SAVE: ctenums.ItemID.DARK_HELM,
        ctenums.TreasureID.DEATH_PEAK_SOUTH_FACE_SUMMIT: ctenums.ItemID.MEMORY_CAP,
        ctenums.TreasureID.DEATH_PEAK_FIELD: ctenums.ItemID.WALL_RING,
        ctenums.TreasureID.GENO_DOME_1F_1: ctenums.ItemID.FULL_TONIC,
        ctenums.TreasureID.GENO_DOME_1F_2: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.GENO_DOME_1F_3: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.GENO_DOME_1F_4: ctenums.ItemID.VIGIL_HAT,
        ctenums.TreasureID.GENO_DOME_ROOM_1: ctenums.ItemID.FULL_TONIC,
        ctenums.TreasureID.GENO_DOME_ROOM_2: Gold(50000),
        ctenums.TreasureID.GENO_DOME_PROTO4_1: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.GENO_DOME_PROTO4_2: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.FACTORY_RIGHT_DATA_CORE_1: Gold(400),
        ctenums.TreasureID.FACTORY_RIGHT_DATA_CORE_2: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.DEATH_PEAK_KRAKKER_PARADE: ctenums.ItemID.VEDICBLADE,
        ctenums.TreasureID.DEATH_PEAK_CAVES_LEFT: ctenums.ItemID.GIGA_ARM,
        ctenums.TreasureID.DEATH_PEAK_CAVES_CENTER: ctenums.ItemID.STARSCYTHE,
        ctenums.TreasureID.DEATH_PEAK_CAVES_RIGHT: ctenums.ItemID.BRAVESWORD,
        ctenums.TreasureID.GENO_DOME_2F_1: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.GENO_DOME_2F_2: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.GENO_DOME_2F_3: Gold(15000),
        ctenums.TreasureID.GENO_DOME_2F_4: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.MYSTIC_MT_STREAM: ctenums.ItemID.BERSERKER,
        ctenums.TreasureID.FOREST_MAZE_1: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.FOREST_MAZE_2: ctenums.ItemID.REVIVE,
        ctenums.TreasureID.FOREST_MAZE_3: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.FOREST_MAZE_4: ctenums.ItemID.HEAL,
        ctenums.TreasureID.FOREST_MAZE_5: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.FOREST_MAZE_6: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.FOREST_MAZE_7: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.FOREST_MAZE_8: ctenums.ItemID.REVIVE,
        ctenums.TreasureID.FOREST_MAZE_9: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.REPTITE_LAIR_SECRET_B1_SW: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.REPTITE_LAIR_SECRET_B1_NE: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.REPTITE_LAIR_SECRET_B1_SE: ctenums.ItemID.FULL_TONIC,
        ctenums.TreasureID.REPTITE_LAIR_SECRET_B2_SE_RIGHT: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.REPTITE_LAIR_SECRET_B2_NE_OR_SE_LEFT: ctenums.ItemID.RUBY_VEST,
        ctenums.TreasureID.REPTITE_LAIR_SECRET_B2_SW: ctenums.ItemID.FULL_TONIC,
        ctenums.TreasureID.REPTITE_LAIR_REPTITES_1: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.REPTITE_LAIR_REPTITES_2: ctenums.ItemID.ROCK_HELM,
        ctenums.TreasureID.DACTYL_NEST_1: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.DACTYL_NEST_2: ctenums.ItemID.MID_TONIC,
        ctenums.TreasureID.DACTYL_NEST_3: ctenums.ItemID.MESO_MAIL,
        ctenums.TreasureID.TYRANO_LAIR_THRONE_1: ctenums.ItemID.CERATOPPER,
        ctenums.TreasureID.TYRANO_LAIR_THRONE_2: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.TYRANO_LAIR_TRAPDOOR: ctenums.ItemID.FULL_TONIC,
        ctenums.TreasureID.TYRANO_LAIR_KINO_CELL: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.TYRANO_LAIR_MAZE_1: ctenums.ItemID.TONIC,
        ctenums.TreasureID.TYRANO_LAIR_MAZE_2: ctenums.ItemID.MESO_MAIL,
        ctenums.TreasureID.TYRANO_LAIR_MAZE_3: ctenums.ItemID.REVIVE,
        ctenums.TreasureID.TYRANO_LAIR_MAZE_4: ctenums.ItemID.CERATOPPER,
        ctenums.TreasureID.BLACK_OMEN_AUX_COMMAND_MID: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.BLACK_OMEN_AUX_COMMAND_NE: Gold(30000),
        ctenums.TreasureID.BLACK_OMEN_GRAND_HALL: ctenums.ItemID.MAGIC_SEAL,
        ctenums.TreasureID.BLACK_OMEN_NU_HALL_NW: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.BLACK_OMEN_NU_HALL_W: ctenums.ItemID.NOVA_ARMOR,
        ctenums.TreasureID.BLACK_OMEN_NU_HALL_SW: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.BLACK_OMEN_NU_HALL_NE: ctenums.ItemID.HASTE_HELM,
        ctenums.TreasureID.BLACK_OMEN_NU_HALL_E: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.BLACK_OMEN_NU_HALL_SE: ctenums.ItemID.VIGIL_HAT,
        ctenums.TreasureID.BLACK_OMEN_ROYAL_PATH: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.BLACK_OMEN_RUMINATOR_PARADE: ctenums.ItemID.ZODIACCAPE,
        ctenums.TreasureID.BLACK_OMEN_EYEBALL_HALL: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.BLACK_OMEN_TUBSTER_FLY: ctenums.ItemID.POWER_SEAL,
        ctenums.TreasureID.BLACK_OMEN_MARTELLO: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.BLACK_OMEN_ALIEN_SW: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.BLACK_OMEN_ALIEN_NE: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.BLACK_OMEN_ALIEN_NW: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.BLACK_OMEN_TERRA_W: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.BLACK_OMEN_TERRA_ROCK: ctenums.ItemID.WHITE_ROCK,
        ctenums.TreasureID.BLACK_OMEN_TERRA_NE: ctenums.ItemID.MEGAELIXIR,
        ctenums.TreasureID.ARRIS_DOME_FOOD_STORE: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.MT_WOE_2ND_SCREEN_1: ctenums.ItemID.BARRIER,
        ctenums.TreasureID.MT_WOE_2ND_SCREEN_2: ctenums.ItemID.SHIELD,
        ctenums.TreasureID.MT_WOE_2ND_SCREEN_3: ctenums.ItemID.LODE_VEST,
        ctenums.TreasureID.MT_WOE_2ND_SCREEN_4: ctenums.ItemID.BARRIER,
        ctenums.TreasureID.MT_WOE_2ND_SCREEN_5: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.MT_WOE_3RD_SCREEN_1: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.MT_WOE_3RD_SCREEN_2: ctenums.ItemID.BARRIER,
        ctenums.TreasureID.MT_WOE_3RD_SCREEN_3: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.MT_WOE_3RD_SCREEN_4: ctenums.ItemID.SHIELD,
        ctenums.TreasureID.MT_WOE_3RD_SCREEN_5: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.MT_WOE_1ST_SCREEN: ctenums.ItemID.LODE_HELM,
        ctenums.TreasureID.MT_WOE_FINAL_1: ctenums.ItemID.FULL_ETHER,
        ctenums.TreasureID.MT_WOE_FINAL_2: ctenums.ItemID.TIME_HAT,
        ctenums.TreasureID.OCEAN_PALACE_MAIN_S: ctenums.ItemID.AEON_SUIT,
        ctenums.TreasureID.OCEAN_PALACE_MAIN_N: ctenums.ItemID.RUNE_BLADE,
        ctenums.TreasureID.OCEAN_PALACE_E_ROOM: ctenums.ItemID.AEON_HELM,
        ctenums.TreasureID.OCEAN_PALACE_W_ROOM: ctenums.ItemID.STAR_SWORD,
        ctenums.TreasureID.OCEAN_PALACE_SWITCH_NW: ctenums.ItemID.SHOCK_WAVE,
        ctenums.TreasureID.OCEAN_PALACE_SWITCH_SW: ctenums.ItemID.SONICARROW,
        ctenums.TreasureID.OCEAN_PALACE_SWITCH_NE: ctenums.ItemID.KAISER_ARM,
        ctenums.TreasureID.OCEAN_PALACE_SWITCH_SECRET: ctenums.ItemID.DEMON_HIT,
        ctenums.TreasureID.OCEAN_PALACE_FINAL: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.GUARDIA_TREASURY_1: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.GUARDIA_TREASURY_2: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.GUARDIA_TREASURY_3: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.QUEENS_TOWER_600: ctenums.ItemID.TONIC,
        ctenums.TreasureID.MAGUS_CASTLE_LEFT_HALL: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.MAGUS_CASTLE_UNSKIPPABLES: ctenums.ItemID.REVIVE,
        ctenums.TreasureID.MAGUS_CASTLE_PIT_E: ctenums.ItemID.MID_ETHER,
        ctenums.TreasureID.MAGUS_CASTLE_PIT_NE: ctenums.ItemID.LAPIS,
        ctenums.TreasureID.MAGUS_CASTLE_PIT_NW: ctenums.ItemID.BARRIER,
        ctenums.TreasureID.MAGUS_CASTLE_PIT_W: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.KINGS_TOWER_600: Gold(100),
        ctenums.TreasureID.KINGS_TOWER_1000: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.QUEENS_TOWER_1000: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.GUARDIA_COURT_TOWER: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.PRISON_TOWER_1000: ctenums.ItemID.SHELTER,
        ctenums.TreasureID.NORTHERN_RUINS_BASEMENT_600: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.NORTHERN_RUINS_BASEMENT_1000: ctenums.ItemID.HYPERETHER,
        ctenums.TreasureID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600: ctenums.ItemID.ELIXIR,
        ctenums.TreasureID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000: ctenums.ItemID.MOON_ARMOR,
        ctenums.TreasureID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600: ctenums.ItemID.NOVA_ARMOR,
        ctenums.TreasureID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000: ctenums.ItemID.SHIVA_EDGE,
        ctenums.TreasureID.NORTHERN_RUINS_BACK_LEFT_SEALED_600: ctenums.ItemID.KALI_BLADE,
        ctenums.TreasureID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000: ctenums.ItemID.VALKERYE,
        ctenums.TreasureID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600: ctenums.ItemID.SIREN,
        ctenums.TreasureID.TRUCE_INN_SEALED_600: ctenums.ItemID.BLUE_VEST,
        ctenums.TreasureID.TRUCE_INN_SEALED_1000: ctenums.ItemID.BLUE_MAIL,
        ctenums.TreasureID.PYRAMID_LEFT: ctenums.ItemID.SAFE_HELM,
        ctenums.TreasureID.PYRAMID_RIGHT: ctenums.ItemID.SWALLOW,
        ctenums.TreasureID.PORRE_ELDER_SEALED_1: ctenums.ItemID.WHITE_VEST,
        ctenums.TreasureID.PORRE_ELDER_SEALED_2: ctenums.ItemID.BLACK_VEST,
        ctenums.TreasureID.PORRE_MAYOR_SEALED_1: ctenums.ItemID.WHITE_MAIL,
        ctenums.TreasureID.PORRE_MAYOR_SEALED_2: ctenums.ItemID.BLACK_MAIL,
        ctenums.TreasureID.GUARDIA_CASTLE_SEALED_600: ctenums.ItemID.RED_VEST,
        ctenums.TreasureID.GUARDIA_FOREST_SEALED_600: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.GUARDIA_FOREST_SEALED_1000: ctenums.ItemID.POWER_RING,
        ctenums.TreasureID.GUARDIA_CASTLE_SEALED_1000: ctenums.ItemID.RED_MAIL,
        ctenums.TreasureID.HECKRAN_SEALED_1: ctenums.ItemID.WALL_RING,
        ctenums.TreasureID.HECKRAN_SEALED_2: ctenums.ItemID.DASH_RING,
        ctenums.TreasureID.MAGIC_CAVE_SEALED: ctenums.ItemID.MAGIC_RING,
        ctenums.TreasureID.REPTITE_LAIR_KEY: ctenums.ItemID.GATE_KEY,
        ctenums.TreasureID.MELCHIOR_RAINBOW_SHELL: ctenums.ItemID.PRISM_HELM,
        ctenums.TreasureID.MELCHIOR_SUNSTONE_RAINBOW: ctenums.ItemID.RAINBOW,
        ctenums.TreasureID.MELCHIOR_SUNSTONE_SPECS: ctenums.ItemID.PRISMSPECS,
        ctenums.TreasureID.FROGS_BURROW_LEFT: ctenums.ItemID.BENT_HILT,
        ctenums.TreasureID.MT_WOE_KEY: ctenums.ItemID.RUBY_KNIFE,
        ctenums.TreasureID.FIONA_KEY: ctenums.ItemID.GREENDREAM,
        ctenums.TreasureID.ARRIS_DOME_DOAN_KEY: ctenums.ItemID.BIKE_KEY,
        ctenums.TreasureID.SUN_PALACE_KEY: ctenums.ItemID.MOON_STONE,
        ctenums.TreasureID.GENO_DOME_BOSS_1: ctenums.ItemID.TERRA_ARM,
        ctenums.TreasureID.GENO_DOME_BOSS_2: ctenums.ItemID.CRISIS_ARM,
        ctenums.TreasureID.GIANTS_CLAW_KEY: ctenums.ItemID.RAINBOW_SHELL,
        ctenums.TreasureID.KINGS_TRIAL_KEY: ctenums.ItemID.PRISMSHARD,
        ctenums.TreasureID.ZENAN_BRIDGE_CHEF: ctenums.ItemID.JERKY,
        ctenums.TreasureID.ZENAN_BRIDGE_CHEF_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.ZENAN_BRIDGE_CAPTAIN: ctenums.ItemID.GOLD_HELM,
        ctenums.TreasureID.SNAIL_STOP_KEY: ctenums.ItemID.JERKY,
        ctenums.TreasureID.LAZY_CARPENTER: ctenums.ItemID.TOOLS,
        ctenums.TreasureID.TABAN_GIFT_VEST: ctenums.ItemID.TABAN_VEST,
        ctenums.TreasureID.DENADORO_MTS_KEY: ctenums.ItemID.BENT_SWORD,
        ctenums.TreasureID.TABAN_GIFT_HELM: ctenums.ItemID.TABAN_HELM,
        ctenums.TreasureID.TABAN_GIFT_SUIT: ctenums.ItemID.TABAN_SUIT,
        ctenums.TreasureID.JERKY_GIFT: ctenums.ItemID.MOP,
        ctenums.TreasureID.DENADORO_ROCK: ctenums.ItemID.GOLD_ROCK,
        ctenums.TreasureID.LARUBA_ROCK: ctenums.ItemID.SILVERROCK,
        ctenums.TreasureID.KAJAR_ROCK: ctenums.ItemID.BLACK_ROCK,
        ctenums.TreasureID.BEKKLER_KEY: ctenums.ItemID.CLONE,
        ctenums.TreasureID.CYRUS_GRAVE_KEY: ctenums.ItemID.MASAMUNE_2,
        ctenums.TreasureID.SUN_KEEP_2300: ctenums.ItemID.SUN_STONE,
        ctenums.TreasureID.ARRIS_DOME_FOOD_LOCKER_KEY: ctenums.ItemID.SEED,
        ctenums.TreasureID.LUCCA_WONDERSHOT: ctenums.ItemID.WONDERSHOT,
        ctenums.TreasureID.TABAN_SUNSHADES: ctenums.ItemID.SUN_SHADES,
        ctenums.TreasureID.TATA_REWARD: ctenums.ItemID.HERO_MEDAL,
        ctenums.TreasureID.TOMA_REWARD: ctenums.ItemID.TOMAS_POP,
        ctenums.TreasureID.MELCHIOR_FORGE_MASA: ctenums.ItemID.MASAMUNE_1,
        ctenums.TreasureID.EOT_GASPAR_REWARD: ctenums.ItemID.C_TRIGGER,
        ctenums.TreasureID.FAIR_PENDANT: ctenums.ItemID.PENDANT,
        ctenums.TreasureID.HUNTING_RANGE_NU_REWARD: ctenums.ItemID.THIRD_EYE,
        ctenums.TreasureID.ZEAL_MAMMON_MACHINE: ctenums.ItemID.PENDANT_CHARGE,
        ctenums.TreasureID.MAGUS_CASTLE_FOUR_KIDS: ctenums.ItemID.BARRIER,
        ctenums.TreasureID.MAGUS_CASTLE_SLASH_SWORD_FLOOR: ctenums.ItemID.SLASHER,
        ctenums.TreasureID.GUARDIA_PRISON_LUNCH_BAG: ctenums.ItemID.ETHER,
        ctenums.TreasureID.DORINO_BROMIDE_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.GUARDIA_FOREST_POWER_TAB_600: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.GUARDIA_FOREST_POWER_TAB_1000: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.MANORIA_CONFINEMENT_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.PORRE_MARKET_600_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.DENADORO_MTS_SPEED_TAB: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.TOMAS_GRAVE_SPEED_TAB: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.GIANTS_CLAW_CAVERNS_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.GIANTS_CLAW_ENTRANCE_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.GIANTS_CLAW_TRAPS_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.SUN_KEEP_600_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.MEDINA_ELDER_SPEED_TAB: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.MEDINA_ELDER_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.MAGUS_CASTLE_FLEA_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.MAGUS_CASTLE_DUNGEONS_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.TRANN_DOME_SEALED_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.ARRIS_DOME_SEALED_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.DEATH_PEAK_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.BLACKBIRD_DUCTS_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.KEEPERS_DOME_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.GENO_DOME_ATROPOS_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.GENO_DOME_CORRIDOR_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.GENO_DOME_LABS_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.GENO_DOME_LABS_SPEED_TAB: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.ENHASA_NU_BATTLE_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.ENHASA_NU_BATTLE_SPEED_TAB: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.KAJAR_SPEED_TAB: ctenums.ItemID.SPEED_TAB,
        ctenums.TreasureID.KAJAR_NU_SCRATCH_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.LAST_VILLAGE_NU_SHOP_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.SUNKEN_DESERT_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.MOUNTAINS_RE_NICE_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.BEAST_NEST_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.MT_WOE_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.OCEAN_PALACE_ELEVATOR_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.OZZIES_FORT_GUILLOTINES_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.PROTO_DOME_PORTAL_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.NORTHERN_RUINS_HEROS_GRAVE_MAGIC_TAB: ctenums.ItemID.MAGIC_TAB,
        ctenums.TreasureID.NORTHERN_RUINS_LANDING_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.CRONOS_MOM: Gold(400),
        ctenums.TreasureID.TRUCE_MAYOR_2F_OLD_MAN: Gold(300),
        ctenums.TreasureID.IOKA_SWEETWATER_TONIC: ctenums.ItemID.TONIC,
        ctenums.TreasureID.DORINO_INN_POWERMEAL: ctenums.ItemID.POWER_MEAL,
        ctenums.TreasureID.YAKRA_KEY_CHEST: ctenums.ItemID.TONIC,
        ctenums.TreasureID.COURTROOM_YAKRA_KEY: ctenums.ItemID.YAKRA_KEY,
        ctenums.TreasureID.JOHNNY_RACE_POWER_TAB: ctenums.ItemID.POWER_TAB,
        ctenums.TreasureID.TRADING_POST_PETAL_FANG_BASE: ctenums.ItemID.RUBY_GUN,
        ctenums.TreasureID.TRADING_POST_PETAL_FANG_UPGRADE: ctenums.ItemID.DREAM_GUN,
        ctenums.TreasureID.TRADING_POST_PETAL_HORN_BASE: ctenums.ItemID.SAGE_BOW,
        ctenums.TreasureID.TRADING_POST_PETAL_HORN_UPGRADE: ctenums.ItemID.DREAM_BOW,
        ctenums.TreasureID.TRADING_POST_PETAL_FEATHER_BASE: ctenums.ItemID.STONE_ARM,
        ctenums.TreasureID.TRADING_POST_PETAL_FEATHER_UPGRADE: ctenums.ItemID.MAGMA_HAND,
        ctenums.TreasureID.TRADING_POST_FANG_HORN_BASE: ctenums.ItemID.FLINT_EDGE,
        ctenums.TreasureID.TRADING_POST_FANG_HORN_UPGRADE: ctenums.ItemID.AEON_BLADE,
        ctenums.TreasureID.TRADING_POST_FANG_FEATHER_BASE: ctenums.ItemID.RUBY_VEST,
        ctenums.TreasureID.TRADING_POST_FANG_FEATHER_UPGRADE: ctenums.ItemID.RUBY_VEST,
        ctenums.TreasureID.TRADING_POST_HORN_FEATHER_BASE: ctenums.ItemID.ROCK_HELM,
        ctenums.TreasureID.TRADING_POST_HORN_FEATHER_UPGRADE: ctenums.ItemID.ROCK_HELM,
        ctenums.TreasureID.TRADING_POST_SPECIAL: ctenums.ItemID.RUBY_ARMOR,
    }
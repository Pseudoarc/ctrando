"""
Module for Overworld Event Commands.

Based off "Overworld Commmands.txt" from the Chrono Trigger Database.
"""
from __future__ import annotations
from typing import Type, TypeVar, Optional, TypeGuard
from ctrando.common import cttypes


T = TypeVar('T', bound='OverworldEventCommand')


class OverworldEventCommand(cttypes.BinaryData):
    """Base class for overworld commands."""
    SIZE = 1
    CMD_ID: int = 0xFF  # Not valid

    @classmethod
    def _get_default_value(cls) -> bytearray:
        if cls.SIZE is None:
            return bytearray()

        init_data = bytearray(cls.SIZE)
        init_data[0] = cls.CMD_ID
        return init_data

    @property
    def cmd_id(self) -> int:
        """Get this command's id."""
        return self[0]

    @classmethod
    def validate_data(cls: Type[T], data: T):
        super(OverworldEventCommand, cls).validate_data(data)
        if data[0] != cls.CMD_ID:
            raise ValueError('Command ID mismatch')

    def _set_properties(self, *args: tuple[str, Optional[int]]):
        for name, val in args:
            if val is not None:
                setattr(self, name, val)

    def __str__(self):
        ret_str = super().__str__()
        props = self.get_bytesprops()
        for name in props:
            val = self.__getattribute__(name)
            ret_str += '\n\t' + f'{name}={val} (0x{val:X})'

        return ret_str


class OWBranchCommand(OverworldEventCommand):
    """Any OverworldEventCommand which can branch"""
    def __init__(self, *args, to_label: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.to_label = to_label

    def get_copy(self) -> OWBranchCommand:
        ret = super().get_copy()
        ret.to_label = self.to_label
        return ret


class OWLocalBranchCommand(OWBranchCommand):
    """OWEvent Commands that can branch relative to current position"""
    def __init__(self, *args, to_label: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.to_label = to_label

    @property
    def jump_bytes(self) -> int:
        """The number of bytes this command jumps if condition is unmet"""
        raise NotImplementedError

    @jump_bytes.setter
    def jump_bytes(self, val: int) -> None:
        raise NotImplementedError


class OWLocalJumpCommand(OWBranchCommand):
    """OWEvent Commands that jump to a particular bank 7F address"""

    @property
    def jump_address(self) -> int:
        """Address to jump to (in bank 7F)"""
        raise NotImplementedError

    @jump_address.setter
    def jump_address(self, val: int) -> None:
        raise NotImplementedError


class OWLongJumpCommand(OWBranchCommand):
    """OWEvent Commands that jump to arbitrary addresses"""
    @property
    def jump_address(self) -> int:
        """Address to jump to"""
        raise NotImplementedError

    @jump_address.setter
    def jump_address(self, val: int) -> None:
        raise NotImplementedError


class InitMemory(OverworldEventCommand):
    """Initialize memory of an OW object."""
    CMD_ID = 0
    SIZE = 1


class SetPalette(OverworldEventCommand):
    """Set the palette of an OW object."""
    CMD_ID = 1
    SIZE = 2

    palette = cttypes.byte_prop(1)

    def __init__(self, *args,
                 palette: Optional[int] = None,
                 **kwargs):
        OverworldEventCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ('palette', palette),
        )


class Assign02(OverworldEventCommand):
    """
    02 vv  assignment
           vv - value to OR and store to process memory 0F
    """
    CMD_ID = 2
    SIZE = 2

    value = cttypes.byte_prop(1)

    def __init__(self, *args,
                 value: Optional[int] = None,
                 **kwargs):
        OverworldEventCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ('value', value),
        )


class Unknown03(OverworldEventCommand):
    """
    03 ?? ?? ?? ?? ?? ?? ?? ?? ?? ??  unknown
    arguments do not appear to be loaded
    """
    CMD_ID = 3
    SIZE = 10


class LoadPalette(OverworldEventCommand):
    """
    04 aaaaaa ?? ??  unknown
                     aaaaaa - address
    """
    CMD_ID = 4
    SIZE = 6

    palette_address = cttypes.bytes_prop(1, 3)
    palette_id = cttypes.byte_prop(4)
    mode = cttypes.byte_prop(5)

    def __init__(self, *args,
                 palette_address: Optional[int] = None,
                 palette_id: Optional[int] = None,
                 mode: Optional[int] = None,
                 **kwargs):
        OverworldEventCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ('palette_address', palette_address),
            ('palette_id', palette_id),
            ('mode', mode)
        )


class ChangeLocation(OverworldEventCommand):
    """
    05 llll xx yy  change location
                   llll - location to chage to  (not quite)
                     01FF - location to change to
                     FE00 - Unknown (facing probably)
                   xx - X Coord
                   yy - Y Coord
    """
    CMD_ID = 5
    SIZE = 5

    unknown = cttypes.bytes_prop(1, 2, 0xFE00)
    location = cttypes.bytes_prop(1, 2, 0x01FF)
    x_coord = cttypes.byte_prop(3)
    y_coord = cttypes.byte_prop(4)

    # Experimental
    facing = cttypes.byte_prop(2, 0x06)
    half_tile_x = cttypes.byte_prop(2, 0x10)
    half_tile_y = cttypes.byte_prop(2, 0x08)

    def __init__(self, *args,
                 unknown: Optional[int] = None,
                 location: Optional[int] = None,
                 x_coord: Optional[int] = None,
                 y_coord: Optional[int] = None,
                 **kwargs):
        OverworldEventCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ('location', location),
            ('x_coord', x_coord),
            ('y_coord', y_coord),
            ('unknown', unknown)
        )


class DirectPageJump06(OverworldEventCommand):
    """
    06	direct page jump
    unused . uses direct page register as jump value
    """
    CMD_ID = 6
    SIZE = 1


class SetTile(OverworldEventCommand):
    """
    07 ll xx yy vv    set tile
                      ll - offset to ROM location that determines layer
                      xx - X Coord
                      yy - Y Coord
                      vv - value to store
    """
    CMD_ID = 7
    SIZE = 5

    layer = cttypes.byte_prop(1)
    x_coord = cttypes.byte_prop(2)
    y_coord = cttypes.byte_prop(3)
    value = cttypes.byte_prop(4)

    def __init__(self, *args,
                 layer: Optional[int] = None,
                 x_coord: Optional[int] = None,
                 y_coord: Optional[int] = None,
                 value: Optional[int] = None,
                 **kwargs):
        OverworldEventCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ('layer', layer),
            ('x_coord', x_coord),
            ('y_coord', y_coord),
            ('value', value)
        )


class PCSub(OWLocalJumpCommand):
    """
    08 ???? ??
    TF output gives PCSub.  Example: [0A9C] PCSub([0ACA], Crono).
    The idea seems to be calling a subroutine on a given character.
        aaaa - memory address (offset in 0x7F0000)
        cc - character id (0=Crono, etc)
    """
    CMD_ID = 8
    SIZE = 4

    jump_address = cttypes.bytes_prop(1, 2)
    char_id = cttypes.byte_prop(3)

    def __init__(self, *args,
                 jump_address: Optional[int] = None,
                 char_id: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('jump_address', jump_address),
            ('char_id', char_id),
        )


class AddProcess09(OWLongJumpCommand):
    """
    Adds extra processing to be done after an ""end"" is reached, slightly
    different from 43

    09 aaaaaa    add proc
                 aaaaaa - memory address
    """
    CMD_ID = 9
    SIZE = 4

    jump_address = cttypes.bytes_prop(1, 3)

    def __init__(self, *args,
                 jump_address: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('jump_address', jump_address),
        )


class Assign0A(OverworldEventCommand):
    """0A oo		oo - offset to store a value to (+7E0C30)"""
    CMD_ID = 0xA
    SIZE = 2

    offset = cttypes.byte_prop(1)


class IncrementProcessMemory(OverworldEventCommand):
    """
    0B oo    increment
             oo - offset to increment in process memory
    """
    CMD_ID = 0xB
    SIZE = 2

    offset = cttypes.byte_prop(1)


class DecrementProcessMemory(OverworldEventCommand):
    """0C oo    decrement
                oo - offset to decrement in process memory
    """
    CMD_ID = 0xC
    SIZE = 2

    offset = cttypes.byte_prop(1)


class AssignProcess(OverworldEventCommand):
    """
    0D oo vv    assignment
                oo - offset to store to process memory
                vv -value to store
    """
    CMD_ID = 0xD
    SIZE = 3

    offset = cttypes.byte_prop(1)
    value = cttypes.byte_prop(2)


class SetBitsProcess(OverworldEventCommand):
    """
    0E oo bb    set bits
                oo - offset to set bits in process memory
                bb - bits to set
    """
    CMD_ID = 0xE
    SIZE = 3

    offset = cttypes.byte_prop(1)
    bits = cttypes.byte_prop(2)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 bits: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset), ('bits', bits)
        )


class ResetBitsProcess(OverworldEventCommand):
    """
    0F oo bb    reset bits
                oo - offset to reset bits in process memory
                bb - bits to reset
    """
    CMD_ID = 0xF
    SIZE = 3

    offset = cttypes.byte_prop(1)
    bits = cttypes.byte_prop(2)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 bits: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset), ('bits', bits)
        )


class ResetByte7E(OverworldEventCommand):
    """
    10 aaaa	reset byte	aaaa - address of byte to reset (+7E0000)
    """
    CMD_ID = 0x10
    SIZE = 3

    offset = cttypes.bytes_prop(1, 2)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset)
        )


class IncrementByte7E(OverworldEventCommand):
    """
    11 aaaa	increment	aaaa - address to increment (+7E0000)
    """
    CMD_ID = 0x11
    SIZE = 3

    offset = cttypes.bytes_prop(1, 2)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset)
        )


class DecrementByte7E(OverworldEventCommand):
    """
    12 aaaa	decrement	aaaa - address to decrement (+7E0000)
    """
    CMD_ID = 0x12
    SIZE = 3

    offset = cttypes.bytes_prop(1, 2)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset)
        )


class AssignByte7E(OverworldEventCommand):
    """
    13 aaaa vv	assignment
        aaaa - address to store to (+7E0000)
        vv - value to store
    """
    CMD_ID = 0x13
    SIZE = 4

    offset = cttypes.bytes_prop(1, 2)
    value = cttypes.byte_prop(3)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 value: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset), ('value', value)
        )


class SetBits7E(OverworldEventCommand):
    """
    14 aaaa vv	set bits
        aaaa - address to store to (+7E0000)
        bb - bits to set
    """
    CMD_ID = 0x14
    SIZE = 4

    offset = cttypes.bytes_prop(1, 2)
    bits = cttypes.byte_prop(3)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 bits: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset), ('bits', bits)
        )


class ResetBits7E(OverworldEventCommand):
    """
    15 aaaa vv	reset bits
        aaaa - address to store to (+7E0000)
        bb - bits to reset
    """
    CMD_ID = 0x15
    SIZE = 4

    offset = cttypes.bytes_prop(1, 2)
    bits = cttypes.byte_prop(3)

    def __init__(self, *args,
                 offset: Optional[int] = None,
                 bits: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset', offset), ('bits', bits)
        )


class AssignProcessTo7E(OverworldEventCommand):
    """
    16 oo aaaa	assignment
        oo - offset to load from process memory
        aaaa - address to store to
    """
    CMD_ID = 0x16
    SIZE = 4

    offset_process_load = cttypes.byte_prop(1)
    offset_7e_store = cttypes.byte_prop(2, 2)

    def __init__(self, *args,
                 offset_process_load: Optional[int] = None,
                 offset_7e_store: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process_load', offset_process_load),
            ('offset_7e_store', offset_7e_store)
        )


class Assign7EtoProcess(OverworldEventCommand):
    """
    17 oo aaaa	assignment
        oo - offset to store to process memory
        aaaa - address to load from (+7E0000)
    """
    CMD_ID = 0x17
    SIZE = 4

    offset_process_store = cttypes.byte_prop(1)
    offset_7e_load = cttypes.bytes_prop(2, 2)

    def __init__(self, *args,
                 offset_process_store: Optional[int] = None,
                 offset_7e_load: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process_store', offset_process_store),
            ('offset_7e_load', offset_7e_load)
        )


class AssignProcessToProcess(OverworldEventCommand):
    """
    18 oo aa	assignment (unused)
        oo - offset to store to
        aa - offset to load from . both offsets use process memory
    """
    CMD_ID = 0x18
    SIZE = 3

    offset_process_store = cttypes.byte_prop(1)
    offset_process_load = cttypes.byte_prop(2)

    def __init__(self, *args,
                 offset_process_store: Optional[int] = None,
                 offset_process_load: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process_store', offset_process_store),
            ('offset_process_load', offset_process_load)
        )


class Assign7ETo7E(OverworldEventCommand):
    """
    19 aaaa oooo    assignment (unused)
        aaaa - address to store to (+7E0000)
        oooo - address to load from (+7E0000)
    """
    CMD_ID = 0x19
    SIZE = 5

    offset_7e_store = cttypes.bytes_prop(1, 2)
    offset_7e_load = cttypes.bytes_prop(3, 2)

    def __init__(self, *args,
                 offset_7e_store: Optional[int] = None,
                 offset_7e_load: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e_store', offset_7e_store),
            ('offset_7e_load', offset_7e_load)
        )


class Goto(OWLocalJumpCommand):
    """1A  aaaa     goto   aaaa - address to branch to"""
    CMD_ID = 0x1A
    SIZE = 3

    jump_address = cttypes.bytes_prop(1, 2)

    def __init__(self, *args,
                 jump_address: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('jump_address', jump_address),
        )


class DecrementUntilZero(OWLocalBranchCommand):
    """
    1B oo jj    decrement until zero
        oo - offset to decrement (for an address in memory)
        jj - bytes to jump if value is not zero
    """
    CMD_ID = 0x1B
    SIZE = 3

    offset_process = cttypes.byte_prop(1)
    jump_bytes = cttypes.byte_prop(2, is_signed=True)

    def __init__(self, *args,
                 offset_process_store: Optional[int] = None,
                 offset_process_load: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process_store', offset_process_store),
            ('offset_process_load', offset_process_load)
        )


class BranchIfProcessZero(OWLocalBranchCommand):
    """
    1C oo jj   if not zero  (unused)
        oo - offset to compare in process memory
        jj - bytes to jump if zero
    """
    CMD_ID = 0x1C
    SIZE = 3

    offset_process_compare = cttypes.byte_prop(1)
    jump_bytes = cttypes.byte_prop(2, is_signed=True)

    def __init__(self, *args,
                 offset_process_compare: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process_compare', offset_process_compare),
            ('jump_bytes', jump_bytes)
        )


class BranchIfProcessNotZero(OWLocalBranchCommand):
    """
    1D oo jj   if zero  (unused)
        oo - offset to compare in process memory
        jj - bytes to jump if zero
    """
    CMD_ID = 0x1D
    SIZE = 3

    offset_process_compare = cttypes.byte_prop(1)
    jump_bytes = cttypes.byte_prop(2, is_signed=True)

    def __init__(self, *args,
                 offset_process_compare: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process_compare', offset_process_compare),
            ('jump_bytes', jump_bytes)
        )


class BranchIfProcessNotEqualValue(OWLocalBranchCommand):
    """
    1E oo vv jj    if equal
        oo - offset to check in process memory
        vv - value to compare to
        jj - byte to jump if not equal
    """
    CMD_ID = 0x1E
    SIZE = 4

    offset_process = cttypes.byte_prop(1)
    value_compare = cttypes.byte_prop(2)
    jump_bytes = cttypes.byte_prop(3, is_signed=True)

    def __init__(self, *args,
                 offset_process: Optional[int] = None,
                 value_compare: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process', offset_process),
            ('value_compare', value_compare),
            ('jump_bytes', jump_bytes)
        )


class BranchIfProcessEqualValue(OverworldEventCommand):
    """
    1F oo vv jj    if equal
        oo - offset to check in process memory
        vv - value to compare to
        jj - byte to jump if equal
    """
    CMD_ID = 0x1F
    SIZE = 4

    offset_process = cttypes.byte_prop(1)
    value_compare = cttypes.byte_prop(2)
    jump_bytes = cttypes.byte_prop(3, is_signed=True)

    def __init__(self, *args,
                 offset_process: Optional[int] = None,
                 value_compare: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process', offset_process),
            ('value_compare', value_compare),
            ('jump_bytes', jump_bytes)
        )


class BranchIfProcessBitsSet(OWLocalBranchCommand):
    """
    20 oo bb jj    if bits reset
        oo - offset to check in process memory
        bb - bits to check
        jj - bytes to jump if bits set
    """
    CMD_ID = 0x20
    SIZE = 4

    offset_process = cttypes.byte_prop(1)
    bits_check = cttypes.byte_prop(2)
    jump_bytes = cttypes.byte_prop(3, is_signed=True)

    def __init__(self, *args,
                 offset_process: Optional[int] = None,
                 bits_check: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process', offset_process),
            ('bits_check', bits_check),
            ('jump_bytes', jump_bytes)
        )


class BranchIfProcessBitsReset(OWLocalBranchCommand):
    """
    21 oo bb jj    if bits reset
        oo - offset to check in process memory
        bb - bits to check
        jj - bytes to jump if bits set
    """
    CMD_ID = 0x21
    SIZE = 4

    offset_process = cttypes.byte_prop(1)
    bits_check = cttypes.byte_prop(2)
    jump_bytes = cttypes.byte_prop(3, is_signed=True)

    def __init__(self, *args,
                 offset_process: Optional[int] = None,
                 bits_check: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_process', offset_process),
            ('bits_check', bits_check),
            ('jump_bytes', jump_bytes)
        )


class BranchIf7EZero(OWLocalBranchCommand):
    """
    22 aaaa jj    if not zero
        aaaa - address to check (+7E0000)
        jj - bytes to jump if value is zero
    """
    CMD_ID = 0x22
    SIZE = 4

    offset_7e = cttypes.bytes_prop(1, 2)
    jump_bytes = cttypes.byte_prop(3, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('jump_bytes', jump_bytes),
        )


class BranchIf7ENotZero(OWLocalBranchCommand):
    """
    23 aaaa jj    if zero
        aaaa - address to check (+7E0000)
        jj - bytes to jump if value is not zero
    """
    CMD_ID = 0x23
    SIZE = 4

    offset_7e = cttypes.bytes_prop(1, 2)
    jump_bytes = cttypes.byte_prop(3, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('jump_bytes', jump_bytes),
        )


class BranchIf7ENotEqualValue(OWLocalBranchCommand):
    """
    24 aaaa vv jj    if equal
        aaaa - address to compare
        vv - value to compare
        jj - bytes to jump if value is not equal to memory
    """
    CMD_ID = 0x24
    SIZE = 5

    offset_7e = cttypes.bytes_prop(1, 2)
    value_compare = cttypes.byte_prop(3)
    jump_bytes = cttypes.byte_prop(4, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 value_compare: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('value_compare', value_compare),
            ('jump_bytes', jump_bytes),
        )


class BranchIf7EEqualValue(OWLocalBranchCommand):
    """
    25 aaaa vv jj    if not equal
        aaaa - address to compare
        vv - value to compare
        jj - bytes to jump if value is equal to memory
    """
    CMD_ID = 0x25
    SIZE = 5

    offset_7e = cttypes.bytes_prop(1, 2)
    value_compare = cttypes.byte_prop(3)
    jump_bytes = cttypes.byte_prop(4, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 value_compare: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('value_compare', value_compare),
            ('jump_bytes', jump_bytes),
        )


class BranchIf7EBitsSet(OWLocalBranchCommand):
    """
    26 aaaa bb jj    check bits reset
        aaaa - address to check bits in (+7E0000)
        bb - bits to check
        jj - bytes to jump if bits set
    """
    CMD_ID = 0x26
    SIZE = 5

    offset_7e = cttypes.bytes_prop(1, 2)
    bits_check = cttypes.byte_prop(3)
    jump_bytes = cttypes.byte_prop(4, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 bits_check: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('bits_check', bits_check),
            ('jump_bytes', jump_bytes),
        )


class BranchIf7EBitsReset(OWLocalBranchCommand):
    """
    27 aaaa bb jj    check bits reset
        aaaa - address to check bits in (+7E0000)
        bb - bits to check
        jj - bytes to jump if bits not set
    """
    CMD_ID = 0x27
    SIZE = 5

    offset_7e = cttypes.bytes_prop(1, 2)
    bits_check = cttypes.byte_prop(3)
    jump_bytes = cttypes.byte_prop(4, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 bits_check: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('bits_check', bits_check),
            ('jump_bytes', jump_bytes),
        )


class Unknown28(OverworldEventCommand):
    """unknown - does not appear to actually use second byte"""
    CMD_ID = 0x28
    SIZE = 2


class Unknown29(OverworldEventCommand):
    """unknown - does not appear to actually use second byte"""
    CMD_ID = 0x29
    SIZE = 2


class Unknown2A(OverworldEventCommand):
    """2A ?? ??    unused . unknown - arguments do not appear to be used"""
    CMD_ID = 0x2A
    SIZE = 3


class Unknown2B(OverworldEventCommand):
    """2B ?? ??    unused . unknown - arguments do not appear to be used"""
    CMD_ID = 0x2B
    SIZE = 3


class SetObjectCoord(OverworldEventCommand):
    """
    2C xxxx yyyy    set obj coord
        xxxx - X Coord
        yyyy - Y Coord . coords measured in pixels
    """
    CMD_ID = 0x2C
    SIZE = 5

    x_coord = cttypes.bytes_prop(1, 2)
    y_coord = cttypes.bytes_prop(3, 2)

    def __init__(self, *args,
                 x_coord: Optional[int] = None,
                 y_coord: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('x_coord', x_coord),
            ('y_coord', y_coord),
        )


class SkipByte(OverworldEventCommand):
    """
    2D bb    skip next byte	unused
    literally does nothing but skip the next byte (next byte may still be
    used by other commands though)
    """
    CMD_ID = 0x2D
    SIZE = 2


class Unknown2E(OverworldEventCommand):
    """
    2E ???? ????
    """
    CMD_ID = 0x2E
    SIZE = 5


class Unknown2F(OverworldEventCommand):
    """
    2F ???? ????
    """
    CMD_ID = 0x2F
    SIZE = 5


class LoadSprite(OverworldEventCommand):
    """
    30 ss	load sprite	ss - index for sprite to load
    """
    CMD_ID = 0x30
    SIZE = 2

    sprite_index = cttypes.byte_prop(1)

    def __init__(self, *args,
                 sprite_index: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('sprite_index', sprite_index),
        )


class Pause31(OverworldEventCommand):
    """31 tt	pause	Appears to be a pause command of sorts"""
    CMD_ID = 0x31
    SIZE = 2


class Pause32(OverworldEventCommand):
    """32 tt	pause	Appears to be a pause command of sorts"""
    CMD_ID = 0x32
    SIZE = 2


class Unknown33(OverworldEventCommand):
    """33 ?? ???? ???? ????"""
    CMD_ID = 0x33
    SIZE = 8


class CallLocalFunction(OverworldEventCommand):
    """34 aaaa	call function	aaaa - address of (local) function to call"""
    CMD_ID = 0x34
    SIZE = 3

    bank_c2_offset = cttypes.bytes_prop(1, 2)

    def __init__(self, *args,
                bank_c2_offset: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('bank_c2_offset', bank_c2_offset),
        )


class SetDestCoord(OverworldEventCommand):
    """
    35 xx yy    set dest coord
        xx - X coord
        yy - Y coord . sets destination coordinates for end of Boat trip
    """
    CMD_ID = 0x35
    SIZE = 3

    x_coord = cttypes.byte_prop(1)
    y_coord = cttypes.byte_prop(2)

    def __init__(self, *args,
                 x_coord: Optional[int] = None,
                 y_coord: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('x_coord', x_coord),
            ('y_coord', y_coord),
        )


class GoSubroutine(OWLocalJumpCommand):
    """
    36 aaaa    go sub
        aaaa - address to branch to
        stores current pointer before branching to subroutine
    """
    CMD_ID = 0x36
    SIZE = 3

    jump_address = cttypes.bytes_prop(1, 2)

    def __init__(self, *args,
                 jump_address: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('jump_address', jump_address),
        )


class Return(OverworldEventCommand):
    """37	return	returns from a subroutine"""
    CMD_ID = 0x37
    SIZE = 1


class SetUnknownFacing(OverworldEventCommand):
    """
    38 xx
        xx - multipurpose variable?
             06 - sets destination facing for end of Boat trip
    """
    CMD_ID = 0x38
    SIZE = 2

    facing = cttypes.byte_prop(1, 0x06)


class SetSpeed(OverworldEventCommand):
    """
    39 ss    set speed
        ss - speed of sprite
            00 - fastest . sets speed of Boat sprite in 1000 AD
    """
    CMD_ID = 0x39
    SIZE = 2

    speed = cttypes.byte_prop(1)

    def __init__(self, *args,
                 speed: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('speed', speed),
        )


class Unknown3A(OverworldEventCommand):
    """
    3A ????    unused
        unknown - looks like it compares the argument to a value in memory
        and if greater or equal it makes a direct page jump
    """
    CMD_ID = 0x3A
    SIZE = 3


class PlayPositionalSound3B(OverworldEventCommand):
    """
    3B ss pp    play positional sound
        ss - sound effect index
        pp - panning position (same as AllPurpSnd 18) . Overlaps 3C
    """
    CMD_ID = 0x3B
    SIZE = 3

    sound_effect_index = cttypes.byte_prop(1)
    panning_position = cttypes.byte_prop(2)

    def __init__(self, *args,
                 sound_effect_index: Optional[int] = None,
                 panning_position: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('sound_effect_index', sound_effect_index),
            ('panning_position', panning_position)
        )


class PlayPositionalSound3C(OverworldEventCommand):
    """
    3C ss pp    play positional sound
        ss - sound effect index
        pp - panning position (same as AllPurpSnd 19) . overlapped by 3B
    """
    CMD_ID = 0x3C
    SIZE = 3

    sound_effect_index = cttypes.byte_prop(1)
    panning_position = cttypes.byte_prop(2)

    def __init__(self, *args,
                 sound_effect_index: Optional[int] = None,
                 panning_position: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('sound_effect_index', sound_effect_index),
            ('panning_position', panning_position)
        )


class PlaySong(OverworldEventCommand):
    """
    3D ss    play song
        ss - song to play . only plays if 7F01ED is equal to 00
    """
    CMD_ID = 0x3D
    SIZE = 2

    song_index = cttypes.byte_prop(1)

    def __init__(self, *args,
                 song_index: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('song_index', song_index)
        )


class Unknown3E(OverworldEventCommand):
    """
    3E ??    unknown - may have something to do with layer 3
    """
    CMD_ID = 0x3E
    SIZE = 2


class Unknown3F(OverworldEventCommand):
    """3F ???? ????"""
    CMD_ID = 0x3F
    SIZE = 5


class Unknown40(OverworldEventCommand):
    """40 ???? ????"""
    CMD_ID = 0x40
    SIZE = 5


class DirectPageJump41(OverworldEventCommand):
    """
    41	direct page jump	unused . identical to 06
    """
    CMD_ID = 0x41
    SIZE = 1


class Unknown42(OverworldEventCommand):
    """42 ????    unused"""
    CMD_ID = 0x42
    SIZE = 3


class AddProcess43(OWLongJumpCommand):
    """
    43 aaaaaa    add proc
        aaaaaa - memory address
                 adds extra processing to be done after an ""end"" is reached,
                 slightly different from 09"
    """
    CMD_ID = 0x43
    SIZE = 4

    jump_address = cttypes.bytes_prop(1, 3)

    def __init__(self, *args,
                 jump_address: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('jump_address', jump_address)
        )


class SetExitActive(OverworldEventCommand):
    """
    44 ii oo    set negative
        ii - index to subroutine
            - When ii==0, set a normal exit
            - When ii==1, set a special exit (e.g. vortex exit)
              0x7E8300 + 3*(oo)
        oo - offset to set negative (exit index)
    """
    CMD_ID = 0x44
    SIZE = 3

    exit_type = cttypes.byte_prop(1)
    exit_index = cttypes.byte_prop(2)

    def __init__(self, *args,
                 exit_type: Optional[int] = None,
                 exit_index: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('exit_type', exit_type),
            ('exit_index', exit_index)
        )


class SetExitInactive(OverworldEventCommand):
    """
    45 ii oo    set positive
        ii - index to subroutine
            - When ii==0, set a normal exit
            - When ii==1, set a special exit (e.g. vortex exit)
              0x7E8300 + 3*(oo)
        oo - offset to set positive (exit index)
    """
    CMD_ID = 0x45
    SIZE = 3

    exit_type = cttypes.byte_prop(1)
    exit_index = cttypes.byte_prop(2)

    def __init__(self, *args,
                 exit_type: Optional[int] = None,
                 exit_index: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('exit_type', exit_type),
            ('exit_index', exit_index)
        )


class AddValueToProcessMemory(OverworldEventCommand):
    """
    46 oo vv    add
        oo - offset to add to in process memory
        vv - value to add
    """
    CMD_ID = 0x46
    SIZE = 3

    process_offset = cttypes.byte_prop(1)
    value = cttypes.byte_prop(2)

    def __init__(self, *args,
                 process_offset: Optional[int] = None,
                 value: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('process_offset', process_offset),
            ('value', value)
        )


class SubValueFromProcessMemory(OverworldEventCommand):
    """
    47 oo vv    subtract
        oo - offset to subtract from in process memory
        vv - value to subtract
    """
    CMD_ID = 0x47
    SIZE = 3

    process_offset = cttypes.byte_prop(1)
    value = cttypes.byte_prop(2)

    def __init__(self, *args,
                 process_offset: Optional[int] = None,
                 value: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('process_offset', process_offset),
            ('value', value)
        )


class AddValueTo7EMemory(OverworldEventCommand):
    """
    48 aaaa vv    add
        aaaa - address to add to (+7E0000)
        vv - value to add
    """
    CMD_ID = 0x48
    SIZE = 4

    memory_7e_offset = cttypes.bytes_prop(1, 2)
    value = cttypes.byte_prop(3)

    def __init__(self, *args,
                 memory_7e_offset: Optional[int] = None,
                 value: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('memory_7e_offset', memory_7e_offset),
            ('value', value)
        )


class SubValueFrom7EMemory(OverworldEventCommand):
    """
    49 aaaa vv    subtract
        aaaa - address to subtract from (+7E0000)
        vv - value to subtrace
    """
    CMD_ID = 0x49
    SIZE = 4

    memory_7e_offset = cttypes.bytes_prop(1, 2)
    value = cttypes.byte_prop(3)

    def __init__(self, *args,
                 memory_7e_offset: Optional[int] = None,
                 value: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('memory_7e_offset', memory_7e_offset),
            ('value', value)
        )


class PlaySongAlways(OverworldEventCommand):
    """
    4A ss	play song	ss - song to play
    """
    CMD_ID = 0x4A
    SIZE = 2

    song_index = cttypes.byte_prop(1)

    def __init__(self, *args,
                 song_index: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('song_index', song_index)
        )


class Unknown4B(OverworldEventCommand):
    """4B ?? ?? ?? ??"""
    CMD_ID = 0x4B
    SIZE = 5


class BranchIf7ELessThan(OWLocalBranchCommand):
    """
    4C aaaa vv jj    if less than
        aaaa - address to compare (in 0x7E)
        vv - value to compare
        jj - bytes to jump
    """
    CMD_ID = 0x4C
    SIZE = 5

    offset_7e = cttypes.bytes_prop(1, 2)
    value = cttypes.byte_prop(3)
    jump_bytes = cttypes.byte_prop(4, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 value: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('value', value),
            ('jump_bytes', jump_bytes)
        )


class BranchIf7EGreaterOrEqual(OWLocalBranchCommand):
    """
    4D aaaa vv jj    if greater or equal
        aaaa - address to compare
        vv - value to compare
        jj - bytes to jump
    """
    CMD_ID = 0x4D
    SIZE = 5

    offset_7e = cttypes.bytes_prop(1, 2)
    value = cttypes.byte_prop(3)
    jump_bytes = cttypes.byte_prop(4, is_signed=True)

    def __init__(self, *args,
                 offset_7e: Optional[int] = None,
                 value: Optional[int] = None,
                 jump_bytes: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('offset_7e', offset_7e),
            ('value', value),
            ('jump_bytes', jump_bytes)
        )


class CallExternalFunction(OWLongJumpCommand):
    """
    4E aaaaaa    call function
        aaaaaa - address of (non-local) function to call
    """
    CMD_ID = 0x4E
    SIZE = 4

    jump_address = cttypes.bytes_prop(1, 3)

    def __init__(self, *args,
                 jump_address: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('jump_address', jump_address)
        )


class CopyTiles(OverworldEventCommand):
    """
    4F ll xx yy mm uu vv ww hh    copy tiles
        ll - source layer
        xx - source X Coord, yy - source Y Coord,  mm - dest layer
        uu - dest X Coord, vv - dest Y Coord
        ww - copy width, hh - copy height
    """
    CMD_ID = 0x4F
    SIZE = 9

    source_layer = cttypes.byte_prop(1)
    source_x = cttypes.byte_prop(2)
    source_y = cttypes.byte_prop(3)

    dest_layer = cttypes.byte_prop(4)
    dest_x = cttypes.byte_prop(5)
    dest_y = cttypes.byte_prop(6)

    copy_width = cttypes.byte_prop(7)
    copy_height = cttypes.byte_prop(8)

    def __init__(self, *args,
                 source_layer: Optional[int] = None,
                 source_x: Optional[int] = None,
                 source_y: Optional[int] = None,
                 dest_layer: Optional[int] = None,
                 dest_x: Optional[int] = None,
                 dest_y: Optional[int] = None,
                 copy_width: Optional[int] = None,
                 copy_height: Optional[int] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('source_layer', source_layer),
            ('source_x', source_x), ('source_y', source_y),
            ('dest_layer', dest_layer),
            ('dest_x', dest_x), ('dest_y', dest_y),
            ('copy_width', copy_width), ('copy_height', copy_height)
        )


class Unknown50(OverworldEventCommand):
    """50 ?? ?? ?? ??"""
    CMD_ID = 0x50
    SIZE = 5


class Unknown51(OverworldEventCommand):
    """51 ?? ??"""
    CMD_ID = 0x51
    SIZE = 3


class End(OverworldEventCommand):
    """
    52    end
        appears to be a break / end style command . not sure as to its severity
    """
    CMD_ID = 0x52
    SIZE = 1


_cmd_id_dict: dict[int, Type[OverworldEventCommand]] = {
    0: InitMemory, 1: SetPalette, 2: Assign02, 3: Unknown03,
    4: LoadPalette,
    5: ChangeLocation, 6: DirectPageJump06, 7: SetTile, 8: PCSub,
    9: AddProcess09, 0xA: Assign0A, 0xB: IncrementProcessMemory,
    0xC: DecrementProcessMemory, 0xD: AssignProcess, 0xE: SetBitsProcess,
    0xF: ResetBitsProcess, 0x10: ResetByte7E, 0x11: IncrementByte7E,
    0x12: DecrementByte7E, 0x13: AssignByte7E, 0x14:  SetBits7E,
    0x15: ResetBits7E, 0x16: AssignProcessTo7E, 0x17: Assign7EtoProcess,
    0x18: AssignProcessToProcess, 0x19: Assign7ETo7E, 0x1A: Goto,
    0x1B: DecrementUntilZero, 0x1C: BranchIfProcessZero,
    0x1D: BranchIfProcessNotZero,
    0x1E: BranchIfProcessNotEqualValue, 0x1F: BranchIfProcessEqualValue,
    0x20: BranchIfProcessBitsSet, 0x21: BranchIfProcessBitsReset,
    0x22: BranchIf7EZero, 0x23: BranchIf7ENotZero,
    0x24: BranchIf7ENotEqualValue, 0x25: BranchIf7EEqualValue,
    0x26: BranchIf7EBitsSet, 0x27: BranchIf7EBitsReset,
    0x28: Unknown28, 0x29: Unknown29, 0x2A: Unknown2A, 0x2B: Unknown2B,
    0x2C: SetObjectCoord, 0x2D: SkipByte, 0x2E: Unknown2E, 0x2F: Unknown2F,
    0x30: LoadSprite, 0x31: Pause31, 0x32: Pause32, 0x33: Unknown33,
    0x34: CallLocalFunction, 0x35: SetDestCoord, 0x36: GoSubroutine,
    0x37: Return, 0x38: SetUnknownFacing, 0x39: SetSpeed, 0x3A: Unknown3A,
    0x3B: PlayPositionalSound3B, 0x3C: PlayPositionalSound3C, 0x3D: PlaySong,
    0x3E: Unknown3E, 0x3F: Unknown3F, 0x40: Unknown40,
    0x41: DirectPageJump41, 0x42: Unknown42, 0x43: AddProcess43,
    0x44: SetExitActive, 0x45: SetExitInactive,
    0x46: AddValueToProcessMemory, 0x47: SubValueFromProcessMemory,
    0x48: AddValueTo7EMemory, 0x49: SubValueFrom7EMemory,
    0x4A: PlaySongAlways, 0x4B: Unknown4B,
    0x4C: BranchIf7ELessThan, 0x4D: BranchIf7EGreaterOrEqual,
    0x4E: CallExternalFunction, 0x4F: CopyTiles, 0x50: Unknown50,
    0x51: Unknown51, 0x52:  End
}


def get_command(buf: bytes, pos: int = 0) -> OverworldEventCommand:
    """Return the command at a given position in a buffer."""
    cmd_id = buf[pos]
    cmd_type = _cmd_id_dict[cmd_id]
    cmd_size = cmd_type.SIZE

    if pos + cmd_size > len(buf):
        raise IndexError("Command would exceed buffer length")

    return cmd_type(buf[pos:pos+cmd_size])


def is_branch_command(
        command: OverworldEventCommand
) -> TypeGuard[OWLocalBranchCommand | OWLocalJumpCommand |
               OWLongJumpCommand]:
    """Convenience for testing whether a command jumps."""
    if isinstance(command,
                  OWLocalBranchCommand | OWLocalJumpCommand |
                  OWLongJumpCommand):
        return True
    return False


def main():
    """Do main stuff"""
    data = bytearray.fromhex(
        "00134500021346004436690627040180081A6C042704014008"
        "1A7E0427A71B04081A7F04"
    )

    pos = 0
    while pos < len(data):
        cmd = get_command(data, pos)
        print(f'[{pos:04X}] {cmd}')

        pos += len(cmd)


if __name__ == '__main__':
    main()

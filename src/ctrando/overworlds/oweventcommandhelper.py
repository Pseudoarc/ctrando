"""
Helpful functions for generating overworld commands.
"""
from typing import Optional

from ctrando.common import memory
from ctrando.overworlds import oweventcommand as owc


def flag_to_ow_flag(flag: memory.Flags | memory.FlagData) -> memory.FlagData:
    """Convert a usual 0x7F flag to its overworld version."""
    if isinstance(flag, memory.Flags):
        data = flag.value
    else:
        data = flag

    if data.address not in range(0x7F01F0, 0x800000):
        raise ValueError("OW Flags must be in range(0x7F0100, 0x800000)")

    address = data.address - 0x7F01F0 + 0x7E1BA7

    return memory.FlagData(address, data.bit)


def branch_if_storyline_lt(value: int, to_label: Optional[str] = None):
    """
    Return a command that branches if the storyline counter < value.
    """
    return owc.BranchIf7ELessThan(
        offset_7e=memory.Memory.OW_STORYLINE_COUNTER & 0xFFFF,
        value=value, to_label=to_label)


def branch_if_storyline_ge(value: int, to_label: Optional[str] = None):
    """
    Return a command that branches if the storyline counter < value.
    """
    return owc.BranchIf7EGreaterOrEqual(
        offset_7e=memory.Memory.OW_STORYLINE_COUNTER & 0xFFFF,
        value=value, to_label=to_label)


def branch_if_flag_set(
        flag_7f: memory.Flags | memory.FlagData,
        to_label: Optional[str] = None
        ) -> owc.BranchIf7EBitsSet:
    """Return an OW Command which branches when the given 7F flag is set."""
    ow_flagdata = flag_to_ow_flag(flag_7f)

    return owc.BranchIf7EBitsSet(
        offset_7e=ow_flagdata.address & 0xFFFF,
        bits_check=ow_flagdata.bit,
        to_label=to_label
    )


def branch_if_flag_reset(
        flag_7f: memory.Flags | memory.FlagData,
        to_label: Optional[str] = None
        ) -> owc.BranchIf7EBitsReset:
    """Return an OW Command which branches when the given 7F flag is reset."""
    ow_flagdata = flag_to_ow_flag(flag_7f)

    return owc.BranchIf7EBitsReset(
        offset_7e=ow_flagdata.address & 0xFFFF,
        bits_check=ow_flagdata.bit,
        to_label=to_label
    )


"""Module to support modification of CT overworld events."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Type, NamedTuple

from ctrando.common import ctrom, cttypes
from ctrando.overworlds import oweventcommand as owc


_ow_event_rw = cttypes.CompressedAbsPtrTableRW(0x022A30)


class InvalidOffsetException(Exception):
    """Exception to raise when an offset does not correspond to a command."""


class CommandNotFoundException(Exception):
    """Exception to raise when failing to find a command."""


class InvalidJumpException(Exception):
    """Exception to raise when something goes wrong with a jump command."""


@dataclass
class _OWEventRecord:
    offset: int
    command: owc.OverworldEventCommand


@dataclass
class _JumpRecord:
    jump_cmd_pos: int
    target_cmd_pos: int


CommandList = str | owc.OverworldEventCommand | \
    list[str | owc.OverworldEventCommand]


class OverworldEvent:
    """Class for manipulating overworld event data."""
    def __init__(self, data: bytes):

        self.commands: list[owc.OverworldEventCommand] = []
        self.jump_cmd_indices = []
        self.labels: dict[str, int] = {}

        offset_index_dict: dict[int, int] = {}
        index_offset_dict: dict[int, int] = {}

        pos = 0
        index = 0
        while pos < len(data):
            cmd = owc.get_command(data, pos)
            self.commands.append(cmd)
            if isinstance(cmd, owc.OWBranchCommand):
                self.jump_cmd_indices.append(len(self.commands)-1)

            offset_index_dict[pos] = index
            index_offset_dict[index] = pos
            pos += len(cmd)
            index += 1

        # Resolve jumps to command index.
        self.__internal_label_counter = 0
        for index in self.jump_cmd_indices:
            command = self.commands[index]
            command_offset = index_offset_dict[index]
            target_offset = get_jump_target(command, command_offset)
            if target_offset in range(0x1900):
                target_index = offset_index_dict[target_offset]
                self.__add_internal_label(index, target_index)

        # for record in self.cmd_records:
        #     print(f'[{record.offset:04X}] {record.command}')

    def get_bytes(self) -> bytearray:
        """Get the event as bytes for a CTRom"""
        command_copies = [
            command.get_copy() for command in self.commands
        ]

        index_offset_dict: dict[int, int] = {}
        offset = 0
        for index, command in enumerate(command_copies):
            index_offset_dict[index] = offset
            offset += len(command)
        index_offset_dict[len(command_copies)] = offset

        for index in self.jump_cmd_indices:
            command = command_copies[index]
            if not isinstance(command, owc.OWBranchCommand):
                print(self.jump_cmd_indices)
                print(index)
                raise TypeError

            if command.to_label is not None:
                target = self.labels[command.to_label]
                set_jump_target(
                    command,
                    index_offset_dict[index],
                    index_offset_dict[target]
                )

        out_bytes = b''.join(command[:] for command in command_copies)

        return bytearray(out_bytes)

    @classmethod
    def from_command_list(
            cls,
            commands: CommandList
    ) -> OverworldEvent:
        """
        Create an OverworldEvent from a list of commands and labels.
        """
        if isinstance(commands, str | owc.OverworldEventCommand):
            commands = [commands]

        labels: dict[str, int] = {}
        jump_indices: list[int] = []
        owcommands: list[owc.OverworldEventCommand] = []

        offset_index_dict: dict[int, int] = {}
        index_offset_dict: dict[int, int] = {}

        command_offset = 0
        command_index = 0
        for item in commands:
            if isinstance(item, str):
                if item in labels:
                    raise ValueError("Repeat Label")
                labels[item] = command_index
            else:
                if isinstance(
                        item, owc.OWBranchCommand
                ):
                    jump_indices.append(command_index)
                owcommands.append(item)

                offset_index_dict[command_offset] = command_index
                index_offset_dict[command_index] = command_offset
                command_offset += len(item)
                command_index += 1

        # Record the end of the event as well.
        offset_index_dict[command_offset] = command_index
        index_offset_dict[command_index] = command_offset

        Record = NamedTuple("Record", [('from_index', int),
                                       ('to_index', int)])
        records: list[Record] = []

        # Resolve jumps.
        for index in jump_indices:
            command = owcommands[index]
            if not isinstance(command, owc.OWBranchCommand):
                raise TypeError

            if (
                    command.to_label is not None and
                    cls._is_label_internal(command.to_label)
            ):
                raise ValueError("User-defined labels must begin with alnum")

            if command.to_label is None:
                # Add an internal label for the jump.
                command_offset = index_offset_dict[index]
                target_offset = get_jump_target(command, command_offset)

                if target_offset in range(0x1900):  # really internal
                    target_index = offset_index_dict[target_offset]
                    records.append(Record(from_index=index,
                                          to_index=target_index))

        ret_owevent = OverworldEvent(b'')
        ret_owevent.commands = owcommands
        ret_owevent.jump_cmd_indices = jump_indices
        ret_owevent.labels.update(labels)

        for from_index, to_index in records:
            ret_owevent.__add_internal_label(from_index, to_index)

        return ret_owevent

    def __add_internal_label(self, from_index, to_index):
        command = self.commands[from_index]
        if isinstance(command, owc.OWBranchCommand):
            label = f"_{self.__internal_label_counter}"
            self._set_label(to_index, label)
            command.to_label = label
            self.__internal_label_counter += 1
        else:
            raise TypeError("From command is not a branch")

    def _set_label(self, index: int, label: str):
        self.labels[label] = index

    def set_label(self, index: int, label: str):
        """
        Mark the given offset with a label.  Error if label exists.
        """
        if not label[0].isalnum():
            raise ValueError(
                "User labels must begin with a letter or number.")

        if label in self.labels:
            raise ValueError("Redefinition of existing label")

        self._set_label(index, label)

    def get_label(self, index: int) -> str:
        """
        Get a label for the given index.
        """

        # Use the internal label counter to make sure we never re-gen the
        # same label.
        while True:
            label = f"label_{self.__internal_label_counter}"
            if label in self.labels:
                self.__internal_label_counter += 1
            else:
                self.set_label(index, label)
                return label

    def replace_jump_command(
            self,
            index: int,
            new_command: owc.OWBranchCommand,
    ):
        """
        Replace the branching command at the given index.  Preserve the jump.
        """
        command = self.commands[index]
        if not isinstance(command, owc.OWBranchCommand):
            print(command)
            raise TypeError("Command is not a branch.")

        if command.to_label is None:
            raise ValueError("No label set on branch.")

        new_command = new_command.get_copy()
        new_command.to_label = command.to_label
        self.commands[index] = new_command

    def delete_commands(
            self,
            del_st_index: int,
            del_end_index: Optional[int] = None
    ):
        """
        Delete all commands in the given region and update labels.  If end
        is not given, just delete the command at del_st_index.
        """
        if del_end_index is None:
            del_end_index = del_st_index+1
        self.replace_commands(del_st_index, del_end_index, [])

    def insert_commands(
            self,
            insertion_index: int,
            ins_commands: CommandList | OverworldEvent
    ):
        """Insert commands at given index"""
        self.replace_commands(insertion_index, insertion_index, ins_commands)

    def replace_commands(
            self,
            del_st_index: int,
            del_end_index: int,
            commands: CommandList | OverworldEvent,
    ):
        """
        Replace the commands in [del_st_index, del_end_index).
        """

        if not isinstance(commands, OverworldEvent):
            if isinstance(commands, str | owc.OverworldEventCommand):
                commands = [commands]
            ins_event = OverworldEvent.from_command_list(commands)
        else:
            ins_event = commands

        num_inserted = len(ins_event.commands)
        num_deleted = del_end_index - del_st_index
        command_len_delta = num_inserted - num_deleted

        # Deletion stuff:
        self.jump_cmd_indices = [
            index for index in self.jump_cmd_indices
            if index not in range(del_st_index, del_end_index)
        ]

        # Check for jumps invalidated by the deletion
        for index in self.jump_cmd_indices:

            command = self.commands[index]
            if not isinstance(command, owc.OWBranchCommand):
                raise TypeError

            if command.to_label is not None:
                target = self.labels[command.to_label]
                if target in range(del_st_index+1, del_end_index):
                    raise InvalidJumpException("Jump into deleted region")

        # Delete labels inside the deleted region.
        # Note:  We allow labels to the start of the deleted region.
        self.labels = {
            label: target for label, target in self.labels.items()
            if target not in range(del_st_index+1, del_end_index)
        }

        # Insertion Stuff:
        self.commands[del_st_index: del_end_index] = ins_event.commands

        self.jump_cmd_indices = [
            index if index < del_st_index else index+command_len_delta
            for index in self.jump_cmd_indices
        ]

        # Shift own labels ahead
        for label, label_index in self.labels.items():
            if label_index > del_end_index:
                self.labels[label] += command_len_delta

        # Merge in *User* labels from the inserted commands
        for label in ins_event.labels:
            if not OverworldEvent._is_label_internal(label):
                self.set_label(ins_event.labels[label] + del_st_index,
                               label)

        # Merge in internal labels from the inserted commands
        for index in ins_event.jump_cmd_indices:
            command = ins_event.commands[index]
            if not isinstance(command, owc.OWBranchCommand):
                raise TypeError

            self.jump_cmd_indices.append(index+del_st_index)
            to_label = command.to_label
            if to_label is not None:
                if OverworldEvent._is_label_internal(to_label):
                    from_index = del_st_index + index
                    to_index = del_st_index + ins_event.labels[to_label]
                    self.__add_internal_label(from_index, to_index)

    def find_next_exact_command(
            self,
            find_command: owc.OverworldEventCommand,
            start: Optional[int] = None,
            end: Optional[int] = None
    ) -> int:
        """
        Find the next occurrence of the given command.  Ignores jump targets.
        """
        start = 0 if start is None else start
        end = len(self.commands) if end is None else end

        command_copy = find_command.get_copy()

        jump_attr: Optional[str] = None
        if isinstance(command_copy, owc.OWLocalBranchCommand):
            jump_attr = 'jump_bytes'
        elif isinstance(command_copy,
                        owc.OWLongJumpCommand | owc.OWLocalJumpCommand):
            jump_attr = 'jump_address'

        for ind, command in enumerate(self.commands[start:end]):
            if command.cmd_id == command_copy.cmd_id and jump_attr is not None:
                setattr(command_copy, jump_attr, getattr(command, jump_attr))

            if command[:] == command_copy[:]:
                return ind + start

        raise CommandNotFoundException

    def find_next_command(self,
                          command_type: (
                              Type[owc.OverworldEventCommand] |
                              list[Type[owc.OverworldEventCommand]]
                          ),
                          start_offset: Optional[int] = None,
                          end_offset: Optional[int] = None
                          ) -> tuple[int, owc.OverworldEventCommand]:
        """
        Find a command of a particular type.
        """

        if start_offset is None:
            start_offset = 0
        if end_offset is None:
            end_offset = len(self.commands)

        if isinstance(command_type, type):
            command_type = [command_type]

        for index in range(start_offset, end_offset):
            command = self.commands[index]
            if type(command) in command_type:
                return index, command

        raise CommandNotFoundException

    def find_index_of_offset(self, bank_7f_offset: int):
        """
        Find the index of the command with the given offset in bank 0x7F.
        """
        target_offset = bank_7f_offset - 0x400
        cur_offset = 0
        for ind, command in enumerate(self.commands):

            if cur_offset > target_offset:
                raise CommandNotFoundException

            if cur_offset == target_offset:
                return ind

            cur_offset += len(command)

        raise CommandNotFoundException

    def find_offset_of_index(self, index: int):
        """
        Find the bank 0x7F offset of the command at the given index.
        """

        cur_offset = 0
        for ind, command in enumerate(self.commands):
            if ind == index:
                return cur_offset
            cur_offset += len(command)

        raise IndexError

    @staticmethod
    def _is_label_internal(label: str):
        return not label[0].isalnum()

    def __str__(self):
        ret_str = ''

        offsets = []
        offset = 0
        for cmd in self.commands:
            offsets.append(offset)
            offset += len(cmd)

        offsets.append(offset)

        # for offset in offsets:
        #     print(f'[{offset:04X}]')

        # for label, index in self.labels.items():
        #     print(f'{label} --> {index}')
        # input()

        for ind, (cmd, offset) in enumerate(zip(self.commands, offsets)):
            ret_str += f'[{ind}, 0x{offset:04X}]'
            cmd_str = str(cmd)

            if hasattr(cmd, 'to_label'):
                # print(f"[{ind}, 0x{offset:04X}] {cmd}")
                if cmd.to_label is None:
                    target = get_jump_target(cmd, offset)
                    target_index = None
                else:
                    target_index = self.labels[cmd.to_label]
                    target = offsets[target_index]

                parts = cmd_str.split('\n', 1)
                if target_index is not None:
                    target_index_str = f'{target_index}, '
                else:
                    target_index_str = ''
                parts[0] += f' (To: [{target_index_str}0x{target:04X}, '\
                    + f'{cmd.to_label}])'

                cmd_str = '\n'.join(parts)

            ret_str += cmd_str
            ret_str += '\n'

        return ret_str

    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom,
                        event_index: int) -> OverworldEvent:
        """Read an OverworldEvent from a CTRom"""
        event_b = _ow_event_rw.read_data_from_ctrom(ct_rom, event_index)
        return OverworldEvent(event_b)

    @classmethod
    def free_data_on_ctrom(cls, ct_rom: ctrom.CTRom, event_index: int):
        """Free an OverworldEvent on a CTRom"""
        _ow_event_rw.free_data_on_ct_rom(ct_rom, event_index)

    def write_to_ctrom(self, ct_rom: ctrom.CTRom,
                       event_index: int,
                       free_existing: bool = True):
        """Write an OverWorldEvent to a CTrom"""
        _ow_event_rw.write_data_to_ct_rom(ct_rom, self.get_bytes(),
                                          event_index, free_existing)


def get_jump_target(
        command: owc.OverworldEventCommand,
        offset: int) -> int:
    """Given a branch/jump command at given position, find jump target."""
    if isinstance(command, owc.OWLocalBranchCommand):
        jump_bytes = command.jump_bytes
        return offset + jump_bytes

    if isinstance(command, owc.OWLocalJumpCommand):
        target = command.jump_address - 0x400
        if isinstance(command, owc.Goto):
            target += 1

        return target

    if isinstance(command, owc.OWLongJumpCommand):
        return command.jump_address - 0x7F0400

    print(type(command))
    print(command.__class__.mro())
    raise TypeError("Command is not a local branch or jump.")


def set_jump_target(
        command: owc.OWBranchCommand,
        command_offset: int, jump_target: int):
    """Helper for setting a jump's target given a target offset."""

    if isinstance(command, owc.OWLocalBranchCommand):
        command.jump_bytes = jump_target - command_offset
    elif isinstance(command, owc.OWLocalJumpCommand):
        command.jump_address = jump_target + 0x400
        if isinstance(command, owc.Goto):
            command.jump_address -= 1
    elif isinstance(command, owc.OWLongJumpCommand):
        command.jump_address = jump_target + 0x7F0400
    else:
        raise TypeError("Command is not a local branch or jump.")

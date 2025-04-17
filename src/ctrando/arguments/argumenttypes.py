from __future__ import annotations

import abc
import argparse
import enum
from dataclasses import dataclass, fields
from enum import Enum
import typing


class ArgumentGroup(typing.Protocol):

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        ...

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        ...


class ArgumentType(typing.Protocol):
    _argument_names: typing.ClassVar[list[str]]


_T = typing.TypeVar('_T')


def extract_from_namespace(
        return_type: typing.Type[_T],
        arg_names: list[str],
        namespace: argparse.Namespace
) -> _T:
    opt_dict: dict[str, typing.AnyStr] = {
        name: getattr(namespace, name)
        for name in arg_names
        if hasattr(namespace, name)
    }

    return return_type(**opt_dict)


class ArgparseGroup(typing.Protocol):
    """Stupid thing we do because argparse._ArgumentGroup is private."""
    def add_argument(self, *args, **kwargs):
        ...


    # def add_argument(
    #         self,
    #         *name_or_flags: str,
    #         action: str | typing.Type[argparse.Action] = ...,
    #         nargs: int | str | None = None,
    #         const: typing.Any=...,
    #         default: typing.Any=...,
    #         # type: typing.Callable[[str], _ET] | argparse.FileType = ...,
    #         choices: typing.Iterable[_ET] | None = ...,
    #         required: bool=...,
    #         help: str | None = ...,
    #         metavar: str | tuple[str, ...] | None = None,
    #         dest: str | None = None
    # ):
    #     ...


def arg_name_to_attr_name(arg_name: str) -> str:
    """Convert "--some-argument-name" to "some_argument_name" """
    return arg_name.lstrip('-').replace('-', '_')


def attr_name_to_arg_name(attr_name: str) -> str:
    """Convert "some_attr_name" to "--some-attr-name" """
    return "--"+attr_name.replace('_', '-')


_ET = typing.TypeVar("_ET", bound=enum.Enum)
def add_enum_to_group(
        group: ArgparseGroup,
        arg_name: str,
        enum_type: typing.Type[_ET],
        enum_str_dict: dict[_ET, str],
        flag_name: str | None = None,
        help_str: str | None = None,
        default_value: _ET | None = None,
):

    inv_dict: dict[str, _ET] = {value: key for key, value in enum_str_dict.items()}

    def type_fn(string: str) -> _ET:
        if string not in inv_dict:
            raise ValueError
        return inv_dict.get(string, ...)


    options: dict[str, typing.Any] = {
        "action": "store",
        "type": type_fn,
        "default": default_value,
        "choices": enum_str_dict.values()
    }

    if help_str is not None:
        options['help'] = help_str

    names = [arg_name]
    if flag_name is not None:
        names.append(flag_name)

    group.add_argument(*names, **options)


_ST = typing.TypeVar("_ST", bound=enum.StrEnum)


def add_str_enum_to_group(
        group: ArgparseGroup,
        arg_name: str,
        enum_type: typing.Type[_ST],
        flag_name: str | None = None,
        help_str: str | None = None,
        default_value: _ST | typing.Type[argparse.SUPPRESS] = argparse.SUPPRESS,
):
    enum_str_dict = {
        val: val.value for val in list(enum_type)
    }

    add_enum_to_group(
        group, arg_name, enum_type, enum_str_dict, flag_name, help_str, default_value
    )


def extract_enum_from_namespace(
        enum_type: typing.Type[_ET],
        arg_name: str,
        namespace: argparse.Namespace
) -> typing.Optional[_ET]:
    if not hasattr(namespace, arg_name):
        return None

    arg_value = getattr(namespace, arg_name)
    if not isinstance(arg_value, enum_type):
        raise TypeError(f"{arg_name} is of type {type(arg_value)}, not {enum_type}")

    return arg_value


def add_dataclass_to_group(
        data_class: typing.Any,
        arg_group: ArgparseGroup,
        help_dict: dict[str, str] | None = None,
        short_flag_dict: dict[str, str] | None = None
):
    if help_dict is None:
        help_dict = dict()

    if short_flag_dict is None:
        short_flag_dict = dict()

    for field in fields(data_class):
        arg_name = attr_name_to_arg_name(field.name)

        help_str = help_dict.get(field.name, None)
        short_flag = short_flag_dict.get(field.name, None)

        name_or_flags = [arg_name]
        if short_flag is not None:
            name_or_flags.append(short_flag)

        opt_dict: dict[str, typing.Any] = dict()

        if issubclass(field.type, bool):
            if field.default == True:
                opt_dict['action'] = 'store_false'
            elif field.default == False:
                opt_dict['action'] = 'store_true'
            else:
                raise ValueError
            opt_dict['default'] = argparse.SUPPRESS
        else:
            opt_dict['type'] = field.type
            opt_dict['action'] = 'store'
            # if isinstance(field.default, field.type):
            #     opt_dict['default'] = field.default
            # else:
            #     opt_dict['required'] = True
            opt_dict['default'] = argparse.SUPPRESS

        if help_str is not None:
            opt_dict['help'] = help_str


        arg_group.add_argument(*name_or_flags, **opt_dict)


_DT = typing.TypeVar("_DT")
def extract_dataclass_from_namespace(dataclass_type: typing.Type[_DT],
                                     namespace: argparse.Namespace) -> _DT:
    """
    Fill out a dataclass using the values in the namespace
    """

    init_dict: dict[str, typing.Any] = dict()
    namespace_dict = vars(namespace)

    for field in fields(dataclass_type):
        if hasattr(namespace, field.name):
            init_dict[field.name] = namespace_dict[field.name]
        # else:
        #     if not isinstance(field.default, field.type):
        #         raise ValueError("No value given")
        #
        #     init_dict[field.name] = field.default

    return dataclass_type(**init_dict)


def str_to_enum_dict(
        enum_type: typing.Type[enum.Enum],
):
    lookup_dict = {
        enum_member.name.lower(): enum_member for enum_member in enum_type
    }
    return lookup_dict


def str_to_enum(
        string: str,
        enum_type: typing.Type[enum.Enum]
):
    lookup_dict = str_to_enum_dict(enum_type)
    return lookup_dict[string]

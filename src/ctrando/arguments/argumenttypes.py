from __future__ import annotations

import argparse
import functools
from collections.abc import Iterable
import enum
import inspect
from dataclasses import dataclass, fields
from enum import Enum, StrEnum
import typing

from collections.abc import Callable, Iterable
from typing import Protocol, TypeVar, Any
from unicodedata import lookup


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
        arg_names: Iterable[str],
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
        if inspect.isclass(field.type) and issubclass(field.type, bool):
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
        enum_type: typing.Type[_ET],
        force_enum_names: bool = False
) -> dict[str, _ET]:
    if issubclass(enum_type, StrEnum) and not force_enum_names:
        lookup_dict = {
            enum_member.value: enum_member for enum_member in enum_type
        }
    else:
        lookup_dict = {
            enum_member.name.lower(): enum_member for enum_member in enum_type
        }
    return lookup_dict


def str_to_enum(
        string: str,
        enum_type: typing.Type[enum.Enum],
        force_enum_names: bool = False
):
    lookup_dict = str_to_enum_dict(enum_type, force_enum_names)
    return lookup_dict[string]


def enum_to_str(
        enum_member: _ET,
        enum_type: typing.Type[_ET],
        force_enum_names: bool = False
):
    if issubclass(enum_type, StrEnum) and not force_enum_names:
        return enum_member.value

    return enum_member.name.lower()

_Number = TypeVar("_Number", bound=int | float)

class Argument[_T](Protocol):
    default_value: _T
    help_text: str

    def add_to_argparse(
            self,
            argparse_name: str,
            argparse_obj: argparse.ArgumentParser | argparse._ArgumentGroup,
    ):
        ...

    def get_toml_value(self, value: typing.Any) -> typing.Any:
        """Return a value representing value suitable for a toml dictionary"""
        ...


class FlagArg:
    def __init__(
            self,
            help_text: str
    ):
        self.default_value = False
        self.help_text = help_text

    def add_to_argparse(
            self,
            argparse_name: str,
            argparse_obj: argparse.ArgumentParser | argparse._ArgumentGroup,
    ):
        argparse_obj.add_argument(
            argparse_name,
            action = "store_true",
            default=argparse.SUPPRESS,
            help=self.help_text,
        )

    def get_toml_value(self, value: typing.Any) -> typing.Any:
        if not isinstance(value, bool):
            raise TypeError

        return value



class DiscreteNumericalArg[_Number]:
    def __init__(
            self,
            min_value: _Number,
            max_value: _Number,
            interval: float,
            default_value: float,
            help_text: str,
            type_fn: Callable[[typing.Any], _Number]
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.interval = interval
        self.default_value = default_value
        self.help_text = help_text
        self.type_fn = type_fn

    def add_to_argparse(
            self,
            argparse_name: str,
            argparse_obj: argparse.ArgumentParser | argparse._ArgumentGroup,
    ):
        if self.type_fn is None:
            type_fn = self.default_value.__class__
        else:
            type_fn = self.type_fn

        argparse_obj.add_argument(
            argparse_name,
            default=argparse.SUPPRESS,
            action="store",
            type=type_fn,
            help=self.help_text
        )

    def get_toml_value(self, value: typing.Any) -> typing.Any:
        if not self.min_value <= value <= self.max_value:
            raise ValueError(
                f"Value must be in range({self.min_value}, {self.max_value+1})")

        return self.type_fn(value)


class DiscreteCategorialArg[_T]:
    def __init__(
            self,
            choices: Iterable[_T],
            default_value: _T,
            help_text: str,
            choice_from_str_fn: Callable[[str], _T] | None = None,
            str_from_choice_fn: Callable[[_T], str] | None = None
    ):
        self.choices = list(choices)
        self.default_value = default_value
        self.help_text = help_text
        self.choice_from_str_fn = choice_from_str_fn
        self.str_from_choice_fn = str_from_choice_fn

    def add_to_argparse(
            self,
            argparse_name: str,
            argparse_obj: argparse.ArgumentParser | argparse._ArgumentGroup,
    ):
        if self.choice_from_str_fn is None:
            type_fn = self.default_value.__class__
        else:
            type_fn = self.choice_from_str_fn

        argparse_obj.add_argument(
            argparse_name,
            default=argparse.SUPPRESS,
            type=type_fn
        )

    def get_toml_value(self, value: typing.Any) -> typing.Any:
        return self.str_from_choice_fn(value)


def arg_from_enum(
        enum_type: typing.Type[_ET],
        default_value: _ET,
        help_text: str,
        force_enum_names: bool = False
):
    return DiscreteCategorialArg(
        list(enum_type), default_value, help_text,
        choice_from_str_fn=functools.partial(str_to_enum, enum_type=enum_type,
                                             force_enum_names=force_enum_names),
        str_from_choice_fn=functools.partial(enum_to_str, enum_type=enum_type,
                                             force_enum_names=force_enum_names)
    )


class MultipleDiscreteSelection[_T]:
    def __init__(
            self,
            choices: Iterable[_T],
            default_value: Iterable[_T],
            help_text: str,
            choice_from_str_fn: Callable[[str], _T] | None = None,
            str_from_choice_fn: Callable[[_T], str] | None = None,
    ):
        self.choices = list(choices)
        self.default_value = list(default_value)
        self.help_text = help_text
        self.choice_from_str_fn = choice_from_str_fn
        self.str_from_choice_fn = str_from_choice_fn

    def add_to_argparse(
            self,
            argparse_name: str,
            argparse_obj: argparse.ArgumentParser | argparse._ArgumentGroup
    ):
        argparse_obj.add_argument(
            argparse_name, nargs="*",
            help=self.help_text,
            type=self.choice_from_str_fn,
            default=argparse.SUPPRESS
        )

    def get_toml_value(self, value: typing.Any) -> typing.Any:
        if not isinstance(value, Iterable):
            raise ValueError

        if self.str_from_choice_fn is None:
            str_fn = str
        else:
            str_fn = self.str_from_choice_fn

        return [str_fn(x) for x in value]


class StringArgument[_T]:
    def __init__(
            self,
            help_text: str,
            parser: Callable[[str], _T]
    ):
        self.help_text = help_text
        self.parser = parser

    def add_to_argparse(
            self,
            argparse_name: str,
            argparse_obj: argparse.ArgumentParser | argparse._ArgumentGroup,
    ):
        argparse_obj.add_argument(
            argparse_name,
            action = "store",
            default=argparse.SUPPRESS,
            help=self.help_text,
            type=self.parser
        )

    def get_toml_value(self, value: typing.Any) -> typing.Any:
        if not isinstance(value, str):
            raise TypeError

        return self.parser(value)


def arg_multiple_from_enum(
        enum_type: typing.Type[_ET],
        default_value: Iterable[_ET],
        help_text: str,
        force_enum_names: bool = False,
        available_pool: Iterable[_ET] = None
):
    if available_pool is not None:
        pool = list(available_pool)
        def choice_from_str_fn(val: str) -> _ET:
            choice = str_to_enum(val, enum_type, force_enum_names)
            if choice not in pool:
                raise ValueError
            return choice

        def str_from_choice_fn(val: _ET) -> str:
            if val not in pool:
                raise ValueError
            return enum_to_str(val, enum_type, force_enum_names)
    else:
        pool = list(enum_type)
        choice_from_str_fn = functools.partial(
            str_to_enum, enum_type=enum_type, force_enum_names=force_enum_names)
        str_from_choice_fn = functools.partial(
            enum_to_str, enum_type=enum_type, force_enum_names=force_enum_names)

    return MultipleDiscreteSelection(
        pool, default_value, help_text,
        choice_from_str_fn=choice_from_str_fn,
        str_from_choice_fn=str_from_choice_fn
    )

# type ArgSpec = dict[str, Argument | ArgSpec]
ArgSpec: typing.TypeAlias = dict[str, typing.Union['ArgSpec', Argument]]


class SettingsObject(typing.Protocol):
    name: typing.ClassVar[str]
    description: typing.ClassVar[str]

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        ...

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        ...

    @classmethod
    def get_argument_spec(cls) -> ArgSpec:
        ...


def main():

    class Foo(StrEnum):
        a_elem = "a"
        b_elem = "b"

    print(str_to_enum_dict(Foo))



if __name__ == "__main__":
    main()
"""Module for reading a toml file and converting for use by argparse"""
import argparse
import typing

from ctrando.arguments import argumenttypes



def toml_data_to_args(
        toml_data: dict,
        exclusion_namespace: typing.Optional[argparse.Namespace] = None

) -> list[str]:
    """Convert toml_data into a list of strings suitable for argparse"""
    ret_args: list[str] = []
    if exclusion_namespace is None:
        exclusion_namespace = argparse.Namespace()

    for key, val in toml_data.items():
        if not isinstance(key, str):
            raise TypeError

        if hasattr(exclusion_namespace, key):
            continue

        if isinstance(val, list):
            ret_args.append(argumenttypes.attr_name_to_arg_name(key))
            ret_args.extend([str(elem) for elem in val])
        elif isinstance(val, dict):
            # Ignore the name of the table.  Just load in the keys.
            ret_args.extend(toml_data_to_args(val))
        else:
            if isinstance(val, bool) and val is True:
                new_args = [argumenttypes.attr_name_to_arg_name(key)]
            elif not isinstance(val, bool):
                new_args = [
                    argumenttypes.attr_name_to_arg_name(key),
                    str(val)
                ]
            else:
                new_args = []
            ret_args.extend(new_args)

    return ret_args

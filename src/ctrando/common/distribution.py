"""
Implement Distribution objects.

A Distribtuion is just a collection of (weight, value_list) pairs.
When generating a random item from the distribution, pick a pair based on
the weights, then return a random element of the pair's value_list.
"""

from __future__ import annotations

import copy
import itertools
import random
# import random
from collections.abc import Iterable, Sequence
import typing

from ctrando.common.random import RNGType


T = typing.TypeVar('T')
ObjType = typing.Union[T, Sequence[T]]
WeightType = typing.Union[int, float]


class ZeroWeightException(ValueError):
    """Raised when an entry in a distributuion is given zero weight."""


class Distribution(typing.Generic[T]):
    """
    This class allows the user to define relative frequencies of objects and
    generate random objects according to that distribution.  If the object
    given is a sequence, then the behavior is to give a random item from the
    sequence.
    """
    def __init__(
            self,
            *weight_object_pairs: typing.Tuple[WeightType, ObjType],
    ):
        """
        Define the initial weight/object pairs for the distributuion

        Example:
        dist = Distributution(
            (5, range(0, 10, 2),
            (10, range(1, 10, 2)
        )
        This defines a distribution that choose uniformly from (0, 2, 4, 8)
        one third of the time and will choose uniformly from (1, 3, 5, 9) the
        other two thirds of the time.
        """

        self.__total_weight = 0
        self.weight_object_pairs: list[typing.Tuple[WeightType, ObjType]] = []

        self.set_weight_object_pairs(list(weight_object_pairs))

    @staticmethod
    def _handle_weight_object_pairs(
            weight_object_pairs: typing.Sequence[typing.Tuple[WeightType, ObjType]]
    ) -> list[typing.Tuple[WeightType, ObjType]]:
        """
        Replace non-sequences with a one element list so that random.choice()
        can be used.
        """
        new_pairs: list[tuple[WeightType, ObjType]] = []
        for ind, pair in enumerate(weight_object_pairs):
            weight, obj = pair

            if weight == 0:
                continue

            if not isinstance(obj, list):
                obj = [obj]

            if not obj:
                continue

            new_pairs.append((weight, obj))

        return new_pairs

    def get_total_weight(self) -> float:
        """
        Return the total weight that the distribution has.
        """
        return self.__total_weight

    def get_random_item(self,
                        rng: RNGType) -> T:
        """
        Get a random item from the distribution.
        First choose a weight-object pair based on weights.  Then (uniformly)
        choose an element of that object.
        """
        # target = random.randrange(0, self.__total_weight)
        target = rng.random()*self.__total_weight

        cum_weight = 0
        for weight, obj in self.weight_object_pairs:
            cum_weight += weight

            if cum_weight > target:
                return rng.choice(obj)

        raise ValueError('No choice made.')

    def get_all_items(self) -> set[T]:
        ret = set()
        for weight, items in self.weight_object_pairs:
            ret.update(items)

        return ret

    def get_weight_object_pairs(self):
        """Returns list of (weight, object_list) pairs in the Distribution."""
        return list(self.weight_object_pairs)

    def set_weight_object_pairs(
            self,
            new_pairs: list[typing.Tuple[WeightType, ObjType]]):
        """
        Sets the Distribution to have the given (float, object_list) pairs.
        """
        cleaned_pairs = self._handle_weight_object_pairs(new_pairs)
        self.weight_object_pairs = cleaned_pairs
        self.__total_weight = sum(x[0] for x in cleaned_pairs)

        if self.__total_weight == 0:
            raise ZeroWeightException

    def get_restricted_distribution(
            self, remove_values: Iterable[T],
            remove_weight: bool = True
    ) -> typing.Self:
        """
        Removes the given values from the distribution.  By default removes weight
        proportional to the values removed.
        """

        new_pairs: list[WeightType, list[T]] = []
        remove_values = set(remove_values)

        for weight, vals in self.weight_object_pairs:
            trimmed_vals = [x for x in vals if x not in remove_values]

            if remove_weight:
                weight = weight*(len(trimmed_vals)/len(vals))

            if weight > 0:
                new_pairs.append((weight, trimmed_vals))

        return Distribution[T](*new_pairs)


class DistributionGenerator(typing.Generic[T]):
    def __init__(self, symbol_dict: dict[str, Sequence[T]]):
        """
        Make a new Distribution Generator.  Note that symbol_dict should be
        sequences (e.g.  {"wood_sword": [ItemID.WoodSword]})
        """
        self.symbol_dict = copy.deepcopy(symbol_dict)
        self.singleton_dict = {
            key: val[0] for key,val in self.symbol_dict.items() if len(val) == 1
        }
        self.singleton_dict_inv = {
            val: key for key, val in self.singleton_dict.items()
        }

    def validate_string(self, dist_str: str) -> str:
        self.generate_distribution(dist_str)
        return dist_str

    def generate_distribution(self, dist_str: str) -> Distribution[T]:
        """
        Generate a distribution from a string.  The format is:
            "weight1: [symbol_1, symbol_2,...], weight2: [symbol_1, ...]"
        """

        dist_str = "".join(dist_str.split())
        wo_pairs: list[tuple[float, ObjType]] = []

        while dist_str:
            parts = dist_str.split(":", maxsplit=1)
            weight = float(parts[0])

            rest = parts[1]
            if rest[0] == "[":
                vals_str, rest = rest[1:].split("]", maxsplit=1)
                if rest and rest[0] == ",":
                    rest = rest[1:]
            else:
                rest_parts = rest.split(",", maxsplit=1)
                vals_str = rest_parts[0]
                if len(rest_parts) == 2:
                    rest = rest_parts[1]
                else:
                    rest = ""

            vals = list(itertools.chain.from_iterable(self.symbol_dict[x] for x in vals_str.split(",")))
            wo_pairs.append((weight, vals))

            dist_str = rest

        return Distribution[T](*wo_pairs)


def main():
    """Sample for using Distribution and DistributionGenerator"""
    from ctrando.common.ctenums import ItemID

    symbol_dict = {
        "wood_sword": [ItemID.WOOD_SWORD],
        "iron_sword": [ItemID.IRON_SWORD],
        "bad_wpns": [ItemID.MOP, ItemID.GRAEDUS],
        "good_wpns": [ItemID.RAINBOW, ItemID.CRISIS_ARM],
    }

    dist_str = "10: wood_sword, 20: [wood_sword, bad_wpns], 5: good_wpns"
    gen = DistributionGenerator(symbol_dict)
    dist = gen.generate_distribution(dist_str)

    rng = random.Random("asdf")

    for _ in range(10):
        print(dist.get_random_item(rng))


if __name__ == "__main__":
    main()

from __future__ import annotations
import enum
import typing

from ctrando.common.ctenums import CharID, ItemID
from ctrando.common.memory import Flags


#
# This file holds various classes/types used by the logic placement code.
#


class ScriptReward(enum.Enum):
    EPOCH = enum.auto()
    FLIGHT = enum.auto()


# OtherReward = typing.Union[ScriptReward, Flags]
OtherReward = typing.Any

RewardType = typing.Union[ItemID, CharID, OtherReward]
SingleRule = list[RewardType]


class Game:
    """
    The Game class is used to keep track of game state
    as the randomizer places key items.  It:
      - Tracks key items obtained
      - Tracks characters obtained
      - Keeps track of user selected flags
      - Provides logic convenience functions
    """

    def __init__(
            self,
            held_chars: typing.Optional[set[CharID]] = None,
            held_items: typing.Optional[list[ItemID]] = None,
            other_rewards: typing.Optional[set[OtherReward]] = None
    ):
        if held_chars is None:
            held_chars = set()
        if held_items is None:
            held_items = list()
        if other_rewards is None:
            other_rewards = list()

        self.characters: set[CharID] = set(held_chars)
        self.key_items: list[ItemID] = list(held_items)
        self.other_rewards: set[OtherReward] = set(other_rewards)

    def __eq__(self, other: Game):
        """Do two games have the same rewards"""
        return (
                self.characters == other.characters and
                self.key_items == other.key_items and
                self.other_rewards == other.other_rewards
        )

    def get_copy(self) -> Game:
        """Get a copy of this Game"""
        return Game(self.characters, self.key_items, self.other_rewards)

    def get_key_item_count(self):
        """
        Get the number of key items that have been acquired by the player.

        :return: Number of obtained key items
        """
        return len(self.key_items)

    def has_character(self, character: CharID) -> bool:
        """
        Check if the player has the specified character

        :param character: Name of a character
        :return: true if the character has been acquired, false if not
        """
        return character in self.characters

    def add_character(self, character: CharID):
        """
        Add a character to the set of characters acquired.

        :param character: The character to add
        """
        self.characters.add(character)

    def remove_character(self, character: CharID):
        """
        Remove a character from the set of characters acquired.

        :param character: The character to remove
        """
        self.characters.discard(character)

    def has_key_item(self, item: ItemID) -> bool:
        """
        Check if the player has a given key item.

        :param item: The key item to check for
        :return: True if the player has the key item, false if not
        """
        return item in self.key_items

    def add_key_item(self, item: ItemID):
        """
        Add a key item to the set of key items acquired.

        :param item: The Key Item to add
        """
        self.key_items.append(item)

    def remove_key_item(self, item: ItemID):
        """
        Remove a key item from the set of key items acquired.

        :param item: The Key Item to remove
        """
        if item in self.key_items:
            self.key_items.remove(item)

    def has_other_reward(self, reward: OtherReward) -> bool:
        return reward in self.other_rewards

    def update_available_characters(self):
        """
        Determine which characters are available based on what key items/time
        periods are available to the player.
        """

        # charLocations is a dictionary from cfg.RandoConfig whose keys come
        # from RecruitID.  The corresponding value gives the held
        # character in a held_char field

        # Empty the set just in case the placement algorithm had to
        # backtrack and a character is no longer available.
        self.characters.clear()

    # end update_available_characters function


class LogicRule:
    """
    This class holds logical access rules for a LocationGroup.
    """

    def __init__(
        self,
        initial_rules: typing.Optional[SingleRule | typing.Iterable[SingleRule]] = None,
    ):
        self._rules: list[SingleRule]

        if initial_rules is None:
            self._rules = []
        else:
            if all(
                isinstance(x, ItemID) or isinstance(x, CharID)
                or isinstance(x, ScriptReward) or isinstance(x, Flags)
                for x in initial_rules
            ):
                initial_rules = [initial_rules]
            self._rules = [rule for rule in initial_rules]

    def __or__(self, other: LogicRule) -> LogicRule:
        """Or this rule with another rule"""
        ret_rule = LogicRule(self._rules)
        for rule in other.get_access_rule():
            ret_rule.add_rule(rule)

        return ret_rule

    def __and__(self, other: LogicRule) -> LogicRule:
        """And this rule with another rule"""
        new_rules: list[SingleRule] = []
        for rule in self.get_access_rule():
            for other_rule in other.get_access_rule():
                temp_other_rule = list(other_rule)
                for key in rule:
                    if key in temp_other_rule:
                        temp_other_rule.remove(key)
                new_rules.append(rule + temp_other_rule)

        return LogicRule(initial_rules=new_rules)

    def add_rule(self, rule: SingleRule):
        """
        Add a rule to this object.
        Rules are a list of item or character IDs that block access to a location.

        :param rule: List of items or characters needed to access a location
        :return: A reference to this object
        """
        self._rules.append(rule)
        return self

    def get_access_rule(self) -> list[SingleRule]:
        """
        Get the access requirements in this rule.

        :return: List of access requirements
        """
        return list(self._rules)

    def get_forced_keys(self) -> list[RewardType]:
        """
        Get keys which are required to access this spot.
        """
        if not self._rules:
            return list()

        forced_keys = list(self._rules[0])
        for rule in self._rules[1:]:
            forced_copy = list(forced_keys)
            rule_copy = list(rule)

            for key in forced_keys:
                if key not in rule_copy:
                    forced_copy.remove(key)
                else:
                    rule_copy.remove(key)

            forced_keys = forced_copy

        return forced_keys

    def add_requirement(self, new_rule: SingleRule) -> LogicRule:
        """
        Extend an existing rule with a new set of requirements.

        :param new_rule: new rule to append to the existing rules
        """
        if len(self._rules) == 0:
            self.add_rule(new_rule)
        else:
            for rule in self._rules:
                rule.extend(new_rule)
        return self

    def __call__(self, game: Game) -> bool:
        """
        Evaluate this set of rules to see if a location group is accessible.

        :param game: Game object with current game state
        :return: True if the location is accessible, false if not
        """
        if len(self._rules) == 0:
            # Empty rules list means this is a sphere 0 check
            return True

        for rule in self._rules:
            total_tokens = list(game.other_rewards) + list(game.key_items) + list(game.characters)
            can_access = True
            for requirement in rule:
                if requirement not in total_tokens:
                    can_access = False
                    break
                else:
                    total_tokens.remove(requirement)
                # has_char = (
                #     game.has_character(requirement) if requirement in CharID else False
                # )
                # has_key = (
                #     game.has_key_item(requirement) if requirement in ItemID else False
                # )
                # has_other = (
                #     game.has_other_reward(requirement)
                # )
                # if not (has_char or has_key or has_other):
                #     can_access = False
                #     break

            if can_access:
                return True

        return False

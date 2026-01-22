"""
Module for defining types of AI commands, conditions, and scripts.
Based from work by:
- https://www.neoseeker.com/chrono-trigger/faqs/3085264-enemy-ai.html
- https://www.chronocompendium.com/Term/Enemy_AI.html

"""
from dataclasses import dataclass, field
from enum import IntEnum
import typing
from typing import Optional

from ctrando.common import byteops, ctenums, ctrom, cttypes as cty, freespace


class StatOffset(IntEnum):
    LEVEL = 0x12
    SPEED = 0x38
    MAGIC = 0x39
    HIT = 0x3A
    EVADE = 0x3B
    MAGIC_DEFENSE = 0x3C
    OFFENSE = 0x3D
    DEFENSE = 0x3E
    LIT_DEFENSE = 0x3F
    SHADOW_DEFENSE = 0x40
    WATER_DEFENSE = 0x41
    FIRE_DEFENSE = 0x42


class Target(IntEnum):
    NOTHING = 0
    ALL_PCS = 1
    ALL_ENEMIES = 2
    CURRENT_ENEMY = 3
    ATTACKING_PC = 4
    RANDOM_PC = 5
    NEAREST_PC = 6
    FARTHEST_PC = 7
    # TODO: This routine does not properly check  |
    #   PC1's HP. To fix, replace 0x01A50C (unheadered US or   |
    #   Japanese ROM) with D0 05 EA EA
    LOWEST_HP_PC = 8
    PCS_1D_NONZERO = 9
    PCS_NEGATIVE_STATUS = 0xA
    PCS_1F_NONZERO = 0xB
    PCS_POSITIVE_STATUS_T8 = 0xC  # Type 08 is 2x Evade, Haste
    PCS_POSITIVE_STATUS_T9 = 0xD  # Type  09 is Specs/Prot/Shield/Bers
    PCS_SLEEPING = 0xE
    PCS_STOPPED = 0xF
    PCS_CHAOS = 0x10
    PCS_SHIELDED = 0x11
    PCS_BARRIERED = 0x12
    PCS_T9_10_UNUSED = 0x13
    PCS_T8_08_UNUSED = 0x14
    OTHER_ENEMIES = 0x15
    LIVING_ENEMIES = 0x16
    NEAREST_ENEMY = 0x17
    FARTHEST_ENEMY = 0x18
    ENEMY_LOWEST_HP = 0x19
    OTHER_ENEMIES_1D_NONZERO = 0x1A
    ALL_ENEMIES_1D_NONZERO = 0x1B
    OTHER_ENEMIES_NEGATIVE_STATUS = 0x1C
    ALL_ENEMIES_NEGATIVE_STATUS = 0x1D
    OTHER_ENEMIES_1F_NONZERO = 0x1E
    ALL_ENEMIES_1F_NONZERO = 0x1F
    OTHER_ENEMIES_SLEEPING = 0x20
    OTHER_ENEMIES_STOPPED = 0x21
    OTHER_ENEMIES_CHAOS = 0x22
    OTHER_ENEMIES_BARRIER = 0x23
    OTHER_ENEMIES_1D_02 = 0x24
    OTHER_ENEMIES_1D_01 = 0x25
    OTHER_ENEMY_LOWEST_HP = 0x26
    ENEMY_03 = 0x27
    ENEMY_04 = 0x28
    ENEMY_05 = 0x29
    ENEMY_06 = 0x2A
    ENEMY_07 = 0x2B
    ENEMY_08 = 0x2C
    ENEMY_09 = 0x2D
    ENEMY_0A = 0x2E
    ENEMY_RANDOM_AF15_80 = 0x2F
    PC1_UNK = 0x30
    PC2_UNK = 0x31
    PC3_UNK = 0x32
    Enemy3_UNK = 0x33
    Enemy4_UNK = 0x34
    Enemy5_UNK = 0x35
    Enemy6_UNK = 0x36
    Enemy7_UNK = 0x37
    PC_HIGHEST_HP = 0x37
    OTHER_ENEMY_RANDOM = 0x38


S = typing.TypeVar('S', bound='_EnemyAICondition')


class _AttrSizedBinaryData(cty.SizedBinaryData):
    def _set_properties(self, *args: tuple[str, typing.Optional[int]]):
        for name, val in args:
            if val is not None:
                setattr(self, name, val)


class _EnemyAICondition(_AttrSizedBinaryData):
    """Base class for an AI condition."""
    SIZE = 4
    COND_ID: typing.ClassVar[int]

    @classmethod
    def _get_default_value(cls) -> bytearray:
        default = super()._get_default_value()
        default[0] = cls.COND_ID

        return default


class IfTrue(_EnemyAICondition):
    """Always true.  Use for default behavior."""
    COND_ID = 0

    def __str__(self):
        return f"If True:"


class IfHPLessThanEqualHalf(_EnemyAICondition):
    COND_ID = 1
    target = cty.byte_prop(1, ret_type=Target)

    def __str__(self):
        return f"If {self.target} has HP < 50%"


class IfStatus(_EnemyAICondition):
    COND_ID = 2
    target = cty.byte_prop(1, ret_type=Target)
    offset = cty.byte_prop(2)
    bitmask = cty.byte_prop(3)

    def __str__(self):
        return f"If bits {self.bitmask:02X} are set in byte {self.offset:02X} of {self.target}"


class IfMoved(_EnemyAICondition):
    COND_ID = 3
    target = cty.byte_prop(1, ret_type=Target)  # Not sure how these are used
    index = cty.byte_prop(2)

    def __str__(self):
        return f"If {self.target}/index {self.index:02X} moved"


class IfMonsterDead(_EnemyAICondition):
    COND_ID = 4
    index = cty.byte_prop(2)
    is_dead = cty.byte_prop(2, ret_type=bool)

    def __str__(self):
        status_str = "Dead" if self.is_dead else "Alive"
        return f"If Enemy {self.index:02X} is {status_str}"


class IfNumLivingEnemiesLessThanEqual(_EnemyAICondition):
    COND_ID = 5
    num_enemies = cty.byte_prop(1)

    def __init__(self, *args,
                 num_enemies: int | None = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ("num_enemies", num_enemies)
        )

    def __str__(self):
        return f"If Number of Living Enemies <= {self.num_enemies}"


class IfStatusCounter(_EnemyAICondition):
    COND_ID = 7

    value = cty.byte_prop(1)
    _compare_type = cty.byte_prop(2)

    @property
    def compare_type(self) -> typing.Literal['<=', '>=']:
        if self._compare_type == 0:
            return '>='
        elif self._compare_type == 1:
            return '<='
        else:
            raise ValueError

    @compare_type.setter
    def compare_type(self, value: typing.Literal['<=', '>=']):
        if value == ">=":
            self._compare_type = 0
        elif value == "<=":
            self._compare_type = 1
        else:
            raise ValueError

    def __str__(self):
        return f"If status counter {self.compare_type} {self.value}"


class IfHPLessThanEqual(_EnemyAICondition):
    COND_ID = 8

    target = cty.byte_prop(1, ret_type=Target)
    hp = cty.bytes_prop(2, 2)

    def __str__(self):
        return f"If HP of {self.target} <= {self.hp}"


class IfStatLessThan(_EnemyAICondition):
    COND_ID = 9
    target = cty.byte_prop(1, ret_type=Target)
    stat_offset = cty.byte_prop(2)
    value = cty.byte_prop(3)

    def __init__(
            self, *args,
            target: typing.Optional[Target] = None,
            stat_offset: typing.Optional[StatOffset] = None,
            value: typing.Optional[int] = None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('target', target),
            ('stat_offset', stat_offset),
            ('value', value)
        )

    def __str__(self):
        return f"If stat {self.stat_offset:02X} of {self.target} < {self.value}"


class IfStatLessThanEqual(_EnemyAICondition):
    COND_ID = 0xB
    target = cty.byte_prop(1, ret_type=Target)
    stat_offset = cty.byte_prop(2)
    value = cty.byte_prop(3)

    def __init__(self, *args,
                 target: typing.Optional[Target] = None,
                 stat_offset: typing.Optional[int] = None,
                 value: typing.Optional[int] = None,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('target', target),
            ('stat_offset', stat_offset),
            ('value', value)
        )

    def __str__(self):
        return f"If stat {self.stat_offset:02X} of {self.target} <= {self.value}"


class IfCompareTarget32Px(_EnemyAICondition):
    COND_ID = 0xC
    target = cty.byte_prop(1, ret_type=Target)
    is_outside = cty.byte_prop(2, ret_type=bool)

    def __str__(self):
        compare_str = "Within" if not self.is_outside else "Not Within"
        return f"If {self.target} is {compare_str} 32 pixels"


class IfOwnPosition(_EnemyAICondition):
    COND_ID = 0x10

    @property
    def mode(self):
        return self[1] * 2*self[2]

    @mode.setter
    def mode(self, val: int):
        if val == 0:
            self[1], self[2] = 0, 0
        elif val == 1:
            self[1], self[2] = 1, 0
        elif val == 2:
            self[1], self[2] = 0, 1
        elif val == 3:
            self[1], self[2] = 1, 1
        else:
            raise ValueError

    def __str__(self):
        if self.mode == 0:
            return "If 128 or more pixels from the top of the screen"
        elif self.mode == 1:
            return "If less than 128 pixels from the top of the screen"
        elif self.mode == 2:
            return "If less than 80 pixels from the left of the screen"
        elif self.mode == 3:
            return "If 176px or more from the left of the screen"
        else:
            raise ValueError


class IfHitByTechType(_EnemyAICondition):
    COND_ID = 0x11

    is_enemy_tech = cty.byte_prop(1, ret_type=bool)
    is_not_equal = cty.byte_prop(3, ret_type=bool)

    def __str__(self):
        tech_type_str = "Enemy Tech" if self.is_enemy_tech else "Player Tech"
        comp_str = "Is Not" if self.is_not_equal else "Is"

        return f"If {comp_str} hit by {tech_type_str}"


class IfHitByTechID(_EnemyAICondition):
    COND_ID = 0x12

    is_enemy_tech = cty.byte_prop(1, ret_type=bool)
    tech_id = cty.byte_prop(2)
    is_not_equal = cty.byte_prop(3, ret_type=bool)

    def __init__(self, *args,
                 is_enemy_tech: bool | None = None,
                 tech_id: int | None = None,
                 is_not_equal: bool | None = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ("is_enemy_tech", is_enemy_tech),
            ("tech_id", tech_id),
            ("is_not_equal", is_not_equal)
        )

    def __str__(self):
        tech_type_str = "Enemy Tech" if self.is_enemy_tech else "Player Tech"
        # comp_str = "Is Not" if self.is_not_equal else "Is"

        return f"If {tech_type_str} hit by {tech_type_str} #{self.tech_id}"


class IfAttacker(_EnemyAICondition):
    COND_ID = 0x13

    is_enemy = cty.byte_prop(1, ret_type=bool)
    is_not_equal = cty.byte_prop(3, ret_type=bool)

    def __str__(self):
        attacker_type_str = "Enemy" if self.is_enemy else "Player"
        comp_str = "Is Not" if self.is_not_equal else "Is"

        return f"If {comp_str} hit by {attacker_type_str}"


class AIElement(IntEnum):
    LIGHTNING = 0x80
    SHADOW = 0x40
    WATER = 0x20
    FIRE = 0x10
    PHYSICAL = 0x04
    MAGICAL = 0x02


class IfAttackElement(_EnemyAICondition):
    COND_ID = 0x15

    element = cty.byte_prop(1, ret_type=AIElement)
    is_not_equal = cty.byte_prop(3)

    def __init__(self, *args,
                 element: Optional[AIElement] = None,
                 is_not_equal: Optional[bool] = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ('element', element),
            ('is_not_equal', is_not_equal)
        )

    def __str__(self):
        comp_str = "Is Not" if self.is_not_equal else "Is"
        return f"If Hit By Tech Whose Element {comp_str} {self.element}"


class IfRandom(_EnemyAICondition):
    COND_ID = 0x17

    percent_chance = cty.byte_prop(1)

    def __str__(self):
        return f"If Random Number < {self.percent_chance}"


class IfStatEqual(_EnemyAICondition):
    COND_ID = 0x18
    value = cty.byte_prop(1)
    target = cty.byte_prop(2, ret_type=Target)
    stat_offset = cty.byte_prop(3)

    def __init__(self, *args,
                 value: int | None = None,
                 target: Target | None = None,
                 stat_offset: int | None = None,
                 **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ("value", value),
            ("target", target),
            ("stat_offset", stat_offset)
        )

    def __str__(self):
        return f"If stat {self.stat_offset:02X} of {self.target} equals {self.value}"


class IfOnlyOfType(_EnemyAICondition):
    COND_ID = 0x1A

    monster_index = cty.byte_prop(1)
    is_not_alone = cty.byte_prop(2, ret_type=bool)
    is_with_other_types = cty.byte_prop(3, ret_type=bool)

    def __str__(self):
        return f"If monster {self.monster_index:02X} is with other types (Fix this)"


class IfNumLivingPCsLessThanEqual(_EnemyAICondition):
    COND_ID = 0x1B

    num_pcs = cty.byte_prop(1)

    def __str__(self):
        return f"If Number of Living PCs <= {self.num_pcs}"


class IfCompareTarget48Px(_EnemyAICondition):
    COND_ID = 0x1F
    target = cty.byte_prop(1, ret_type=Target)
    is_outside = cty.byte_prop(2, ret_type=bool)

    def __str__(self):
        compare_str = "Within" if not self.is_outside else "Not Within"
        return f"If {self.target} is {compare_str} 48 pixels"


class IfKilled(_EnemyAICondition):
    COND_ID = 0x20

    def __str__(self):
        return "If Killed"


_ind_condition_dict: dict[int: typing.Type[_EnemyAICondition]] = {
    0: IfTrue,
    1: IfHPLessThanEqualHalf,
    2: IfStatus,
    3: IfMoved,
    4: IfMonsterDead,
    5: IfNumLivingEnemiesLessThanEqual,
    7: IfStatusCounter,
    8: IfHPLessThanEqual,
    9: IfStatLessThan,
    0xB: IfStatLessThanEqual,
    0xC: IfCompareTarget32Px,
    0x10: IfOwnPosition,
    0x11: IfHitByTechType,
    0x12: IfHitByTechID,
    0x13: IfAttacker,
    0x15: IfAttackElement,
    0x17: IfRandom,
    0x18: IfStatEqual,
    0x1A: IfOnlyOfType,
    0x1B: IfNumLivingPCsLessThanEqual,
    0x1F: IfCompareTarget48Px,
    0x20: IfKilled,
    0x23: IfStatEqual,
    0x24: IfStatEqual,
    0x25: IfStatEqual,
    0x26: IfStatEqual,
    0x27: IfStatEqual,
    0x28: IfStatEqual,
}


def get_condition_from_buffer(buf: typing.ByteString, pos: int = 0) -> _EnemyAICondition:
    """
    Returns an AI condition from the given position in the buffer
    """

    cond_id = buf[pos]
    cond_type = _ind_condition_dict[cond_id]
    size = cond_type.SIZE

    ret_cond = cond_type(buf[pos:pos+size])
    return ret_cond


T = typing.TypeVar('T', bound='_EnemyAIAction')


class _EnemyAIAction(_AttrSizedBinaryData):
    ACTION_ID: typing.ClassVar[int]

    @classmethod
    def _get_default_value(cls) -> bytearray:
        default = super()._get_default_value()
        default[0] = cls.ACTION_ID

        return default

    @classmethod
    def validate_data(cls: typing.Type[T], data: T):
        super().validate_data(data)
        if data[0] != cls.ACTION_ID:
            raise ValueError

    def __str__(self):
        return f"{self.__class__.__name__}: " + " ".join(f"{x:02X}" for x in self)


class Wander(_EnemyAIAction):
    ACTION_ID = 0
    SIZE = 4


class Attack(_EnemyAIAction):
    ACTION_ID = 1
    SIZE = 4

    attack_id = cty.byte_prop(1)


class Tech(_EnemyAIAction):
    ACTION_ID = 2
    SIZE = 6

    tech_id = cty.byte_prop(1)
    target = cty.byte_prop(2, ret_type=Target)
    message_id = cty.byte_prop(5)

    def __init__(self, *args,
                 tech_id: int | None = None,
                 target: Target | None = None,
                 message_id: int | None = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ("tech_id", tech_id),
            ("target", target),
            ("message_id", message_id)
        )


class RandomAction(_EnemyAIAction):
    ACTION_ID = 4
    SIZE = 1


class BecomeMonster(_EnemyAIAction):
    ACTION_ID = 7
    SIZE = 4

    monster_id = cty.byte_prop(1, ret_type=ctenums.EnemyID)
    animation_id = cty.byte_prop(2)
    refill_hp = cty.byte_prop(3, ret_type=bool)

    def __str__(self):
        refill_str = "HP Refill" if self.refill_hp else "No HP Refill"
        return f"Become {self.monster_id} With {refill_str} ({_EnemyAIAction.__str__(self)})"


class RunAway(_EnemyAIAction):
    ACTION_ID = 0xA
    SIZE = 3

    animation_id = cty.byte_prop(1)
    message_id = cty.byte_prop(2)

    def __str__(self):
        return f"Run Away with message {self.message_id}"


class SetStat(_EnemyAIAction):
    ACTION_ID = 0xB
    SIZE = 5

    stat_offset = cty.byte_prop(1)
    stat_value = cty.byte_prop(2)
    set_equal = cty.byte_prop(3, ret_type=bool)
    message_id = cty.byte_prop(4)


class StatMath(_EnemyAIAction):
    ACTION_ID = 0xC
    SIZE = 4

    stat_offset = cty.byte_prop(1)
    is_addition = cty.byte_prop(2, 0x80)
    magnitude = cty.byte_prop(2, 0x7F)
    message_id = cty.byte_prop(3)


class StateChange(_EnemyAIAction):
    ACTION_ID = 0xD
    SIZE = 3


class DisplayMessage(_EnemyAIAction):
    ACTION_ID = 0xF
    SIZE = 2

    message_id = cty.byte_prop(1)

    def __init__(self,
                 *args,
                 message_id: int | None = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._set_properties(
            ("message_id", message_id)
        )


class ReviveSupportEnemies(_EnemyAIAction):
    ACTION_ID = 0x10
    SIZE = 4

    unknown = cty.byte_prop(1)  # Copy to 0x7E000E
    sound_id = cty.byte_prop(2)
    message_id = cty.byte_prop(3)


class MultiStatSet(_EnemyAIAction):
    ACTION_ID = 0x11
    SIZE = 10

    stat_offset_1 = cty.byte_prop(1)
    stat_value_1 = cty.byte_prop(2)
    stat_offset_2 = cty.byte_prop(3)
    stat_value_2 = cty.byte_prop(4)
    stat_offset_3 = cty.byte_prop(5)
    stat_value_3 = cty.byte_prop(6)
    stat_offset_4 = cty.byte_prop(7)
    stat_value_4 = cty.byte_prop(8)
    message_id = cty.byte_prop(9)


class TechAndMultiStatSet(_EnemyAIAction):
    ACTION_ID = 0x12
    SIZE = 16

    target = cty.byte_prop(2, ret_type=Target)
    tech_id = cty.byte_prop(1)

    stat_offset_1 = cty.byte_prop(5)
    stat_value_1 = cty.byte_prop(6)
    stat_offset_2 = cty.byte_prop(7)
    stat_value_2 = cty.byte_prop(8)
    stat_offset_3 = cty.byte_prop(9)
    stat_value_3 = cty.byte_prop(10)
    stat_offset_4 = cty.byte_prop(11)
    stat_value_4 = cty.byte_prop(12)
    stat_offset_5 = cty.byte_prop(13)
    stat_value_5 = cty.byte_prop(14)
    message_id = cty.byte_prop(15)


class MultiStatMath(_EnemyAIAction):
    ACTION_ID = 0x14
    SIZE = 10

    stat_offset_1 = cty.byte_prop(1)
    is_subtraction_1 = cty.byte_prop(2, 0x80)
    magnitude_1 = cty.byte_prop(2, 0x7F)
    stat_offset_2 = cty.byte_prop(3)
    is_subtraction_2 = cty.byte_prop(4, 0x80)
    magnitude_2 = cty.byte_prop(4, 0x7F)
    stat_offset_3 = cty.byte_prop(5)
    is_subtraction_3 = cty.byte_prop(6, 0x80)
    magnitude_3 = cty.byte_prop(6, 0x7F)
    stat_offset_4 = cty.byte_prop(7)
    is_subtraction_4 = cty.byte_prop(8, 0x80)
    magnitude_4 = cty.byte_prop(8, 0x7F)
    message_id = cty.byte_prop(9)


class TechAndMultiStatMath(_EnemyAIAction):
    ACTION_ID = 0x15
    SIZE = 16

    target = cty.byte_prop(2, ret_type=Target)
    tech_id = cty.byte_prop(1)

    stat_offset_1 = cty.byte_prop(5)
    is_subtraction_1 = cty.byte_prop(6, 0x80)
    magnitude_1 = cty.byte_prop(6, 0x7F)
    stat_offset_2 = cty.byte_prop(7)
    is_subtraction_2 = cty.byte_prop(8, 0x80)
    magnitude_2 = cty.byte_prop(8, 0x7F)
    stat_offset_3 = cty.byte_prop(9)
    is_subtraction_3 = cty.byte_prop(10, 0x80)
    magnitude_3 = cty.byte_prop(10, 0x7F)
    stat_offset_4 = cty.byte_prop(11)
    is_subtraction_4 = cty.byte_prop(12, 0x80)
    magnitude_4 = cty.byte_prop(12, 0x7F)
    stat_offset_5 = cty.byte_prop(13)
    is_subtraction_5 = cty.byte_prop(14, 0x80)
    magnitude_5 = cty.byte_prop(14, 0x7F)
    message_id = cty.byte_prop(15)


class ReviveAndMultiStatSet(_EnemyAIAction):
    ACTION_ID = 0x16
    SIZE = 12

    tech_id = cty.byte_prop(2)
    stat_offset_1 = cty.byte_prop(3)
    stat_value_1 = cty.byte_prop(4)
    stat_offset_2 = cty.byte_prop(5)
    stat_value_2 = cty.byte_prop(6)
    stat_offset_3 = cty.byte_prop(7)
    stat_value_3 = cty.byte_prop(8)
    stat_offset_4 = cty.byte_prop(9)
    stat_value_4 = cty.byte_prop(10)
    message_id = cty.byte_prop(11)


_ind_action_dict: dict[int, typing.Type[_EnemyAIAction]] = {
    0: Wander,
    1: Attack,
    2: Tech,
    4: RandomAction,
    7: BecomeMonster,
    0xA: RunAway,
    0xB: SetStat,
    0xC: StatMath,
    0xD: StateChange,
    0xF: DisplayMessage,
    0x10: ReviveSupportEnemies,
    0x11: MultiStatSet,
    0x12: TechAndMultiStatSet,
    0x14: MultiStatMath,
    0x15: TechAndMultiStatMath,
    0x16: ReviveAndMultiStatSet,
}


def get_action_from_buffer(buf: typing.ByteString, pos: int = 0) -> _EnemyAIAction:
    """Extract an AI Action from the buffer at the given position."""
    action_id = buf[pos]
    action_type = _ind_action_dict[action_id]
    action_size = action_type.SIZE

    ret_action = action_type(buf[pos:pos+action_size])
    return ret_action


@dataclass
class EnemyAIScriptBlock:
    condition_list: list[_EnemyAICondition] = field(default_factory=list)
    action_list: list[_EnemyAIAction] = field(default_factory=list)

    def to_bytes(self):
        """Convert to CT-usable bytes"""
        if not self.condition_list or not self.action_list:
            raise ValueError

        ret_bytes = (
            b''.join(condition for condition in self.condition_list) +
            b'\xFE' +
            b''.join(action for action in self.action_list) +
            b'\xFE'
        )

        return ret_bytes

    def __str__(self):
        ret_str = ""
        for condition in self.condition_list:
            ret_str += str(condition) + "\n"

        for action in self.action_list:
            ret_str += "\t"+str(action) + "\n"

        return ret_str


class EnemyAIScript:
    """Class for storing an enemy's AI script."""
    SCRIPT_PTR_ADDR = 0x01AFD7

    def __init__(
            self,
            action_script: typing.Optional[list[EnemyAIScriptBlock]] = None,
            reaction_script: typing.Optional[list[EnemyAIScriptBlock]] = None,
    ):
        if action_script is None:
            action_script: list[EnemyAIScriptBlock] = []

        if reaction_script is None:
            reaction_script: list[EnemyAIScriptBlock] = []

        self.action_script: list[EnemyAIScriptBlock] = list(action_script)
        self.reaction_script: list[EnemyAIScriptBlock] = list(reaction_script)

    def get_message_ids_used(self) -> list[int]:
        """returns indices of battle messages used."""
        used_indices: set[int] = set()
        for block in self.action_script + self.reaction_script:
            for action in block.action_list:
                if hasattr(action, "message_id"):
                    used_indices.add(action.message_id)

        return list(used_indices)

    @classmethod
    def get_script_ptr_start(cls, ct_rom: ctrom.CTRom) -> int:
        """Get the start of the script pointer table."""
        ct_rom.seek(cls.SCRIPT_PTR_ADDR)
        rom_addr = int.from_bytes(ct_rom.read(3), "little")
        return byteops.to_file_ptr(rom_addr)

    @classmethod
    def _get_script_start(
            cls,
            ct_rom: ctrom.CTRom,
            enemy_id: ctenums.EnemyID,
            ai_script_ptr_start: typing.Optional[int] = None
    ) -> int:
        """Find the start of enemy_id's script."""
        if ai_script_ptr_start is None:
            ai_script_ptr_start = cls.get_script_ptr_start(ct_rom)

        ct_rom.seek(ai_script_ptr_start + 2*enemy_id)
        offset = int.from_bytes(ct_rom.read(2), "little")

        return offset + (ai_script_ptr_start & 0xFF0000)

    @classmethod
    def _get_script_length(
            cls, ct_rom: ctrom.CTRom, pos: int
    ) -> int:
        """
        Find the length of a script starting at pos.
        This does not do a full parse but just finds two 0xFFs.  This mimics what CT
        does.
        """
        action_len = byteops.get_string_length(ct_rom.getbuffer(), pos, 0xFF)
        reaction_len = byteops.get_string_length(ct_rom.getbuffer(), pos+action_len, 0xFF)

        return action_len + reaction_len

    @classmethod
    def free_script_on_ct_rom(
            cls,
            ct_rom: ctrom.CTRom, enemy_id: ctenums.EnemyID,
            ai_script_ptr_start: typing.Optional[int] = None
    ):
        """
        Frees the space currently used by the enemy's script.
        """
        start = cls._get_script_start(ct_rom, enemy_id, ai_script_ptr_start)
        length = cls._get_script_length(ct_rom, start)

        ct_rom.space_manager.mark_block(
            (start, start+length),
            freespace.FSWriteType.MARK_FREE
        )

    def write_script_to_ct_rom(
            self, ct_rom: ctrom.CTRom, enemy_id: ctenums.EnemyID,
            ai_script_ptr_start: typing.Optional[int] = None
    ):
        """Write a script to a given enemy's spot on the ct rom"""
        if ai_script_ptr_start is None:
            ai_script_ptr_start = self.get_script_ptr_start(ct_rom)

        script_b = self.to_bytes()
        new_addr = ct_rom.space_manager.get_free_addr(len(script_b), hint=0x0C0000)

        if (new_addr & 0xFF0000) != 0x0C0000:
            raise freespace.FreeSpaceError("Insufficient bank 0x0C space")

        ct_rom.seek(new_addr)
        ct_rom.write(script_b, freespace.FSWriteType.MARK_USED)
        ct_rom.seek(ai_script_ptr_start + 2*enemy_id)
        ct_rom.write(int.to_bytes(new_addr & 0xFFFF, 2, "little"))

    @staticmethod
    def _read_script_from_bytestring(
            buf: typing.ByteString,
            pos: int
    ) -> tuple[list[EnemyAIScriptBlock], int]:
        """
        Read Action or Reaction part of an AIScript.
        Returns the list of blocks and the position immediately following the script.
        """

        blocks: list[EnemyAIScriptBlock] = []

        while buf[pos] != 0xFF:
            conditions: list[_EnemyAICondition] = []
            actions: list[_EnemyAIAction] = []

            while buf[pos] != 0xFE:
                condition = get_condition_from_buffer(buf, pos)
                conditions.append(condition)
                pos += len(condition)

            pos += 1
            # Very rarely a script will skip the 0xFE that should end the block
            # and go straight to 0xFF
            while buf[pos] not in (0xFE, 0xFF):
                action = get_action_from_buffer(buf, pos)
                actions.append(action)
                pos += len(action)

            blocks.append(EnemyAIScriptBlock(conditions, actions))
            if buf[pos] == 0xFE:
                pos += 1

        return blocks, pos+1

    @classmethod
    def from_bytestring(cls, buf: typing.ByteString, pos: int = 0):
        """Read an AI Script from a buffer."""
        action_script, pos = cls._read_script_from_bytestring(buf, pos)
        reaction_script, pos = cls._read_script_from_bytestring(buf, pos)

        return EnemyAIScript(action_script, reaction_script)

    def to_bytes(self) -> bytes:
        """Get ct-usable byte representation of the script."""
        ret_b = (
            b"".join(block.to_bytes() for block in self.action_script) +
            b"\xFF" +
            b"".join(block.to_bytes() for block in self.reaction_script) +
            b"\xFF"
        )

        return ret_b

    @classmethod
    def read_from_ct_rom(
            cls, ct_rom: ctrom.CTRom, enemy_id: ctenums.EnemyID,
            ai_script_ptr_addr: typing.Optional[int] = None
    ) -> 'EnemyAIScript':
        """Read an enemy's AI Script"""
        if ai_script_ptr_addr is None:
            ct_rom.seek(cls.SCRIPT_PTR_ADDR)
            ai_script_ptr_addr = int.from_bytes(ct_rom.read(3), 'little')
            ai_script_ptr_addr = byteops.to_file_ptr(ai_script_ptr_addr)

        ct_rom.seek(ai_script_ptr_addr + 2*enemy_id)
        offset = int.from_bytes(ct_rom.read(2), "little")
        script_addr = (ai_script_ptr_addr & 0xFF0000) + offset

        script = cls.from_bytestring(ct_rom.getbuffer(), script_addr)
        return script

    def __str__(self):
        ret_str = "Action:\n"
        for block in self.action_script:
            ret_str += str(block)

        ret_str += "Reaction:\n"
        for block in self.reaction_script:
            ret_str += str(block)

        return ret_str

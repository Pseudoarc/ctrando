"""Reworked itemdata module."""
import functools
import typing
from typing import Self

from ctrando.common import ctenums, cttypes as cty, ctrom
from ctrando.common.ctenums import ArmorEffects


class StatBit(ctenums.StrIntEnum):
    """Associate Stat to bit for StatBoost."""
    POWER = 0x80
    SPEED = 0x40
    STAMINA = 0x20
    HIT = 0x10
    EVADE = 0x08
    MAGIC = 0x04
    MDEF = 0x02


class StatBoost(cty.SizedBinaryData):
    """Two byte gear stat boost data."""
    SIZE = 2
    ROM_RW = cty.AbsPointerRW(0x0292CE)


    def __le__(self: Self, other: Self):
        return (
            self[0] & other[0] == self[0] and
            self.magnitude <= other.magnitude
        )

    def __eq__(self: Self, other: Self):
        return self == other

    def __ne__(self, other: Self):
        return not self == other

    def __lt__(self, other: Self):
        return self <= other and self != other

    def __gt__(self, other: Self):
        return self >= other and self != other

    def __ge__(self: Self, other: Self):
        return (
            self[0] & other[0] == other[0] and
            self.magnitude >= other.magnitude
        )

    magnitude = cty.byte_prop(1)

    @property
    def stats_boosted(self) -> list[StatBit]:
        """Which stats are included in the boost."""
        stat_list = [
            x for x in list(StatBit)
            if int(x) & self[0]
        ]

        return stat_list

    def stat_string(self) -> str:
        """Get an abbreviated string representing the StatBoost."""
        abbrev_dict = {
            StatBit.POWER: 'Pw',
            StatBit.SPEED: 'Sp',
            StatBit.STAMINA: 'St',
            StatBit.HIT: 'Hi',
            StatBit.EVADE: 'Ev',
            StatBit.MAGIC: 'Mg',
            StatBit.MDEF: 'Md'
        }

        if self.magnitude == 0 or not self.stats_boosted:
            return ''

        stat_str = '/'.join(abbrev_dict[x] for x in self.stats_boosted)

        return stat_str+'+'+str(self.magnitude)


class _ItemSecondaryData(cty.SizedBinaryData):
    """Base Class for Item Secondary Data."""
    SIZE = 0
    ROM_RW = None

    price = cty.bytes_prop(1, 2)
    is_unsellable = cty.byte_prop(0, 0x04, ret_type=bool)
    is_key_item = cty.byte_prop(0, 0x08, ret_type=bool)
    ngplus_carryover = cty.byte_prop(0, 0x10, ret_type=bool)

    def get_equipable_by(self) -> list[ctenums.CharID]:
        equip_list = []
        for char in list(ctenums.CharID):
            bitmask = 0x80 >> int(char)
            if self[3] & bitmask:
                equip_list.append(char)

        return equip_list

    def set_equipable_by(
            self,
            chars: typing.Union[ctenums.CharID,
                                typing.Iterable[ctenums.CharID]]
    ):
        if isinstance(chars, ctenums.CharID):
            chars = [chars]

        equip_byte = 0
        for char in chars:
            bitmask = 0x80 >> int(char)
            equip_byte |= bitmask

        self[3] = equip_byte


class AccessorySecondaryStats(_ItemSecondaryData):
    """Accessory Secondary Stats"""
    SIZE = 4
    ROM_RW = cty.AbsRomRW(0x0C0A1C)


class GearSecondaryStats(_ItemSecondaryData):
    """
    Class for gear secondary stats. Adds stat boosts and elemental protection.
    """
    SIZE = 6
    ROM_RW = cty.AbsRomRW(0x0C06A4)

    elem_bit_dict = {
        ctenums.Element.LIGHTNING: 0x80,
        ctenums.Element.SHADOW: 0x40,
        ctenums.Element.ICE: 0x20,
        ctenums.Element.FIRE: 0x10
    }

    elem_abbrev_dict = {
        ctenums.Element.LIGHTNING: 'Li',
        ctenums.Element.SHADOW: 'Sh',
        ctenums.Element.ICE: 'Wa',
        ctenums.Element.FIRE: 'Fi'
    }

    stat_boost_index = cty.byte_prop(4)
    elemental_protection_magnitude = cty.byte_prop(5, 0x0F)

    @staticmethod
    def prot_mag_to_percent(cls, prot_mag: int):
        """Get the protection magnitude as a percentage reduction."""
        return round(100 - 400/(4+prot_mag))

    def set_protect_element(self, element: ctenums.Element,
                            has_protection: bool):
        """
        Sets the elements that this gear protects against.
        """
        if element == ctenums.Element.NONELEMENTAL:
            print('Warning: Gear cannot protect against nonelemental.')
            return

        elem_bit = self.elem_bit_dict[element]

        if has_protection:
            bit_mask = elem_bit
            self[5] |= bit_mask
        else:
            bit_mask = 0xFF - elem_bit
            self[5] &= bit_mask

    def get_protection_desc_str(self) -> str:
        """
        Gets a string representation of this gear's elemental protection.
        For descriptions.
        """
        mag = self.prot_mag_to_percent(self.elemental_protection_magnitude)
        elems = self.get_protected_elements()

        elem_str = '/'.join(self.elem_abbrev_dict[elem]
                            for elem in elems)

        if mag == 0 or not elems:
            return ''

        return f'R:{elem_str} {mag}%'

    def get_protected_elements(self) -> list[ctenums.Element]:
        """
        Gets the elements that this gear protects against.
        """
        elements = [
            elem for elem in self.elem_bit_dict
            if self.elem_bit_dict[elem] & self[5]
        ]

        return elements

    def get_stat_string(self):
        """
        Gets a string representing these stats.  For spoilers/testing.
        """
        price_str = f'Price: {self.price}'
        equip_str = 'Equippable by: ' \
            + ', '.join(str(x) for x in self.get_equipable_by())
        prot_mag = GearSecondaryStats.prot_mag_to_percent(self.elemental_protection_magnitude)
        if prot_mag == 0 or not self.get_protected_elements:
            prot_str = 'No Elemental Protection'
        else:
            prot_str = f'Protects {prot_mag:.0f}% vs ' \
                + ', '.join(str(x) for x in self.get_protected_elements())

        return '\n'.join((price_str, equip_str, prot_str))


class ConsumableKeySecondaryStats(_ItemSecondaryData):
    """Class for Consumable and Key Item Stats."""
    SIZE = 3
    ROM_RW = cty.AbsRomRW(0x0C0ABC)

    def get_equipable_by(self) -> list[ctenums.CharID]:
        raise TypeError("Consumables are not Equippable")

    def set_equipable_by(
            self,
            chars: typing.Union[ctenums.CharID,
                                typing.Iterable[ctenums.CharID]]
    ):
        raise TypeError("Consumables are not Equippable")


class WeaponStats(cty.SizedBinaryData):
    SIZE = 5
    ROM_RW = cty.AbsRomRW(0x0C0262)

    attack = cty.byte_prop(0)
    # Unknown byte 1
    critical_rate = cty.byte_prop(2, input_filter=lambda self, x: sorted([0, x, 100])[1])
    effect_id = cty.byte_prop(3)
    has_effect = cty.byte_prop(4, ret_type=bool)


_armor_status_abbrev_dict: dict[ArmorEffects, str] = {
    ArmorEffects.NONE: '',
    ArmorEffects.SHIELD: 'Shd',
    ArmorEffects.ABSORB_LIT_25: 'Ab:Li 25%',
    ArmorEffects.ABSORB_SHD_25: 'Ab:Sh 25%',
    ArmorEffects.ABSORB_WAT_25: 'Ab:Wa 25%',
    ArmorEffects.ABSORB_FIR_25: 'Ab:Fi 25%',
    ArmorEffects.ABSORB_LIT_100: 'Ab:Li 100%',
    ArmorEffects.ABSORB_SHD_100: 'Ab:Sh 100%',
    ArmorEffects.ABSORB_WAT_100: 'Ab:Wa 100%',
    ArmorEffects.ABSORB_FIR_100: 'Ab:Fi 100%',
    ArmorEffects.IMMUNE_CHAOS: 'P:Chaos',
    ArmorEffects.IMMUNE_LOCK: 'P:Lock',
    ArmorEffects.IMMUNE_SLOW_STOP: 'P:Sl/St',
    ArmorEffects.IMMUNE_ALL: 'P:All',
    ArmorEffects.BARRIER: 'Bar',
    ArmorEffects.CHAOS_HP_DOWN: 'Chaos/HP Dn',
    ArmorEffects.HASTE: 'Haste'
}


class ArmorStats(cty.SizedBinaryData):
    SIZE = 3
    ROM_RW = cty.AbsRomRW(0x0C047E)

    def _armor_effect_validator(self, effect_id):
        if effect_id == ArmorEffects.NONE:
            self.has_effect = False
        else:
            self.has_effect = True

    defense = cty.byte_prop(0)
    effect_id = cty.byte_prop(1, input_filter=lambda self, x: self._armor_effect_validator(x))
    has_effect = cty.byte_prop(2, ret_type=bool)

    def get_effect_string(self) -> str:
        """Returns a string representation of this armor's effect."""
        if self.has_effect:
            return _armor_status_abbrev_dict[self.effect_id]
        return ''


class Type_09_Buffs(ctenums.StrIntEnum):
    """
    Buffs with a type of 9.  Used by Accessories.

    The type of a buff is an index into the array of stats which indicates
    the byte to modify.
    """
    BERSERK = 0x80
    BARRIER = 0x40
    MP_REGEN = 0x20
    UNK_10 = 0x10
    SPECS = 0x08
    SHIELD = 0x04
    SHADES = 0x02
    UNK_01 = 0x01

    def get_abbrev(self) -> str:
        """Get an abbreviated string of the buff.  For Item descriptions."""
        type_09_abbrev: dict[Type_09_Buffs, str] = {
            Type_09_Buffs.BERSERK: 'Bers',
            Type_09_Buffs.BARRIER: 'Bar',
            Type_09_Buffs.MP_REGEN: 'RegMP',
            Type_09_Buffs.UNK_10: '?',
            Type_09_Buffs.SPECS: '+50%Dmg',
            Type_09_Buffs.SHIELD: 'Shld',
            Type_09_Buffs.SHADES: '+25%Dmg',
            Type_09_Buffs.UNK_01: '?'
        }

        return type_09_abbrev[self]


class Type_05_Buffs(ctenums.StrIntEnum):
    """
    Buffs with a type of 5.  Used by Accessories.  Presently, only the
    autorevive status (Greendream) uses this type.

    The type of a buff is an index into the array of stats which indicates
    the byte to modify.
    """

    GREENDREAM = 0x80

    def get_abbrev(self) -> str:
        """Get an abbreviated string of the buff.  For Item descriptions."""
        if self == Type_05_Buffs.GREENDREAM:
            return 'Autorev'

        raise ValueError("Undefined Buff Type")


class Type_06_Buffs(ctenums.StrIntEnum):
    """
    Buffs with a type of 6.  Used by Accessories.

    The type of a buff is an index into the array of stats which indicates
    the byte to modify.
    """
    PROT_STOP = 0x80
    PROT_POISON = 0x40
    PROT_SLOW = 0x20
    PROT_HPDOWN = 0x10  # ?
    PROT_LOCK = 0x08
    PROT_CHAOS = 0x04
    PROT_SLEEP = 0x02
    PROT_BLIND = 0x01

    def get_abbrev(self) -> str:
        """Get an abbreviated string of the buff.  For Item descriptions."""
        status_abbrev = {
            Type_06_Buffs.PROT_STOP: 'Stp',
            Type_06_Buffs.PROT_POISON: 'Psn',
            Type_06_Buffs.PROT_SLOW: 'Slw',
            Type_06_Buffs.PROT_HPDOWN: 'HPdn',
            Type_06_Buffs.PROT_LOCK: 'Lck',
            Type_06_Buffs.PROT_CHAOS: 'Chs',
            Type_06_Buffs.PROT_SLEEP: 'Slp',
            Type_06_Buffs.PROT_BLIND: 'Bnd'
        }

        return status_abbrev[self]


class Type_08_Buffs(ctenums.StrIntEnum):
    """
    Buffs with a type of 8.  Used by Accessories.

    The type of a buff is an index into the array of stats which indicates
    the byte to modify.
    """

    HASTE = 0x80
    EVADE = 0x40

    def get_abbrev(self) -> str:
        """Get an abbreviated string of the buff.  For Item descriptions."""
        type_08_abbrev: dict[Type_08_Buffs, str] = {
            Type_08_Buffs.HASTE: 'Haste',
            Type_08_Buffs.EVADE: '2xEvd'
        }

        return type_08_abbrev[self]


_Buff = typing.Union[Type_05_Buffs, Type_06_Buffs, Type_08_Buffs,
                     Type_09_Buffs]
_BuffList = typing.Iterable[_Buff]


def get_buff_string(buffs: typing.Union[_Buff, _BuffList]) -> str:
    """
    Return a string representation of the _Buff or _BuffList.  In the case of
    a _BuffList, all buffs must be of the same type.
    """
    if isinstance(buffs, typing.Iterable):
        if not buffs:
            return ''

        buff_str = ""
        buff_types = list(set(type(buff) for buff in buffs))
        buffs = list(set(buffs))

        if len(buff_types) > 1:
            raise TypeError('Buff list has multiple types.')

        buff_type = buff_types[0]
        if buff_type in (Type_05_Buffs, Type_09_Buffs, Type_08_Buffs):
            buff_str = '/'.join(x.get_abbrev() for x in buffs)
        elif buff_type == Type_06_Buffs:
            if len(buffs) == 8:
                buff_str = 'P:All'
            else:
                buff_str = 'P:'+'/'.join(x.get_abbrev() for x in buffs)

        return buff_str

    raise TypeError("Invalid Buff Type")


class AccessoryStats(cty.SizedBinaryData):
    """Class for accessory stats."""
    SIZE = 4
    ROM_RW = cty.AbsRomRW(0x0C052C)

    has_battle_buff = cty.byte_prop(1, 0x80, ret_type=bool)

    def _get_buff_type(self):
        """The type of the _Buff.  Only used internally."""
        if not self.has_battle_buff:
            return None
        if self[2] == 0x05:
            return Type_05_Buffs
        if self[2] == 0x06:
            return Type_06_Buffs
        if self[2] == 0x08:
            return Type_08_Buffs
        if self[2] == 0x09:
            return Type_09_Buffs

        raise ValueError('Invalid buff type')

    def _get_buff_type_index(self, buff: _Buff) -> int:
        """Get offset into stat array for byte modified by the buff."""
        if isinstance(buff, Type_05_Buffs):
            return 5
        if isinstance(buff, Type_06_Buffs):
            return 6
        if isinstance(buff, Type_08_Buffs):
            return 8
        if isinstance(buff, Type_09_Buffs):
            return 9
        raise ValueError('Invalid buff type')

    @property
    def battle_buffs(self) -> list[_Buff]:
        """List of buffs this accessory has."""
        BuffType = self._get_buff_type()
        return [x for x in list(BuffType) if self._data[3] & x]

    @battle_buffs.setter
    def battle_buffs(self, val: typing.Union[_Buff, _BuffList]):

        if not self.has_battle_buff:
            raise ValueError('Adding buffs to item without buffs set.')

        if not isinstance(val, typing.Iterable):
            val = [val]

        if not val:
            self[3] = 0
        else:
            buffs = list(set(val))
            types = list(set(type(x) for x in buffs))

            if len(types) != 1:
                raise TypeError('Multiple types of buffs')

            buff_type = types[0]
            type_val = {
                Type_05_Buffs: 5,
                Type_06_Buffs: 6,
                Type_08_Buffs: 8,
                Type_09_Buffs: 9
            }

            buff_type_val = type_val[buff_type]
            self[2] = buff_type_val

            buff_byte = functools.reduce(lambda a, b: a | b, buffs, 0)
            self[3] = buff_byte

    has_stat_boost = cty.byte_prop(1, 0x40, ret_type=bool)

    @property
    def stat_boost_index(self):
        """
        The index of the stat boost had by this accessory.

        Unsure of behavior if has_stat_boost is False.
        """
        if not self.has_stat_boost:
            # raise exception?
            return 0
        return self[2]

    @stat_boost_index.setter
    def stat_boost_index(self, val: int):
        if not self.has_stat_boost:
            # raise Exception
            pass
        else:
            self[2] = val

    has_counter_effect = cty.byte_prop(0, 0x40, ret_type=bool)

    @property
    def has_normal_counter_mode(self) -> bool:
        """Whether accessory counters with a basic attack."""
        return bool(self.has_counter_effect and self[2] & 0x80)

    # non-normal = atb counter
    @has_normal_counter_mode.setter
    def has_normal_counter_mode(self, normal_mode: bool):
        if self.has_counter_effect:
            if normal_mode:
                self[2] |= 0x80
            else:
                self[2] &= 0x7F
        else:
            # raise exception
            pass

    @property
    def counter_rate(self):
        """Percentage chance of counter effect triggering."""
        if self.has_counter_effect:
            return self[3]

        raise ValueError("Counter Effect Not Set")

    @counter_rate.setter
    def counter_rate(self, val: int):
        if self.has_counter_effect:
            self[3] = val
        else:
            # raise exception?  Force counter mode on?
            raise ValueError("Counter Effect Not Set")
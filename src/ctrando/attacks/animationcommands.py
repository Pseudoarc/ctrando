"""Commands for use in battle animations"""
import enum
import inspect
import sys
import typing

# Initial command list is taken from https://www.chronocompendium.com/Term/Tech_Data_Notes.html
# and Mauron's Hi-Tech tool.
from ctrando.common import cttypes as cty
from ctrando.overworlds import oweventcommand


class EnumTarget(enum.IntEnum):
    CASTER_0 = 0
    CASTER_1 = 1



class AnimationCommand(oweventcommand.OverworldEventCommand):
    ...

class ReturnCommand(AnimationCommand):
    SIZE = 1
    CMD_ID = 0


class EndTech(AnimationCommand):
    SIZE = 1
    CMD_ID = 1


class _PlayAnimationBase(AnimationCommand):
    CMD_ID = -1
    SIZE = 2
    animation_id = cty.byte_prop(1)

    def __init__(self, *args, animation_id: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ('animation_id', animation_id)
        )


class PlayAnimationLoop(_PlayAnimationBase):
    CMD_ID = 2


class PlayAnimationOnce(_PlayAnimationBase):
    CMD_ID = 3


class PlayAnimationFirstFrame(_PlayAnimationBase):
    CMD_ID = 4


class PlayAnimationFirstFrame05(_PlayAnimationBase):
    CMD_ID = 5


class PlayAnimationFirstFrame06(_PlayAnimationBase):
    CMD_ID = 6


class SetDefaultspeed(AnimationCommand):
    SIZE = 1
    CMD_ID = 7


class SetSpeedSlowest(AnimationCommand):
    SIZE = 1
    CMD_ID = 8


class SetSpeedSlow(AnimationCommand):
    SIZE = 1
    CMD_ID = 9


class SetSpeedMedium(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA


class SetSpeedFast(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x0B


class SetSpeedFastest(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x0C


class SetSpeedFastestShort(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x0D


class SetSpeedFastestShorter(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x0E


class SetSpeedFastestShortest(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x0F


class SlideSpriteToCoordinates(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x10

    x_coord = cty.byte_prop(1)
    y_coord = cty.byte_prop(2)

    def __init__(self, *args, x_coord: int = None, y_coord: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("x_coord", x_coord),
            ("y_coord", y_coord)
        )


class SlideSpriteToStoredCoordinates(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x11


# 12 tt Slide sprite to target tt - Uses target routine list
class SlideSpriteToTarget(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x12

    target = cty.byte_prop(1)

    def __init__(self, *args, target: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("target", target),
        )


# 13 cc xx yy Spiral Sprite to Coordinates - cc = 1 for clockwise, xx yy coordinates.
class SpiralSpriteToCoordinates(AnimationCommand):
    SIZE = 4
    CMD_ID = 0x13

    is_clockwise = cty.byte_prop(1, ret_type=bool)
    x_coord = cty.byte_prop(2)
    y_coord = cty.byte_prop(3)


# 14 cc Spiral Sprite to Stored Coordinates - cc = 1 for clockwise
class SpiralSpriteToStoredCoordinates(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x14

    is_clockwise = cty.byte_prop(1, ret_type=bool)


# 15 cc tt Spiral Sprite to Target - cc = 1 for clockwise
class SpiralSpriteToTarget(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x15

    is_clockwise = cty.byte_prop(1, ret_type=bool)
    target = cty.byte_prop(2)


# 16 xx yy Move X, then Y to coordinates
class MoveXThenYToCoordinates(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x16

    x_coord = cty.byte_prop(1)
    y_coord = cty.byte_prop(2)


# 17 Move X, then Y to stored coordinates
class MoveXThenYToStoredCoordinates(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x17


# 18 Move X, then Y to target -- Unused?
class MoveXThenYToTarget(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x18

    target = cty.byte_prop(1)


# 19 xx yy Teleport to coordinates xx yy
class TeleportToCoordinates(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x19

    x_coord = cty.byte_prop(1)
    y_coord = cty.byte_prop(2)

    def __init__(self, *args, x_coord: int = None, y_coord: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("x_coord", x_coord),
            ("y_coord", y_coord)
        )


# 1A Teleport to stored coordinates
class TeleportToStoredCoordinates(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x1A


# 1B tt Teleport to target
class TeleportToTarget(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x1B

    target = cty.byte_prop(1)

    def __init__(self, *args, target: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("target", target)
        )


# 1C oo Link effect Object to target or caster object oo. Used for movement, like Cyclone's sword effect
class LinkEffectObjToCasterObj(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x1C

    # Effect Obect is "This" effect
    caster_obj = cty.byte_prop(1)


# 1D Unlink Object
class UnlinkObject(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x1D


# 1E ss perform super command ss (example cyclone)
class PerformSuperCommand(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x1E

    super_command = cty.byte_prop(1)

    def __init__(self, *args, super_command: int = None, **kwargs):
        AnimationCommand.__init__(self, *args,  **kwargs)
        self._set_properties(
            ("super_command", super_command)
        )


# 1F Return from super command - signifies end of super command data
class ReturnFromSuperCommand(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x1F


# 20 tt pause for time tt
class Pause(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x20

    duration = cty.byte_prop(1)

    def __init__(self, *args, duration: int = None, **kwargs):
        AnimationCommand.__init__(self, *args,  **kwargs)
        self._set_properties(
            ("duration", duration)
        )


# 21 Return from super command if counter 0x1F (Y coordinate) is zero.
class ReturnFromSuperCommandZero1F(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x21


# 22 cc vv Wait for counter cc to reach value vv
class WaitForCounterValue(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x22

    counter = cty.byte_prop(1)
    value = cty.byte_prop(2)

    def __init__(self, *args, counter: int = None, value: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("counter", counter),
            ("value", value)
        )


# 23 vv Wait for counter 0x1C (flow control) to reach value vv
class WaitForCounter1CValue(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x23

    value = cty.byte_prop(1)

    def __init__(self, *args, value: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("value", value)
        )


# 24 vv Wait for counter 0x1D (flow control) to reach value vv
class WaitForCounter1DValue(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x24

    value = cty.byte_prop(1)

    def __init__(self, *args, value: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("value", value)
        )


# 25 xx Return if target (xx + 1) is not present.
class ReturnIfTargetAbsent(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x25

    target = cty.byte_prop(1)

    def __init__(self, *args, target: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("target", target)
        )

# 26 aa ff Load frame of animation aa - animation ff - frame
class LoadAnimationFrame(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x26

    animation = cty.byte_prop(1)
    frame = cty.byte_prop(2)


# 27 Unknown
class Unknown27(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x27


# 28 Unknown
class Unknown28(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x28


# 29 Hide Caster or Target Object
class HideCasterOrTarget(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x29


# 2A Show Caster or Target Object
class ShowCasterOrTarget(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x2A


# 2B Unknown
class Unknown2B(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x2B


# 2C Unknown
class Unknown2C(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x2C


# 2D Unknown
class Unknown2D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x2D


# 2E Unknown
class Unknown2E(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x2E


# 2F End Tech - identical to 01
class EndTech2F(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x2F


# 30 cc vv Set counter cc to value vv
class SetCounterToValue(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x30

    counter = cty.byte_prop(1)
    value = cty.byte_prop(2)

    def __init__(self, *args, counter: int = None, value: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("counter", counter),
            ("value", value)
        )


# 31 vv Set counter 0x1C to value vv
class SetCounter1CToValue(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x31

    value = cty.byte_prop(1)


# 32 vv Set counter 0x1D to value vv
class SetCounter1DToValue(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x32

    value = cty.byte_prop(1)


# 33 tt Store Coordinates of Target tt
class StoreTargetCoordinates(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x33

    target = cty.byte_prop(1)

    def __init__(self, *args, target: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("target", target)
        )


# 34 cc Increment counter cc
class IncrementCounter(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x34

    counter = cty.byte_prop(1)

    def __init__(self, *args, counter: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("counter", counter)
        )


# 35 increment counter 0x1C
class IncrementCounter1C(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x35


# 36 increment counter 0x1D
class IncrementCounter1D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x36


# 37 cc Decrement counter cc
class DecrementCounter(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x37

    counter = cty.byte_prop(1)


# 38 Decrement counter 0x1C
class DecrementCounter1C(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x38


# 39 Decrement counter 0x1D
class DecrementCounter1D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x39


# 3A cc vv Add value vv to counter cc
class IncreaseCounterByValue(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x3A

    counter = cty.byte_prop(1)
    value = cty.byte_prop(2)


# 3B vv Increase Counter 0x1C by vv
class IncreaseCounter1CByValue(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x3B

    value = cty.byte_prop(1)


# 3C oo Increase Counter 0x1D by value, offset by oo. Details unknown
class IncreaseCounter1DByValue(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x3C

    value = cty.byte_prop(1)


# 3D tt Load sprite at target tt (00 caster, 01 caster 2, 02 caster 3, 03 target 1 etc)
class LoadSpriteAtTarget(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x3D

    target = cty.byte_prop(1)

    def __init__(self, *args,
                 target: int = None,
                 **kwargs):
        AnimationCommand.__init__(self,*args, **kwargs)
        self._set_properties(
            ("target", target),
        )


# 3E tt Load sprite at target tt (00 caster, 01 caster 2, 02 caster 3, 03 target 1 etc) (Differences Unknown)
class LoadSpriteAtTarget3E(LoadSpriteAtTarget):
    CMD_ID = 0x3E


# 3F tt Load sprite at target tt (00 caster, 01 caster 2, 02 caster 3, 03 target 1 etc) (Differences Unknown)
class LoadSpriteAtTarget3F(LoadSpriteAtTarget):
    CMD_ID = 0x3F


# 40 tt Load sprite at target tt (00 caster, 01 caster 2, 02 caster 3, 03 target 1 etc) (Differences Unknown)
class LoadSpriteAtTarget40(LoadSpriteAtTarget):
    CMD_ID = 0x40


# 41 c1 c2 Copy Counter c1 to Counter c2
class CopyCounterToCounter(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x41

    source = cty.byte_prop(1)
    destination = cty.byte_prop(2)


# 42 cc Copy Counter 0x1c to Counter cc
class CopyCounter1CToCounter(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x42

    destination = cty.byte_prop(1)


# 43 tt xx yy Store Coordinates of target tt, plus or minus xx and yy.
class StoreTargetCoordinatesWithOffset(AnimationCommand):
    SIZE = 4
    CMD_ID = 0x43

    target = cty.byte_prop(1)
    x_offset = cty.byte_prop(2)
    y_offset = cty.byte_prop(3)

    def __init__(self, *args,
                 target: int = None,
                 x_offset: int = None,
                 y_offset: int = None,
                 **kwargs):
        AnimationCommand.__init__(self,*args, **kwargs)
        self._set_properties(
            ("target", target),
            ("x_offset", x_offset),
            ("y_offset", y_offset)
        )


# 44 Store Coordinates of Current Object
class StoreCurrentObjectCoordinates(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x44


# 45 tt Load sprite at target tt (00 caster, 01 caster 2, 02 caster 3, 03 target 1 etc) (Differences Unknown)
class LoadSpriteAtTarget45(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x45

    target = cty.byte_prop(1)


# 46 tt Load sprite at target tt (00 caster, 01 caster 2, 02 caster 3, 03 target 1 etc) (Differences Unknown)
class LoadSpriteAtTarget46(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x46

    target = cty.byte_prop(1)


# 47 tt Store Target tt to RAM at $7E:A4EC
class StoreTargetTo7E4AEC(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x47

    target = cty.byte_prop(1)


# 48 tt Store Target tt to RAM at $7E:A4ED
class StoreTargetTo7E4AED(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x48

    target = cty.byte_prop(1)


# 49 cc mv Add or Subtract value mv (max 0x7F) to/from counter cc. mv 0x80 - Subtract.
class AddSubFromCounter(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x49

    counter = cty.byte_prop(1)
    # is_subtraction = cty.byte_prop(2, 0x80)
    value = cty.byte_prop(2, 0xFF)

    def __init__(self, *args,
                 counter: int = None,
                 # is_subtraction: bool = None,
                 value: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("counter", counter),
            # ("is_subtraction", is_subtraction),
            ("value", value)
        )


# 4A Swap Counters 0x1C and 0x1D
class SwapCounters1C1D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x4A


# 4B End Tech - Same as 01
class EndTech4B(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x4B


# 4C End Tech - Same as 01
class EndTech4C(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x4C


# 4D Swap Counters 0x1C and 0x1D
class SwapCounters1C1D4D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x4D


# 4E Swap Counters 0x1C and 0x1E - X Coordinate
class SwapCounters1C1E(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x4E


# 4F Swap Counters 0x1C and 0x1F - Y Coordinate
class SwapCounters1C1F(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x4F


# 50 Show Damage
class ShowDamage(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x50


# 51 Show Damage (Differences are Unknown)
class ShowDamage51(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x51


# 52 Show Damage (Differences are Unknown)
class ShowDamage52(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x52


# 53 Show Damage (Differences are Unknown)
class ShowDamage53(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x53


# 54 Show Damage (Differences are Unknown)
class ShowDamage54(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x54


# 55 Show Damage (Differences are Unknown)
class ShowDamage55(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x55


# 56 End Tech - Same as 01
class EndTech56(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x56


# 57 End Tech - Same as 01
class EndTech57(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x57


# 58 End Tech - Same as 01
class EndTech58(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x58


# 59 End Tech - Same as 01
class EndTech59(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x59


# 5A End Tech - Same as 01
class EndTech5A(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x5A


# 5B End Tech - Same as 01
class EndTech5B(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x5B


# 5C End Tech - Same as 01
class EndTech5C(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x5C


# 5D Draw target or caster object (differences between this and 2a are unknown)
class ShowCasterOrTarget5D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x5D


# 5E Hide target or caster object (differences between this and 29 are unknown)
class HideCasterOrTarget5E(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x5E


# 5F nn Empty Command - Does nothing
class DoNothing(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x5F


# 60 pp switch to pallette pp
class SwitchToPalette(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x60

    palette = cty.byte_prop(1)

    def __init__(self, *args, palette: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("palette", palette)
        )


# 61 xx yy zz Unknown
class Unknown61(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x61


# 62 xx yy zz Unknown (Variant of 61)
class Unknown62(Unknown61):
    CMD_ID = 0x62


# 63 xx yy zz Unknown (Variant of 61)
class Unknown63(Unknown61):
    CMD_ID = 0x63


# 64 xx yy zz Unknown (Variant of 61)
class Unknown64(Unknown61):
    CMD_ID = 0x64


# 65 Turn off 61
class DisableUnknown61(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x65


# 66 Turn off 62
class DisableUnknown62(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x66


# 67 Turn off 63
class DisableUnknown63(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x67


# 68 Turn off 64
class DisableUnknown64(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x68


# 69 pp Set Object Palette pp. Palettes start at 0x114D90, 0x18 bytes each
class SetObjectPalette(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x69

    palette = cty.byte_prop(1)

    def __init__(self, *args, palette: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("palette", palette)
        )


# 6A Reset Object Palette to normal
class ResetPalette(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x6A


# 6B xx Unknown
class Unknown6B(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x6B


# 6C pp dd Flash Object Palette with palette pp, delay of dd. Same palettes as 69
class FlashObjectPaletteWithColor(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x6C

    color = cty.byte_prop(1)
    delay = cty.byte_prop(2)

    def __init__(self, *args,
                 color: int = None,
                 delay: int = None,
                 **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("color", color),
            ("delay", delay)
        )


# 6D Unknown
class Unknown6D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x6D


# 6E Draw All Effect Objects
class DrawAllEffects(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x6E


# 6F Hide All Effect Objects
class HideAllEffects(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x6F


# 70 Draw Effect Object
class DrawEffect(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x70


# 71 Hide Effect Object
class HideEffect(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x71


# 72 xx Set Object Facing. 00 North, 01 South, 02 West, 03 East, others unknown
class SetObjectFacing(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x72

    facing = cty.byte_prop(1)

    def __init__(self, *args, facing: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("facing", facing)
        )


class EnumSpritePriority(enum.IntEnum):
    IN_FRONT = 3


# 73 xx Set Priority, 00 in front of sprite, 02 behind sprite, 03 in front of sprite, 04 behind sprite, others unknown.
class SetPriority(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x73

    priority = cty.byte_prop(1)

    def __init__(self, *args, priority: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("priority", priority)
        )


# 74 xx Set Priority (Differences from 73 unknown)
class SetPriority74(SetPriority):
    CMD_ID = 0x74


# 75 oo Set Angle, Copy from Object oo.
class SetAngleFromObject(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x75

    angle = cty.byte_prop(1)


# 76 t1 t2 Set Angle, Target t1 as source position, Target t2 as object to face.
class SetAngleBetweenTargets(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x76

    source_target = cty.byte_prop(1)
    destination_target = cty.byte_prop(2)


# 77 aa Set Angle, add aa to current Angle
class AddToCurrentAngle(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x77

    add_amount = cty.byte_prop(1)

    def __init__(self, *args, add_amount: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("add_amount", add_amount)
        )

# 78 ss Play Sound ss
class PlaySound(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x78

    sound = cty.byte_prop(1)

    def __init__(self, *args, sound: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("sound", sound)
        )


# 79 ss Play Sound ss
class PlaySound79(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x79

    sound = cty.byte_prop(1)

    def __init__(self, *args, sound: int = None, unknown: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("sound", sound),
        )


# 7A ss yy Play Sound ss
class PlaySound7A(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x7A

    sound = cty.byte_prop(1)
    unknown = cty.byte_prop(2)

    def __init__(self, *args, sound: int = None, unknown: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("sound", sound),
            ("unknown", unknown)
        )


# 7B ss yy Play Sound ss
class PlaySound7B(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x7B

    sound = cty.byte_prop(1)

    def __init__(self, *args, sound: int = None, unknown: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("sound", sound),
            ("unknown", unknown)
        )


# 7C Play Regular/Ranged weapon sound
class PlayRegularWeaponSound(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x7C


# 7D Play Critical/Melee weapon sound
class PlayCriticalWeaponSound(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x7D


# 7E End Tech - Same as 01
class EndTech7E(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x7E


# 7F End Tech - Same as 01
class EndTech7F(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x7F


# 80 ul vv Flash Screen Color (Variable length command) ul - Unknown 0xF0, length - 1 0x0F, vv - variable length data, details unknown.
class FlashScreenColor(AnimationCommand):
    SIZE = None
    CMD_ID = 0x80

    length = cty.byte_prop(1, 0x0F)


# 81 tt Store Target tt to RAM at $7E:A4E8
class StoreTargetTo7E4AE8(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x81

    target = cty.byte_prop(1)


# 82 tt Store Target tt to RAM at $7E:A4E9
class StoreTargetTo7E4AE9(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x82

    target = cty.byte_prop(1)



# 83 tt Store Target tt to RAM at $7E:A4EA
class StoreTargetTo7E4AEA(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x83

    target = cty.byte_prop(1)


# 84 tt Store Target tt to RAM at $7E:A4EB
class StoreTargetTo7E4AEB(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x84

    target = cty.byte_prop(1)


# 85 aa Set Angle Absolute aa - angle
class SetAngle(AnimationCommand):
    SIZE = 2
    CMD_ID = 0x85

    angle = cty.byte_prop(1)

    def __init__(self, *args, angle: int = None, **kwargs):
        AnimationCommand.__init__(self,*args, **kwargs)
        self._set_properties(
            ("angle", angle)
        )


# 86 End Tech - Same as 01
class EndTech86(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x86


# 87 End Tech - Same as 01
class EndTech87(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x87


# 88 End Tech - Same as 01
class EndTech88(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x88


# 89 End Tech - Same as 01
class EndTech89(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x89


# 8A End Tech - Same as 01
class EndTech8A(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x8A


# 8B End Tech - Same as 01
class EndTech8B(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x8B


# 8C End Tech - Same as 01
class EndTech8C(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x8C


# 8D End Tech - Same as 01
class EndTech8D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x8D


# 8E End Tech - Same as 01
class EndTech8E(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x8E


# 8F End Tech - Same as 01
class EndTech8F(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x8F


# 90 End Tech - Same as 01
class EndTech90(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x90


# 91 End Tech - Same as 01
class EndTech91(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x91


# 92 End Tech - Same as 01
class EndTech92(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x92


# 93 End Tech - Same as 01
class EndTech93(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x93


# 94 End Tech - Same as 01
class EndTech94(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x94


# 95 End Tech - Same as 01
class EndTech95(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x95


# 96 End Tech - Same as 01
class EndTech96(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x96


# 97 End Tech - Same as 01
class EndTech97(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x97


# 98 tt xx Move To (0x98 variants) tt - Target
class MoveToTarget(AnimationCommand):
    SIZE = 3
    CMD_ID = 0x98

    target = cty.byte_prop(1)


# 99 Move To Stored Coordinates (0x98 variants)
class MoveToStoredCoordinates(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x99


# 9A tt xx Move To (0x98 variants) tt - Target
class MoveToTarget9A(MoveToTarget):
    SIZE = 3
    CMD_ID = 0x9A


# 9B Move To Stored Coordinates (0x98 variants)
class MoveToTarget9B(MoveToTarget):
    SIZE = 3
    CMD_ID = 0x9B


# 9C tt xx Move To (0x98 variants) tt - Target
class MoveToTarget9C(MoveToTarget):
    SIZE = 3
    CMD_ID = 0x9C


# 9D Move To Stored Coordinates (0x98 variants)
class MoveToStoredCoordinates9D(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x9D


# 9E End Tech - Same as 01
class EndTech9E(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x9E


# 9F End Tech - Same as 01
class EndTech9F(AnimationCommand):
    SIZE = 1
    CMD_ID = 0x9F


# A0 End Tech - Same as 01
class EndTechA0(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA0


# A1 End Tech - Same as 01
class EndTechA1(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA1


# A2 Move Forward Fixed distance.
class MoveForwardFixedDistance(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA2


# A3 End Tech - Same as 01
class EndTechA3(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA3


# A4 ll tt Draw Copies ll - length (Distance between copies?) tt - Transparency)
class DrawSpacedCopies(AnimationCommand):
    SIZE = 3
    CMD_ID = 0xA4

    spacing = cty.byte_prop(1)
    transparency = cty.byte_prop(2)


# A5 Reset Copies
class ResetCopies(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA5


# A6 End Tech - Same as 01
class EndTechA6(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA6


# A7 End Tech - Same as 01
class EndTechA7(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xA7


# A8 dd Move Forward dd - Distance
class MoveForward(AnimationCommand):
    SIZE = 2
    CMD_ID = 0xA8

    distance = cty.byte_prop(1)

    def __init__(self, *args, distance: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("distance", distance)
        )


# A9 dd Move Forward dd - Distance
class MoveForwardA9(MoveForward):
    SIZE = 2
    CMD_ID = 0xA9


# AA End Tech - Same as 01
class EndTechAA(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xAA


# AB End Tech - Same as 01
class EndTechAB(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xAB


# AC End Tech - Same as 01
class EndTechAC(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xAC


# AD End Tech - Same as 01
class EndTechAD(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xAD


# AE End Tech - Same as 01
class EndTechAE(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xAE


# AF End Tech - Same as 01
class EndTechAF(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xAF


# B0 End Tech - Same as 01
class EndTechB0(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB0


# B1 End Tech - Same as 01
class EndTechB1(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB1


# B2 End Tech - Same as 01
class EndTechB2(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB2


# B3 End Tech - Same as 01
class EndTechB3(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB3


# B4 End Tech - Same as 01
class EndTechB4(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB4


# B5 End Tech - Same as 01
class EndTechB5(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB5


# B6 End Tech - Same as 01
class EndTechB6(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB6


# B7 End Tech - Same as 01
class EndTechB7(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB7


# B8 End Tech - Same as 01
class EndTechB8(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB8


# B9 End Tech - Same as 01
class EndTechB9(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xB9


# BA End Tech - Same as 01
class EndTechBA(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xBA


# BB End Tech - Same as 01
class EndTechBB(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xBB


# BC End Tech - Same as 01
class EndTechBC(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xBC


# BD End Tech - Same as 01
class EndTechBD(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xBD


# BE End Tech - Same as 01
class EndTechBE(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xBE


# BF End Tech - Same as 01
class EndTechBF(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xBF


# C0 ww xx yy zz Circular Sprite Movement
class CircularSpriteMovement(AnimationCommand):
    SIZE = 5
    CMD_ID = 0xC0


# C1 ww xx yy Circular Sprite Movement
class CircularSpriteMovementC1(AnimationCommand):
    SIZE = 4
    CMD_ID = 0xC1


# C2 ww xx yy zz Circular Sprite Movement
class CircularSpriteMovementC2(AnimationCommand):
    SIZE = 5
    CMD_ID = 0xC2


# C3 ww xx yy Circular Sprite Movement
class CircularSpriteMovementC3(AnimationCommand):
    SIZE = 4
    CMD_ID = 0xC3


# C4 xx yy
class UnknownC4(AnimationCommand):
    SIZE = 3
    CMD_ID = 0xC4


# C5 End Tech - Same as 01
class EndTechC5(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xC5


# C6 End Tech - Same as 01
class EndTechC6(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xC6


# C7 End Tech - Same as 01
class EndTechC7(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xC7


# C8 End Tech - Same as 01
class EndTechC8(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xC8


# C9 End Tech - Same as 01
class EndTechC9(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xC9


# CA End Tech - Same as 01
class EndTechCA(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xCA


# CB End Tech - Same as 01
class EndTechCB(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xCB


# CC End Tech - Same as 01
class EndTechCC(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xCC


# CD End Tech - Same as 01
class EndTechCD(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xCD


# CE End Tech - Same as 01
class EndTechCE(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xCE


# CF End Tech - Same as 01
class EndTechCF(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xCF


# D0 Draw Shadow
class DrawShadow(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xD0


# D1 Hide Shadow
class HideShadow(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xD1


# D2 xx Unknown
class UnknownD2(AnimationCommand):
    SIZE = 2
    CMD_ID = 0xD2

# D3 Unknown
class UnknownD3(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xD3


# D4 Unknown
class UnknownD4(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xD4


# D5 Unknown
class UnknownD5(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xD5


# D6 Unknown
class UnknownD6(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xD6


# D7 xx yy
class UnknownD7(AnimationCommand):
    SIZE = 3
    CMD_ID = 0xD7


# D8 xx ss nn Shake Sprite nn times at speed ss.  xx is undocumented
class ShakeSprite(AnimationCommand):
    SIZE = 4
    CMD_ID = 0xD8

    speed = cty.byte_prop(2)
    num_times = cty.byte_prop(3)


# D9 xx Load Graphics Packet 1.
class LoadGraphicsPacket1(AnimationCommand):
    SIZE = 2
    CMD_ID = 0xD9

    arg = cty.byte_prop(1)

    def __init__(self, *args, arg: int = None, **kwargs):
        AnimationCommand.__init__(self, *args, **kwargs)
        self._set_properties(
            ("arg", arg)
        )


# DA xx Unknown  - wrong, only 1 bytw
class UnknownDA(AnimationCommand):
    SIZE = 1
    CMD_ID = 0xDA


_this_module = sys.modules[__name__]
def _predicate(obj: typing.Any) -> typing.TypeGuard[typing.Type[AnimationCommand]]:
    if not inspect.isclass(obj):
        return False
    if not issubclass(obj, AnimationCommand) or type(obj) == AnimationCommand:
        return False
    if obj.CMD_ID is None or not 0 <= obj.CMD_ID <= 0xDE:
        return False

    return True

_anim_commands = inspect.getmembers(_this_module, _predicate)
_anim_opcode_dict: dict[int, typing.Type[AnimationCommand]] = {}
for name, cmd_class in _anim_commands:
    opcode = cmd_class.CMD_ID
    if opcode in _anim_opcode_dict:
        raise KeyError(f"{opcode:02X}, {cmd_class.__name__}")
    _anim_opcode_dict[opcode] = cmd_class


def get_command(buffer: typing.ByteString, pos: int) -> AnimationCommand:
    cmd_id = buffer[pos]
    cmd_type = _anim_opcode_dict[cmd_id]

    if cmd_type.SIZE is None:
        if cmd_type != FlashScreenColor:
            raise TypeError
        length = (buffer[pos+1] & 0x0F) + 1
        return FlashScreenColor(buffer[pos:pos+length])

    return cmd_type(buffer[pos: pos + cmd_type.SIZE])

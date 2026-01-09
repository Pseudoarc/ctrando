"""Module for handling animation scripts"""
import copy
import enum
import typing
from collections.abc import Sequence

from ctrando.attacks import animationcommands as ac
from ctrando.attacks.animationcommands import EnumTarget
from ctrando.common import byteops, cttypes as cty, ctrom, ctenums
from ctrando.attacks import pctech


_T = typing.TypeVar("_T", bound=ac.AnimationCommand)
ObjectScript = list[_T]


class NewScriptID(enum.IntEnum):
    ARROW_HAIL = 0x80
    HASTE_ALL = 0x81
    PROTECT_ALL = 0x82
    MAGUS_LUCCA_ANTI2 = 0x83
    MAGUS_LUCCA_ANTI3 = 0x84
    MAGUS_MARLE_ANTI2 = 0x85
    MAGUS_CRONO_ICESWORD2 = 0x86
    RERAISE = 0x87
    GALE_SLASH = 0x88
    BLURP = 0x89
    IRON_ORB = 0x8A
    BURST_BALL = 0x8B
    DOUBLE_TAP = 0x8C


def extract_object_script_from_buffer(
        buf: typing.ByteString, pos: int = 0
):
    script: ObjectScript = []
    cur_pos = pos
    while True:
        cmd = ac.get_command(buf, cur_pos)
        # print(cmd)
        script.append(cmd)
        cur_pos += len(cmd)

        if cmd.CMD_ID == 0:
            break

    return script


def extract_object_script(ct_rom: ctrom.CTRom, start_addr: int) -> ObjectScript:
    return extract_object_script_from_buffer(ct_rom.getbuffer(), start_addr)


def object_script_to_bytes(script: ObjectScript) -> bytes:
    return b''.join(x for x in script)


def print_object_script(script: ObjectScript):
    for x in script:
        print(x)


class AnimationScriptHeader(cty.BinaryData):
    SIZE = 2
    ROM_RW = None
    MAX_CASTERS = 3
    MAX_TARGETS = 5
    MAX_EFFECTS = 8

    _casters = cty.byte_prop(0, 0xE0)
    _targets = cty.byte_prop(0, 0x1F)
    _effects = cty.byte_prop(1, 0xFF)

    @property
    def num_casters(self) -> int:
        return bin(self._casters).count("1")

    @num_casters.setter
    def num_casters(self, val):
        if not 1 <= val <= self.MAX_CASTERS:
            raise ValueError

        self._casters = int(("1"*val).ljust(self.MAX_CASTERS, "0"), 2)

    @property
    def num_targets(self) -> int:
        return bin(self._targets).count("1")

    @num_targets.setter
    def num_targets(self, val):
        if not 0 <= val <= self.MAX_TARGETS:
            raise ValueError()

        self._targets = int(("1" * val).ljust(self.MAX_TARGETS, "0"), 2)

    @property
    def num_effects(self) -> int:
        return bin(self._effects).count("1")

    @num_effects.setter
    def num_effects(self, val):
        if not 0 <= val <= self.MAX_EFFECTS:
            raise ValueError

        self._effects = int(("1" * val).ljust(self.MAX_EFFECTS, "0"), 2)

    @property
    def num_objects(self) -> int:
        return self.num_effects + self.num_targets + self.num_casters


class BankOffsetFinder:

    def __init__(
            self,
            bank_ptr_table_addr: int,
            offset_ptr_table_addr: int
    ):
        self.bank_ptr_table_addr =  bank_ptr_table_addr
        self.offset_ptr_table_addr = offset_ptr_table_addr

    def get_bank_table_start(self, ct_rom: ctrom.CTRom):
        rom_start = int.from_bytes(
            ct_rom.getbuffer()[self.bank_ptr_table_addr: self.bank_ptr_table_addr+3],
            "little"
        )
        return byteops.to_file_ptr(rom_start)

    def get_offset_table_start(self, ct_rom: ctrom.CTRom):
        rom_start = int.from_bytes(
            ct_rom.getbuffer()[self.offset_ptr_table_addr: self.offset_ptr_table_addr + 3],
            "little"
        )
        return byteops.to_file_ptr(rom_start)

    def get_bank(self, ct_rom: ctrom.CTRom, index: int) -> int:
        bank_st = self.get_bank_table_start(ct_rom)
        bank_st += index

        return ct_rom.getbuffer()[bank_st]

    def get_offset(self, ct_rom: ctrom.CTRom, index: int) -> int:
        offset_st = self.get_offset_table_start(ct_rom)
        offset_st += 2*index

        return int.from_bytes(
            ct_rom.getbuffer()[offset_st: offset_st+2], "little"
        )

    def get_data_start(self, ct_rom: ctrom.CTRom, index: int) -> int:
        bank = self.get_bank(ct_rom, index)
        offset = self.get_offset(ct_rom, index)

        rom_addr = bank * 0x10000 + offset
        file_addr = byteops.to_file_ptr(rom_addr)

        return file_addr


class SingleAnimationScript:
    def __init__(
            self,
            caster_objects: Sequence[ObjectScript],
            target_objects: Sequence[ObjectScript],
            effect_objects: Sequence[ObjectScript]
    ):

        # This is just checking for coherent data in the number of objects
        header = AnimationScriptHeader()
        header.num_casters = len(caster_objects)
        header.num_targets = len(target_objects)
        header.num_effects = len(effect_objects)

        self.caster_objects: list[ObjectScript] = list(caster_objects)
        self.target_objects: list[ObjectScript] = list(target_objects)
        self.effect_objects: list[ObjectScript] = list(effect_objects)

    def get_object_list(self) -> list[ObjectScript]:
        return self.caster_objects + self.target_objects + self.effect_objects


# After Mauron Patch:
# C14615  A8             TAY
# C14616  0A             ASL
# C14617  AA             TAX
# C14618  BF 65 F3 C5    LDA $C5F365,X  <-- offset
# C1461C  85 40          STA $40
# C1461E  BB             TYX
# C1461F  BF 65 F5 C5    LDA $C5F565,X  <-- bank
# C14623  85 42          STA $42


class AnimationScript:
    FINDER: typing.ClassVar[BankOffsetFinder] = \
        BankOffsetFinder(0x014620, 0x014619)

    def __init__(
            self,
            main_script: SingleAnimationScript,
            miss_script: SingleAnimationScript,
    ):

        self.main_script = copy.deepcopy(main_script)
        self.miss_script = copy.deepcopy(miss_script)

    @classmethod
    def read_from_ctrom_addr(cls, ct_rom: ctrom.CTRom, data_start: int):
        ct_rom.seek(data_start)
        main_header = AnimationScriptHeader(ct_rom.read(2))
        miss_header = AnimationScriptHeader(ct_rom.read(2))
        num_objs = main_header.num_objects + miss_header.num_objects
        ptrs = [
            int.from_bytes(ct_rom.read(2), "little")
            for _ in range(num_objs)
        ]

        main_casters: list[ObjectScript] = []
        main_targets: list[ObjectScript] = []
        main_effects: list[ObjectScript] = []
        miss_casters: list[ObjectScript] = []
        miss_targets: list[ObjectScript] = []
        miss_effects: list[ObjectScript] = []

        objects = (main_casters, main_targets, main_effects,
                   miss_casters, miss_targets, miss_effects)
        counts = (main_header.num_casters, main_header.num_targets, main_header.num_effects,
                  miss_header.num_casters, miss_header.num_targets, miss_header.num_effects)

        bank = data_start & 0xFF0000
        for object_group, count in zip(objects, counts):
            for _ in range(count):
                ptr = ptrs.pop(0)
                addr = bank + ptr
                script = extract_object_script(ct_rom, addr)
                object_group.append(script)

        main_script = SingleAnimationScript(main_casters, main_targets, main_effects)
        miss_script = SingleAnimationScript(miss_casters, miss_targets, miss_effects)

        return AnimationScript(main_script, miss_script)

    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom, index: int) -> typing.Self:
        """Read an AnimationScript from a CTRom"""
        data_start = cls.FINDER.get_data_start(ct_rom, index)
        return cls.read_from_ctrom_addr(ct_rom, data_start)


    def write_to_ctrom(self, ct_rom: ctrom.CTRom, index: int):
        main_header = AnimationScriptHeader()
        main_header.num_casters = len(self.main_script.caster_objects)
        main_header.num_targets = len(self.main_script.target_objects)
        main_header.num_effects = len(self.main_script.effect_objects)

        miss_header = AnimationScriptHeader()
        miss_header.num_casters = len(self.miss_script.caster_objects)
        miss_header.num_targets = len(self.miss_script.target_objects)
        miss_header.num_effects = len(self.miss_script.effect_objects)

        total_objects = (
            self.main_script.get_object_list() + self.miss_script.get_object_list()
        )

        total_objects_b = [
            object_script_to_bytes(obj) for obj in total_objects
        ]
        total_object_size = sum(len(x) for x in total_objects_b)

        payload_size = (
            4 +                         # 2x Headers
            2*len(total_objects) +      # pointers
            total_object_size           # Object scripts
        )

        new_addr = ct_rom.space_manager.get_free_addr(
            payload_size, 0x410000
        )

        new_rom_addr = byteops.to_rom_ptr(new_addr)
        rom_bank = (new_rom_addr & 0xFF0000) >> 16
        offset = new_rom_addr & 0x00FFFF

        ptrs: list[int] = [offset + 4 + 2*len(total_objects)]  # After headers, ptrs
        for obj_b in total_objects_b[:-1]:
            ptrs.append(ptrs[-1] + len(obj_b))
        ptr_b = b''.join(int.to_bytes(ptr, 2, "little") for ptr in ptrs)
        object_b = b''.join(x for x in total_objects_b)

        payload = bytes(
            main_header + miss_header + ptr_b + object_b
        )
        ct_rom.seek(new_addr)
        ct_rom.write(payload, ctrom.freespace.FSWriteType.MARK_USED)
        bank_table_st = self.FINDER.get_bank_table_start(ct_rom)
        ct_rom.seek(bank_table_st + index)
        ct_rom.write(rom_bank.to_bytes(1))

        offset_table_st = self.FINDER.get_offset_table_start(ct_rom)
        ct_rom.seek(offset_table_st + 2*index)
        ct_rom.write(offset.to_bytes(2, "little"))


def read_enemy_tech_script_from_ctrom(ct_rom: ctrom.CTRom, index: int) -> AnimationScript:
    """
    Read an enemy script.  May need to change if a Mauron-style patch is applied.
    """
    ptr_table_st = 0x0D61F0
    ct_rom.seek(ptr_table_st + 2*index)
    ptr = int.from_bytes(ct_rom.read(2), "little")

    script_addr = 0x0D0000 + ptr
    return AnimationScript.read_from_ctrom_addr(ct_rom, script_addr)


def make_arrow_rain_script(ct_rom: ctrom.CTRom) -> AnimationScript:
    basic_script = AnimationScript.read_from_ctrom_addr(ct_rom, 0x0E041E)
    caster0 = [
        ac.SetObjectFacing(facing=0),
        ac.PerformSuperCommand(super_command=0x1D),
        # ac.Unknown27(),
        ac.Pause(duration=0x10),
        ac.PlayAnimationLoop(animation_id=0x33),
        ac.StoreCurrentObjectCoordinates(),
        ac.AddSubFromCounter(counter=0x1F, value=0xE0),
        ac.IncrementCounter1C(),
        ac.Pause(duration=0x28),
        ac.PlayAnimationOnce(animation_id=0xE),
        ac.Pause(duration=0x28),
        ac.WaitForCounter1CValue(value=0x2),
        ac.SetCounterToValue(counter=0, value=0),
        ac.PerformSuperCommand(super_command=0x1E),
        ac.PlayAnimationLoop(animation_id=0x1A),
        ac.Pause(duration=0x18),
        ac.WaitForCounter1CValue(value=3),
        ac.PlayAnimationFirstFrame(animation_id=0x3),
        ac.Unknown2E(),
        ac.EndTech(),
        ac.ReturnCommand(),
    ]

    target0 = [
        ac.IncrementCounter(counter=0),
        ac.WaitForCounter1DValue(value=7),
        ac.IncrementCounter1C(),
        ac.Pause(duration=0x10),
        ac.FlashObjectPaletteWithColor(color=0, delay=4),
        # ac.PlayAnimationFirstFrame(animation_id=3),
        ac.WaitForCounter1DValue(value=14),
        # ac.Pause(duration=0x15),
        ac.Pause(duration=0x10),
        ac.PerformSuperCommand(super_command=0),
        ac.IncrementCounter1C(),
        ac.ReturnCommand()
    ]
    target1 = [
        ac.WaitForCounter1DValue(value=7),
        ac.Pause(duration=0x10),
        ac.FlashObjectPaletteWithColor(color=0, delay=4),
        # ac.PlayAnimationFirstFrame(animation_id=3),
        ac.WaitForCounter1DValue(value=14),
        # ac.Pause(duration=0x15),
        ac.Pause(duration=0x10),
        ac.PerformSuperCommand(super_command=5),
        ac.ReturnCommand()
    ]

    basic_script.main_script.caster_objects[0] = caster0
    basic_script.main_script.target_objects = [target0, target1]

    def make_effect(
            angle_offset: int,
            init_delay: int,
            final_x1,           # X-coord for falling down
            final_y1,           # Y-coord to fall down to
            final_x2: int,
            final_y2: int,
    ) -> ObjectScript:

        cmd = ac.LoadGraphicsPacket1()
        cmd.arg = 0

        effect = [
            ac.SetObjectFacing(facing=0),
            ac.SwitchToPalette(palette=0),
            ac.SetPriority(priority=ac.EnumSpritePriority.IN_FRONT),
            ac.WaitForCounter1CValue(value=1),
            ac.Pause(duration=init_delay),
            ac.TeleportToStoredCoordinates(),
            ac.SetAngle(angle=0xC0-angle_offset),
            ac.DrawEffect(),
            ac.PlayAnimationLoop(animation_id=0),
            # ac.PlayAnimationFirstFrame(animation_id=1),
            # ac.Pause(duration=0x20),
            ac.SetSpeedFastestShorter(),
            # ac.PlayAnimationLoop(animation_id=0),
            ac.PlaySound(sound=0x43),
            ac.MoveForward(distance=0xFF),
            ac.HideEffect(),
            ac.TeleportToStoredCoordinates(),
            ac.SetAngle(angle=0xC0 + angle_offset),
            # ac.Pause(duration=0x5),
            ac.DrawEffect(),
            ac.PlaySound(sound=0x43),
            ac.MoveForward(distance=0xFF),
            ac.HideEffect(),
            ac.SetSpeedFastest(),
            ac.SetAngle(angle=0x40),
            ac.TeleportToCoordinates(x_coord=final_x1, y_coord=0),
            ac.DrawEffect(),
            ac.IncrementCounter1D(),
            ac.SlideSpriteToCoordinates(x_coord=final_x1, y_coord=final_y1),
            ac.TeleportToCoordinates(x_coord=final_x1, y_coord=final_y1),
            ac.PlaySound(sound=0x5F),

            # ac.SwitchToPalette(palette=1),
            # ac.PlayAnimationOnce(animation_id=1),
            ac.HideEffect(),
            ac.TeleportToCoordinates(x_coord=final_x2, y_coord=0),
            ac.DrawEffect(),
            ac.SlideSpriteToCoordinates(x_coord=final_x2, y_coord=final_y2),
            ac.PlaySound(sound=0x5F),
            # ac.PlayAnimationOnce(animation_id=1),
            ###
            ac.IncrementCounter1D(),
            ac.Pause(duration=0xA),
            ac.HideEffect(),
            ac.ReturnCommand()
        ]
        return effect



    basic_script.main_script.effect_objects[0] = make_effect(
        angle_offset=5, init_delay=0, final_x1=0x68, final_y1=0x90, final_x2=0x98, final_y2=0x80
    )
    basic_script.main_script.effect_objects.append(make_effect(
        angle_offset=-3, init_delay=3, final_x1=0x88, final_y1=0x78, final_x2=0x80, final_y2=0xA0
    ))
    basic_script.main_script.effect_objects.append(make_effect(
        angle_offset=-1, init_delay=2, final_x1=0xD0, final_y1=0x78, final_x2=0x78, final_y2=0x68
    ))
    basic_script.main_script.effect_objects.append(make_effect(
        angle_offset=2, init_delay=0, final_x1=0x60, final_y1=0x68, final_x2=0x50, final_y2=0x88
    ))
    basic_script.main_script.effect_objects.append(make_effect(
        angle_offset=-4, init_delay=1, final_x1=0x38, final_y1=0x88, final_x2=0x80, final_y2=0x68
    ))
    basic_script.main_script.effect_objects.append(make_effect(
        angle_offset=-6, init_delay=2, final_x1=0x90, final_y1=0x98, final_x2=0xA8, final_y2=0x78
    ))
    basic_script.main_script.effect_objects.append(make_effect(
        angle_offset=2, init_delay=2, final_x1=0xA8, final_y1=0x78, final_x2=0x50, final_y2=0x70
    ))
    return basic_script


def make_single_lucca_prot_all_script(ct_rom: ctrom.CTRom):

    prot_scr = AnimationScript.read_from_ctrom(ct_rom, ctenums.TechID.PROTECT)
    cast_0 = [
        ac.SetObjectFacing(facing=0x01),
        ac.PlayAnimationOnce(animation_id=0x10),
        ac.IncrementCounter1D(),
        # ac.WaitForCounter1DValue(value=3),
        ac.WaitForCounter1CValue(value=0),
        ac.Unknown2E(),
        ac.EndTech(),
        ac.ReturnCommand()
    ]

    target_0 = [
        ac.IncrementCounter1C(),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.WaitForCounter1DValue(value=2),
        ac.PlayAnimationOnce(animation_id=0x24),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.Pause(duration=5),
        ac.IncrementCounter1D(),
        ac.ReturnIfTargetAbsent(target=1),
        ac.IncrementCounter1C(),
        ac.ReturnCommand()
    ]
    target_1 = [
        ac.IncrementCounter1C(),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.WaitForCounter1DValue(value=4),
        ac.PlayAnimationOnce(animation_id=0x24),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.Pause(duration=0x5),
        # ac.IncrementCounter1D(),
        ac.ReturnCommand()
    ]


    effect_0 = [
        ac.TeleportToTarget(target=0),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.Unknown61([0x61, 0x02, 0x00, 0x04]),
        ac.TeleportToTarget(target=0x0C),
        ac.PlayAnimationFirstFrame(animation_id=0x1B),
        ac.SetSpeedFastest(),
        ac.WaitForCounter1DValue(value=1),  # When caster has animated
        ac.PlaySound7A(sound=0xEA, unknown=0x0C),
        ac.PlayAnimationOnce(animation_id=1),
        ac.IncrementCounter1D(),
        ac.SetAngle(angle=0x20),
        ac.PlaySound7A(sound=0xF0, unknown=0xC),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.Pause(duration=1),
        ac.DecrementCounter1C(),
        ac.IncrementCounter1D(),
        ac.ReturnIfTargetAbsent(target=1),
        ac.TeleportToTarget(target=0x0E),
        ac.PlaySound7A(sound=0xEA, unknown=0x0E),
        ac.PlayAnimationOnce(animation_id=1),
        ac.WaitForCounter1DValue(value=5),
        ac.SetAngle(angle=0x20),
        ac.PlaySound7A(sound=0xF0, unknown=0xE),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.Pause(duration=1),
        ac.DecrementCounter1C(),
        ac.ReturnCommand()
    ]

    effect_1 = [
        ac.TeleportToTarget(target=0),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.TeleportToTarget(target=0x0C),
        ac.SetSpeedFastest(),
        ac.SetAngle(angle=0x60),
        ac.WaitForCounter1DValue(value=2),  # When caster has animated
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnIfTargetAbsent(target=1),
        ac.TeleportToTarget(target=0x0E),
        ac.WaitForCounter1DValue(value=5),
        ac.SetAngle(angle=0x60),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    effect_2 = [
        ac.TeleportToTarget(target=0),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.TeleportToTarget(target=0x0C),
        ac.SetSpeedFastest(),
        ac.SetAngle(angle=0xA0),
        ac.WaitForCounter1DValue(value=2),  # When caster has animated
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnIfTargetAbsent(target=1),
        ac.TeleportToTarget(target=0x0E),
        ac.WaitForCounter1DValue(value=5),
        ac.SetAngle(angle=0xA0),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    effect_3 = [
        ac.TeleportToTarget(target=0),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.TeleportToTarget(target=0x0C),
        ac.SetSpeedFastest(),
        ac.SetAngle(angle=0xE0),
        ac.WaitForCounter1DValue(value=2),  # When caster has animated
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnIfTargetAbsent(target=1),
        ac.TeleportToTarget(target=0x0E),
        ac.DrawEffect(),
        ac.WaitForCounter1DValue(value=5),
        ac.SetAngle(angle=0xE0),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    effect_4 = [
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.ReturnIfTargetAbsent(target=0),
        ac.PlayAnimationFirstFrame(animation_id=0x1B),
        ac.SetSpeedFastest(),
        ac.TeleportToTarget(target=0x0D),
        ac.WaitForCounter1DValue(value=4),
        ac.PlaySound7A(sound=0xEA, unknown=0x0D),
        ac.PlayAnimationOnce(animation_id=1),
        ac.IncrementCounter1D(),
        ac.SetAngle(angle=0x20),
        ac.PlaySound7A(sound=0xF0, unknown=0xD),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.Pause(duration=2),
        ac.DecrementCounter1C(),
        ac.ReturnCommand()
    ]

    effect_5 = [
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.ReturnIfTargetAbsent(target=0),
        ac.TeleportToTarget(target=0x0D),
        ac.SetSpeedFastest(),
        ac.WaitForCounter1DValue(value=5),
        ac.SetAngle(angle=0x60),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    effect_6 = [
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.ReturnIfTargetAbsent(target=0),
        ac.TeleportToTarget(target=0x0D),
        ac.SetSpeedFastest(),
        ac.WaitForCounter1DValue(value=5),
        ac.SetAngle(angle=0xA0),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    effect_7 = [
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=3),
        ac.ReturnIfTargetAbsent(target=0),
        ac.TeleportToTarget(target=0x0D),
        ac.SetSpeedFastest(),
        ac.WaitForCounter1DValue(value=5),
        ac.SetAngle(angle=0xE0),
        ac.PerformSuperCommand(super_command=0x25),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    obj = extract_object_script_from_buffer(
        bytearray.fromhex('06 03' +
                          '24 02'  # Wait for 1D to hit 2 (from shld_eff)
                          '03 24' +
                          '06 03' +
                          '20 05' +
                          '36' +  # Increment counter 1D (to 3)
                          '00')
    )
    prot_scr.main_script.caster_objects = [cast_0]
    prot_scr.main_script.target_objects = [target_0, target_1]
    prot_scr.main_script.effect_objects = [effect_0, effect_1, effect_2, effect_3,
                                           effect_4, effect_5, effect_6, effect_7]

    return prot_scr


def make_single_marle_haste_all_script(ct_rom: ctrom.CTRom) -> AnimationScript:

    haste_scr = AnimationScript.read_from_ctrom(ct_rom, 0xD)
    caster_0 = [
        ac.LoadSpriteAtTarget(target=3),
        ac.SetObjectFacing(facing=0x15),
        ac.PlayAnimationOnce(animation_id=0x10),
        ac.PlayAnimationLoop(animation_id=0x36),
        ac.IncrementCounter1D(),
        ac.WaitForCounter1DValue(value=5),
        # ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.Pause(duration=0x10),
        ac.Unknown2E(),
        ac.EndTech(),
        ac.ReturnCommand(),
    ]

    target_0 = [
        ac.WaitForCounter1DValue(value=2),
        ac.PlaySound7A(sound=0x87, unknown=3),
        ac.WaitForCounter1DValue(value=3),
        ac.IncrementCounter(counter=0x1B),
        ac.IncrementCounter1D(),
        ac.PlayAnimationLoop(animation_id=0x24),
        ac.WaitForCounterValue(counter=0x1B, value=0),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.Unknown2D(),
        ac.FlashScreenColor(bytes([0x80, 0x12, 0x29])),
        ac.IncrementCounter1D(),
        ac.ReturnCommand()
    ]

    target_1 = [
        ac.WaitForCounter1DValue(value=2),
        ac.PlaySound7A(sound=0x87, unknown=3),
        ac.WaitForCounter1DValue(value=4),
        ac.PlayAnimationLoop(animation_id=0x24),
        ac.WaitForCounterValue(counter=0x1B, value=0),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.ReturnCommand()
    ]

    clock_0 = [
        ac.TeleportToTarget(target=9),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=0),
        ac.SwitchToPalette(palette=0),
        ac.LoadGraphicsPacket1(arg=0x30),
        ac.WaitForCounter1DValue(value=1),
        ac.DrawEffect(),
        ac.PlaySound7A(sound=0x86, unknown=0),
        ac.PlayAnimationLoop(animation_id=0),
        ac.Pause(duration=0x0A),
        ac.SetSpeedMedium(),
        ac.SetAngle(angle=0xC0),
        ac.MoveForward(distance=0x0A),
        ac.SetSpeedFast(),
        ac.MoveForward(distance=0x32),
        ac.HideEffect(),
        ac.IncrementCounter1D(),
        # ac.WaitForCounter1DValue(value=2),
        ac.SetPriority(priority=3),
        ac.StoreTargetCoordinates(target=3),
        ac.SetCounterToValue(counter=0x1F, value=0x10),
        ac.TeleportToStoredCoordinates(),
        ac.IncrementCounter1C(),
        ac.WaitForCounter1CValue(value=3),
        ac.PlayAnimationLoop(animation_id=1),
        ac.SetSpeedFast(),
        ac.Pause(duration=0x28),
        ac.DrawEffect(),
        ac.SlideSpriteToTarget(target=0xC),
        ac.IncrementCounter1D(),
        ac.WaitForCounter1DValue(value=4),
        ac.WaitForCounterValue(counter=0x1B, value=0),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    clock_1 = [
        ac.WaitForCounter1CValue(value=1),
        ac.SetPriority(priority=3),
        ac.StoreTargetCoordinates(target=4),
        ac.SetCounterToValue(counter=0x1F, value=0x10),
        ac.TeleportToStoredCoordinates(),
        ac.IncrementCounter1C(),
        ac.ReturnIfTargetAbsent(target=0),
        ac.WaitForCounter1CValue(value=3),
        ac.PlayAnimationLoop(animation_id=1),
        ac.SetSpeedFast(),
        ac.Pause(duration=0x28),
        ac.DrawEffect(),
        ac.SlideSpriteToTarget(target=0xD),
        # ac.IncrementCounter1D(),
        ac.WaitForCounter1DValue(value=4),
        ac.WaitForCounterValue(counter=0x1B, value=0),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    clock_2 = [
        ac.WaitForCounter1CValue(value=2),
        ac.SetPriority(priority=3),
        ac.StoreTargetCoordinates(target=5),
        ac.SetCounterToValue(counter=0x1F, value=0x10),
        ac.TeleportToStoredCoordinates(),
        ac.IncrementCounter1C(),
        ac.ReturnIfTargetAbsent(target=1),
        ac.WaitForCounter1CValue(value=3),
        ac.PlayAnimationLoop(animation_id=1),
        ac.SetSpeedFast(),
        ac.Pause(duration=0x28),
        ac.DrawEffect(),
        ac.SlideSpriteToTarget(target=0xE),
        # ac.IncrementCounter1D(),
        ac.WaitForCounter1DValue(value=4),
        ac.WaitForCounterValue(counter=0x1B, value=0),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    haste_scr.main_script.caster_objects = [caster_0]
    haste_scr.main_script.effect_objects = [clock_0, clock_1, clock_2]
    haste_scr.main_script.target_objects = [target_0, target_1]

    return haste_scr


def make_marle_reraise_script(ct_rom: ctrom.CTRom):
    reraise_scr = AnimationScript.read_from_ctrom(ct_rom, ctenums.TechID.LIFE)

    caster_0: ObjectScript = [
        ac.SetObjectFacing(facing=ac.EnumTarget.TARGET_0),
        ac.PlayAnimationLoop(animation_id=0x36),
        ac.Pause(duration=0x78),
        ac.PlayAnimationLoop(animation_id=0x35),
        ac.PlaySound(sound=0x89),
        ac.Pause(duration=0x15),
        ac.IncrementCounter1D(),
        # ac.LoadSpriteAtTarget(target=3),
        ac.Pause(duration=0x90),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.Pause(duration=0x10),
        ac.IncrementCounter1D(),
        # ac.WaitForCounter1DValue(value=2),
        ac.Pause(duration=0x14),
        ac.IncrementCounter1D(),
        ac.Unknown2E(),
        ac.EndTech(),
        ac.ReturnCommand()
    ]

    target_0 = [
        ac.WaitForCounter1DValue(value=2),
        ac.PlayAnimationLoop(animation_id=0x24),
        ac.WaitForCounter1DValue(value=3),
        ac.PlayAnimationFirstFrame06(animation_id=3),
        ac.ReturnCommand()
    ]

    # Sparkles
    effect_0 = [
        ac.TeleportToTarget(target=9),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=0),
        ac.SwitchToPalette(palette=0),
        ac.PlayAnimationLoop(animation_id=0),
        ac.SetSpeedFastestShort(),
        ac.DrawEffect(),
        ac.PlaySound7A(sound=0x7C, unknown=0),
        ac.PerformSuperCommand(super_command=0x1C),
        ac.HideEffect(),
        ac.SetPriority(priority=3),
        ac.WaitForCounter1DValue(value=1),
        ac.SwitchToPalette(palette=2),
        ac.TeleportToTarget(target=3),
        ac.PlayAnimationLoop(animation_id=1),
        ac.PlaySound(sound=0xAD),
        ac.DrawEffect(),
        ac.WaitForCounter1DValue(value=2),
        ac.HideAllEffects(),
        ac.ReturnCommand()
    ]

    effect_1 = [
        ac.TeleportToTarget(target=9),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=0),
        ac.Pause(duration=0x02),
        ac.PlayAnimationLoop(animation_id=0),
        ac.SetSpeedFastestShort(),
        ac.Pause(duration=8),
        ac.DrawEffect(),
        ac.PerformSuperCommand(super_command=0x1C),
        ac.HideEffect(),
        ac.SetPriority(priority=3),
        ac.SwitchToPalette(palette=1),
        ac.WaitForCounter1DValue(value=1),
        ac.Pause(duration=0x3C),
        ac.TeleportToTarget(target=3),
        ac.PlayAnimationOnce(animation_id=2),
        ac.ReturnCommand()
    ]

    effect_2 = [
        ac.TeleportToTarget(target=9),
        ac.SetObjectFacing(facing=3),
        ac.SetPriority(priority=0),
        ac.Pause(duration=5),
        ac.PlayAnimationLoop(animation_id=0),
        ac.SetSpeedFastestShort(),
        ac.Pause(duration=0x10),
        ac.DrawEffect(),
        ac.PerformSuperCommand(super_command=0x1C),
        ac.HideEffect(),
        ac.SetPriority(priority=3),
        ac.SwitchToPalette(palette=1),
        ac.WaitForCounter1DValue(value=1),
        ac.Pause(duration=0x5A),
        ac.TeleportToTarget(target=3),
        ac.PlayAnimationOnce(animation_id=2),
        ac.ReturnCommand()
    ]

    test = extract_object_script_from_buffer(bytearray.fromhex(
        '1B09' +
        '7203' +
        '7300' +
        '2005' +
        '0200' +
        '0D' +
        '2010' +
        '70' +
        '1E1C' +
        '71' +
        '7303' +
        '2401' +
        '205A' +
        '1B03' +
        '0302' +
        '00'
    )
    )

    # print_object_script(test)
    # input()

    reraise_scr.main_script.caster_objects = [caster_0]
    reraise_scr.main_script.target_objects = [target_0]
    reraise_scr.main_script.effect_objects = [effect_0, effect_1, effect_2]

    return  reraise_scr


def make_gale_slash_script(ct_rom: ctrom.CTRom) -> AnimationScript:
    script = read_enemy_tech_script_from_ctrom(ct_rom, 0x74)
    # print_object_script(script.main_script.target_objects[0])
    # input()
    script.main_script.target_objects.append(
        [
            ac.WaitForCounter1DValue(value=2),
            ac.SetObjectPalette(palette=0),
            ac.Pause(duration=4),
            ac.PlayAnimationFirstFrame06(animation_id=5),
            ac.Pause(duration=8),
            ac.ResetPalette(),
            ac.Pause(duration=8),
            ac.PlayAnimationFirstFrame06(animation_id=3),
            ac.ReturnCommand()
        ]
    )
    return script


def make_iron_orb_script(ct_rom: ctrom.CTRom) -> AnimationScript:
    script = read_enemy_tech_script_from_ctrom(ct_rom, 0x41)

    script.main_script.caster_objects[0][2] = ac.PlayAnimationOnce(animation_id=0x22)
    target_obj = script.main_script.target_objects[0]
    target_obj[1] = ac.PlayAnimationFirstFrame06(animation_id=3)
    target_obj[4]  =ac.PlayAnimationFirstFrame06(animation_id=5)
    return script


def make_double_tap_script(ct_rom: ctrom.CTRom):
    script = AnimationScript.read_from_ctrom_addr(ct_rom,
                                                  0x0d7a6d,
                                                  #0x0E0810
                                                  )

    script.main_script.caster_objects[0] = [
        ac.SetObjectFacing(facing=0xD),
        ac.PlayAnimationFirstFrame(animation_id=0x31),
        ac.LoadSpriteAtTarget3E(target=0x0C),
        ac.LoadSpriteAtTarget3F(target=0x19),
        ac.LoadSpriteAtTarget40(target=0x03),
        ac.LoadSpriteAtTarget(target=0x9),
        ac.PlaySound7A(sound=0x96, unknown=9),
        ac.SetCounterToValue(counter=0xE, value=6),
        ac.SetCounterToValue(counter=0xA, value=0x28),
        ac.IncrementCounter(counter=0x1B),  ############
        ac.ShakeSprite(unknown=2, speed=3, num_times=0x20),
        ac.Pause(duration=0x5),
        ac.SetCounterToValue(counter=0xE, value=5),
        ac.Pause(duration=0x5),
        ac.SetCounterToValue(counter=0xE, value=4),
        ac.Pause(duration=0x5),
        ac.SetCounterToValue(counter=0xE, value=3),
        ac.Pause(duration=0x5),
        ac.SetCounterToValue(counter=0xE, value=2),
        ac.Pause(duration=0x10),
        ac.PlaySound(sound=0xB),
        ac.Pause(duration=20),
        ac.IncrementCounter1D(),
        ac.Unknown2D(),
        ac.FlashScreenColor(bytes.fromhex("80 12 A8")),
        ac.PlayAnimationOnce(animation_id=0x31),
        ac.WaitForCounter1DValue(value=4),
        ac.PlayAnimationFirstFrame(animation_id=3),
        ac.Pause(duration=0x0F),
        # ac.ShowDamage(),
        ac.Unknown2E(),
        ac.EndTech(),
        ac.ReturnCommand()
    ]
    # script.main_script.caster_objects[0][0] = ac.PlaySound7A(sound=0x50)
    # script.main_script.effect_objects = [] # script.main_script.effect_objects[:3]
    indices =  [0, 3, 4] #[0, 3, 4, 7]
    script.main_script.effect_objects = [script.main_script.effect_objects[ind]
                                         for ind in indices]
    # script.main_script.effect_objects[-1].insert(-2, ac.IncrementCounter1D())
    # script.main_script.effect_objects[0].pop(0)
    # script.main_script.effect_objects[0].insert(0, ac.Unknown61(bytes.fromhex("61 02 00 04")))

    script.main_script.effect_objects[0] = [
        ac.SwitchToPalette(palette=0),
        ac.SetObjectFacing(facing=0),
        ac.SetPriority(priority=0),
        ac.WaitForCounter1DValue(value=1),
        ac.SetSpeedFastestShort(),
        ac.StoreTargetCoordinates(target=0x09),
        ac.AddSubFromCounter(counter=0x1E, value=0x02),
        ac.TeleportToStoredCoordinates(),
        ac.PlayAnimationLoop(animation_id=0),
        ac.DrawEffect(),
        ac.PlaySound(sound=0x50),
        ac.StoreTargetCoordinates(target=0x0C),
        ac.AddSubFromCounter(counter=0x1E, value=0x02),
        ac.SlideSpriteToStoredCoordinates(),
        ac.SlideSpriteToTarget(target=3),
        ac.IncrementCounter1D(),
        ac.IncrementCounter(counter=0x1A),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    script.main_script.effect_objects[1] = [
        ac.SetObjectFacing(facing=0),
        ac.SetPriority(priority=0),
        ac.WaitForCounter1DValue(value=1),
        ac.Pause(duration=0xC),
        ac.SetSpeedFastestShort(),
        ac.StoreTargetCoordinates(target=0x09),
        ac.AddSubFromCounter(counter=0x1E, value=0x02),
        ac.TeleportToStoredCoordinates(),
        ac.DrawEffect(),
        ac.PlayAnimationLoop(animation_id=0),
        ac.PlaySound(sound=0x50),
        ac.StoreTargetCoordinates(target=0x0C),
        ac.AddSubFromCounter(counter=0x1E, value=0x02),
        ac.SlideSpriteToStoredCoordinates(),
        ac.HideEffect(),
        ac.ReturnCommand()
    ]

    script.main_script.effect_objects[2] = [
        ac.SetObjectFacing(facing=0),
        ac.SetPriority(priority=0),
        ac.WaitForCounter1DValue(value=1),
        ac.Pause(duration=0xC),
        ac.SetSpeedFastestShort(),
        ac.TeleportToTarget(target=0x09),
        ac.StoreTargetTo7E4AE8(target=0x1E),
        ac.SlideSpriteToTarget(target=0x0C),
        ac.IncrementCounter1D(),
        ac.ReturnCommand()
    ]

    # for obj in script.main_script.effect_objects:
    #     for ind, cmd in enumerate(obj):
    #         if cmd.CMD_ID == ac.TeleportToTarget.CMD_ID:
    #             pass
    #             block = [
    #                 ac.StoreTargetCoordinates(target=0x09),
    #                 ac.AddSubFromCounter(counter=0x1E, value=0x08),
    #                 ac.TeleportToStoredCoordinates()
    #             ]
    #             # obj[ind] = ac.TeleportToTarget(target=0x9)
    #             obj[ind:ind+1] = block
    #             ind += len(block)
    #         elif cmd.CMD_ID == ac.SlideSpriteToTarget.CMD_ID:
    #             pass
    #             block = [
    #                 ac.StoreTargetCoordinates(target=0x0C),
    #                 ac.AddSubFromCounter(counter=0x1E, value=0x08),
    #                 ac.SlideSpriteToStoredCoordinates()
    #             ]
    #             obj[ind:ind+1] = block
    #         if cmd.CMD_ID == ac.PlayAnimationLoop.CMD_ID:
    #             obj[ind] = ac.PlayAnimationLoop(animation_id=0)


    script.main_script.target_objects[0] = [
        ac.WaitForCounter1DValue(value=2),
        # ac.SetObjectFacing(facing=0x0A),
        ac.PlayAnimationFirstFrame(animation_id=5),
        ac.SetObjectPalette(palette=0),
        ac.SetAngle(angle=0),
        ac.ShakeSprite(unknown=4, speed=2, num_times=0x20),
        ac.Pause(duration=2),
        ac.PlayAnimationFirstFrame(animation_id=3),
        ac.Pause(duration=2),
        ac.PlayAnimationFirstFrame(animation_id=5),
        ac.WaitForCounter1DValue(value=3),
        ac.Pause(duration=8),
        ac.PlayAnimationFirstFrame(animation_id=3),
        ac.ResetPalette(),
        ac.ShowDamage(),
        # ac.Pause(duration=4),
        ac.ShowDamage51(),
        # ac.Pause(duration=4),
        ac.IncrementCounter1D(),
        ac.ReturnCommand()
    ]
    return script


def write_scripts_to_ct_rom(ct_rom: ctrom.CTRom):
    dt_script = make_double_tap_script(ct_rom)
    arrow_hail_script = make_arrow_rain_script(ct_rom)
    haste_all_script = make_single_marle_haste_all_script(ct_rom)
    prot_all_script = make_single_lucca_prot_all_script(ct_rom)
    reraise_script = make_marle_reraise_script(ct_rom)

    arrow_hail_script.write_to_ctrom(ct_rom, NewScriptID.ARROW_HAIL)
    haste_all_script.write_to_ctrom(ct_rom, NewScriptID.HASTE_ALL)
    prot_all_script.write_to_ctrom(ct_rom, NewScriptID.PROTECT_ALL)
    reraise_script.write_to_ctrom(ct_rom, NewScriptID.RERAISE)
    dt_script.write_to_ctrom(ct_rom, NewScriptID.DOUBLE_TAP)

    gale_slash_script = make_gale_slash_script(ct_rom)
    gale_slash_script.write_to_ctrom(ct_rom, NewScriptID.GALE_SLASH)

    blurp_script = read_enemy_tech_script_from_ctrom(ct_rom, 0x5D)
    blurp_script.main_script.caster_objects[0][1] = ac.PlayAnimationOnce(animation_id=0x5)
    blurp_script.write_to_ctrom(ct_rom, NewScriptID.BLURP)

    iron_orb_script = make_iron_orb_script(ct_rom)
    iron_orb_script.write_to_ctrom(ct_rom, NewScriptID.IRON_ORB)

    burst_ball_script = read_enemy_tech_script_from_ctrom(ct_rom, 0x88)
    burst_ball_script.main_script.caster_objects[0][4] = ac.PlayAnimationOnce(animation_id=0x22)
    burst_ball_script.write_to_ctrom(ct_rom, NewScriptID.BURST_BALL)


def main():
    from ctrando.base import basepatch
    from ctrando.postrando import palettes
    import random

    dalton_magus = palettes.SNESPalette.from_hex_sequence("#281820#E4DAA4#DCA264#B09058#DCA264#9C6A34#72897B#C6641E#3F626A#D47A34#34220C#302028")

    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")
    dalton_magus.write_to_ctrom(ct_rom, 6)
    basepatch.base_patch_ct_rom(ct_rom)
    tech_man = pctech.PCTechManager.read_from_ctrom(ct_rom)
    base_tech = tech_man.get_tech(ctenums.TechID.DARK_BOMB)
    script_id = base_tech.graphics_header.script_id
    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    # tech.effect_headers[0] = pctech.ctt.PCTechEffectHeader(gale_slash_effect)
    # tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_MELEE
    base_tech.target_data = pctech.ctt.PCTechTargetData(b'\x07\x00')
    base_tech.effect_headers[0].power = 0x2A
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("88 CE 0B 35 A9 A9 4A")
    )
    base_tech.graphics_header.script_id = script_id
    base_tech.name = "*Burst Ball"

    tech_man.set_tech_by_id(base_tech, ctenums.TechID.DARK_BOMB)

    script = read_enemy_tech_script_from_ctrom(ct_rom, 0x88)
    script.write_to_ctrom(ct_rom, script_id)

    tech_man.write_to_ctrom(ct_rom, 5, 5)
    #
    # script = make_arrow_rain_script(ct_rom)
    # script.write_to_ctrom(ct_rom, 0xA)
    #
    # script = make_single_marle_haste_all_script(ct_rom)
    # script.write_to_ctrom(ct_rom, 0xD)

    with open("/home/ross/Documents/ct-mod.sfc", "wb") as outfile:
        outfile.write(ct_rom.getvalue())




if __name__ == "__main__":
    main()
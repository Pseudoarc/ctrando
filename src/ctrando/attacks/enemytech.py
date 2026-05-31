"""Module for modifying enemy techs and attacks."""
import typing
from collections.abc import Sequence
import copy
from dataclasses import dataclass

from ctrando.attacks import cttechtypes as ctt
from ctrando.common import byteops, ctenums, ctrom
from ctrando.enemydata.enemystats import EnemyStats


@dataclass
class RomRef:
    file_loc: int = 0
    offset: int = 0


_tech_control_refs = [
    RomRef(0x01D7F0, 0x01), RomRef(0x01D817, 0x05), RomRef(0x01D854, 0x08),
    RomRef(0x01D875, 0x03), RomRef(0x01D8A1, 0x01), RomRef(0x01D8B5, 0x01),
    RomRef(0x3CBAC3, 0x03), RomRef(0x3DAAEA, 0x02), RomRef(0x3DAAF7, 0x03)
]
_tech_effect_refs = [
    RomRef(0x01D839, 0x00)
]
_atk_control_refs = [
    RomRef(0x01D8FD, 0x00), RomRef(0x01D924, 0x04), RomRef(0x01D961, 0x07),
    RomRef(0x01D9A7, 0x00), RomRef(0x01D9BB, 0x00), RomRef(0x3DAB19, 0x01),
    RomRef(0x3DAB26, 0x02)
]
_atk_effect_refs = [RomRef(0x01D946, 0x00)]


class EnemyTech:
    def __init__(
            self,
            control: ctt.EnemyTechControlHeader,
            effect: ctt.EnemyTechEffectHeader,
            target: ctt.EnemyTechTargetData,
            graphics: ctt.EnemyTechGfxHeader
    ):
        self.control = control
        self.effect = effect
        self.target = target
        self.graphics = graphics

    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom, tech_id: int) -> typing.Self:
        control = ctt.EnemyTechControlHeader.read_from_ctrom(ct_rom, tech_id)
        effect = ctt.EnemyTechEffectHeader.read_from_ctrom(ct_rom, tech_id)
        target = ctt.EnemyTechTargetData.read_from_ctrom(ct_rom, tech_id)
        graphics = ctt.EnemyTechGfxHeader.read_from_ctrom(ct_rom, tech_id)

        return cls(control, effect, target, graphics)



class EnemyAttack:
    def __init__(
            self,
            control: ctt.EnemyAttackControlHeader,
            effect: ctt.EnemyAttackEffectHeader,
    ):
        self.control = control
        self.effect = effect

    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom, attack_id: int) -> typing.Self:
        control = ctt.EnemyAttackControlHeader.read_from_ctrom(ct_rom, attack_id)
        effect = ctt.EnemyAttackEffectHeader.read_from_ctrom(ct_rom, attack_id)

        return cls(control, effect)


class EnemyAttackManager:
    def __init__(
            self,
            enemy_techs: dict[int, EnemyTech],
            enemy_attacks: Sequence[EnemyAttack],
            main_attack_graphics: Sequence[ctt.EnemyBaseAttackGfxHeader],
            alt_attack_graphics: Sequence[ctt.EnemyAltAttackGfxHeader],
    ):
        self.enemy_techs: list[EnemyTech] = [
            EnemyTech(ctt.EnemyTechControlHeader(),
                      ctt.EnemyTechEffectHeader(),
                      ctt.EnemyTechTargetData(),
                      ctt.EnemyTechGfxHeader())
            for _ in range(0x100)
        ]
        for tech_id, tech in enemy_techs.items():
            self.enemy_techs[tech_id] = tech

        self.enemy_attacks = list(enemy_attacks)

        if len(main_attack_graphics) != 0x100:
            raise ValueError
        self.main_attack_graphics = list(main_attack_graphics)

        if len(alt_attack_graphics) != 0x100:
            raise ValueError
        self.alt_attack_graphics = list(alt_attack_graphics)

    def get_tech(self, tech_id: int) -> EnemyTech:
        return copy.deepcopy(self.enemy_techs[tech_id])

    def set_tech(self, tech: EnemyTech, tech_id: int):
        tech.control.set_effect_index(0, tech_id)
        self.enemy_techs[tech_id] = tech

    def append_attack(self, attack: EnemyAttack) -> int:
        ret_val = len(self.enemy_attacks)
        self.enemy_attacks.append(attack)
        return ret_val


    def get_attack(self, attack_id: int) -> EnemyAttack:
        return copy.deepcopy(self.enemy_attacks[attack_id])

    def set_attack(self, attack: EnemyAttack, attack_id: int):
        self.enemy_attacks[attack_id] = attack


    @staticmethod
    def _get_num_attacks_from_ctrom(ct_rom: ctrom.CTRom):
        atk_inds = [
            EnemyStats.from_ctrom(ct_rom, enemy_id).secondary_attack_id
            for enemy_id in ctenums.EnemyID
        ]
        num_attacks = max(atk_inds) + 1
        return num_attacks

    @staticmethod
    def _repoint_data(
            ct_rom: ctrom.CTRom,
            base_rom_ptr: int,
            refs: list[RomRef],
    ):
        for ref in refs:
            new_ptr = base_rom_ptr + ref.offset
            ct_rom.seek(ref.file_loc)
            ct_rom.write(int.to_bytes(new_ptr, 3, "little"))

    @staticmethod
    def _repoint_attack_effects(ct_rom: ctrom.CTRom, new_rom_start: int):
        ptr_loc = ctt.EnemyAttackEffectHeader.ROM_RW.get_ptr_loc(ct_rom)
        ct_rom.seek(ptr_loc)
        ct_rom.write(new_rom_start.to_bytes(3, "little"))

    @classmethod
    def read_from_ctrom(
            cls,
            ct_rom: ctrom.CTRom,
            num_attacks: int | None = None
    ):
        enemy_techs = {
            tech_id: EnemyTech.read_from_ctrom(ct_rom, tech_id)
            for tech_id in range(0x100)
        }

        main_attack_graphics = [
            ctt.EnemyBaseAttackGfxHeader.read_from_ctrom(ct_rom, ind)
            for ind in range(0x100)
        ]

        alt_attack_graphics = [
            ctt.EnemyAltAttackGfxHeader.read_from_ctrom(ct_rom, ind)
            for ind in range(0x100)
        ]

        if num_attacks is None:
            num_attacks = cls._get_num_attacks_from_ctrom(ct_rom)

        enemy_attacks = [
            EnemyAttack.read_from_ctrom(ct_rom, atk_ind)
            for atk_ind in range(num_attacks)
        ]

        return EnemyAttackManager(
            enemy_techs,
            enemy_attacks,
            main_attack_graphics,
            alt_attack_graphics
        )

    def write_to_ctrom(self, ct_rom: ctrom.CTRom):
        for ind, tech in enumerate(self.enemy_techs):
            tech.control.write_to_ctrom(ct_rom, ind)
            tech.effect.write_to_ctrom(ct_rom, ind)
            tech.target.write_to_ctrom(ct_rom, ind)
            tech.graphics.write_to_ctrom(ct_rom, ind)

        num_attacks = self._get_num_attacks_from_ctrom(ct_rom)
        if len(self.enemy_attacks) > num_attacks:
            for ind, atk in enumerate(self.enemy_attacks):
                atk.control.free_data_on_ct_rom(ct_rom, ind)
                atk.effect.free_data_on_ct_rom(ct_rom, ind)

                new_num_attacks = len(self.enemy_attacks)
                new_atk_control_st = ct_rom.space_manager.get_free_addr(
                    ctt.EnemyAttackControlHeader.SIZE*new_num_attacks,
                    hint=0x410000
                )
                self._repoint_data(ct_rom, byteops.to_rom_ptr(new_atk_control_st),
                                   _atk_control_refs)

                new_atk_effect_st = ct_rom.space_manager.get_free_addr(
                    ctt.EnemyAttackEffectHeader.SIZE*new_num_attacks,
                    hint=0x410000
                )
                self._repoint_attack_effects(ct_rom, byteops.to_rom_ptr(new_atk_effect_st))

        for ind, attack in enumerate(self.enemy_attacks):
            attack.control.write_to_ctrom(ct_rom, ind)
            attack.effect.write_to_ctrom(ct_rom, ind)

        for ind in range(0x100):
            base_gfx = self.main_attack_graphics[ind]
            alt_gfx = self.alt_attack_graphics[ind]

            base_gfx.write_to_ctrom(ct_rom, ind)
            alt_gfx.write_to_ctrom(ct_rom, ind)


def main():
    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")
    rom_b = ct_rom.getvalue()
    enemy_atk_man = EnemyAttackManager.read_from_ctrom(ct_rom)
    enemy_atk_man.write_to_ctrom(ct_rom)

    new_rom_b = ct_rom.getvalue()
    print(new_rom_b == rom_b)


if __name__ == "__main__":
    main()



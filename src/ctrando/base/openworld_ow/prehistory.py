"""Alter 65M BC Overworld for open world."""
from ctrando.common import memory
from ctrando.overworlds import oweventcommand as owc, oweventcommandhelper as owh, \
    overworld as ow


def modify_overworld(overworld: ow.Overworld):
    """
    Modify the G5M BC overworld for an open world.
    """
    script = overworld.event

    # Storyline Checks:
    # 4CA61B751D        [00A6] If(Mem.StorylineCtr < 75) Goto [00C3]
    # 450002            [00AB] BitMath(Exit02, 80, Reset)
    # 450003            [00AE] BitMath(Exit03, 80, Reset)
    # 450004            [00B1] BitMath(Exit04, 80, Reset)
    # 450005            [00B4] BitMath(Exit05, 80, Reset)
    # 440006            [00B7] BitMath(Exit06, 80, Set)
    # 440007            [00BA] BitMath(Exit07, 80, Set)
    # 440008            [00BD] BitMath(Exit08, 80, Set)
    # 440009            [00C0] BitMath(Exit09, 80, Set)
    #  - Reset exits 2-4 and set exits 6-9 after the gate key is stolen.
    #    Exits 2 and 3 are face Forest Maze exits.
    #  - For rando, this should always be the state of the world.
    ind = script.find_next_exact_command(owh.branch_if_storyline_lt(0x75))
    script.delete_commands(ind)

    # 4CA61B9908        [00C3] If(Mem.StorylineCtr < 99) Goto [00CB]
    # 1AD704            [00C8] Goto [00D8]
    # - If Lavos has fallen to earth (storyline 0x99), go to [00D8] to copy
    #   a bunch of tiles (and then jump back to [00CB] after)
    ind = script.find_next_exact_command(owh.branch_if_storyline_lt(0x99), ind)
    script.replace_jump_command(
        ind, owh.branch_if_flag_reset(memory.Flags.OW_LAVOS_HAS_FALLEN))

    # 4CA61B8D08        [00CB] If(Mem.StorylineCtr < 8D) Goto [00D3]
    # 1AE705            [00D0] Goto [01E8]
    # - This is the one that reveals Laruba village.
    # - The [01E8] block also returns to [00D3] so it's fine to just remove this
    ind = script.find_next_exact_command(owh.branch_if_storyline_lt(0x8D), ind)
    script.delete_commands(ind)
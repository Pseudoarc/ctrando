"""Alter 600AD Overworld for open world."""
from ctrando.common import memory
from ctrando.overworlds import oweventcommand as owc, oweventcommandhelper as owh, \
    overworld as ow


def modify_overworld(overworld: ow.Overworld):
    """
    Modify the 600AD overworld for an open world.
    """

    script = overworld.event

    # Storyline checks:
    # 4DA61B8A0D        [00AD] If(Mem.StorylineCtr >= 8A) Goto [00BA]
    #  - If Magus is defeated skip a few commands.  I think these are the bats
    #    that fly around the castle.
    #  - Replace with a check for a (newly added) Magus Defeated OW flag

    ind = script.find_next_exact_command(owh.branch_if_storyline_ge(0x8A))
    repl_cmd = owh.branch_if_flag_set(memory.Flags.OW_MAGUS_DEFEATED)
    script.replace_jump_command(ind, repl_cmd)

    # 4CA61B5422        [00BA] If(Mem.StorylineCtr < 54) Goto [00DC]
    #  - If the quest to defeat Magus has not begun, skip the following
    #       450000            [00BF] BitMath(Exit00, 80, Reset)
    #       440001            [00C2] BitMath(Exit01, 80, Set)
    #       440002            [00C5] BitMath(Exit02, 80, Set)
    #         - Remove wrecked entrance, add fixed entrance
    #       07010F1C66        [00C8] SetTile(L2, x0F, y1C, 66)
    #       07010F1D76        [00CD] SetTile(L2, x0F, y1D, 76)
    #       07010F1E76        [00D2] SetTile(L2, x0F, y1E, 76)
    #       07010F1F86        [00D7] SetTile(L2, x0F, y1F, 86)
    #         - Add the fixed bridge map tiles
    #  - What we want is:
    #    1) Exit00 (wrecked bridge) is always disabled
    #    2) Exit01 (fixed bridge N) is always enabled
    #    3) Exit02 (fixed bridge S) is only enabled after Zombor is defeated
    #  - Delete the branch at [00DC].
    #  - Insert a branch to skip the Exit02 setting unless Zenan is complete.

    ind = script.find_next_exact_command(
        owh.branch_if_storyline_lt(0x54), start=ind)
    script.delete_commands(ind)

    ind = script.find_next_exact_command(
        owc.SetExitActive(exit_type=0, exit_index=2))
    target = ind+1
    to_label = script.get_label(target)
    script.insert_commands(
        ind,
        [
            owh.branch_if_flag_reset(memory.Flags.OW_ZENAN_COMPLETE,
                                     to_label)
        ]
    )

    # 0701212971        [00DC] SetTile(L2, x21, y29, 71)
    #  - The rock in front of the magic cave
    # 4CA61B8710        [00E1] If(Mem.StorylineCtr < 87) Goto [00F1]
    #  - If the magic cave has not been opened skip the following
    # 	450003            [00E6] BitMath(Exit03, 80, Reset)
    #         - Disable exit to closed cave
    # 	440004            [00E9] BitMath(Exit04, 80, Set)
    #         - Enable exit to Magic Cave
    # 	0701212900        [00EC] SetTile(L2, x21, y29, 00)
    #         - Remove the rock in front of the cave
    #  - Replace with a check for the Magic Cave being open.
    closed_cave_exit = overworld.exit_data.exits[3]
    closed_cave_exit.is_active = False

    open_cave_exit = overworld.exit_data.exits[4]
    open_cave_exit.is_active = True

    ind = script.find_next_exact_command(
        owh.branch_if_storyline_lt(0x87), start=ind
    )
    script.replace_jump_command(
        ind,
        owh.branch_if_flag_reset(memory.Flags.OW_MAGIC_CAVE_OPEN))
    script.delete_commands(ind+1, ind+3)

    # 4CA61B8A2C        [0101] If(Mem.StorylineCtr < 8A) Goto [012D]
    #  - If Magus is not defeated, skip these commands that kill a bunch of
    #    trees around Fiona's house
    #      4F02              [0106] CopyTiles(L2, x30, y3B, L02, x16, y26,
    #                                          w07, h05) -> 4F02303B0216260705
    #      07011A2800        [010F] SetTile(L2, x1A, y28, 00)
    # 	   07011B2800        [0114] SetTile(L2, x1B, y28, 00)
    # 	   0701182700        [0119] SetTile(L2, x18, y27, 00)
    # 	   0701192700        [011E] SetTile(L2, x19, y27, 00)
    # 	   0701172800        [0123] SetTile(L2, x17, y28, 00)
    # 	   0701172900        [0128] SetTile(L2, x17, y29, 00)
    #   - Again, just replace this with a flag check for Magus defeated.

    ind = script.find_next_exact_command(owh.branch_if_storyline_lt(0x8A),
                                         start=ind)
    script.replace_jump_command(
        ind,
        owh.branch_if_flag_reset(memory.Flags.OW_MAGUS_DEFEATED))

    # 4CA61B8A08        [014E] If(Mem.StorylineCtr < 8A) Goto [0156]
    # - If Magus not defeated, skip resetting the castle entrance
    #      450009            [0153] BitMath(Exit09, 80, Reset)
    # - Replace with a check to the Magus Defeated OW Flag
    # - TODO: Possibly allow re-entrance to Magus's Castle for boxes?

    ind = script.find_next_exact_command(
        owh.branch_if_storyline_lt(0x8A), start=ind)
    script.replace_jump_command(
        ind, owh.branch_if_flag_reset(memory.Flags.OW_MAGUS_DEFEATED))

    # 4CA61B5A19        [0166] If(Mem.StorylineCtr < 5A) Goto [017F]
    #  - If Ozzie has not yet summoned Zombor, skip the following
    #       07020F1C39        [016B] SetTile(L1, x0F, y1C, 39)
    #       07020F1D49        [0170] SetTile(L1, x0F, y1D, 49)
    #       07020F1E59        [0175] SetTile(L1, x0F, y1E, 59)
    #       07020F1F69        [017A] SetTile(L1, x0F, y1F, 69)
    #  - The above commands just make the bridge walkable
    #  - Replace with newly created Zenan Complete OW flag
    #  - TESTING: Let the bridge always be walkable.

    # TESTING: always let the bridge be walkable.  The bottom exit is still
    #   disabled until the quest is complete.
    ind = script.find_next_exact_command(
        owh.branch_if_storyline_lt(0x5A), start=ind)
    script.delete_commands(ind)

    # ind = script.find_next_exact_command(
    #     owh.branch_if_storyline_lt(0x5A), start=ind)
    # script.replace_jump_command(
    #     ind,
    #     owh.branch_if_flag_reset(memory.Flags.OW_ZENAN_COMPLETE))

    # 4CA61BD42D        [0283] If(Mem.StorylineCtr < D4) Goto [02B0]
    #  - If Black Omen not out, skip a bunch of stuff
    #  - Could maybe delete, but will just make a flag for it.
    #  - Decided that deletion is best for now.

    ind = script.find_next_exact_command(
        owh.branch_if_storyline_lt(0xD4), start=ind)
    # script.replace_jump_command(
    #     ind,
    #     owh.branch_if_flag_reset(memory.Flags.OW_BLACK_OMEN_RISEN))
    script.delete_commands(ind, ind+1)

    # 27AE1B0428        [0288] If(Mem.7E1BAE !& 04) Goto [02B0]
    #  - If Black Omen not out in 600 AD skip it too
    #     097E0D7F          [028D] AddObject([097E], t0)
    #     09D70D7F          [0291] AddObject([09D7], t0)
    #     09040E7F          [0295] AddObject([0A04], t0)
    #     09170E7F          [0299] AddObject([0A17], t0)
    #     27A81B800C        [029D] If(Mem.7E1BA8 !& 80) Goto [02A9]
    #       - If Sunken desert is not complete skip these
    #       - If the sunken desert is complete, we'll load the A2A object.
    #         Otherwise, load the A81 object.
    #       - These are essentially the same except for an argument to
    #         Command04 (load palette).  If the desert is not completed, it
    #         uses pallete 0xA for the sand vortex, so the Black Omen uses
    #         palette 0xB
    #         instead of 0xA. Why not just always use 0xB?
    #        092A0E7F          [02A2] AddObject([0A2A], t0)
    #        1AAC06            [02A6] Goto [02AD]
    #     09810E7F          [02A9] AddObject([0A81], t0)
    #     35CF49            [02AD] SetDestCoords(CF, 49)
    # 37                [02B0] Return

    # Other Issues:
    # By default, Giant's claw is enabled but the entrance doesn't have text.
    # This can either be fixed by disabling the exit in the overworld or by
    # editing the event.
    # 27AD1B8010        [0156] If(Mem.7E1BAD !& 80) Goto [0166]
    #  - If Giant's Claw has not been revealed skip these
    #     45000A            [015B] BitMath(Exit0A, 80, Reset)
    #     44000B            [015E] BitMath(Exit0B, 80, Set)
    #       - These just change the name to Giant's Claw
    #       - NOTE: Giant's claw is accessible (no name) without using the pop
    #     07013B2400        [0161] SetTile(L2, x3B, y24, 00)
    #       - Add the open entrance to claw
    claw_exit = overworld.exit_data.exits[0xA]
    claw_exit.is_active = False

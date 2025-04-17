"""Alter 1000AD Overworld for open world."""
from ctrando.common import memory
from ctrando.overworlds import oweventcommand as owc, oweventcommandhelper as owh, \
    overworld as ow


def modify_overworld(overworld: ow.Overworld):
    """
    Modify the 1000AD overworld for an open world.
    - Adjust Black Omen appearance
    """

    # 4CA61BD421        [0247] If(Mem.StorylineCtr < D4) Goto [0268]
    #  - If the Black Omen is not out, skip some object loads
    #  - This is now controlled just by flags, so remove it.
    script = overworld.event
    ind = script.find_next_exact_command(
        owh.branch_if_storyline_lt(0xD4)
    )
    script.delete_commands(ind, ind+1)
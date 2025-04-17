"""Alter Overworlds for open world."""
from ctrando.base.openworld_ow import middleages, prehistory, present, lastvillage, future
from ctrando.common import ctenums
from ctrando.common.randostate import OWManager


def update_all_overworlds(ow_manager: OWManager):
    """
    Apply all openworld overworld mods
    """
    present.modify_overworld(ow_manager[ctenums.OverWorldID.PRESENT])
    middleages.modify_overworld(ow_manager[ctenums.OverWorldID.MIDDLE_AGES])
    future.modify_overworld(ow_manager[ctenums.OverWorldID.FUTURE])
    prehistory.modify_overworld(ow_manager[ctenums.OverWorldID.PREHISTORY])
    lastvillage.modify_overworld(ow_manager[ctenums.OverWorldID.LAST_VILLAGE])

from ctrando.common import ctenums
from ctrando.common.random import RNGType
from ctrando.locations import scriptmanager, locationevent
from ctrando.encounters import encountertypes


def assign_random_elevators(rng: RNGType) -> encountertypes.OmenElevatorData:

    return encountertypes.OmenElevatorData(
        rng.randrange(0, 256) < 0xA0,  # up 1
        rng.randrange(0, 256) < 0x60,  # up 2
        rng.randrange(0, 256) < 0x80,  # up 3
        rng.randrange(0, 256) < 0x80,  # down 1
        rng.randrange(0, 256) < 0xA0,  # down 2
        rng.randrange(0, 256) < 0x60,  # down 3
    )


def write_omen_elevators(script_manager: scriptmanager.ScriptManager,
                         elevator_data: encountertypes.OmenElevatorData):

    def write_elevator_script(
            script: locationevent.LocationEvent,
            battle_1: bool, battle_2: bool, battle_3: bool
    ):
        pos, _ = script.find_command([0x7F])

        battles = (battle_1, battle_2, battle_3)
        for battle in battles:
            pos, cmd = script.find_command([0x12], pos)
            if battle:
                script.delete_commands(pos, 1)
            else:
                script.delete_jump_block(pos)

    omen_up_script = script_manager[ctenums.LocID.BLACK_OMEN_ELEVATOR_UP]
    write_elevator_script(
        omen_up_script,
        elevator_data.omen_elevator_up_battle_1,
        elevator_data.omen_elevator_up_battle_2,
        elevator_data.omen_elevator_up_battle_3
    )

    omen_down_script = script_manager[ctenums.LocID.BLACK_OMEN_ELEVATOR_DOWN]
    write_elevator_script(
        omen_down_script,
        elevator_data.omen_elevator_down_battle_1,
        elevator_data.omen_elevator_down_battle_2,
        elevator_data.omen_elevator_down_battle_3
    )

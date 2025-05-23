import random
import mahjong.constants as mc

from game.src.core.round import Round
from game.src.core.replay_round import ReplayRound
from ml.src.data_structures import DataPoint


# For now, collect_data works only on replay
def run_match(competitors, seed=0, match_type=mc.EAST, gui=None, match_replay=None, collect_data=False):
    # Initialize
    scores = [250, 250, 250, 250]
    if seed:
        random.seed(seed)
    non_repeat_round_no = 0
    round_no = 0
    collected_data: list[DataPoint] = []

    if match_replay is not None:
        match_type = match_replay.prevalent_wind
    wind_offset = mc.EAST  # mahjong.constants WINDS are offset by 27 == mc.EAST
    match_type -= wind_offset  # 0

    if collect_data and match_replay is None:
        raise NotImplementedError("Collecting data not on replay isn't implemented")

    while not (
        min(scores) <= 0 or
        (non_repeat_round_no >= 3 and max(scores) >= 500) or
        round_no >= 12 or
        (match_replay is not None and round_no >= len(match_replay.round_data))
    ):
        if match_replay is None:
            rnd = Round(competitors, scores, non_repeat_round_no, match_type, gui)
        else:
            rnd = ReplayRound(competitors, scores, non_repeat_round_no, match_type,
                              match_replay.round_data[round_no], collect_data, gui)
        scores, dealer_won, data = rnd.run()

        if collect_data:
            collected_data.extend(data)
        round_no += 1
        if not dealer_won:
            non_repeat_round_no += 1

    '''
    if min(scores) <= 0 or (non_repeat_round_no >= 3 and max(scores) >= 500):
        print("Match won by someone")
    else:
        print("Draw: too many rounds")
    '''

    return scores, collected_data
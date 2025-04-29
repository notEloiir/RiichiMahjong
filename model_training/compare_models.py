import random
from operator import add

from game.core.game_logic import simulate_match


def versus(competitors, how_many, init_seed, device):

    total = [0, 0, 0, 0]
    for match in range(how_many):
        seed = random.randint(1717, 7171) if match else init_seed
        match_total = [0, 0, 0, 0]
        print("Match {} seed {}".format(match, seed))
        for order in range(4):
            scores = simulate_match(competitors[order:] + competitors[:order], seed, device)
            scores = scores[-order:] + scores[:-order]
            match_total = list(map(add, match_total, scores))
            print("Match {} var {} completed with scores {}".format(match, order, scores))
        total = list(map(add, total, match_total))

    return [total[i] / sum(total) for i in range(4)]

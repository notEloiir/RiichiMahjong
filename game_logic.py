import random
from parse_matches import Tile, InputFeatures, MoveType
from enum import Enum

from mahjong import shanten, agari
from mahjong.meld import Meld
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
import mahjong.constants as mc

import torch
from models import MahjongNN


class EventType(Enum):
    DRAW_TILE = 0
    DRAW_TILE_AFTER_KAN = 1
    DISCARD_TILE = 2
    TILE_DISCARDED = 3
    ROUND_DRAW = 4
    WALL_EXHAUSTED = 5
    WINNER = 6


def wind_from_int(wind_id):
    match wind_id:
        case 0:
            return mc.EAST
        case 1:
            return mc.SOUTH
        case 2:
            return mc.WEST
        case 3:
            return mc.NORTH


class Event:
    def __init__(self, what: EventType, who):
        self.what: EventType = what
        self.who = who


def simulate_round(competitors: list[MahjongNN], scores, non_repeat_round_no, device):
    hand_calculator = HandCalculator()

    # INIT
    dealer_id = non_repeat_round_no % 4
    prevalent_wind = (non_repeat_round_no // 4) % 4  # starting from east
    seat_wind = [(non_repeat_round_no + i) % 4 for i in range(4)]
    turn_no = 1
    curr_player_id = dealer_id
    closed_hands: list[list[Tile]] = [[] for _ in range(4)]
    closed_hand_counts = [[0] * 34 for _ in range(4)]
    open_hands: list[list[Tile]] = [[] for _ in range(4)]
    open_hand_counts = [[0] * 34 for _ in range(4)]
    open_melds_tile_ids = [[] for _ in range(4)]
    melds: list[list[Meld]] = [[] for _ in range(4)]
    discard_piles: list[list[Tile]] = [[] for _ in range(4)]
    discard_orders = [[0] * 34 for _ in range(4)]
    hidden_tile_counts = [[4] * 34 for _ in range(4)]
    hand_in_riichi = [0] * 4
    hand_is_closed = [1] * 4
    visible_dora = [0] * 34
    red5_closed_hand = [[0] * 3 for _ in range(4)]
    red5_open_hand = [[0] * 3 for _ in range(4)]
    red5_discarded = [0] * 3
    red5_hidden = [[1] * 3 for _ in range(4)]

    # PREP ROUND
    game_tiles = [Tile(t) for t in range(34 * 4)]
    random.shuffle(game_tiles)

    # give out tiles to players
    for p in range(4):
        for i in range(13):
            tile = game_tiles[p * 13 + i]
            closed_hands[p].append(tile)
            closed_hand_counts[p][tile.to_int()] += 1
            if tile.is_red5():
                red5_hidden[p][tile.to_int() // 9] = 0
                red5_closed_hand[p][tile.to_int() // 9] = 1

    # build walls
    wall = game_tiles[52:122]  # from 13*4, 70 tiles
    dora_indicators = game_tiles[122:127]  # 5 tiles
    uradora_indicators = game_tiles[127:132]  # 5 tiles
    dead_wall = game_tiles[132:]  # 4 tiles
    dora_revealed_no = 0

    # reveal the first dora indicator
    dora_indicator = dora_indicators[dora_revealed_no]
    visible_dora[dora_indicator.to_int()] += 1
    dora_revealed_no += 1
    for p in range(4):
        hidden_tile_counts[p][dora_indicator.to_int()] -= 1
        if dora_indicator.is_red5():
            red5_hidden[p][dora_indicator.to_int() // 9] = 0

    # TODO: handle draw conditions bs (four winds, nine orphans)
    # TODO: implement temp furiten and perma furiten (in riichi)
    # TODO: after fourth quad discard, check if draw
    # GAME LOGIC
    event = Event(EventType.DRAW_TILE, dealer_id)
    while True:
        match event.what:
            case EventType.DRAW_TILE | EventType.DRAW_TILE_AFTER_KAN:
                # draw the tile and related game logic
                curr_player_id = event.who

                if event.what == EventType.DRAW_TILE:
                    if turn_no == 70:
                        event = Event(EventType.WALL_EXHAUSTED, None)
                        continue
                    tile = wall[turn_no - 1]
                    turn_no += 1
                else:
                    tile = dead_wall[dora_revealed_no - 1]
                    if dora_revealed_no == 5 and sum(open_hand_counts[curr_player_id]) != 16:  # 4 kans by >1 player
                        # TODO: set flag to check for draw
                        pass

                closed_hand_counts[curr_player_id][tile.to_int()] += 1
                closed_hands[curr_player_id].append(tile)
                hidden_tile_counts[curr_player_id][tile.to_int()] -= 1
                if tile.is_red5():
                    red5_closed_hand[curr_player_id][tile.to_int() // 9] = 1
                    red5_hidden[curr_player_id][tile.to_int() // 9] = 0

                # checking whether KAN, RIICHI, TSUMO possible
                is_kan_possible = closed_hand_counts[curr_player_id][tile.to_int()] == 4
                tiles_to_ready_hand = shanten.Shanten().calculate_shanten(closed_hand_counts[curr_player_id])
                is_riichi_possible = tiles_to_ready_hand == 0 and hand_is_closed[curr_player_id] \
                                     and not hand_in_riichi[curr_player_id]
                is_tsumo_possible = False
                if agari.Agari().is_agari(
                        [closed_hand_counts[curr_player_id][i] + open_hand_counts[curr_player_id][i] for i in range(34)]
                        , open_melds_tile_ids[curr_player_id]):
                    tiles136 = [t.true_id() for t in closed_hands[curr_player_id] + open_hands[curr_player_id]]
                    win_tile136 = closed_hands[curr_player_id][-1].true_id()
                    hand_result = hand_calculator.estimate_hand_value(tiles=tiles136, win_tile=win_tile136,
                                                                      melds=melds[curr_player_id])
                    is_tsumo_possible = hand_result.error is None

                # if nothing but discard is possible
                if not (is_kan_possible or is_riichi_possible or is_tsumo_possible):
                    event = Event(EventType.DISCARD_TILE, curr_player_id)
                    continue

                # decide what to do
                if competitors[curr_player_id] is not None:
                    tile_to_call = None
                    tile_origin = None
                    if is_kan_possible:
                        tile_to_call = tile.to_int()
                        tile_origin = curr_player_id
                    inputs = InputFeatures(device, curr_player_id, non_repeat_round_no, turn_no, dealer_id,
                                           prevalent_wind, seat_wind[curr_player_id], closed_hand_counts[curr_player_id]
                                           , open_hand_counts, discard_orders, hidden_tile_counts[curr_player_id],
                                           visible_dora, hand_is_closed, hand_in_riichi, scores,
                                           red5_closed_hand[curr_player_id], red5_open_hand, red5_discarded,
                                           red5_hidden[curr_player_id], tile_to_call, tile_origin)

                    # query the model
                    discard_tiles, call_tiles, action = competitors[curr_player_id].get_prediction(inputs.to_tensor())
                    action = action.clone()

                    # zero out everything that isn't possible
                    action[1], action[2], action[4], action[7] = 0., 0., 0., 0.
                    if not is_kan_possible:
                        action[6] = 0.
                    if not is_riichi_possible:
                        action[3] = 0.
                    if not is_tsumo_possible:
                        action[5] = 0.

                    # turn the results to probabilities
                    action /= torch.sum(action)

                    # decide what to do
                    what_do = MoveType(action.argmax(0).item() + 1)

                else:
                    # TODO: let player decide
                    if is_tsumo_possible:
                        # ask player
                        pass
                    elif is_riichi_possible:
                        # ask player
                        pass
                    elif is_kan_possible:
                        # ask player
                        pass

                    # temporary
                    what_do = MoveType.DISCARD

                # game logic based on decision made
                match what_do:
                    case MoveType.KAN:
                        # move tiles to "open" hand
                        # though the hand stays closed, since it's closed kan
                        open_hand_counts[curr_player_id][tile.to_int()] = 4
                        closed_hand_counts[curr_player_id][tile.to_int()] = 0
                        i = 0
                        while i < len(closed_hands[curr_player_id]):
                            if tile.to_int()*4 <= closed_hands[curr_player_id][i].true_id() <= tile.to_int()*4 + 3:
                                open_hands[curr_player_id].append(closed_hands[curr_player_id].pop(i))
                            else:
                                i += 1

                        melds[curr_player_id].append(
                            Meld(meld_type=Meld.KAN,
                                 tiles=[i for i in range(tile.to_int() * 4, (tile.to_int() + 1) * 4)],
                                 opened=False, called_tile=tile.true_id(), who=curr_player_id, from_who=curr_player_id))

                        # reveal dora
                        dora_indicator = dora_indicators[dora_revealed_no]
                        visible_dora[dora_indicator.to_int()] += 1
                        dora_revealed_no += 1
                        for p in range(4):
                            hidden_tile_counts[p][dora_indicator.to_int()] -= 1
                            if dora_indicator.is_red5():
                                red5_hidden[p][dora_indicator.to_int() // 9] = 0

                        # get another tile (from dead wall)
                        event = Event(EventType.DRAW_TILE_AFTER_KAN, curr_player_id)
                        continue

                    case MoveType.RIICHI:
                        hand_in_riichi[curr_player_id] = turn_no

                    case MoveType.TSUMO:
                        event = Event(EventType.WINNER, [curr_player_id, [curr_player_id]])
                        continue

                event = Event(EventType.DISCARD_TILE, curr_player_id)

            case EventType.DISCARD_TILE:
                if hand_in_riichi[curr_player_id] and hand_in_riichi[curr_player_id] != turn_no:
                    discard_tile = closed_hands[curr_player_id][-1]
                elif competitors[curr_player_id] is None:
                    # TODO: ask player what to discard
                    discard_tile = closed_hands[curr_player_id][-1]
                else:
                    # query the model what to discard
                    inputs = InputFeatures(device, curr_player_id, non_repeat_round_no, turn_no, dealer_id,
                                           prevalent_wind, seat_wind[curr_player_id], closed_hand_counts[curr_player_id]
                                           , open_hand_counts, discard_orders, hidden_tile_counts[curr_player_id],
                                           visible_dora, hand_is_closed, hand_in_riichi, scores,
                                           red5_closed_hand[curr_player_id], red5_open_hand, red5_discarded,
                                           red5_hidden[curr_player_id])

                    # query the model
                    discard_tiles, call_tiles, action = competitors[curr_player_id].get_prediction(inputs.to_tensor())
                    discard_tiles = discard_tiles.clone()

                    # zero out everything that isn't possible
                    for tile_id in range(34):
                        if not closed_hand_counts[curr_player_id][tile_id]:
                            discard_tiles[tile_id] = 0.

                    # turn the results to probabilities
                    discard_tiles /= torch.sum(discard_tiles)

                    # decide what to do
                    tid34 = discard_tiles.argmax(0)

                    discard_tile = None
                    if closed_hand_counts[curr_player_id][tid34]:
                        # find the actual tile
                        for tid136 in range(tid34 * 4 + 3, tid34 * 4 - 1, -1):
                            discard_tile = Tile(tid136)
                            if discard_tile in closed_hands[curr_player_id]:
                                break
                    else:
                        # model is confused and has no idea what to do
                        discard_tile = random.choice(closed_hands[curr_player_id])

                closed_hand_counts[curr_player_id][discard_tile.to_int()] -= 1
                closed_hands[curr_player_id].remove(discard_tile)
                discard_piles[curr_player_id].append(discard_tile)
                discard_orders[curr_player_id][discard_tile.to_int()] = turn_no

                if discard_tile.is_red5():
                    red5_closed_hand[curr_player_id][discard_tile.to_int() // 9] = 0
                    red5_discarded[discard_tile.to_int() // 9] = 1

                event = Event(EventType.TILE_DISCARDED, curr_player_id)

            case EventType.TILE_DISCARDED:
                from_who = event.who
                decision = MoveType.PASS
                tile = discard_piles[from_who][-1]

                is_chi_possible = [False] * 4
                is_pon_possible = [False] * 4
                is_kan_possible = [False] * 4
                is_ron_possible = [False] * 4
                possible_chi = [[] for _ in range(4)]
                for p in range(4):
                    if p != from_who:
                        hidden_tile_counts[p][tile.to_int()] -= 1
                        if tile.is_red5():
                            red5_hidden[p][tile.to_int() // 9] = 0

                    if tile.to_int() < 27:  # normal tiles, not wind or dragon
                        order_in_set = tile.to_int() % 9
                        if 0 < order_in_set < 8 and \
                                closed_hand_counts[p][tile.to_int() - 1] and closed_hand_counts[p][tile.to_int() + 1]:
                            possible_chi[p].append((-1, 1))
                        if order_in_set > 1 and \
                                closed_hand_counts[p][tile.to_int() - 2] and closed_hand_counts[p][tile.to_int() - 1]:
                            possible_chi[p].append((-2, -1))
                        if order_in_set < 7 and \
                                closed_hand_counts[p][tile.to_int() + 1] and closed_hand_counts[p][tile.to_int() + 2]:
                            possible_chi[p].append((1, 2))

                    is_chi_possible[p] = bool(possible_chi[p]) and not hand_in_riichi[p]
                    is_pon_possible[p] = closed_hand_counts[p][tile.to_int()] >= 2 and not hand_in_riichi[p]
                    is_kan_possible[p] = closed_hand_counts[p][tile.to_int()] == 3 and not hand_in_riichi[p]
                    if agari.Agari().is_agari(
                        [closed_hand_counts[p][i] + open_hand_counts[p][i] for i in range(34)], open_melds_tile_ids[p]):
                        tiles136 = [t.true_id() for t in closed_hands[p] + open_hands[p]]
                        win_tile136 = closed_hands[p][-1].true_id()
                        hand_result = hand_calculator.estimate_hand_value(tiles=tiles136, win_tile=win_tile136,
                                                                          melds=melds[p])
                        is_ron_possible[p] = hand_result.error is None

                wants = [MoveType.PASS for _ in range(4)]
                call_tiles = [[] for _ in range(4)]
                for p in range(4):
                    if p == from_who:
                        continue

                    if competitors[p] is None:
                        # TODO: ask player what they want in life*
                        # *limited to what is possible :/
                        pass
                    else:
                        # prepare the rest of input tensor
                        inputs = InputFeatures(device, p, non_repeat_round_no, turn_no, dealer_id, prevalent_wind,
                                               seat_wind[p], closed_hand_counts[p], open_hand_counts, discard_orders,
                                               hidden_tile_counts[p], visible_dora, hand_is_closed, hand_in_riichi,
                                               scores, red5_closed_hand[p], red5_open_hand, red5_discarded,
                                               red5_hidden[p])

                        # query the model
                        discard_tiles, call_tiles_curr, action = competitors[p].get_prediction(inputs.to_tensor())
                        call_tiles[p] = call_tiles_curr
                        action = action.clone()

                        action[0], action[3], action[5] = 0., 0., 0.
                        if not is_chi_possible[p]:
                            action[1] = 0.
                        if not is_pon_possible[p]:
                            action[2] = 0.
                        if not is_ron_possible[p]:
                            action[4] = 0
                        if not is_kan_possible[p]:
                            action[6] = 0.

                        # turn the results to probabilities
                        action /= torch.sum(action)

                        # decide what to do
                        wants[p] = MoveType(action.argmax(0).item() + 1)

                # set current_player_id to the one with prio
                if MoveType.RON in wants:
                    for p in range(4):
                        if wants[p] == MoveType.RON:
                            closed_hands[p].append(tile)

                    event = Event(EventType.WINNER, [curr_player_id, [p for p in range(4) if wants[p] == MoveType.RON]])
                    continue
                elif MoveType.KAN in wants or MoveType.PON in wants:
                    # find who
                    curr_player_id = 0
                    while wants[curr_player_id] != MoveType.KAN and wants[curr_player_id] != MoveType.PON:
                        curr_player_id += 1
                    decision = wants[curr_player_id]
                elif MoveType.CHI in wants:
                    decision = MoveType.CHI
                    # find who
                    curr_player_id = 0
                    while wants[curr_player_id] != MoveType.CHI:
                        curr_player_id += 1

                new_meld_ids = []
                match decision:
                    case MoveType.KAN:
                        i = 0
                        ctr = 0
                        meld_tiles = []
                        while i < len(closed_hands[curr_player_id]) and ctr < 3:
                            if closed_hands[curr_player_id][i].to_int() == tile.to_int():
                                meld_tiles.append(closed_hands[curr_player_id].pop(i))
                                ctr += 1
                            else:
                                i += 1
                        closed_hand_counts[curr_player_id][tile.to_int()] = 0
                        open_hand_counts[curr_player_id][tile.to_int()] = 4
                        meld_tiles.append(tile)
                        open_hands[curr_player_id].extend(meld_tiles)
                        if tile.is_red5():
                            red5_discarded[tile.to_int() // 9] = 0
                            red5_open_hand[curr_player_id][tile.to_int() // 9] = 1

                        new_meld_ids = [tile.to_int()] * 4
                        melds[curr_player_id].append(Meld(meld_type=Meld.KAN, tiles=[t.true_id() for t in meld_tiles],
                                                          opened=True, called_tile=tile.true_id(), who=curr_player_id,
                                                          from_who=from_who))

                        # reveal dora
                        dora_indicator = dora_indicators[dora_revealed_no]
                        visible_dora[dora_indicator.to_int()] += 1
                        dora_revealed_no += 1
                        for p in range(4):
                            hidden_tile_counts[p][dora_indicator.to_int()] -= 1
                            if dora_indicator.is_red5():
                                red5_hidden[p][dora_indicator.to_int() // 9] = 0

                    case MoveType.PON:
                        i = 0
                        ctr = 0
                        meld_tiles = []
                        while i < len(closed_hands[curr_player_id]) and ctr < 2:
                            if closed_hands[curr_player_id][i].to_int() == tile.to_int():
                                meld_tiles.append(closed_hands[curr_player_id].pop(i))
                                ctr += 1
                            else:
                                i += 1
                        closed_hand_counts[curr_player_id][tile.to_int()] -= 2  # you take the third one from someone
                        open_hand_counts[curr_player_id][tile.to_int()] += 3
                        meld_tiles.append(tile)
                        open_hands[curr_player_id].extend(meld_tiles)
                        if tile.is_red5():
                            red5_discarded[tile.to_int() // 9] = 0
                            red5_open_hand[curr_player_id][tile.to_int() // 9] = 1

                        new_meld_ids = [tile.to_int()] * 3
                        melds[curr_player_id].append(Meld(meld_type=Meld.PON, tiles=[t.true_id() for t in meld_tiles],
                                                          opened=True, called_tile=tile.true_id(), who=curr_player_id,
                                                          from_who=from_who))

                    case MoveType.CHI:
                        # query what chi exactly
                        if competitors[curr_player_id] is None and len(possible_chi[curr_player_id]) > 1:
                            # TODO: ask player what chi do they want
                            best_chi = (-1, 1)
                        elif competitors[curr_player_id] is not None and len(possible_chi[curr_player_id]) > 1:
                            chi_value = [0.] * len(possible_chi[curr_player_id])
                            best_chi = []
                            best_chi_value = 0.
                            for i, chi in enumerate(possible_chi[curr_player_id]):
                                for tile_id_mod in chi:
                                    chi_value[i] += float(call_tiles[curr_player_id][tile.to_int() + tile_id_mod])
                                if best_chi_value < chi_value[i]:
                                    best_chi = possible_chi[curr_player_id][i]
                        else:
                            best_chi = possible_chi[curr_player_id][0]

                        # move tiles to open hand
                        meld_tiles = []
                        for tile_id_mod in best_chi:
                            found = False
                            for tile_id in range((tile.to_int() + tile_id_mod) * 4 + 3,
                                                 (tile.to_int() + tile_id_mod) * 4 - 1, -1):
                                for i in range(len(closed_hands[curr_player_id])):
                                    if closed_hands[curr_player_id][i].true_id() == tile_id:
                                        meld_tiles.append(closed_hands[curr_player_id].pop(i))
                                        open_hand_counts[curr_player_id][tile.to_int() + tile_id_mod] += 1
                                        closed_hand_counts[curr_player_id][tile.to_int() + tile_id_mod] -= 1
                                        new_meld_ids.append(tile.to_int() + tile_id_mod)

                                        found = True
                                        break
                                if found:
                                    break

                        meld_tiles.append(tile)
                        open_hands[curr_player_id].extend(meld_tiles)
                        open_hand_counts[curr_player_id][tile.to_int()] += 1
                        new_meld_ids.append(tile.to_int())
                        melds[curr_player_id].append(Meld(meld_type=Meld.CHI, tiles=[t.true_id() for t in meld_tiles],
                                                          opened=True, called_tile=tile.true_id(), who=curr_player_id,
                                                          from_who=from_who))
                        if tile.is_red5():
                            red5_discarded[tile.to_int() // 9] = 0
                            red5_open_hand[curr_player_id][tile.to_int() // 9] = 1

                if decision != MoveType.PASS:
                    open_melds_tile_ids[curr_player_id].append(new_meld_ids)
                    hand_is_closed[curr_player_id] = 0
                    discard_piles[from_who].pop()
                    if decision == MoveType.KAN:
                        event = Event(EventType.DRAW_TILE_AFTER_KAN, curr_player_id)
                    else:
                        event = Event(EventType.DISCARD_TILE, curr_player_id)
                else:
                    event = Event(EventType.DRAW_TILE, (curr_player_id + 1) % 4)

            case EventType.ROUND_DRAW:
                # no score change, same dealer next round
                return scores, True

            case EventType.WALL_EXHAUSTED:
                has_tenpai = [0] * 4  # ready hand
                for p in range(4):
                    has_tenpai[p] = int(shanten.Shanten().calculate_shanten(closed_hand_counts[p]) <= 0)
                match sum(has_tenpai):
                    case 3:
                        for p in range(4):
                            scores[p] += 10 if has_tenpai[p] else -30
                    case 2:
                        for p in range(4):
                            scores[p] += 15 if has_tenpai[p] else -15
                    case 1:
                        for p in range(4):
                            scores[p] += 30 if has_tenpai[p] else -10
                return scores, has_tenpai[dealer_id]

            case EventType.WINNER:
                dealt_in, winners = event.who

                points_gained = [0] * 4
                for p in range(4):
                    if p in winners:
                        # TODO: track all this crap
                        # possible
                        is_tsumo = (dealt_in == -1)
                        is_riichi = hand_in_riichi[p]
                        is_ippatsu = False
                        is_rinshan = False  # after a kan
                        is_chankan = False  # robbing a kan
                        is_haitei = False  # tsumo on last tile
                        is_houtei = False  # ron on last tile
                        is_daburu_riichi = False  # double riichi

                        # pretty much impossible
                        is_nagashi_mangan = False  # wtf...? https://riichi.wiki/Nagashi_mangan
                        is_tenhou = False  # win on first draw (dealer)
                        is_renhou = False  # ron on starting hand (no draws) as a first call of the round
                        is_chiihou = False  # win on first draw, before any call (not dealer)
                        is_open_riichi = False  # what?
                        is_paarenchan = False  # if you keep dealership for 8 consecutive rounds

                        # other info
                        player_wind = wind_from_int(seat_wind[p])
                        round_wind = wind_from_int(non_repeat_round_no)
                        kyoutaku_number = 0  # ???
                        tsumi_number = 0  # ???
                        options = OptionalRules(has_aka_dora=True)

                        config = HandConfig(is_tsumo, is_riichi, is_ippatsu, is_rinshan, is_chankan, is_haitei,
                                            is_houtei, is_daburu_riichi, is_nagashi_mangan, is_tenhou, is_renhou,
                                            is_chiihou, is_open_riichi, player_wind, round_wind, kyoutaku_number,
                                            tsumi_number, is_paarenchan, options)

                        tiles136 = [t.true_id() for t in closed_hands[p] + open_hands[p]]
                        win_tile136 = closed_hands[p][-1].true_id()
                        dora_indicators136 = [t.true_id() for t in dora_indicators[:dora_revealed_no]] + \
                                             [t.true_id() for t in uradora_indicators[:dora_revealed_no]]
                        hand_result = hand_calculator.estimate_hand_value(tiles=tiles136, win_tile=win_tile136,
                                                                          melds=melds[p], config=config,
                                                                          dora_indicators=dora_indicators136)

                        if hand_result.error:
                            print(agari.Agari().is_agari(
                                [closed_hand_counts[curr_player_id][i] + open_hand_counts[curr_player_id][i] for i in
                                 range(34)],
                                open_melds_tile_ids[curr_player_id]
                            ))
                            raise Exception(hand_result.error)

                        # show result
                        print(hand_result.han, hand_result.fu)
                        print(hand_result.cost['main'])
                        print(hand_result.yaku)
                        for fu_item in hand_result.fu_details:
                            print(fu_item)
                        print('')

                        points_gained[p] = hand_result.cost['main'] // 100
                total_plus = sum(points_gained)

                if dealt_in not in winners:  # win by ron
                    points_gained[dealt_in] = -total_plus
                else:  # win by tsumo
                    for p in range(4):
                        if p in winners:
                            continue
                        if dealer_id in winners:
                            points_gained[p] = -total_plus // 3
                        elif dealer_id == p:
                            points_gained[p] = -total_plus // 2
                        else:
                            points_gained[p] = -total_plus // 4

                for p in range(4):
                    scores[p] += points_gained[p]

                return scores, dealer_id in winners


def simulate_match(competitors, seed, device):
    scores = [250, 250, 250, 250]
    random.seed(seed)
    non_repeat_round_no = 0
    round_no = 0
    while not (min(scores) <= 0 or (non_repeat_round_no >= 3 and max(scores) >= 500) or round_no >= 12):
        scores, dealer_won = simulate_round(competitors, scores, non_repeat_round_no, device)
        round_no += 1
        if not dealer_won:
            non_repeat_round_no += 1

    # limit round number - if models are too "weak" or too similar, the simulation will never end
    if round_no < 12:
        print("Match won by someone")
    else:
        print("Draw: too many rounds")

    return scores
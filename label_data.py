from mahjong_enums import MoveType
from tile import Tile
from training_data_classes import TrainingData, InputFeatures, Label
from mahjong import shanten
from parse_logs import MatchData, MoveData


def count_tiles(tiles: list[Tile]):
    counts = [0] * 34
    for tile in tiles:
        counts[tile.to_int()] += 1
    return counts


def get_data_from_replay(matches_data: list[MatchData], device):
    # features and labels to train the discard and call models
    training_data: list[TrainingData] = []

    for match_data in matches_data:
        round_no = 0
        non_repeat_round_no = 0
        prev_dealer = 0

        for round_data in match_data.rounds:
            if all(sc_change == 0 for sc_change in round_data.score_change):
                # not interesting, skip
                continue

            closed_hand: list[list[Tile]] = round_data.init_hands.copy()
            open_hand: list[list[Tile]] = [[] for _ in range(4)]
            discard_pile: list[list[Tile]] = [[] for _ in range(4)]
            discard_orders = [[0] * 34 for _ in range(4)]
            hand_in_riichi = [0] * 4
            hand_is_closed = [1] * 4
            visible_dora_ind = [0] * 34
            visible_dora_ind[round_data.initial_dora.to_int()] = 1
            curr_player_id = round_data.dealer
            prev_player_id = curr_player_id
            turn_no = 0

            for move_i, move_data in enumerate(round_data.moves):
                if move_data.player_id is not None:
                    curr_player_id = move_data.player_id

                # initialize data point when not drawing a tile, the player didn't deal in, and is not in riichi
                data_point: None | TrainingData = None
                if move_data.move_type != MoveType.DRAW and curr_player_id != round_data.dealt_in \
                        and (not hand_in_riichi[curr_player_id] or move_data.move_type == MoveType.TSUMO or
                             move_data.move_type == MoveType.RON):
                    label_discard_tile = [0] * 34
                    label_call_tile = [0] * 34
                    label_move_type = [0] * 8

                    if move_data.move_type == MoveType.DISCARD:
                        label_discard_tile[move_data.tile.to_int()] = 1
                    if move_data.move_type != MoveType.DRAW:
                        label_move_type[move_data.move_type.value - 1] = 1
                    if move_data.move_type == MoveType.CHI or move_data.move_type == MoveType.PON or \
                            move_data.move_type == MoveType.KAN:
                        for tile in move_data.base:
                            label_call_tile[tile.to_int()] = 1

                    data_point = TrainingData(None, Label(label_discard_tile, label_call_tile, label_move_type, device),
                                              device)
                    training_data.append(data_point)

                open_hand_counts = [count_tiles(open_hand[i]) for i in range(4)]
                closed_hand_counts = [count_tiles(closed_hand[i]) for i in range(4)]
                if data_point is not None:
                    # EXTRACT FEATURES
                    prevalent_wind = (match_data.rounds[0].dealer + (non_repeat_round_no // 4)) % 4
                    seat_wind = (curr_player_id + non_repeat_round_no) % 4

                    discard_counts = [count_tiles(pile) for pile in discard_pile]
                    hidden_tile_counts = [0] * 34
                    for tile in range(34):
                        hidden_tile_counts[tile] = 4 - closed_hand_counts[curr_player_id][tile] - visible_dora_ind[tile]
                        for p in range(4):
                            hidden_tile_counts[tile] -= (discard_counts[p][tile] + open_hand_counts[p][tile])

                    red5_closed_hand = [0] * 3
                    red5_open_hand = [[0] * 3 for _ in range(4)]
                    red5_discarded = [0] * 3
                    red5_hidden = [0] * 3
                    for tile in closed_hand[curr_player_id]:
                        if tile.is_red5():
                            red5_closed_hand[tile.to_int() // 9] = 1
                    for p in range(4):
                        for tile in discard_pile[p]:
                            if tile.is_red5():
                                red5_discarded[tile.to_int() // 9] = 1
                        for tile in open_hand[p]:
                            if tile.is_red5():
                                red5_open_hand[p][tile.to_int() // 9] = 1
                    for red in range(3):
                        red5_hidden[red] = 1 - red5_discarded[red] - red5_closed_hand[red]
                        for p in range(4):
                            red5_hidden[red] -= red5_open_hand[p][red]

                    tile_to_call = None
                    tile_origin = None
                    if move_data.tile is not None:
                        tile_to_call = move_data.tile.to_int()
                        tile_origin = prev_player_id

                    data_point.inputs = InputFeatures.from_args(
                        device, curr_player_id, round_no, turn_no, round_data.dealer, prevalent_wind, seat_wind,
                        closed_hand_counts[curr_player_id], open_hand_counts, discard_orders, hidden_tile_counts,
                        visible_dora_ind, hand_is_closed, hand_in_riichi, round_data.score_before, red5_closed_hand,
                        red5_open_hand, red5_discarded, red5_hidden, tile_to_call, tile_origin,
                        augment=True, move_type=move_data.move_type)
                    data_point.set_weight(move_data.move_type, turn_no, hand_in_riichi)

                    augmented_data = [TrainingData(augmented_features, data_point.label, device, data_point.pos_weight)
                                      for augmented_features in data_point.inputs.augmented_features]

                    training_data.extend(augmented_data)
                    # end inputs

                # GAME LOGIC
                match move_data.move_type:
                    case MoveType.DRAW:
                        closed_hand[curr_player_id].append(move_data.tile)

                    case MoveType.DISCARD:
                        closed_hand[curr_player_id].remove(move_data.tile)
                        discard_pile[curr_player_id].append(move_data.tile)
                        discard_orders[curr_player_id][move_data.tile.to_int()] = turn_no + 1

                    case MoveType.CHI | MoveType.PON | MoveType.KAN:
                        if move_data.move_type == MoveType.KAN and \
                                open_hand_counts[curr_player_id][move_data.tile.to_int()] == 3:  # added kan
                            open_hand[curr_player_id].append(move_data.tile)
                            closed_hand[curr_player_id].remove(move_data.tile)
                        else:
                            for base_tile in move_data.base:
                                if base_tile in closed_hand:
                                    closed_hand[curr_player_id].remove(base_tile)
                            open_hand[curr_player_id].extend(move_data.base)

                        if move_data.dora_revealed_ind is not None:
                            visible_dora_ind[move_data.dora_revealed_ind.to_int()] += 1
                        if move_data.move_type != MoveType.KAN or move_data.player_id != curr_player_id:  # not self-kan
                            hand_is_closed[curr_player_id] = 0
                            discard_pile[prev_player_id].remove(move_data.tile)

                    case MoveType.RIICHI:
                        hand_in_riichi[curr_player_id] = turn_no

                    case _:
                        pass

                # CHECK IF ANY CALL WAS PASSED ON
                if len(round_data.moves) == move_i + 1:
                    continue

                # RIICHI, TSUMO
                if len(open_hand[curr_player_id]) == 0 and move_data.move_type == MoveType.DRAW and not hand_in_riichi[
                    curr_player_id]:
                    closed_hand_count = count_tiles(closed_hand[curr_player_id])

                    shanten_cnt = shanten.Shanten().calculate_shanten(closed_hand_count)
                    if (shanten_cnt == -1 and round_data.moves[move_i + 1].move_type != MoveType.TSUMO) or \
                            (shanten_cnt == 0 and round_data.moves[move_i + 1].move_type != MoveType.RIICHI):
                        new_action = MoveData()
                        new_action.move_type = MoveType.PASS
                        new_action.tile = move_data.tile
                        new_action.player_id = curr_player_id

                        round_data.moves.insert(move_i + 1, new_action)

                # CHI, PON, KAN (assumes RON won't be passed on)
                if move_data.move_type == MoveType.DISCARD and (round_data.moves[move_i + 1].tile is None or
                                                                round_data.moves[move_i + 1].tile.true_id !=
                                                                move_data.tile.true_id):
                    for p in range(4):
                        if p == curr_player_id or hand_in_riichi[p]:
                            continue

                        tile_id = move_data.tile.to_int()
                        potential_chi = []
                        if tile_id < 27:  # normal tiles, not wind or dragon
                            order_in_set = tile_id % 9
                            if 0 < order_in_set < 8:
                                potential_chi.append((-1, 1))
                            if order_in_set > 1:
                                potential_chi.append((-2, -1))
                            if order_in_set < 7:
                                potential_chi.append((1, 2))

                        possible = False
                        for chi in potential_chi:
                            possible = True
                            for mod in chi:
                                if not closed_hand_counts[p][tile_id + mod]:
                                    possible = False
                                    break
                            if possible:
                                break

                        if closed_hand_counts[p][tile_id] >= 2:
                            possible = True

                        if possible:
                            new_action = MoveData()
                            new_action.move_type = MoveType.PASS
                            new_action.tile = move_data.tile
                            new_action.player_id = p

                            round_data.moves.insert(move_i + 1, new_action)

                if move_data.move_type == MoveType.DISCARD:
                    turn_no += 1
                    prev_player_id = curr_player_id
                    curr_player_id = (curr_player_id + 1) % 4
                # end move

            if round_no == 0 or round_data.dealer != prev_dealer:
                non_repeat_round_no += 1
            round_no += 1
            prev_dealer = round_data.dealer

    return training_data

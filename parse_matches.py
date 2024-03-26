import os
import random
import sqlite3
import gzip
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import re
from enum import Enum
from mahjong import shanten
import torch


class Tile:
    def __init__(self, tile_id):
        self.id = tile_id

    def true_id(self):
        return self.id

    def to_int(self):
        return self.id // 4

    def is_red5(self):
        return self.to_int() < 27 and self.to_int() % 9 == 4 and self.id % 4 == 0

    def __str__(self):
        # only for debugging
        return """
            1m 2m 3m 4m 5m 6m 7m 8m 9m
            1p 2p 3p 4p 5p 6p 7p 8p 9p
            1s 2s 3s 4s 5s 6s 7s 8s 9s
            ew sw ww nw
            wd gd rd
        """.split()[self.id // 4]

    def __eq__(self, other):
        if type(other) != Tile:
            return False
        return self.id == other.id


class MoveType(Enum):
    DRAW = 0
    DISCARD = 1
    CHI = 2
    PON = 3
    RIICHI = 4
    RON = 5
    TSUMO = 6
    KAN = 7
    PASS = 8

    def __str__(self):
        return self.name


class MoveData:
    def __init__(self):
        self.move_type = None
        self.tile: Tile | None = None  # used for DRAW, DISCARD, CHI, PON, KAN
        self.base: list[Tile] = []  # only used for CHI, PON, KAN
        self.dora_revealed_ind: Tile | None = None  # only used for KAN
        self.player_id = None


class RoundData:
    def __init__(self, dealer):
        self.moves: list[MoveData] = []
        self.dealer = dealer
        self.dealt_in: int | None = None  # id of player who dealt in, not None only for RON
        self.dora_ind = []
        self.revealed_dora_ind = []
        self.uradora = []
        self.score_before = [0] * 4
        self.score_change = [0] * 4
        self.init_hands: list[list[Tile]] = [[] for _ in range(4)]


class MatchData:
    def __init__(self):
        self.rounds: list[RoundData] = []


def parse_xml(xml_data):
    decoded_xml_data = xml_data.decode('utf-8')
    root = ET.fromstring(decoded_xml_data)

    def decode_url_encoded_attributes(element):
        for key, value in element.items():
            decoded_value = unquote(value)
            element.set(key, decoded_value)

        for child in element:
            decode_url_encoded_attributes(child)

    decode_url_encoded_attributes(root)
    return root


def decode_chi(data, move_info: MoveData):
    t0, t1, t2 = (data >> 3) & 0x3, (data >> 5) & 0x3, (data >> 7) & 0x3
    base_and_called = data >> 10
    called = base_and_called % 3
    base = base_and_called // 3
    base = (base // 7) * 9 + base % 7
    tiles = Tile(t0 + 4 * (base + 0)), Tile(t1 + 4 * (base + 1)), Tile(t2 + 4 * (base + 2))

    move_info.move_type = MoveType.CHI
    move_info.tile = tiles[called]
    move_info.base = tiles


def decode_pon(data, move_info: MoveData):
    t4 = (data >> 5) & 0x3
    t0, t1, t2 = ((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2))[t4]
    base_and_called = data >> 9
    called = base_and_called % 3
    base = base_and_called // 3
    if data & 0x8:
        tiles = Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base)
        move_info.move_type = MoveType.PON
    else:
        tiles = Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base), Tile(t4 + 4 * base)
        # move_info.move_type = MoveType.CHAKAN
        move_info.move_type = MoveType.PASS
    move_info.tile = tiles[called]
    move_info.base = tiles


def decode_kan(data, move_info: MoveData):
    base_and_called = data >> 8
    base = base_and_called // 4
    tiles = Tile(4 * base), Tile(1 + 4 * base), Tile(2 + 4 * base), Tile(3 + 4 * base)

    move_info.move_type = MoveType.KAN
    move_info.tile = tiles[0]
    move_info.base = tiles


def parse_match_log(log_raw):
    match_xml = gzip.decompress(log_raw)
    match_parsed = parse_xml(match_xml)

    match_info = MatchData()

    draw_regex = re.compile("[T-W][0-9]+")
    discard_regex = re.compile("[D-G][0-9]+")

    for event in match_parsed.iter():
        match event.tag:
            case "INIT":  # start round
                new_round = RoundData(int(event.attrib["oya"]))
                for i in range(4):
                    new_round.init_hands[i] = [Tile(int(t)) for t in event.attrib["hai{}".format(i)].split(',')]
                match_info.rounds.append(new_round)
                # TODO: apparently attrib "seed" (list), 6th (last) argument is dora

            case "N":  # call
                new_move = MoveData()
                data = int(event.attrib["m"])
                if data & 0x4:
                    decode_chi(data, new_move)
                elif data & 0x18:
                    decode_pon(data, new_move)
                elif data & 0x20:
                    # what is a nuki (probably 3 player stuff)
                    pass
                else:
                    decode_kan(data, new_move)
                new_move.player_id = int(event.attrib["who"])
                match_info.rounds[-1].moves.append(new_move)

            case "REACH":  # riichi
                if int(event.attrib["step"]) == 2:
                    continue

                new_move = MoveData()
                new_move.move_type = MoveType.RIICHI
                match_info.rounds[-1].moves.append(new_move)
                # tile None base []

            case "DORA":  # dora revealed (after kan)
                match_info.rounds[-1].moves[-1].dora_revealed_ind = Tile(int(event.attrib["hai"]))
                match_info.rounds[-1].revealed_dora_ind.append(Tile(int(event.attrib["hai"])))

            case "AGARI":  # round finishes with someone winning
                new_move = MoveData()
                if int(event.attrib["who"]) == int(event.attrib["fromWho"]):
                    new_move.move_type = MoveType.TSUMO
                else:
                    new_move.move_type = MoveType.RON
                    match_info.rounds[-1].dealt_in = int(event.attrib["fromWho"])
                match_info.rounds[-1].moves.append(new_move)

                match_info.rounds[-1].score_before = [int(score) for score in event.attrib["sc"].split(',')][::2]
                match_info.rounds[-1].score_change = [int(score) for score in event.attrib["sc"].split(',')][1::2]
                if "doraHai" in event.attrib.keys():
                    match_info.rounds[-1].dora_ind = [Tile(int(t)) for t in event.attrib["doraHai"].split(',')]
                if "doraHaiUra" in event.attrib.keys():
                    match_info.rounds[-1].uradora = [Tile(int(t)) for t in event.attrib["doraHaiUra"].split(',')]

            case "RYUUKYOKU":  # round finishes with a draw
                match_info.rounds[-1].score_before = [int(score) for score in event.attrib["sc"].split(',')][::2]
                match_info.rounds[-1].score_change = [int(score) for score in event.attrib["sc"].split(',')][1::2]
                if "doraHai" in event.attrib.keys():
                    match_info.rounds[-1].dora_ind = [Tile(int(t)) for t in event.attrib["doraHai"].split(',')]
                if "doraHaiUra" in event.attrib.keys():
                    match_info.rounds[-1].dora_ind = [Tile(int(t)) for t in event.attrib["doraHaiUra"].split(',')]

            case _:
                if draw_regex.search(event.tag):  # draw tile
                    new_move = MoveData()
                    new_move.move_type = MoveType.DRAW
                    new_move.tile = Tile(int(event.tag[1:]))
                    new_move.player_id = ord(event.tag[0]) - ord("T")
                    match_info.rounds[-1].moves.append(new_move)
                elif discard_regex.search(event.tag):  # discard tile
                    new_move = MoveData()
                    new_move.move_type = MoveType.DISCARD
                    new_move.tile = Tile(int(event.tag[1:]))
                    new_move.player_id = ord(event.tag[0]) - ord("D")
                    match_info.rounds[-1].moves.append(new_move)

    return match_info


def get_match_log_data(db_dir, year):
    db_file = str(year) + ".db"
    if db_file in os.listdir(db_dir):
        db_path = os.path.join(db_dir, db_file)
        connection = sqlite3.connect(db_path)
        with connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM logs WHERE is_processed != 0 AND is_sanma = 0 AND was_error = 0;")
            match_no = cursor.fetchone()[0]

            cursor.execute("SELECT log_content FROM logs WHERE is_processed != 0 AND is_sanma = 0 AND was_error = 0;")
            return cursor, match_no
    else:
        raise Exception(f"No database for year {year}.")


def roll_list_backwards(lst, roll_by):
    if lst is None:
        return None
    return lst[roll_by:] + lst[:roll_by]


class Label:
    def __init__(self, discard_tile, call_tile, move_type, device):
        self.discard_tile = torch.tensor(discard_tile, device=device, dtype=torch.float32)
        self.call_tile = torch.tensor(call_tile, device=device, dtype=torch.float32)
        self.move_type = torch.tensor(move_type, device=device, dtype=torch.float32)

    def to_tensor(self):
        return torch.cat((self.discard_tile, self.call_tile, self.move_type))


class InputFeatures:
    def __init__(self, device, seat, round_no, turn_no, dealer, prevalent_wind, seat_wind, closed_hand_counts,
                 open_hand_counts, discard_pile_orders, hidden_tile_counts, dora_indicator_counts, hand_is_closed,
                 hand_in_riichi, scores, red5_closed_hand, red5_open_hand, red5_discarded, red5_hidden,
                 tile_to_call=None, tile_origin=None):
        dealer_arr = [0]*4
        dealer_arr[dealer] = 1
        prev_wind_arr = [0]*4
        prev_wind_arr[prevalent_wind] = 1
        seat_wind_arr = [0]*4
        seat_wind_arr[seat_wind] = 1
        tile_to_call_arr = [0]*34
        if tile_to_call is not None:
            tile_to_call_arr[tile_to_call] = 1
        tile_origin_arr = [0]*4
        if tile_origin is not None:
            tile_origin_arr[tile_origin] = 1

        if seat:
            roll_list_backwards(dealer_arr, seat)
            roll_list_backwards(open_hand_counts, seat)
            roll_list_backwards(discard_pile_orders, seat)
            roll_list_backwards(hand_is_closed, seat)
            roll_list_backwards(hand_in_riichi, seat)
            roll_list_backwards(scores, seat)
            roll_list_backwards(red5_open_hand, seat)
            roll_list_backwards(tile_origin_arr, seat)

        self.round = torch.tensor([round_no], device=device, dtype=torch.float32)
        self.turn = torch.tensor([turn_no], device=device, dtype=torch.float32)
        self.dealer = torch.tensor(dealer_arr, device=device, dtype=torch.float32)
        self.prevalent_wind = torch.tensor(prev_wind_arr, device=device, dtype=torch.float32)
        self.seat_wind = torch.tensor(seat_wind_arr, device=device, dtype=torch.float32)
        self.closed_hand = torch.tensor(closed_hand_counts, device=device, dtype=torch.float32)
        self.open_hands = torch.tensor(open_hand_counts, device=device, dtype=torch.float32)
        self.discard_piles = torch.tensor(discard_pile_orders, device=device, dtype=torch.float32)
        self.hidden_tiles = torch.tensor(hidden_tile_counts, device=device, dtype=torch.float32)
        self.visible_dora = torch.tensor(dora_indicator_counts, device=device, dtype=torch.float32)
        self.hand_is_closed = torch.tensor(hand_is_closed, device=device, dtype=torch.float32)
        self.hand_in_riichi = torch.tensor(hand_in_riichi, device=device, dtype=torch.float32)
        self.scores = torch.tensor(scores, device=device, dtype=torch.float32)
        self.red5_closed_hand = torch.tensor(red5_closed_hand, device=device, dtype=torch.float32)
        self.red5_open_hand = torch.tensor(red5_open_hand, device=device, dtype=torch.float32)
        self.red5_discarded = torch.tensor(red5_discarded, device=device, dtype=torch.float32)
        self.red5_hidden = torch.tensor(red5_hidden, device=device, dtype=torch.float32)
        self.tile_to_call = torch.tensor(tile_to_call_arr, device=device, dtype=torch.float32)
        self.tile_origin = torch.tensor(tile_origin_arr, device=device, dtype=torch.float32)

    def to_tensor(self):
        return torch.cat((self.round, self.turn, self.dealer, self.prevalent_wind, self.seat_wind, self.closed_hand,
                          self.open_hands.flatten(), self.discard_piles.flatten(), self.hidden_tiles, self.visible_dora,
                          self.hand_is_closed, self.hand_in_riichi, self.scores, self.red5_closed_hand,
                          self.red5_open_hand.flatten(), self.red5_discarded, self.red5_hidden, self.tile_to_call,
                          self.tile_origin))


class TrainingData:
    def __init__(self, inputs, label, device):
        self.inputs: InputFeatures = inputs
        self.label: Label = label
        self.input_tensor = torch.empty(0, dtype=torch.float32)
        self.label_tensor = torch.empty(0, dtype=torch.float32)
        self.device = device

    def proc(self):
        self.input_tensor = self.inputs.to_tensor()
        self.label_tensor = self.label.to_tensor()

    def to(self, device):
        self.input_tensor = self.input_tensor.to(device)
        self.label_tensor = self.label_tensor.to(device)


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
            discard_orders = [[0]*34 for _ in range(4)]
            hand_in_riichi = [0]*4
            hand_is_closed = [1]*4
            visible_dora_ind = [0] * 34
            for dora in round_data.dora_ind:
                if dora not in round_data.revealed_dora_ind:
                    visible_dora_ind[dora.to_int()] = 1
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
                    label_discard_tile = [0]*34
                    label_call_tile = [0]*34
                    label_move_type = [0]*8

                    if move_data.move_type == MoveType.DISCARD:
                        label_discard_tile[move_data.tile.to_int()] = 1
                    if move_data.move_type != MoveType.DRAW:
                        label_move_type[move_data.move_type.value-1] = 1
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
                    prevalent_wind = (non_repeat_round_no // 4) % 4
                    seat_wind = non_repeat_round_no % 4

                    discard_counts = [count_tiles(pile) for pile in discard_pile]
                    hidden_tile_counts = [0] * 34
                    for tile in range(34):
                        hidden_tile_counts[tile] = 4 - closed_hand_counts[curr_player_id][tile] - visible_dora_ind[tile]
                        for p in range(4):
                            hidden_tile_counts[tile] -= (discard_counts[p][tile] + open_hand_counts[p][tile])

                    red5_closed_hand = [0]*3
                    red5_open_hand = [[0]*3 for _ in range(4)]
                    red5_discarded = [0]*3
                    red5_hidden = [0]*3
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

                    training_inputs = InputFeatures(device, curr_player_id, round_no, turn_no, round_data.dealer,
                                                    prevalent_wind, seat_wind, closed_hand_counts[curr_player_id],
                                                    open_hand_counts, discard_orders, hidden_tile_counts,
                                                    visible_dora_ind, hand_is_closed, hand_in_riichi,
                                                    round_data.score_before, red5_closed_hand, red5_open_hand,
                                                    red5_discarded, red5_hidden, tile_to_call, tile_origin)
                    data_point.inputs = training_inputs
                    data_point.set_weight(move_data.move_type)
                    data_point.proc()
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
                if len(open_hand[curr_player_id]) == 0 and move_data.move_type == MoveType.DRAW and not hand_in_riichi[curr_player_id]:
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


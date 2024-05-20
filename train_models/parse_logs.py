import gzip
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import re
from game.mahjong_enums import MoveType
from game.tile import Tile


class MoveData:
    def __init__(self):
        self.move_type = None
        self.tile: Tile | None = None  # used for DRAW, DISCARD, CHI, PON, KAN
        self.base: list[Tile] = []  # only used for CHI, PON, KAN
        self.dora_revealed_ind: Tile | None = None  # only used for KAN
        self.player_id = None


class RoundData:
    def __init__(self, dealer, initial_dora):
        self.moves: list[MoveData] = []
        self.dealer = dealer
        self.dealt_in: int | None = None  # id of player who dealt in, not None only for RON
        self.initial_dora: Tile = initial_dora
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
            # reference: https://m77.hatenablog.com/entry/2017/05/21/214529 (yes, seriously)

            case "GO":
                if "type" in event.attrib.keys():
                    match_type = int(event.attrib["type"])
                    wanted_bits = 0b0000_0000_0001
                    unwanted_bits = 0b1111_0001_0110
                    # don't care about the rest

                    if not((match_type & wanted_bits) == wanted_bits and (match_type & unwanted_bits) == 0):
                        # table settings aren't suitable for training
                        return match_info

            case "UN":
                if "dan" in event.attrib.keys():
                    if max(int(rank) for rank in event.attrib["dan"].split(',')) <= 17:
                        # filter low rank games
                        return match_info

            case "INIT":  # start round
                new_round = RoundData(int(event.attrib["oya"]), Tile(int(event.attrib["seed"][-1])))
                for i in range(4):
                    new_round.init_hands[i] = [Tile(int(t)) for t in event.attrib["hai{}".format(i)].split(',')]
                match_info.rounds.append(new_round)

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
                    match_info.rounds[-1].uradora = [Tile(int(t)) for t in event.attrib["doraHai"].split(',')]
                if "doraHaiUra" in event.attrib.keys():
                    match_info.rounds[-1].uradora += [Tile(int(t)) for t in event.attrib["doraHaiUra"].split(',')]

            case "RYUUKYOKU":  # round finishes with a draw
                match_info.rounds[-1].score_before = [int(score) for score in event.attrib["sc"].split(',')][::2]
                match_info.rounds[-1].score_change = [int(score) for score in event.attrib["sc"].split(',')][1::2]
                if "doraHai" in event.attrib.keys():
                    match_info.rounds[-1].uradora = [Tile(int(t)) for t in event.attrib["doraHai"].split(',')]
                if "doraHaiUra" in event.attrib.keys():
                    match_info.rounds[-1].uradora += [Tile(int(t)) for t in event.attrib["doraHaiUra"].split(',')]

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

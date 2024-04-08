import torch
from mahjong_enums import MoveType


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
        self.pos_weight = torch.empty(0, dtype=torch.float32)
        self.device = device

    def set_weight(self, move_type: MoveType):
        match move_type:
            case MoveType.DISCARD | MoveType.PASS:
                discard_weight = 0.5 + self.inputs.turn[0] * 0.01
                call_weight = 0.
                action_weight = 1.
            case MoveType.CHI | MoveType.PON | MoveType.KAN:
                discard_weight = 0.
                call_weight = 1.
                action_weight = 2.
            case _:  # RIICHI, RON, TSUMO
                discard_weight = 0.
                call_weight = 0.
                action_weight = 2.

        multiplier = 1. + torch.sum(self.inputs.hand_in_riichi) * 0.5
        discard_weight *= multiplier
        call_weight *= multiplier
        action_weight *= multiplier

        weights = [discard_weight]*34 + [call_weight]*34 + [action_weight]*8
        self.pos_weight = torch.tensor(weights, device=self.device, dtype=torch.float32)

    def proc(self):
        self.input_tensor = self.inputs.to_tensor()
        self.label_tensor = self.label.to_tensor()

    def to(self, device):
        self.input_tensor = self.input_tensor.to(device)
        self.label_tensor = self.label_tensor.to(device)
        self.pos_weight = self.pos_weight.to(device)

import torch
from random import randint
from game.mahjong_enums import MoveType


def roll_list_backwards(lst, roll_by):
    if lst is None:
        return None
    return lst[roll_by:] + lst[:roll_by]


def flatten_list(lst):
    return [elem for sublist in lst for elem in sublist]


class Label:
    def __init__(self, discard_tile, call_tile, action, device):
        self.tensor = torch.tensor((discard_tile + call_tile + action), device=device, dtype=torch.float32)


class InputFeatures:
    def __init__(self, tensor: torch.Tensor, augmented=None):
        self.tensor = tensor
        self.augmented_features: list[InputFeatures] = augmented if augmented is not None else []

    @classmethod
    def from_args(cls, device, seat, round_no, turn_no, dealer, prevalent_wind, seat_wind, closed_hand_counts,
                  open_hand_counts, discard_pile_orders, hidden_tile_counts, dora_indicator_counts, hand_is_closed,
                  hand_in_riichi, scores, red5_closed_hand, red5_open_hand, red5_discarded, red5_hidden,
                  tile_to_call=None, tile_origin=None, augment=False, move_type=MoveType.PASS):
        dealer_arr = [0] * 4
        dealer_arr[dealer] = 1
        prev_wind_arr = [0] * 4
        prev_wind_arr[prevalent_wind] = 1
        seat_wind_arr = [0] * 4
        seat_wind_arr[seat_wind] = 1
        tile_to_call_arr = [0] * 34
        if tile_to_call is not None:
            tile_to_call_arr[tile_to_call] = 1
        tile_origin_arr = [0] * 4
        if tile_origin is not None:
            tile_origin_arr[tile_origin] = 1

        if seat:
            dealer_arr = roll_list_backwards(dealer_arr, seat)
            open_hand_counts = roll_list_backwards(open_hand_counts, seat)
            discard_pile_orders = roll_list_backwards(discard_pile_orders, seat)
            hand_is_closed = roll_list_backwards(hand_is_closed, seat)
            hand_in_riichi = roll_list_backwards(hand_in_riichi, seat)
            scores = roll_list_backwards(scores, seat)
            red5_open_hand = roll_list_backwards(red5_open_hand, seat)
            tile_origin_arr = roll_list_backwards(tile_origin_arr, seat)

        open_hand_counts = flatten_list(open_hand_counts)
        discard_pile_orders = flatten_list(discard_pile_orders)
        red5_open_hand = flatten_list(red5_open_hand)

        tensor = torch.tensor(([round_no] + [turn_no] + dealer_arr + prev_wind_arr + seat_wind_arr +
                               closed_hand_counts + open_hand_counts + discard_pile_orders +
                               hidden_tile_counts + dora_indicator_counts + hand_is_closed + hand_in_riichi +
                               scores + red5_closed_hand + red5_open_hand + red5_discarded +
                               red5_hidden + tile_to_call_arr + tile_origin_arr),
                              device=device, dtype=torch.float32)

        if not augment:
            return cls(tensor)

        # augment the minority class samples
        match move_type:
            case MoveType.CHI | MoveType.PON:
                how_many = 6
            case MoveType.RIICHI | MoveType.KAN | MoveType.TSUMO | MoveType.RON:
                how_many = 12
            case _:
                return cls(tensor)

        def shuffle_discards(discard_orders_flat):
            for a in range(20):
                # shuffle discards only amongst player p (discards don't change owners, just orders)
                p = a % 4
                i0 = randint(0, 33)
                i1 = randint(0, 33)
                if discard_orders_flat[p * 34 + i0] and discard_orders_flat[p * 34 + i1]:
                    discard_orders_flat[p * 34 + i0], discard_orders_flat[p * 34 + i1] = \
                        discard_orders_flat[p * 34 + i1], discard_orders_flat[p * 34 + i0]
            return discard_orders_flat

        augmented_features = [
            cls(torch.tensor(([round_no] + [turn_no] + dealer_arr + prev_wind_arr + seat_wind_arr + closed_hand_counts +
                              open_hand_counts + shuffle_discards(discard_pile_orders) + hidden_tile_counts +
                              dora_indicator_counts + hand_is_closed + hand_in_riichi + scores + red5_closed_hand +
                              red5_open_hand + red5_discarded + red5_hidden + tile_to_call_arr + tile_origin_arr),
                             device=device, dtype=torch.float32))
            for _ in range(how_many)]

        return cls(tensor, augmented_features)


class TrainingData:
    def __init__(self, inputs, label, device, pos_weight=None):
        self.inputs: InputFeatures = inputs
        self.label: Label = label
        self.pos_weight = pos_weight if pos_weight is not None else torch.empty(0, dtype=torch.float32)
        self.device = device

    def set_weight(self, move_type: MoveType, turn_no, hand_in_riichi):
        match move_type:
            case MoveType.DISCARD | MoveType.PASS:
                discard_weight = 1.
                call_weight = 0.
                action_weight = 1.
            case MoveType.CHI | MoveType.PON | MoveType.KAN:
                discard_weight = 0.
                call_weight = 1.
                action_weight = 5.
            case _:  # RIICHI, RON, TSUMO
                discard_weight = 0.
                call_weight = 0.
                action_weight = 12.

        multiplier = 1. + sum(hand_in_riichi) * 0.5 + turn_no * 0.01
        discard_weight *= multiplier
        call_weight *= multiplier
        action_weight *= multiplier

        weights = [discard_weight] * 34 + [call_weight] * 34 + [action_weight] * 8
        self.pos_weight = torch.tensor(weights, device=self.device, dtype=torch.float32)

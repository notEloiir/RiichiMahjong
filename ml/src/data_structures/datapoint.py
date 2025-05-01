import numpy as np

from game.src.core.mahjong_enums import MoveType


def roll_list_backwards(lst, roll_by):
    if lst is None:
        return None
    return lst[roll_by:] + lst[:roll_by]


def flatten_list(lst):
    return [elem for sublist in lst for elem in sublist]


class DataPoint:
    input_size = 459
    label_split = (34, 34, len(MoveType))
    label_size = sum(label_split)

    features: np.ndarray
    labels: np.ndarray

    def __init__(self):
        self.features = np.empty(0, dtype=np.float32)
        self.labels = np.empty(0, dtype=np.float32)

    def load_input(self, seat, round_no, turn_no, dealer, prevalent_wind, seat_wind,
                   closed_hand_counts, open_hand_counts, discard_pile_orders,
                   hidden_tile_counts, dora_indicator_counts, hand_is_closed, hand_in_riichi,
                   scores, red5_closed_hand, red5_open_hand, red5_discarded, red5_hidden,
                   tile_to_call=None, tile_origin=None) -> None:
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

        self.features = np.array(
            ([round_no] + [turn_no] + dealer_arr + prev_wind_arr + seat_wind_arr +
            closed_hand_counts + open_hand_counts + discard_pile_orders +
            hidden_tile_counts + dora_indicator_counts + hand_is_closed + hand_in_riichi +
            scores + red5_closed_hand + red5_open_hand + red5_discarded +
            red5_hidden + tile_to_call_arr + tile_origin_arr),
            dtype=np.float32
        )

    def load_labels(self, discard_tile, call_tile, action):
        self.labels = np.array((discard_tile + call_tile + action), dtype=np.float32)

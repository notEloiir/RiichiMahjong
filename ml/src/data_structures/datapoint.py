import numpy as np
import torch


def roll_list_backwards(lst, roll_by):
    if lst is None:
        return None
    return lst[roll_by:] + lst[:roll_by]


def flatten_list(lst):
    return [elem for sublist in lst for elem in sublist]


class DataPoint:
    def __init__(self):
        self.features = np.empty(0, dtype=np.float32)
        self.labels = np.empty(3, dtype=np.int64)

    def load_features(self, seat, round_no, turn_no, dealer, prevalent_wind, seat_wind,
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

    def load_labels(self, discard_tile, which_chi, action):
        ignore_index = -100.  # Default ignore_index for torch.nn.CrossEntropyLoss

        self.labels[0] = discard_tile.id34() if discard_tile is not None else ignore_index
        self.labels[1] = which_chi.index(max(which_chi)) if which_chi is not None else ignore_index
        self.labels[2] = action.value if action is not None else ignore_index

    def torch_features(self) -> torch.Tensor:
        return torch.from_numpy(self.features)

    def torch_labels(self) -> torch.Tensor:
        return torch.from_numpy(self.labels)

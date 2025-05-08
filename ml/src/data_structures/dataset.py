import os
import uuid
import numpy as np
import torch
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds

from .datapoint import DataPoint
from game.src.core.mahjong_enums import MoveType

class DataSet:
    feature_columns = \
        ["round_no", "turn_no"] + \
        [f"dealer_{p}" for p in range(4)] + \
        [f"prevalent_wind_{p}" for p in range(4)] + \
        [f"seat_wind_{p}" for p in range(4)] + \
        [f"closed_hand_counts_{i}" for i in range(34)] + \
        [f"open_hand_counts_{i // 34}_{i % 34}" for i in range(4 * 34)] + \
        [f"discard_pile_orders_{i // 34}_{i % 34}" for i in range(4 * 34)] + \
        [f"hidden_hand_counts_{i}" for i in range(34)] + \
        [f"dora_indicator_counts_{i}" for i in range(34)] + \
        [f"hand_is_closed_{p}" for p in range(4)] + \
        [f"hand_in_riichi_{p}" for p in range(4)] + \
        [f"score_{p}" for p in range(4)] + \
        [f"red5_closed_hand_{i}" for i in range(3)] + \
        [f"red5_open_hand_{i // 3}_{i % 3}" for i in range(4 * 3)] + \
        [f"red5_discarded_{i}" for i in range(3)] + \
        [f"red5_hidden_{i}" for i in range(3)] + \
        [f"tile_to_call_{i}" for i in range(34)] + \
        [f"tile_origin_{p}" for p in range(4)]
    label_columns = \
        [f"discard_tile_{i}" for i in range(34)] + \
        [f"which_chi_{i}" for i in range(3)] + \
        [f"action_{i}" for i in range(len(MoveType))]
    label_sizes = (34, 3, len(MoveType))
    label_split = (34, 34 + 3)
    columns = feature_columns + label_columns
    n_features = len(feature_columns)
    n_labels = len(label_columns)

    def __init__(self, data_dir: str, device: torch.device = torch.device("cpu"), batch_size: int = 256):
        self.data_dir = data_dir
        self.device = device
        self.batch_size = batch_size

        # build a Dataset over all parquet files in the directory
        self._dataset = ds.dataset(data_dir, format="parquet")
        # count total rows via metadata (no full scan)
        self.n_datapoints = sum(
            frag.metadata.num_rows
            for frag in self._dataset.get_fragments()
        )

        self.weights = np.empty(0)
        self.calc_weights()

    def calc_weights(self):
        # placeholder
        self.weights = [np.ones(size) for size in DataPoint.label_sizes]

    def torch_weights(self, labels_part_id):
        w = torch.from_numpy(self.weights[labels_part_id])
        w = w.pin_memory(device=self.device)
        return w.to(self.device, non_blocking=True)

    @staticmethod
    def save_batch(datapoints: list[DataPoint], data_dir: str):
        os.makedirs(data_dir, exist_ok=True)

        features = np.array([dp.features for dp in datapoints])
        labels = np.array([dp.labels for dp in datapoints])

        # Build a dict of Arrow arrays
        data = {}
        for i in range(features.shape[1]):
            data[DataSet.feature_columns[i]] = pa.array(features[:, i])
        # if labels is 1D, shape is (N,), else (N, Dl)
        lbl = labels if labels.ndim > 1 else labels.reshape(-1, 1)
        for i in range(lbl.shape[1]):
            data[DataSet.label_columns[i]] = pa.array(lbl[:, i])

        table = pa.table(data)
        filename = f"chunk_{uuid.uuid4().hex}.parquet"
        pq.write_table(table, os.path.join(data_dir, filename))

    def __iter__(self):
        scanner = self._dataset.scanner(batch_size=self.batch_size)
        for batch in scanner.to_batches():
            X_np = np.column_stack([batch.column(i).to_numpy() for i in range(DataSet.n_features)])
            y_np = np.column_stack([batch.column(i).to_numpy() for i in range(DataSet.n_features, DataSet.n_features + DataSet.n_labels)])

            # convert to torch, pin, move to device
            X = torch.from_numpy(X_np).pin_memory(device=self.device).to(self.device, non_blocking=True)
            y = torch.from_numpy(y_np).pin_memory(device=self.device).to(self.device, non_blocking=True)

            yield X, y

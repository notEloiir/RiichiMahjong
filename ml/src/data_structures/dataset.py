import numpy as np
from pathlib import Path
import math
import torch

from .datapoint import DataPoint


class DataSet:
    def __init__(self, path, device=torch.device("cpu")):
        self.path = path
        self.device = device

        path = Path(path)
        self.n_parts = len(list(path.parent.glob(path.name + '*')))
        self.batch_size = 256
        self.n_datapoints = 0

    def save_batch(self, datapoints: list[DataPoint]=None):
        data = np.array([np.concatenate((dp.features, dp.labels)) for dp in datapoints])

        np.save(self.path + str(self.n_parts) + ".npy", data)
        self.n_parts += 1
        self.n_datapoints += len(datapoints)

    def load_batch(self, part_id: int) -> np.ndarray:
        return np.load(self.path + str(part_id) + ".npy", mmap_mode='r+')

    def __iter__(self):
        self.n_datapoints = 0
        for part_id in range(self.n_parts):
            part = self.load_batch(part_id)
            self.n_datapoints += part.shape[0]

            X_np, y_np = np.hsplit(part, (DataPoint.features_size,))
            for batch_id in range(math.ceil(part.shape[0] / self.batch_size)):
                X = torch.from_numpy(X_np[batch_id * self.batch_size : (batch_id + 1) * self.batch_size])
                y = torch.from_numpy(y_np[batch_id * self.batch_size : (batch_id + 1) * self.batch_size])

                X = X.pin_memory(device=self.device)
                y = y.pin_memory(device=self.device)

                X = X.to(self.device, non_blocking=True)
                y = y.to(self.device, non_blocking=True)

                yield X, y


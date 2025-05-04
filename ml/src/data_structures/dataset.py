import numpy as np
from pathlib import Path

from .datapoint import DataPoint


class DataSet:
    def __init__(self, path):
        self.path = path

        path = Path(path)
        self.n_batches = len(list(path.parent.glob(path.name + '*')))

    # Save datapoints in batches of batch_size
    # Unless called with empty datapoints, then (last batch) saves with any datapoints left unsaved
    def save_batch(self, datapoints: list[DataPoint]=None):
        data = np.array([np.concatenate((dp.features, dp.labels)) for dp in datapoints])

        np.save(self.path + str(self.n_batches) + ".npy", data)
        self.n_batches += 1

    def load_batch(self, batch) -> np.ndarray:
        return np.load(self.path + str(batch) + ".npy")

import numpy as np
import math
import torch

from .datapoint import DataPoint


class DataSet:
    def __init__(self, device=torch.device("cpu"), batch_size=256):
        self.X = np.empty(0)
        self.y = np.empty(0)
        self.device = device
        self.batch_size = batch_size
        self.n_datapoints = 0
        self.weights = self.calc_weights()

    def torch_weights(self, labels_part_id):
        weights_part = torch.from_numpy(self.weights[labels_part_id])
        weights_part = weights_part.pin_memory(device=self.device)
        return weights_part.to(self.device, non_blocking=True)

    def calc_weights(self):
        return [np.ones(weight_size) for weight_size in DataPoint.label_sizes]  # temp

    def save(self, path):
        np.savez(path, X=self.X, y=self.y)

    @staticmethod
    def from_datapoints(datapoints: list[DataPoint], device=torch.device("cpu"), batch_size=256):
        dataset = DataSet(device, batch_size)
        dataset.X = np.array([dp.features for dp in datapoints])
        dataset.y = np.array([dp.labels for dp in datapoints])
        dataset.n_datapoints = len(datapoints)

        return dataset

    @staticmethod
    def from_file(path: str, device=torch.device("cpu"), batch_size=256):
        if not path.endswith(".npz"):
            path += ".npz"
        f = np.load(path, mmap_mode='r+')
        dataset = DataSet(device, batch_size)
        dataset.X = f['X']
        dataset.y = f['y']
        dataset.n_datapoints = dataset.X.shape[0]

        assert dataset.X.shape[0] == dataset.y.shape[0] > 0
        assert dataset.X.shape[1] == DataPoint.features_size
        assert dataset.y.shape[1] == DataPoint.labels_size

        return dataset

    def __iter__(self):
        for batch_id in range(math.ceil(self.n_datapoints / self.batch_size)):
            X = torch.from_numpy(self.X[batch_id * self.batch_size : (batch_id + 1) * self.batch_size])
            y = torch.from_numpy(self.y[batch_id * self.batch_size : (batch_id + 1) * self.batch_size])

            X = X.pin_memory(device=self.device)
            y = y.pin_memory(device=self.device)

            X = X.to(self.device, non_blocking=True)
            y = y.to(self.device, non_blocking=True)

            yield X, y


import os
import torch.nn as nn
import torch.optim as optim
import torch.cuda
import torch.nn.functional as F

from ml.src.data_structures import DataPoint
from ml.src.data_structures.dataset import DataSet


class MahjongNN(nn.Module):
    def __init__(self, num_layers, hidden_size, device):
        super(MahjongNN, self).__init__()
        self.input_size = DataPoint.features_size
        self.hidden_size = hidden_size
        self.output_size = DataPoint.labels_size

        self.num_layers = num_layers
        self.layers = nn.ModuleList()
        self.layers.append(nn.Linear(self.input_size, hidden_size))
        self.layers.append(nn.ReLU())
        for _ in range(num_layers - 2):
            self.layers.append(nn.Linear(hidden_size, hidden_size))
            self.layers.append(nn.ReLU())
        self.layers.append(nn.Linear(hidden_size, self.output_size))
        # sigmoid in is get_prediction() for inference, for training it's in BCEWithLogitsLoss

        self.optimizer = optim.AdamW(self.parameters(), lr=1e-3, weight_decay=1e-3)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=10, factor=0.5, min_lr=1e-6)

        self.to(device)
        self.device = device

    def forward(self, x):
        # pass input through each layer
        for layer in self.layers:
            x = layer(x)
        return x

    def get_prediction(self, input_vector: torch.Tensor):
        out = self(input_vector.unsqueeze(0))[0]

        # discard_tiles, call_tiles, action
        return torch.split(F.sigmoid(out), DataPoint.label_split)

    def train_model(self, dataset: DataSet, epochs_no=10):
        self.train()
        for epoch in range(epochs_no):
            for X, y in dataset:
                # forward pass
                y_pred = self(X)

                # get loss
                criterion = nn.BCEWithLogitsLoss()
                loss = criterion(y_pred, y)

                # backward pass and optimization
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                self.scheduler.step(loss.item())

    def test_model(self, dataset: DataSet):
        total_loss = 0
        self.eval()
        with torch.no_grad():
            for X, y in dataset:
                # forward pass
                y_pred = self(X)

                # get loss
                criterion = nn.BCEWithLogitsLoss()
                loss = criterion(y_pred, y)

                total_loss += loss.item()

        average_loss = total_loss / dataset.n_datapoints
        print("Average Loss on Evaluation Dataset:\t", average_loss)


    def save_model(self, filename: str):
        model_path = os.path.join(os.getcwd(), "ml", "data", "models", filename)
        torch.save({
            'num_layers': self.num_layers,
            'hidden_size': self.hidden_size,
            'model_state_dict': self.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
        }, model_path)
        print("Model saved to {}.".format(filename))


    @staticmethod
    def from_file(filename: str, device):
        model_path = os.path.join(os.getcwd(), "ml", "data", "models", filename)
        checkpoint = torch.load(model_path, map_location=device)

        num_layers = checkpoint['num_layers']
        hidden_size = checkpoint['hidden_size']

        model = MahjongNN(num_layers, hidden_size, device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        model.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        return model


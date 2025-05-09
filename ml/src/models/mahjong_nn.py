import os
import torch.nn as nn
import torch.optim as optim
import torch.cuda

from ml.src.data_structures.dataset import DataSet


class MahjongNN(nn.Module):
    def __init__(self, num_layers, hidden_size, device):
        super(MahjongNN, self).__init__()
        self.input_size = DataSet.n_features
        self.hidden_size = hidden_size
        self.output_size = DataSet.n_labels

        self.num_layers = num_layers
        self.layers = nn.ModuleList()
        self.layers.append(nn.Linear(self.input_size, hidden_size))
        self.layers.append(nn.ReLU())
        for _ in range(num_layers - 2):
            self.layers.append(nn.Linear(hidden_size, hidden_size))
            self.layers.append(nn.ReLU())
        self.heads = nn.ModuleList()
        for head_size in DataSet.label_sizes:
            self.heads.append(nn.Linear(hidden_size, head_size))

        self.optimizer = optim.AdamW(self.parameters(), lr=1e-3, weight_decay=1e-3)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=256, eta_min=1e-6)

        self.to(device)
        self.device = device

    def forward(self, x):
        # pass input through each layer
        for layer in self.layers:
            x = layer(x)

        return [head(x) for head in self.heads]

    def get_prediction(self, input_vector: torch.Tensor):
        y_preds = self(input_vector.unsqueeze(0))

        # probabilities for discard_tiles, which_chi, action
        return [torch.softmax(y_pred, dim=1)[0] for y_pred in y_preds]

    def train_model(self, dataset: DataSet, epochs_no=5):
        criterions = [
            nn.CrossEntropyLoss(weight=dataset.torch_weights(i)) for i in range(len(self.heads))
        ]
        self.scheduler.T_max = dataset.n_datapoints

        self.train()
        for epoch in range(epochs_no):
            for X, y in dataset:
                # forward pass
                y = y.type(torch.int64)
                y_preds = self(X)  # (n_heads, batch, head_size) logits

                # get loss
                total_loss = criterions[0](y_preds[0], y[:, 0])
                for i in range(1, len(self.heads)):
                    total_loss += criterions[i](y_preds[i], y[:, i])

                # backward pass and optimization
                self.optimizer.zero_grad()
                total_loss.backward()
                self.optimizer.step()

                self.scheduler.step()  # T_max == number of datapoints

    def test_model(self, dataset: DataSet):
        criterions = [
            nn.CrossEntropyLoss(weight=dataset.torch_weights(i)) for i in range(len(self.heads))
        ]

        self.eval()
        epoch_loss = 0.0
        with torch.no_grad():
            for X, y in dataset:
                # forward pass
                y_preds = self(X)  # a list of (batch, head_size) logits

                # get loss
                total_loss = criterions[0](y_preds[0], y[:, 0])
                for i in range(1, len(self.heads)):
                    total_loss += criterions[i](y_preds[i], y[:, i])

                epoch_loss += total_loss.item()

        average_loss = epoch_loss / dataset.n_datapoints
        print("Average loss on test:", average_loss)


    def save_model(self, filename: str):
        model_path = os.path.join(os.getcwd(), "ml", "data", "models", filename)
        torch.save({
            'num_layers': self.num_layers,
            'hidden_size': self.hidden_size,
            'model_state_dict': self.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
        }, model_path)


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


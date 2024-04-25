import os
import time
import traceback
from xml.etree.ElementTree import ParseError
from db_connect import get_match_log_data
from parse_logs import parse_match_log
from label_data import get_data_from_replay
from training_data_classes import TrainingData

import torch.nn as nn
import torch.optim as optim
import torch.cuda
import torch.nn.functional as F


class MahjongNN(nn.Module):
    def __init__(self, num_layers, hidden_size, device):
        super(MahjongNN, self).__init__()
        self.input_size = 459
        self.hidden_size = hidden_size
        self.output_size = 76
        self.lr = 0.01

        self.num_layers = num_layers
        self.layers = nn.ModuleList()
        self.layers.append(nn.Linear(self.input_size, hidden_size))
        self.layers.append(nn.ReLU())
        for _ in range(num_layers - 2):
            self.layers.append(nn.Linear(hidden_size, hidden_size))
            self.layers.append(nn.ReLU())
        self.layers.append(nn.Linear(hidden_size, self.output_size))
        # sigmoid in is get_prediction() for usage, for training it's in BCEWithLogitsLoss

        self.optimizer = optim.Adam(self.parameters(), lr=self.lr)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=20, factor=0.5)

        self.device = device
        self.to(device)

    def forward(self, x):
        # pass input through each layer
        for layer in self.layers:
            x = layer(x)
        return x

    def get_prediction(self, input_vector: torch.Tensor):
        out = self(input_vector.unsqueeze(0))[0]

        # discard_tiles, call_tiles, action
        return torch.split(F.sigmoid(out), [34, 34, 8])

    def train_on_replay(self, data: list[TrainingData], epochs_no=10):

        inputs = torch.cat([action.inputs.tensor.unsqueeze(0) for action in data], dim=0)
        labels = torch.cat([action.label.tensor.unsqueeze(0) for action in data], dim=0)
        pos_weights = torch.cat([action.pos_weight.unsqueeze(0) for action in data], dim=0)

        self.train()
        for epoch in range(epochs_no):
            # forward pass
            outputs = self(inputs)

            # get loss
            criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weights)
            loss = criterion(outputs, labels)

            # backward pass and optimization
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            self.scheduler.step(loss.item())

    def evaluate_on_replay(self, data):

        inputs = torch.cat([action.inputs.tensor.unsqueeze(0) for action in data], dim=0)
        labels = torch.cat([action.label.tensor.unsqueeze(0) for action in data], dim=0)
        pos_weights = torch.cat([action.pos_weight.unsqueeze(0) for action in data], dim=0)

        self.eval()
        with torch.no_grad():
            # forward pass
            outputs = self(inputs)

            # get loss
            criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weights)
            loss = criterion(outputs, labels)

        average_loss = loss.item() / len(data)
        print("Average Loss on Evaluation Dataset:\t", average_loss)


def get_device():
    print("Testing CUDA availability...")
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print("\tUsing CUDA")
    else:
        device = torch.device('cpu')
        print("\tUsing CPU")
    return device


def initialize_model(num_layers, hidden_size, device):
    model = MahjongNN(num_layers, hidden_size, device)
    print("Model initialized.")
    return model


"""
# GIL...
def get_data_from_replay_threaded(match_logs, device, thread_no=4):
    logs_per_thread = len(match_logs) // thread_no
    td = []
    td_fraction = [[] for _ in range(thread_no)]

    def worker(thread_id):
        nonlocal logs_per_thread
        start_index = thread_id * logs_per_thread
        end_index = (thread_id + 1) * logs_per_thread
        td_fraction[thread_id] = get_data_from_replay(match_logs[start_index:end_index], device)

    threads: list = [None for _ in range(thread_no)]
    for thread_i in range(thread_no):
        threads[thread_i] = threading.Thread(target=worker, args=[thread_i])
        threads[thread_i].start()

    for thread_i in range(thread_no):
        threads[thread_i].join()
        td.extend(td_fraction[thread_i])

    return td
"""


def train_model(model, how_many, starting_from, batch_size, device, filename, db_file):
    print("train_model(): start")

    print("Connecting to DB...")
    curr_dir = os.getcwd()
    logs_db_dir = os.path.join(curr_dir, "phoenix-logs", "db")
    cursor, match_no = get_match_log_data(logs_db_dir, db_file)
    print("Total number of matches available: ", match_no)

    if starting_from + how_many > match_no:
        print("Not enough matches in DB, download more first")
        return

    print("Skipping to starting point...")
    for _ in range(starting_from // batch_size):
        cursor.fetchmany(batch_size)

    print("Starting training...")
    start_time = time.time()
    n = how_many // batch_size
    for batch in range(n):

        # save checkpoint every 100 batches
        if (batch % 100) == 0 and batch:
            save_model(model, "checkpoint"+str((batch // 100) % 3))

        start = time.time()
        try:
            training_data = get_data_from_replay(
                [parse_match_log(match_log[0]) for match_log in cursor.fetchmany(batch_size)], device)
            """
            training_data = get_data_from_replay_threaded(
                     [parse_match_log(match_log[0]) for match_log in cursor.fetchmany(batch_size)], torch.device('cpu'),
                     thread_no=4)
            """
            td_len = len(training_data)

            if not td_len:
                print("No matches in batch found suitable. Increase batch size or loosen requirements (parse_logs.py)")
                continue

            print("Batch training data processed:\t\t\t\t\t\t\t\t\t", time.time() - start)
            start = time.time()

            model.train_on_replay(training_data)
            print("Batch training complete:\t\t\t\t\t\t\t\t\t", time.time() - start)

            """
            model.train_on_replay(training_data[:int(td_len * 0.9)])
            print("Batch training complete:\t\t\t\t\t\t\t\t\t", time.time() - start)
            start = time.time()
            
            #  versus (compare_models.py) now used to compare models
            model.evaluate_on_replay(training_data[int(td_len * 0.9):])
            print("Batch evaluation complete:\t\t\t\t\t\t\t\t\t", time.time() - start)
            print("Current learning rate:", model.scheduler.get_last_lr())
            """

        except (ValueError, TypeError, ParseError):
            # so that you don't lose progress when database entry is corrupted, and you realize 8h later
            print("Batch failed.")
            traceback.print_exc()

        time_s = int((time.time() - start_time) / (batch + 1) * (n - batch - 1))
        print("Finished {} out of {} batches.\tETA: {}:{:02d}:{:02d}".format(batch + 1, n, time_s // 3600, 
                                                                             (time_s // 60) % 60, time_s % 60))
    time_s = int(time.time() - start_time)
    print("Total time elapsed: {}:{:02d}:{:02d}".format(time_s // 3600, (time_s // 60) % 60, time_s % 60))

    print("Saving model...")
    save_model(model, filename)

    print("train_model(): end")


def save_model(model: MahjongNN, filename: str):
    model_path = os.path.join(os.getcwd(), "models", filename)
    torch.save({
        'num_layers': model.num_layers,
        'hidden_size': model.hidden_size,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': model.optimizer.state_dict(),
        'scheduler_state_dict': model.scheduler.state_dict(),
    }, model_path)
    print("Model saved to {}.".format(filename))


def load_model(filename: str, device):
    model_path = os.path.join(os.getcwd(), "models", filename)
    checkpoint = torch.load(model_path, map_location=device)

    num_layers = checkpoint['num_layers']
    hidden_size = checkpoint['hidden_size']

    model = initialize_model(num_layers, hidden_size, device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    model.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    print("Model loaded.")
    return model


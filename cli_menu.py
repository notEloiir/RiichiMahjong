import torch
import os

from ml.src.data_structures.dataset import DataSet
from ml.src.models import versus, MahjongNN
from ml.src.models.handle_device import get_device
from ml.src.models.mahjong_nn import MahjongNN
from game.src.core.player import Player
from ml.src.data_processing import extract_datapoints, refine_data

if __name__ == "__main__":
    device = get_device()
    model = None

    while True:
        print('''
Select mode:
data [db_year] [raw_data_filename] [how_many_matches] [chunk_size] - extract datapoints
process [raw_data_filename] [processed_data_filename] - refine data
init [num_layers] [hidden_size]
train [processed_data_filename]
save [filename]
load [filename] (will call init with proper arguments)
versus [how_many_matches] [init_seed]  - compare models against each other
quit
        ''')

        user_input = input().split(' ')
        match user_input[0]:
            case "data":
                if len(user_input) != 5:
                    print("Expecting 4 arguments for init, got {}.".format(len(user_input) - 1))
                    continue

                db_year = user_input[1]
                raw_data_filename = user_input[2]
                how_many = int(user_input[3])
                chunk_size = int(user_input[4])

                raw_data_filepath = os.path.join(os.getcwd(), "ml", "data", "raw", raw_data_filename)
                extract_datapoints(db_year + ".db", raw_data_filepath, how_many=how_many, chunk_size=chunk_size)

            case "process":
                if len(user_input) != 3:
                    print("Expecting 2 arguments for init, got {}.".format(len(user_input) - 1))
                    continue

                raw_data_filename = user_input[1]
                raw_data_filepath = os.path.join(os.getcwd(), "ml", "data", "raw", raw_data_filename)
                processed_data_filename = user_input[2]
                processed_data_filepath = os.path.join(os.getcwd(), "ml", "data", "processed", processed_data_filename)

                refine_data(raw_data_filepath, processed_data_filepath)

            case "init":
                if len(user_input) != 3:
                    print("Expecting 2 arguments for init, got {}.".format(len(user_input) - 1))
                    continue

                num_layers = int(user_input[1])
                hidden_size = int(user_input[2])
                model = MahjongNN(num_layers, hidden_size, device)

            case "train":
                if len(user_input) != 2:
                    print("Expecting 1 arguments for train, got {}.".format(len(user_input) - 1))
                    continue

                data_filename = user_input[1]
                data_filepath = os.path.join(os.getcwd(), "ml", "data", "processed", data_filename)
                dataset = DataSet(data_filepath, device=device)
                model.train_model(dataset)

            case "save":
                if len(user_input) != 2:
                    print("Expecting 1 argument for save, got {}.".format(len(user_input) - 1))
                    continue
                filename = user_input[1]
                print("Saving model to ", filename)
                model.save_model(filename)

            case "load":
                if len(user_input) != 2:
                    print("Expecting 1 argument for load, got {}.".format(len(user_input) - 1))
                    continue
                filename = user_input[1]
                print("Loading models from ", filename)
                model = MahjongNN.from_file(filename, device=device)

            case "versus":
                if len(user_input) != 3:
                    print("Expecting 2 argument for load, got {}.".format(len(user_input) - 1))
                    continue
                how_many = int(user_input[1])
                init_seed = user_input[2]

                competitors = []
                names = []
                i = 0
                while i < 4:
                    input2 = input(f"Load competitor {i}: [filename] ").split(' ')
                    if len(input2) != 1:
                        print("Expecting 1 argument for load for versus, got {}.".format(len(input2)))
                        continue
                    filename = input2[0]
                    competitors.append(Player(is_human=False, model=MahjongNN.from_file(filename, torch.device("cpu"))))
                    names.append(filename)
                    i += 1

                win_rates = versus(competitors, how_many, init_seed, torch.device("cpu"))
                print("Win rates:")
                for i in range(4):
                    print("{}: {}".format(names[i], win_rates[i]))

            case "quit":
                print("Bye")
                break

            case _:
                print("Enter valid arguments")


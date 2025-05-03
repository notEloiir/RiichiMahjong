import torch
import os

from ml.src.models import versus
from ml.src.models.mahjong_nn import get_device, initialize_model, train_model, save_model, load_model
from game.src.core.player import Player
from ml.src.data_processing import extract_datapoints, refine_data


if __name__ == "__main__":
    device = get_device()
    model = None

    while True:
        print('''
Select mode:  (train auto-saves checkpoints and saves the result)
data [db_year] [raw_data_filename] - extract datapoints
refine [raw_data_filename] [refined_data_filename] - refine data
init [num_layers] [hidden_size]
train [batch_size] [data_filename] [model_filename] - train on data at data_filename, saves model as model_filename
save [filename]
load [filename] (will call init with proper arguments)
versus [how_many_matches] [init_seed]  - compare models against each other
quit
        ''')

        user_input = input().split(' ')
        match user_input[0]:
            case "data":
                if len(user_input) != 3:
                    print("Expecting 2 arguments for init, got {}.".format(len(user_input) - 1))
                    continue

                db_year = user_input[1]
                raw_data_filename = user_input[2]

                raw_data_filepath = os.path.join(os.getcwd(), "ml", "data", "datasets", raw_data_filename)
                extract_datapoints(db_year + ".db", raw_data_filepath, batch_size=100)

            case "refine":
                if len(user_input) != 3:
                    print("Expecting 2 arguments for init, got {}.".format(len(user_input) - 1))
                    continue

                raw_data_filename = user_input[1]
                raw_data_filepath = os.path.join(os.getcwd(), "ml", "data", "datasets", raw_data_filename)
                refined_data_filename = user_input[2]
                refined_data_filepath = os.path.join(os.getcwd(), "ml", "data", "datasets", raw_data_filename)

                refine_data(raw_data_filepath, refined_data_filepath)

            case "init":
                if len(user_input) != 3:
                    print("Expecting 2 arguments for init, got {}.".format(len(user_input) - 1))
                    continue

                num_layers = int(user_input[1])
                hidden_size = int(user_input[2])
                model = initialize_model(num_layers, hidden_size, device)

            case "train":
                if len(user_input) != 4:
                    print("Expecting 3 arguments for train, got {}.".format(len(user_input) - 1))
                    continue

                batch_size = int(user_input[1])
                data_filename = user_input[2]
                data_filepath = os.path.join(os.getcwd(), "ml", "data", "datasets", data_filename)
                model_filename = user_input[3]
                train_model(model, batch_size, device, model_filename, data_filepath)

            case "save":
                if len(user_input) != 2:
                    print("Expecting 1 argument for save, got {}.".format(len(user_input) - 1))
                    continue
                filename = user_input[1]
                print("Saving model to ", filename)
                save_model(model, filename)

            case "load":
                if len(user_input) != 2:
                    print("Expecting 1 argument for load, got {}.".format(len(user_input) - 1))
                    continue
                filename = user_input[1]
                print("Loading models from ", filename)
                model = load_model(filename, device=device)

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
                    competitors.append(Player(is_human=False, model=load_model(filename, torch.device("cpu"))))
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


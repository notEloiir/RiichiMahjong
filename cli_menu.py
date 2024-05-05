import torch

from models import get_device, initialize_model, train_model, save_model, load_model
from compare_models import versus
from player import Player


if __name__ == "__main__":
    device = get_device()
    model = None

    while True:
        print("""
Select mode:  (train auto-saves checkpoints and saves the result)
init [num_layers] [hidden_size]
train [how_many] [starting_from] [batch_size] [filename] [db_file]
save [filename]
load [filename] (will call init with proper arguments)
versus [how_many_matches] [init_seed]  - compare models against each other
quit
        """)

        user_input = input().split(' ')
        match user_input[0]:
            case "init":
                if len(user_input) != 3:
                    print("Expecting 2 arguments for init, got {}.".format(len(user_input) - 1))
                    continue

                num_layers = int(user_input[1])
                hidden_size = int(user_input[2])
                model = initialize_model(num_layers, hidden_size, device)

            case "train":
                if len(user_input) != 6:
                    print("Expecting 5 arguments for train, got {}.".format(len(user_input) - 1))
                    continue

                how_many = int(user_input[1])
                starting_from = int(user_input[2])
                batch_size = int(user_input[3])
                filename = user_input[4]
                db_file = int(user_input[5])
                train_model(model, how_many, starting_from, batch_size, device, filename, db_file)

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


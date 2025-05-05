import torch


def get_device():
    print("Testing CUDA availability...")
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print("\tUsing CUDA")
    else:
        device = torch.device('cpu')
        print("\tUsing CPU")
    return device

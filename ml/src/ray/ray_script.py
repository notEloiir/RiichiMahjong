import os
import torch
import ray
import ray.data
from ray.train import ScalingConfig, RunConfig, CheckpointConfig
from ray.train.torch import TorchTrainer

from ml.src.models import MahjongNN
from ml.src.ray.ray_trainer import train_loop_per_worker


def run_ray_script(processed_data_dir: str, device=torch.device("cpu"), n_workers=1):
    ray.init(address="auto", ignore_reinit_error=True)

    trainer = TorchTrainer(
        train_loop_per_worker=train_loop_per_worker,
        train_loop_config={
            "model_kwargs": {"num_layers": 4, "hidden_size": 128, "device": device, },
            "epochs": 5,
        },
        datasets={"train": ray.data.read_parquet(processed_data_dir)},
        scaling_config=ScalingConfig(
            num_workers=n_workers,
            use_gpu=(device.type == "cuda"),
        ),
        run_config=RunConfig(
            checkpoint_config=CheckpointConfig(
                checkpoint_score_attribute="loss",
                checkpoint_score_order="min"
            )
        ),
    )
    result = trainer.fit()

    with result.checkpoint.as_directory() as checkpoint_dir:
        path = os.path.join(checkpoint_dir, "model.pt")
        MahjongNN.from_file(path, torch.device("cpu")).save_model("ray.pt")

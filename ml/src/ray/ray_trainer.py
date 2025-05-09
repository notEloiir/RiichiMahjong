import tempfile
import torch
import torch.nn as nn
import ray.train as train

from ml.src.data_structures.dataset import DataSet
from ml.src.models.mahjong_nn import MahjongNN


def train_loop_per_worker(config):
    model = MahjongNN(**config["model_kwargs"])
    criterions = [
        nn.CrossEntropyLoss() for _ in range(len(model.heads))
    ]

    model.train()
    dataset = train.get_dataset_shard("train")
    for epoch in range(config["epochs"]):
        epoch_loss = 0.0
        for batch in dataset.iter_torch_batches(batch_size=256):
            X = torch.stack([batch[col] for col in DataSet.feature_columns], dim=1)  # just for the record I hate this
            y = torch.stack([batch[col] for col in DataSet.label_columns], dim=1)

            # forward pass
            y_preds = model(X)  # (n_heads, batch, head_size) logits

            # get loss
            total_loss = criterions[0](y_preds[0], y[:, 0])
            for i in range(1, len(model.heads)):
                total_loss += criterions[i](y_preds[i], y[:, i])

            # backward pass and optimization
            model.optimizer.zero_grad()
            total_loss.backward()
            model.optimizer.step()

            model.scheduler.step()
            epoch_loss += total_loss.item()
        metrics = {"loss": epoch_loss}

        with tempfile.TemporaryDirectory() as temp_checkpoint_dir:
            checkpoint=None
            if train.get_context().get_world_rank() == 0:
                model.save_model("model.pt", temp_checkpoint_dir)
                checkpoint = train.Checkpoint.from_directory(temp_checkpoint_dir)

            train.report(metrics, checkpoint=checkpoint)



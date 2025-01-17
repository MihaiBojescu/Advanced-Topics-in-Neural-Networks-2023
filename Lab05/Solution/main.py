#!/usr/bin/env python3
import torch
import torch.utils.data as torch_data
import torchvision
from torchvision.transforms import v2
from nn.metered_trainable_sam_model import MeteredTrainableSAMNeuralNetwork
from nn.trainable_model import TrainableNeuralNetwork
from nn.metered_trainable_model import MeteredTrainableNeuralNetwork
from nn.util import get_default_device
from nn.dataset import CachedDataset
from nn.transforms import OneHot
from util.util import Timer
import wandb

models = {
    "SGD": {"constructor": MeteredTrainableNeuralNetwork, "optimiser": torch.optim.SGD},
    "RMSprop": {
        "constructor": MeteredTrainableNeuralNetwork,
        "optimiser": torch.optim.RMSprop,
    },
    "Adam": {
        "constructor": MeteredTrainableNeuralNetwork,
        "optimiser": torch.optim.Adam,
    },
    "Adagrad": {
        "constructor": MeteredTrainableNeuralNetwork,
        "optimiser": torch.optim.Adagrad,
    },
    "SGD with SAM": {
        "constructor": MeteredTrainableSAMNeuralNetwork,
        "optimiser": torch.optim.SGD,
    },
}


def main():
    wandb.init(
        project="atnn-homework-5",
        # name=f"{wandb.config.optimiser}: batch_size = {wandb.config.batch_size}, learning rate = {wandb.config.learning_rate}, epochs = {wandb.config.learning_rate}",
        reinit=True,
    )
    timer = Timer()

    device = get_default_device()
    dataset_path = "./data/datasets"
    logs_path = "./data/logs"
    transforms = torchvision.transforms.Compose(
        [
            v2.ToImageTensor(),
            v2.ToDtype(torch.float32),
            v2.Resize((28, 28), antialias=True),
            v2.Grayscale(),
            torch.flatten,
        ]
    )
    target_transforms = OneHot(range(0, 10))

    training_dataset = torchvision.datasets.CIFAR10(
        root=dataset_path,
        download=True,
        train=True,
        transform=transforms,
        target_transform=target_transforms,
    )
    validation_dataset = torchvision.datasets.CIFAR10(
        root=dataset_path,
        download=True,
        train=False,
        transform=transforms,
        target_transform=target_transforms,
    )

    cached_training_dataset = CachedDataset(dataset=training_dataset, cache=True)
    cached_validation_dataset = CachedDataset(dataset=validation_dataset, cache=True)

    batched_train_dataset = torch_data.DataLoader(
        dataset=cached_training_dataset,
        batch_size=wandb.config.batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=device == "cuda",
    )
    batched_validation_dataset = torch_data.DataLoader(
        dataset=cached_validation_dataset,
        batch_size=256,
        shuffle=False,
        num_workers=2,
        pin_memory=device == "cuda",
    )

    print(
        f"Loading: {timer()}s for {len(training_dataset) + len(validation_dataset)} instances"
    )

    model = build_model(
        constructor=models[wandb.config.optimiser]["constructor"],
        optimiser=models[wandb.config.optimiser]["optimiser"],
        learning_rate=wandb.config.learning_rate,
        device=device,
        logs_path=logs_path,
    )
    wandb.watch(models=model, criterion=model.loss_function)
    run(
        name=wandb.config.optimiser,
        model=model,
        epochs=wandb.config.epochs,
        batched_train_dataset=batched_train_dataset,
        batched_validation_dataset=batched_validation_dataset,
    )
    wandb.finish(0)


def build_model(
    constructor: TrainableNeuralNetwork,
    optimiser: torch.optim.Optimizer,
    learning_rate: float,
    device: str,
    logs_path: str,
) -> TrainableNeuralNetwork:
    model = constructor(
        input_size=784,
        output_size=10,
        loss_function=torch.nn.CrossEntropyLoss,
        optimiser=optimiser,
        learning_rate=learning_rate,
        device=device,
        log_directory=logs_path,
    )

    return model


def run(
    name: str,
    model: TrainableNeuralNetwork,
    epochs: int,
    batched_train_dataset: torch_data.DataLoader,
    batched_validation_dataset: torch_data.DataLoader,
):
    timer = Timer()

    before_training_results = model.run_validation(
        batched_validation_dataset=batched_validation_dataset
    )
    model.run(
        batched_training_dataset=batched_train_dataset,
        batched_validation_dataset=batched_validation_dataset,
        epochs=epochs,
    )
    after_training_results = model.run_validation(
        batched_validation_dataset=batched_validation_dataset
    )

    print(
        f"{name} - Validation accuracy before training: {before_training_results[1] * 100:>6.2f}%"
    )
    print(
        f"{name} - Validation accuracy  after training: {after_training_results[1] * 100:>6.2f}%"
    )
    print(f"{name} - Running: {timer()}s for {epochs} epochs")


if __name__ == "__main__":
    main()

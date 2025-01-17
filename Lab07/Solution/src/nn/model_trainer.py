import time
import typing as t
import torch
import torch.utils.data as torch_data


class NeuralNetworkTrainer:
    neural_network: torch.nn.Module
    device: torch.device
    loss_function: torch.nn.modules.loss._Loss
    optimiser: torch.optim.Optimizer
    exports_path: str

    def __init__(
        self,
        neural_network: torch.nn.Module,
        loss_function: torch.nn.modules.loss._Loss,
        optimiser: torch.optim.Optimizer,
        learning_rate: float,
        device: torch.device = torch.device("cpu"),
        exports_path: str = "/tmp",
    ) -> None:
        self.neural_network = neural_network
        self.loss_function = loss_function()
        self.optimiser = optimiser(self.neural_network.parameters(), lr=learning_rate)
        self.device = device
        self.exports_path = exports_path

        self.loss_function = self.loss_function.to(
            device=self.device, non_blocking=self.device == "cuda"
        )

    def run(
        self,
        batched_training_dataset: torch_data.DataLoader,
        batched_validation_dataset: torch_data.DataLoader,
        epochs: int,
    ):
        epochs_digits = len(str(epochs))

        for epoch in range(0, epochs):
            training_loss, training_accuracy = self.run_training(
                batched_training_dataset
            )
            validation_loss, validation_accuracy = self.run_validation(
                batched_validation_dataset
            )

            print(
                f"Training epoch {epoch + 1:>{epochs_digits}}: training loss = {training_loss:>8.2f}, training accuracy = {training_accuracy * 100:>6.2f}%, validation loss = {validation_loss:>8.2f}, validation accuracy = {validation_accuracy * 100:>6.2f}%",
                end="\r",
            )

        print()

        torch.save(self.neural_network.state_dict(), f"{self.exports_path}/{time.time_ns()}.pt")

    def run_training(
        self,
        batched_training_dataset: torch_data.DataLoader,
    ) -> t.Tuple[float, float]:
        self.neural_network.train()
        total = 0
        correct = 0
        training_loss = 0.0

        for training_image in batched_training_dataset:
            image, label = training_image
            image = image.to(device=self.device, non_blocking=self.device == "cuda")
            label = label.to(device=self.device, non_blocking=self.device == "cuda")

            self.optimiser.zero_grad()
            y_hat = self.neural_network(image)
            loss = self.loss_function(y_hat, label)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                self.neural_network.parameters(), max_norm=1.0
            )
            self.optimiser.step()

            for i in range(label.shape[0]):
                correct += (
                    torch.argmax(y_hat[i]).item() == torch.argmax(label[i]).item()
                )
                total += 1
            training_loss += loss.item()

        accuracy = correct / total
        return training_loss, accuracy

    def run_validation(
        self,
        batched_validation_dataset: torch_data.DataLoader,
    ) -> t.Tuple[float, float]:
        self.neural_network.eval()
        total = 0
        correct = 0
        validation_loss = 0.0

        with torch.no_grad():
            for validation_image in batched_validation_dataset:
                image, label = validation_image
                image = image.to(device=self.device, non_blocking=self.device == "cuda")
                label = label.to(device=self.device, non_blocking=self.device == "cuda")

                y_hat = self.neural_network(image)
                loss = self.loss_function(y_hat, label)

                for i in range(label.shape[0]):
                    correct += (
                        torch.argmax(y_hat[i]).item() == torch.argmax(label[i]).item()
                    )
                    total += 1

                validation_loss += loss.item()

        accuracy = correct / total
        return validation_loss, accuracy

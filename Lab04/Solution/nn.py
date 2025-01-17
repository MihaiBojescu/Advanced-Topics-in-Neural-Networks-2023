import typing as t
import torch
import torch.nn as nn


class NeuralNetwork(nn.Module):
    __activation_function: t.Callable[[torch.Tensor], torch.Tensor]
    __output_layer_activation_function: t.Callable[[torch.Tensor], torch.Tensor]
    __device: str

    def __init__(
        self,
        image_size: int,
        output_layer_activation_function: t.Union[
            None, t.Callable[[torch.Tensor], torch.Tensor]
        ] = None,
        device: str = "cpu",
    ) -> None:
        super(NeuralNetwork, self).__init__()
        self.__device = device

        self.layer_1_weights = nn.Linear(image_size + 1, 2048).to(
            device=self.__device, non_blocking=self.__device == "cuda"
        )
        self.layer_2_weights = nn.Linear(2048, 1024).to(
            device=self.__device, non_blocking=self.__device == "cuda"
        )
        self.layer_3_weights = nn.Linear(1024, 512).to(
            device=self.__device, non_blocking=self.__device == "cuda"
        )
        self.layer_4_weights = nn.Linear(512, 1024).to(
            device=self.__device, non_blocking=self.__device == "cuda"
        )
        self.layer_5_weights = nn.Linear(1024, 2048).to(
            device=self.__device, non_blocking=self.__device == "cuda"
        )
        self.layer_6_weights = nn.Linear(2048, image_size).to(
            device=self.__device, non_blocking=self.__device == "cuda"
        )

        self.__activation_function = nn.LeakyReLU()
        self.__output_layer_activation_function = (
            output_layer_activation_function
            if output_layer_activation_function is not None
            else nn.Identity()
        )

    def forward(self, X: torch.Tensor, time_skip: torch.Tensor) -> torch.Tensor:
        # FIXME: Before call, tensor is of shape [batch_size, image_size]. Here it is [image_size]...
        if len(X.shape) == 1:
            X = X.view(1, -1)
        if len(time_skip.shape) == 1:
            time_skip = time_skip.view(-1, 1)

        X = torch.concat((X, time_skip), dim=-1)

        y_hat = self.__activation_function(self.layer_1_weights(X))
        y_hat = self.__activation_function(self.layer_2_weights(y_hat))
        y_hat = self.__activation_function(self.layer_3_weights(y_hat))
        y_hat = self.__activation_function(self.layer_4_weights(y_hat))
        y_hat = self.__activation_function(self.layer_5_weights(y_hat))
        y_hat = self.__output_layer_activation_function(self.layer_6_weights(y_hat))

        return y_hat

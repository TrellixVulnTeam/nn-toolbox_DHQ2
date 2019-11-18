from torch.utils.data import DataLoader
from torch.nn import Module
from torch.optim import Optimizer
from torch import Tensor
from ...utils import load_model, get_device
import torch
from typing import Iterable, Dict
from ...callbacks import CallbackHandler, Callback
from ...metrics import Metric
from ...transforms import MixupTransformer
from ...learner import SupervisedLearner


class SupervisedImageLearner(SupervisedLearner):
    def __init__(
            self, train_data: DataLoader, val_data: DataLoader, model: Module,
            criterion: Module, optimizer: Optimizer,
            mixup: bool=False, mixup_alpha: float=0.4, device=get_device()
    ):
        super(SupervisedImageLearner, self).__init__(
            train_data=train_data, val_data=val_data, model=model,
            criterion=criterion, optimizer=optimizer
        )
        self._device = device
        self._mixup = mixup
        if mixup:
            self._mixup_transformer = MixupTransformer(alpha=mixup_alpha)

    def learn_one_iter(self, images: Tensor, labels: Tensor):
        data = self._cb_handler.on_batch_begin({'inputs': images, 'labels': labels}, True)
        images = data['inputs']
        labels = data['labels']

        if self._mixup:
            images, labels = self._mixup_transformer.transform_data(images, labels)

        loss = self._cb_handler.after_losses({"loss": self.compute_loss(images, labels, True)}, True)["loss"]

        if self._cb_handler.on_backward_begin():
            loss.backward()
        if self._cb_handler.after_backward():
            self._optimizer.step()
            if self._cb_handler.after_step():
                self._optimizer.zero_grad()

            if self._device.type == 'cuda':
                mem = torch.cuda.memory_allocated(self._device)
                self._cb_handler.on_batch_end({"loss": loss.cpu(), "allocated_memory": mem})
            else:
                self._cb_handler.on_batch_end({"loss": loss})
            # self._cb_handler.on_batch_end({"loss": loss})

    # @torch.no_grad()
    # def evaluate(self) -> float:
    #     self._model.eval()
    #     all_outputs = []
    #     all_labels = []
    #     total_data = 0
    #     loss = 0
    #
    #     for images, labels in self._val_data:
    #         data = self._cb_handler.on_batch_begin({"inputs": images, "labels": labels}, False)
    #         images, labels = data["inputs"], data["labels"]
    #
    #         all_outputs.append(self._model(images))
    #         all_labels.append(labels.cpu())
    #         loss += self.compute_loss(images, labels, False).cpu().item() * len(images)
    #         total_data += len(images)
    #
    #     loss /= total_data
    #
    #     logs = dict()
    #     logs["loss"] = loss
    #     logs["outputs"] = torch.cat(all_outputs, dim=0)
    #     logs["labels"] = torch.cat(all_labels, dim=0)
    #
    #     return self._cb_handler.on_epoch_end(logs)

    def compute_loss(self, images: Tensor, labels: Tensor, train: bool) -> Tensor:
        old_criterion = self._criterion
        if self._mixup:
            self._criterion = self._mixup_transformer.transform_loss(self._criterion, self._model.training)
        ret = super().compute_loss(images, labels, train)
        self._criterion = old_criterion
        return ret

        # outputs = self._cb_handler.after_outputs({"output": self._model(images)}, train)
        #
        # return self._cb_handler.after_losses({"loss": criterion(outputs["output"], labels)}, train)


from .callbacks import Callback
from ..utils import copy_model
from typing import Dict, Any
from torch.nn import Module


class StochasticWeightAveraging(Callback):
    def __init__(self, model: Module, average_after: int, update_every: int=1, timescale: str="iter"):
        '''
        :param model: the model currently being trained
        :param average_after: the first epoch to start averaging
        :param update_every: how many epochs/iters between each average update
        '''
        assert timescale == "epoch" or timescale == "iter"
        self._model = model
        self.model_swa = copy_model(model)
        self._update_every = update_every
        self._average_after = average_after
        self._timescale = timescale

    def on_epoch_end(self, logs: Dict[str, Any]) -> bool:
        if self._timescale == "epoch":
            if logs["epoch"] >= self._average_after and logs["epoch"] % self._update_every == 0:
                n_model = (logs["epoch"] - self._average_after) // self._update_every
                w1 = self._model.named_parameters()
                w2 = self.model_swa.named_parameters()

                dict_params2 = dict(w2)
                for name1, param1 in w1:
                    if name1 in dict_params2:
                        dict_params2[name1].data.copy_((param1.data + n_model * dict_params2[name1].data) / (n_model + 1))

                self.model_swa.load_state_dict(dict_params2)
        return False

    def on_batch_end(self, logs: Dict[str, Any]):
        if self._timescale == "iter":
            if logs["iter_cnt"] >= self._average_after and logs["iter_cnt"] % self._update_every == 0:
                n_model = (logs["iter_cnt"] - self._average_after) // self._update_every
                w1 = self._model.named_parameters()
                w2 = self.model_swa.named_parameters()

                dict_params2 = dict(w2)
                for name1, param1 in w1:
                    if name1 in dict_params2:
                        dict_params2[name1].data.copy_(
                            (param1.data + n_model * dict_params2[name1].data) / (n_model + 1))

                self.model_swa.load_state_dict(dict_params2)
    def get_averaged_model(self) -> Module:
        '''
        Return the post-training average model
        :return: the averaged model
        '''
        return self.model_swa
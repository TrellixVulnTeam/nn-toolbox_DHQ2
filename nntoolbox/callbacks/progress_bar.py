"""
Add a progress bar to learner
Adapt from fastai course 2 v3 notebook
"""
from .callbacks import Callback
from fastprogress import master_bar, progress_bar
from typing import Dict, Any
from torch.utils.data import DataLoader


__all__ = ['ProgressBarCB']


# UNTESTED
class ProgressBarCB(Callback):
    n_epoch: int

    def on_train_begin(self):
        # print("num epoch: " + str(self.n_epoch))
        self.master_bar = master_bar(range(self.n_epoch))
        self.master_bar.on_iter_begin()
        self.set_progress(self.learner._train_data, 0)
        # print("on train begin")

    def on_batch_end(self, logs: Dict[str, Any]):
        # print("On batch end")
        # print("Iter: " + str(logs["iter_cnt"] % len(self.learner._train_data)))
        self.progress_bar.update(logs["iter_cnt"] % len(self.learner._train_data))

    def on_epoch_end(self, logs: Dict[str, Any]) -> bool:
        # print("On epoch end")
        self.set_progress(self.learner._train_data, logs["epoch"] + 1)
        return False

    def on_train_end(self): self.master_bar.on_iter_end()

    def set_progress(self, data: DataLoader, epoch: int):
        # print("Epoch: " + str(epoch))
        self.progress_bar = progress_bar(data, parent=self.master_bar, auto_update=False)
        self.master_bar.update(epoch)

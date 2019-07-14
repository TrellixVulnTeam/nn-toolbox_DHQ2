from torchtext.datasets import WikiText2
from torchtext import data
from nntoolbox.utils import get_device
from nntoolbox.sequence.models import LanguageModel
from nntoolbox.sequence.learner import LanguageModelLearner
from torch import nn
from torch.optim import Adam
from nntoolbox.callbacks import *
from nntoolbox.metrics import *


MAX_VOCAB_SIZE = 25000
BATCH_SIZE = 16

TEXT = data.Field(tokenize='spacy')
LABEL = data.LabelField(dtype=torch.float)

# train_iterator, val_iterator, test_iterator = WikiText2.iters()
# for tmp in train_iterator:
#     print(tmp)

def id_to_text(sequence, vocab):
    ret = []
    for token in sequence:
        ret.append(vocab.itos[token])
    return ret


train_data, val_data, test_data = WikiText2.splits(TEXT)
train_iterator = data.BPTTIterator(
    train_data,
    batch_size=BATCH_SIZE,
    sort_within_batch=True,
    device=get_device(),
    bptt_len=35,
    # shuffle=True
)

val_iterator = data.BPTTIterator(
    val_data,
    batch_size=BATCH_SIZE,
    sort_within_batch=True,
    device=get_device(),
    bptt_len=35,
    # shuffle=True
)
TEXT.build_vocab(train_data, max_size=MAX_VOCAB_SIZE, vectors="glove.6B.100d")
# print(id_to_text(next(iter(train_iterator)).target[:, 1:2], TEXT.vocab))
# print(id_to_text(next(iter(train_iterator)).text[:, 1], TEXT.vocab))

model = LanguageModel(
    encoder=nn.Sequential(
        nn.Embedding(num_embeddings=MAX_VOCAB_SIZE, embedding_dim=128),
        nn.GRU(input_size=128, hidden_size=256)
    ),
    head=nn.Sequential(
        nn.Linear(256, 1024),
        nn.ReLU(),
        nn.Linear(1024, MAX_VOCAB_SIZE)
    )
)
# output = model(next(iter(train_iterator)).target[:, 1:2])
# print(output.shape)
# output = torch.argmax(output, dim=-1)
# print(id_to_text(output, TEXT.vocab))

optimizer = Adam(model.parameters())
learner = LanguageModelLearner(train_iterator, val_iterator, model, optimizer, criterion=nn.CrossEntropyLoss())

callbacks = [
    ToDeviceCallback(),
    # MixedPrecisionV2(),
    Tensorboard(),
    NaNWarner(),
    # ReduceLROnPlateauCB(optimizer, monitor='accuracy', mode='max', patience=10),
    # swa,
    LossLogger(),
    ModelCheckpoint(learner=learner, filepath="weights/model.pt", monitor='accuracy', mode='max'),
    # ProgressBarCB()
]

metrics = {
    "accuracy": Accuracy(),
    "loss": Loss()
}


learner.learn(1, callbacks, metrics)
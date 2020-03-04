from typing import List, Union, Tuple, Any

import torch
from torch import Tensor
from torch.nn.utils.rnn import pad_sequence, PackedSequence, pack_sequence

from torchglyph.proc import BatchProc
from torchglyph.vocab import Vocab


class PadTokBatch(BatchProc):
    Batch = List[int]

    def __init__(self, dtype: torch.dtype = torch.long) -> None:
        super(PadTokBatch, self).__init__()
        self.dtype = dtype

    def __call__(self, batch: Batch, vocab: Vocab) -> Tensor:
        return torch.tensor(batch, dtype=self.dtype, requires_grad=False)


class PadSeqBatch(BatchProc):
    Batch = List[Tensor]

    def __init__(self, pad_token: str, batch_first: bool = True) -> None:
        super(PadSeqBatch, self).__init__()
        self.pad_token = pad_token
        self.batch_first = batch_first

    def __call__(self, batch: Batch, vocab: Vocab) -> Tensor:
        return pad_sequence(
            batch, batch_first=self.batch_first,
            padding_value=vocab.stoi[self.pad_token],
        )


class PackSeqBatch(BatchProc):
    Batch = List[Tensor]

    def __init__(self, enforce_sorted: bool = False) -> None:
        super(PackSeqBatch, self).__init__()
        self.enforce_sorted = enforce_sorted

    def __call__(self, batch: Batch, vocab: Vocab) -> PackedSequence:
        return pack_sequence(batch, enforce_sorted=self.enforce_sorted)


class PadArrayBatch(BatchProc):
    Batch = List[List[Tensor]]

    def __init__(self, pad_token: str, batch_first: bool = True) -> None:
        super(PadArrayBatch, self).__init__()
        self.pad_token = pad_token
        self.batch_first = batch_first

    def __call__(self, batch: Batch, vocab: Vocab) -> Any:
        pass


class PackArrayBatch(BatchProc):
    Batch = List[List[Tensor]]

    def __init__(self, enforce_sorted: bool = False) -> None:
        super(PackArrayBatch, self).__init__()
        self.enforce_sorted = enforce_sorted

    def __call__(self, batch: Batch, vocab: Vocab) -> PackedSequence:
        char = [torch.cat(words, dim=0) for words in batch]
        return pack_sequence(char, enforce_sorted=self.enforce_sorted)


class ToDevice(BatchProc):
    Batch = Union[PackedSequence, Tensor, Tuple[Tensor, ...]]

    def __init__(self, device: Union[int, torch.device]) -> None:
        super(ToDevice, self).__init__()
        if isinstance(device, int):
            if device < 0:
                device = torch.device(f'cpu')
            else:
                device = torch.device(f'cuda:{device}')
        self.device = device

    def __call__(self, batch: Batch, vocab: Vocab) -> Batch:
        if isinstance(batch, (PackedSequence, Tensor)):
            return batch.to(self.device)
        return type(batch)([self(e, vocab=vocab) for e in batch])

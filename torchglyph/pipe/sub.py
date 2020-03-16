from typing import Union, Optional, Tuple

import torch

from torchglyph.pipe import Pipe, THRESHOLD
from torchglyph.proc import Lift, ToDevice, Numbering, UpdateCounter, BuildVocab, ToSubList
from torchglyph.proc import ToTensor, PadSeq, PadSub, PackSubByCat, StatsVocab


class PaddedRawSubPipe(Pipe):
    def __init__(self, device: Union[int, torch.device], pad_token: Optional[str],
                 batch_first: bool = True, dtype: torch.dtype = torch.long) -> None:
        super(PaddedRawSubPipe, self).__init__(
            pre=None,
            vocab=None,
            post=Lift(ToTensor(dtype=dtype)) + PadSeq(pad_token=pad_token, batch_first=True),
            batch=PadSub(pad_token=pad_token, batch_first=batch_first) + ToDevice(device=device),
        )


class PaddedSubPipe(PaddedRawSubPipe):
    def __init__(self, device: Union[int, torch.device],
                 unk_token: Optional[str], pad_token: Optional[str],
                 special_tokens: Tuple[Optional[str], ...] = (),
                 batch_first: bool = True, threshold: int = THRESHOLD, dtype: torch.dtype = torch.long) -> None:
        super(PaddedSubPipe, self).__init__(
            device=device, pad_token=pad_token,
            batch_first=batch_first, dtype=dtype,
        )
        self.with_(
            pre=ToSubList() + Lift(UpdateCounter()),
            vocab=[
                BuildVocab(unk_token=unk_token, pad_token=pad_token, special_tokens=special_tokens),
                StatsVocab(threshold=threshold),
            ],
            post=Numbering() + ...,
        )


class PackedRawSubPipe(Pipe):
    def __init__(self, device: Union[int, torch.device], dtype: torch.dtype = torch.long) -> None:
        super(PackedRawSubPipe, self).__init__(
            pre=None,
            vocab=None,
            post=Lift(ToTensor(dtype=dtype)),
            batch=PackSubByCat(enforce_sorted=False) + ToDevice(device=device),
        )


class PackedSubPipe(PackedRawSubPipe):
    def __init__(self, device: Union[int, torch.device], unk_token: Optional[str],
                 special_tokens: Tuple[Optional[str], ...] = (),
                 threshold: int = THRESHOLD, dtype: torch.dtype = torch.long) -> None:
        super(PackedSubPipe, self).__init__(device=device, dtype=dtype)
        self.with_(
            pre=ToSubList() + Lift(UpdateCounter()),
            vocab=[
                BuildVocab(unk_token=unk_token, pad_token=None, special_tokens=special_tokens),
                StatsVocab(threshold=threshold),
            ],
            post=Numbering() + ...,
        )

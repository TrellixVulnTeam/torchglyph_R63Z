import functools
from typing import Any
from typing import Union, Tuple, Dict

import torch
from torch import Tensor
from torch.nn.utils.rnn import PackedSequence


def support_pack(fn):
    @functools.wraps(fn)
    def wrap(x: Union[Tensor, PackedSequence], *args, **kwargs) -> Union[Tensor, PackedSequence]:
        if torch.is_tensor(x):
            return fn(x, *args, **kwargs)
        else:
            return x._replace(data=fn(x.data, *args, **kwargs))

    return wrap


class SupportPack(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]):
        forward_fn = attrs.get('forward', bases[0].forward)

        @functools.wraps(forward_fn)
        def forward(self, x: Union[Tensor, PackedSequence], *args, **kwargs) -> Union[Tensor, PackedSequence]:
            if torch.is_tensor(x):
                return forward_fn(self, x, *args, **kwargs)
            else:
                return x._replace(data=forward_fn(self, x.data, *args, **kwargs))

        return type(name, bases, {**attrs, 'forward': forward})


def head_pack(pack: PackedSequence) -> Tensor:
    return pack.data[:pack.batch_sizes[0].item()]


def prepend_pack(pack: PackedSequence, value: Union[int, bool, float, Tensor]) -> PackedSequence:
    if not torch.is_tensor(value):
        value = torch.full_like(head_pack(pack), fill_value=value)
    return pack._replace(
        data=torch.cat([value, pack.data], dim=0),
        batch_sizes=torch.cat([pack.batch_sizes[:1], pack.batch_sizes], dim=0),
    )

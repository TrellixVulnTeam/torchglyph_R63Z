import torch
from torch import Tensor
from torch import nn
from torch.nn import functional as F
from torch.nn import init

from torchglyph.nn import init

__all__ = [
    'Linear', 'CosineLinear', 'ConjugatedLinear',
]


class Linear(nn.Linear):
    def __init__(self, bias: bool = True, *,
                 in_features: int, out_features: int,
                 dtype: torch.dtype = torch.float32) -> None:
        super(Linear, self).__init__(
            in_features=in_features, out_features=out_features,
            bias=bias, dtype=dtype,
        )

    def reset_parameters(self) -> None:
        init.kaiming_uniform_(self.weight, fan=self.in_features, a=5 ** 0.5, nonlinearity='leaky_relu')
        if self.bias is not None:
            init.constant_(self.bias, 0.)


class CosineLinear(Linear):
    def forward(self, tensor: Tensor) -> Tensor:
        tensor = F.normalize(tensor, p=2, dim=-1)
        weight = F.normalize(self.weight, p=2, dim=-1)
        return F.linear(tensor, weight=weight, bias=self.bias)


class ConjugatedLinear(nn.Module):
    def __init__(self, bias: bool = True, *,
                 num_conjugates: int, in_features: int, out_features: int,
                 dtype: torch.dtype = torch.float32) -> None:
        super(ConjugatedLinear, self).__init__()

        self.weight = nn.Parameter(torch.empty((num_conjugates, out_features, in_features), dtype=dtype))
        if bias:
            self.bias = nn.Parameter(torch.empty((num_conjugates, out_features), dtype=dtype))
        else:
            self.register_parameter('bias', None)

        self.num_conjugates = num_conjugates
        self.in_features = in_features
        self.out_features = out_features

        self.reset_parameters()

    def reset_parameters(self) -> None:
        init.kaiming_uniform_(self.weight, fan=self.in_features, a=5 ** 0.5, nonlinearity='leaky_relu')
        if self.bias is not None:
            init.constant_(self.bias, 0.)

    def extra_repr(self) -> str:
        return ', '.join([
            f'in_features={self.in_features}',
            f'num_conjugates={self.num_conjugates}',
            f'out_features={self.out_features}',
            f'bias={self.bias is not None}',
        ])

    def forward(self, tensor: Tensor) -> Tensor:
        out = (self.weight @ tensor[..., None])[..., 0]
        if self.bias is not None:
            out = out + self.bias
        return out

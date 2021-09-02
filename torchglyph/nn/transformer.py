from typing import Optional

from torch import nn, Tensor

from torchglyph.nn.attention import MultiHeadAttention

__all__ = [
    'TransformerFfn',
    'TransformerEncoderLayer',
]


class TransformerFfn(nn.Sequential):
    def __init__(self, hidden_size: int, dropout: float, bias: bool = True, *, in_size: int) -> None:
        super(TransformerFfn, self).__init__(
            nn.Linear(in_size, hidden_size, bias=bias),
            nn.Tanh(),
            nn.Dropout(p=dropout, inplace=True),
            nn.Linear(hidden_size, in_size, bias=bias),
        )

        self.in_size = in_size
        self.dropout = dropout
        self.bias = bias

    def extra_repr(self) -> str:
        return ', '.join([
            f'{self.in_size}',
            f'dropout={self.dropout}',
            f'bias={self.bias}',
        ])

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.extra_repr()})'


class TransformerEncoderLayer(nn.Module):
    def __init__(self, hidden_size: int = 2048, num_heads: int = 8,
                 att_dropout: float = 0., ffn_dropout: float = 0., bias: bool = True, *,
                 in_size: int) -> None:
        super(TransformerEncoderLayer, self).__init__()

        self.in_size = in_size
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.att_dropout = att_dropout
        self.ffn_dropout = ffn_dropout
        self.bias = bias

        self.att = MultiHeadAttention(
            num_heads=num_heads,
            head_dim=in_size // num_heads,
            dropout=att_dropout, bias=bias,
            q_dim=in_size, k_dim=in_size, v_dim=in_size,
        )
        self.ffn = TransformerFfn(
            dropout=ffn_dropout, bias=bias,
            in_size=in_size, hidden_size=hidden_size,
        )

        self.norm1 = nn.LayerNorm(in_size)
        self.norm2 = nn.LayerNorm(in_size)
        self.dropout1 = nn.Dropout(ffn_dropout)
        self.dropout2 = nn.Dropout(ffn_dropout)

    def forward(self, src: Tensor, mask: Optional[Tensor] = None) -> Tensor:
        src = self.norm1(src + self.dropout1(self.att(q=src, k=src, v=src, mask=mask)))
        src = self.norm2(src + self.dropout2(self.ffn(src)))
        return src

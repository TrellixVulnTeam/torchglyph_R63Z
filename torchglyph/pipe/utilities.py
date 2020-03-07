from typing import Tuple

from torch import Tensor


def cum_index(t: Tensor, a: int) -> Tuple[Tensor, int]:
    return t + a, t.size(0) + a
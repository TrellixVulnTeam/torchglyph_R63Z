import logging
from collections import Counter
from typing import Tuple, List, Union

from torchglyph.proc.abc import Recur, Proc
from torchglyph.vocab import Vocab, Vectors, Glove


class UpdateCounter(Proc):
    def __call__(self, data: Union[str, List[str]], counter: Counter, **kwargs) -> Union[str, List[str]]:
        if isinstance(data, str):
            data = (data,)
        counter.update(data)
        return data


class BuildVocab(Proc):
    def __init__(self, unk_token: str = '<unk>', pad_token: str = None,
                 special_tokens: Tuple[str, ...] = (),
                 max_size: int = None, min_freq: int = 1) -> None:
        super(BuildVocab, self).__init__()
        self.unk_token = unk_token
        self.pad_token = pad_token
        self.special_tokens = special_tokens
        self.max_size = max_size
        self.min_freq = min_freq

    def extra_repr(self) -> str:
        return f', '.join([
            f'max_size={self.max_size if self.max_size is not None else "inf"}',
            f'min_freq={self.min_freq}',
        ])

    def __call__(self, vocab: Counter, **kwargs) -> Vocab:
        return Vocab(
            counter=vocab,
            unk_token=self.unk_token,
            pad_token=self.pad_token,
            special_tokens=self.special_tokens,
            max_size=self.max_size, min_freq=self.min_freq,
        )


class StatsVocab(Proc):
    def __call__(self, vocab: Vocab, name: str, **kwargs) -> Vocab:
        assert vocab is not None
        assert name is not None

        tok_min, occ_min = min(vocab.freq.items(), key=lambda x: x[1])
        tok_max, occ_max = max(vocab.freq.items(), key=lambda x: x[1])
        tok_cnt = len(vocab.freq.values())
        occ_avg = sum(vocab.freq.values()) / max(1, tok_cnt)

        logging.info(f"{vocab.__class__.__name__} '{name}' has {tok_cnt} token(s) => "
                     f"{occ_avg:.1f} occurrence(s)/token ["
                     f"{occ_min} :: '{tok_min}', "
                     f"{occ_max} :: '{tok_max}']")

        return vocab


class Numbering(Recur):
    def process(self, datum: str, vocab: Vocab, **kwargs) -> int:
        return vocab.stoi[datum]


class LoadVectors(Proc):
    def __init__(self, vectors: Vectors) -> None:
        super(LoadVectors, self).__init__()
        self.vectors = vectors

    def extra_repr(self) -> str:
        return f'{self.vectors.extra_repr()}'

    def __call__(self, vocab: Vocab, name: str, **kwargs) -> Vocab:
        assert vocab is not None, f"did you forget '{BuildVocab.__name__}' before '{LoadVectors.__name__}'?"

        tok, occ = vocab.load_vectors(self.vectors)
        tok = tok / max(1, len(vocab.freq.values())) * 100
        occ = occ / max(1, sum(vocab.freq.values())) * 100
        logging.info(f"{self.vectors} hits {tok:.1f}% tokens and {occ:.1f}% occurrences of {Vocab.__name__} '{name}'")
        return vocab


class LoadGlove(LoadVectors):
    def __init__(self, name: str, dim: int) -> None:
        super(LoadGlove, self).__init__(
            vectors=Glove(name=name, dim=dim),
        )

from collections import Counter
from typing import Optional, Union, List, Any

from torchglyph.proc import Proc, PaLP, compress, subs
from torchglyph.vocab import Vocab


class Pipe(object):
    def __init__(self, pre: PaLP = None, vocab: PaLP = None, post: PaLP = None, batch: PaLP = None) -> None:
        super(Pipe, self).__init__()

        self.vocab: Optional[Union[Vocab]] = None

        self._pre_proc = Proc.from_list(compress(pre))
        self._vocab_proc = Proc.from_list(compress(vocab))
        self._post_proc = Proc.from_list(compress(post))
        self._batch_proc = Proc.from_list(compress(batch))

    def new_(self, pre: PaLP = ..., vocab: PaLP = ..., post: PaLP = ..., batch: PaLP = ...) -> 'Pipe':
        self._pre_proc = Proc.from_list(subs(procs=pre, repl=self._pre_proc))
        self._vocab_proc = Proc.from_list(subs(procs=vocab, repl=self._vocab_proc))
        self._post_proc = Proc.from_list(subs(procs=post, repl=self._post_proc))
        self._batch_proc = Proc.from_list(subs(procs=batch, repl=self._batch_proc))
        return self

    def extra_repr(self):
        return ',\n  '.join([
            f'pre={self._pre_proc}',
            f'vocab={self._vocab_proc}',
            f'post={self._post_proc}',
            f'batch={self._batch_proc}',
        ])

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(\n  {self.extra_repr()}\n)'

    def preprocess(self, *datasets) -> Counter:
        counter = Counter()
        for dataset in datasets:
            for key, pipe in dataset.pipes.items():
                flag = f'@{key}_{self.preprocess.__name__}_done'
                if pipe is self and not getattr(dataset, flag, False):
                    dataset.data[key] = [
                        self._pre_proc(ins, counter=counter)
                        for ins in dataset.data[key]
                    ]
                    setattr(dataset, flag, True)

        return counter

    def postprocess(self, *datasets) -> 'Pipe':
        _ = self.preprocess(*datasets)
        for dataset in datasets:
            for name, pipe in dataset.pipes.items():
                flag = f'@{name}_{self.postprocess.__name__}_done'
                if pipe is self and not getattr(dataset, flag, False):
                    dataset.data[name] = [
                        self._post_proc(ins, vocab=self.vocab)
                        for ins in dataset.data[name]
                    ]
                    setattr(dataset, flag, True)

        return self

    def build_vocab(self, *datasets) -> 'Pipe':
        counter = self.preprocess(*datasets)
        vocab = self._vocab_proc(counter)
        if isinstance(vocab, Vocab):
            self.vocab = vocab
        else:
            raise ValueError(f"vocabulary building produced '{type(vocab).__name__}', "
                             f"instead of '{Vocab.__name__}'")
        return self

    def collate_fn(self, collected_ins: List[Any]) -> Any:
        return self._batch_proc(collected_ins, vocab=self.vocab)

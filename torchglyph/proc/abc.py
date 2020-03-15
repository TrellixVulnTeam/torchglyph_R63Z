from abc import ABCMeta, abstractmethod
from typing import Optional, Union, Any, List, Callable, Tuple

from torchglyph.vocab import Vocab

PaLP = Union[Optional['Proc'], List[Optional['Proc']]]


# TODO: is allowing ellipsis generally safe?
def compress(procs: PaLP, allow_ellipsis: bool = True) -> List['Proc']:
    if procs is None or isinstance(procs, Identity):
        return []
    if procs is ...:
        if allow_ellipsis:
            return [...]
        else:
            raise ValueError(f'ellipsis is not allowed here')
    if isinstance(procs, Chain):
        return procs.procs
    if isinstance(procs, Proc):
        return [procs]
    return [x for proc in procs for x in compress(proc, allow_ellipsis=allow_ellipsis)]


def subs(procs: PaLP, repl: 'Proc') -> PaLP:
    return [repl if proc is ... else proc for proc in compress(procs, allow_ellipsis=True)]


class Proc(object, metaclass=ABCMeta):
    @classmethod
    def from_list(cls, procs: List['Proc']) -> 'Proc':
        if len(procs) == 0:
            return Identity()
        if len(procs) == 1:
            return procs[0]
        return Chain(procs)

    def extra_repr(self) -> str:
        return f''

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.extra_repr()})'

    def __add__(self, rhs: PaLP) -> 'Proc':
        return self.from_list([self] + compress(rhs))

    def __radd__(self, lhs: PaLP) -> 'Proc':
        return self.from_list(compress(lhs) + [self])

    @abstractmethod
    def __call__(self, x: Any, *args, **kwargs) -> Any:
        raise NotImplementedError


class Identity(Proc):
    def __repr__(self) -> str:
        return f'{None}'

    def __call__(self, x: Any, *args, **kwargs) -> Any:
        return x


class Chain(Proc):
    def __init__(self, procs: PaLP) -> None:
        super(Chain, self).__init__()
        self.procs = compress(procs)

    def extra_repr(self) -> str:
        return ' + '.join([str(proc) for proc in self.procs])

    def __repr__(self) -> str:
        return f'{self.extra_repr()}'

    def __add__(self, rhs: PaLP) -> 'Proc':
        return self.from_list(self.procs + compress(rhs))

    def __radd__(self, lhs: PaLP) -> 'Proc':
        return self.from_list(compress(lhs) + self.procs)

    def __call__(self, x: Any, *args, **kwargs) -> Any:
        for process in self.procs:
            x = process(x, *args, **kwargs)
        return x


class Lift(Proc):
    def __init__(self, proc: Proc) -> None:
        super(Lift, self).__init__()
        self.proc = proc

    def __repr__(self) -> str:
        return f'[{self.proc.__repr__()}]'

    def __call__(self, data: Any, *args, **kwargs) -> Any:
        return type(data)([self.proc(datum, *args, **kwargs) for datum in data])


class Recur(Proc, metaclass=ABCMeta):
    @abstractmethod
    def is_target(self, data: Any, *args, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    def process(self, data: str, *args, **kwargs) -> Any:
        raise NotImplementedError

    def __call__(self, data: Any, *args, **kwargs) -> Any:
        if self.is_target(data, *args, **kwargs):
            return self.process(data, *args, **kwargs)
        return type(data)([self(datum, *args, **kwargs) for datum in data])


class RecurStr(Recur, metaclass=ABCMeta):
    def is_target(self, data: str, *args, **kwargs) -> bool:
        return isinstance(data, str)


class Scan(Proc):
    def __init__(self, fn: Callable[[Any, Any], Tuple[Any, Any]], init: Any) -> None:
        super(Scan, self).__init__()
        self.fn = fn
        self.init = init

    def extra_repr(self) -> str:
        return f'fn={self.fn.__name__}, init={self.init}'

    def __call__(self, xs: List[Any], vocab: Vocab = None, **kwargs) -> List[Any]:
        z = self.init

        ys = []
        for x in xs:
            y, z = self.fn(x, z)
            ys.append(y)
        return type(xs)(ys)

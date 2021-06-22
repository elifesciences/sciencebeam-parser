from typing import Iterable


def iter_ids(prefix: str) -> Iterable[str]:
    index = 0
    while True:
        yield f'{prefix}{index}'
        index += 1

from typing import List


def dict_to_args(props: dict) -> List[str]:
    return [
        '--%s' % key if isinstance(value, bool) and value
        else '--%s=%s' % (key, value)
        for key, value in props.items()
    ]

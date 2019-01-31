from apache_beam import Map

NAME = __name__


def MapKeys(key_fn, label='MapKeys'):
    return label >> Map(lambda kv: (key_fn(kv[0]), kv[1]))


def MapValues(value_fn, label='MapValues'):
    return label >> Map(lambda kv: (kv[0], value_fn(kv[1])))

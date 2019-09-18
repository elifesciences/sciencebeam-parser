from collections import namedtuple

import subprocess


Office = namedtuple('Office', ['python'])


def find_offices():
    return [Office(python='python3')]


def find_pyuno_office():
    offices = find_offices()
    if not offices:
        raise RuntimeError('no suitable office installation found')
    for office in offices:
        try:
            subprocess.check_output([office.python, '-c', 'import uno, unohelper'])
            return office
        except subprocess.CalledProcessError:
            pass
        except OSError:
            pass
    raise RuntimeError(
        'none of the potential office installations seem to function, tried: %s' % offices
    )

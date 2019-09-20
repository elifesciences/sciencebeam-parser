import os
from collections import namedtuple
from typing import List

import subprocess


Office = namedtuple('Office', ['python'])


def find_offices():
    return [Office(python=os.environ.get('UNO_PYTHON_PATH') or 'python3')]


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


def get_start_listener_command(port: int) -> List[str]:
    return [
        'soffice',
        '--headless',
        '--invisible',
        '--nocrashreport',
        '--nodefault',
        '--nofirststartwizard',
        '--nologo',
        '--norestore',
        '--accept=socket,host=localhost,port={port};urp;StarOffice.ServiceManager'.format(
            port=port
        )
    ]

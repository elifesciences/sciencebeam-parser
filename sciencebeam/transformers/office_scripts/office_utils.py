import os
from collections import namedtuple
from typing import List

import subprocess


Office = namedtuple('Office', ['unopath', 'python'])


class EnvironmentVariables:
    UNO_PATH = 'UNO_PATH'
    UNO_PYTHON_PATH = 'UNO_PYTHON_PATH'
    UNO_OFFICE_BINARY_PATH = 'UNO_OFFICE_BINARY_PATH'


class DefaultValues:
    UNO_PATH = '/usr/lib/python3/dist-packages'
    UNO_PYTHON_PATH = 'python3'
    UNO_OFFICE_BINARY_PATH = '/usr/lib/libreoffice/program/soffice.bin'


def get_uno_path() -> str:
    return os.environ.get('UNO_PATH') or DefaultValues.UNO_PATH


def get_uno_python_path() -> str:
    return os.environ.get('UNO_PYTHON_PATH') or DefaultValues.UNO_PYTHON_PATH


def get_uno_office_binary_path() -> str:
    return os.environ.get('UNO_OFFICE_BINARY_PATH') or DefaultValues.UNO_OFFICE_BINARY_PATH


def find_offices():
    return [Office(
        unopath=get_uno_path(),
        python=get_uno_python_path()
    )]


def find_pyuno_office():
    offices = find_offices()
    if not offices:
        raise RuntimeError('no suitable office installation found')
    for office in offices:
        try:
            subprocess.check_output(
                [office.python, '-c', 'import uno, unohelper'],
                env={'PYTHONPATH': office.unopath}
            )
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
        get_uno_office_binary_path(),
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

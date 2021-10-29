import logging
import os
import socket
import time
from contextlib import closing
from threading import Lock, current_thread
from typing import Optional, Sequence

from sciencebeam_parser.utils.background_process import (
    BackgroundProcess,
    ChildProcessReturnCodeError,
    CommandRestartableBackgroundProcess,
    exec_with_logging
)

from .office_scripts import get_office_script_directory
from .office_scripts.office_utils import find_pyuno_office, get_start_listener_command


LOGGER = logging.getLogger(__name__)


def change_ext(path: str, old_ext: Optional[str], new_ext: str) -> str:
    if old_ext is None:
        old_ext = os.path.splitext(path)[1]
        if old_ext == '.gz':
            path = path[:-len(old_ext)]
            old_ext = os.path.splitext(path)[1]
    if old_ext and path.endswith(old_ext):
        return path[:-len(old_ext)] + new_ext
    return path + new_ext


class UnoConnectionError(ConnectionError):
    pass


def _exec_pyuno_script(
    script_filename: str,
    args: Sequence[str],
    process_timeout: Optional[float] = None,
    daemon: bool = False
) -> BackgroundProcess:
    if not os.path.exists(script_filename):
        from glob import glob  # pylint: disable=import-outside-toplevel
        LOGGER.info(
            '%s does not exist, found: %s',
            script_filename,
            list(glob('%s/**/*' % os.path.dirname(script_filename)))
        )
        raise RuntimeError('%s does not exist' % script_filename)
    office = find_pyuno_office()
    command = [
        office.uno_python_path,
        script_filename
    ] + list(args)
    env = {'PYTHONPATH': office.uno_path}
    LOGGER.info('executing: %s (env: %s)', command, env)
    try:
        p = exec_with_logging(
            command,
            env=env,
            logging_prefix='converter',
            process_timeout=process_timeout,
            daemon=daemon
        )
    except ChildProcessReturnCodeError as e:
        if e.returncode == 9:
            raise UnoConnectionError('failed to connect to uno server: %s' % e.returncode) from e
        raise type(e)(
            'failed to run converter: %s' % e.returncode,
            returncode=e.returncode
        ) from e
    return p


def _exec_doc_converter(
    args: Sequence[str],
    enable_debug: bool = False,
    process_timeout: Optional[float] = None,
    daemon: bool = False
) -> BackgroundProcess:
    office_scripts_directory = get_office_script_directory()
    doc_converter_script_filename = os.path.abspath(os.path.join(
        office_scripts_directory,
        'doc_converter.py'
    ))
    if enable_debug:
        args = ['--debug'] + list(args)
    return _exec_pyuno_script(
        doc_converter_script_filename,
        args,
        process_timeout=process_timeout,
        daemon=daemon
    )


class ListenerProcess(CommandRestartableBackgroundProcess):
    def __init__(self, port: int, host: str = '127.0.0.1', connect_timeout: int = 10):
        super().__init__(
            command=get_start_listener_command(port=port),
            name='listener on port %s' % port,
            logging_prefix='listener[port:%s]' % port,
            stop_at_exit=True
        )
        self.port = port
        self.host = host
        self.connect_timeout = connect_timeout

    def __repr__(self) -> str:
        return (
            '{type_name}('
            'port={self.port}'
            ', host={self.host}'
            ', connect_timeout={self.connect_timeout}'
            ', command={command}'
            ', process={self.process}'
            ')'
        ).format(
            type_name=type(self).__name__,
            self=self,
            command=repr(self.command)
        )

    def is_alive(self) -> bool:
        if not self.is_running():
            return False
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(self.connect_timeout)  # pylint: disable=no-member
            if sock.connect_ex((self.host, self.port)) == 0:  # pylint: disable=no-member
                return True
        return False

    def wait_for_is_alive(self, timeout: float) -> bool:
        start_time = time.monotonic()
        while not self.is_alive():
            if not self.is_running():
                return False
            if time.monotonic() - start_time >= timeout:
                return False
            time.sleep(0.5)
        return True

    def start_and_check_alive(self, timeout=10, **kwargs) -> None:
        super().start(**kwargs)
        if self.wait_for_is_alive(timeout=timeout):
            return
        self.stop_if_running()
        assert self.process is not None
        if self.process.returncode == 81:
            # see https://bugs.documentfoundation.org/show_bug.cgi?id=107912
            #     "headless firstrun crashes (exit code 81)"
            LOGGER.info('detected first-run error code 81, re-trying..')
            self.start_and_check_alive(timeout=timeout, **kwargs)
            return
        raise ConnectionError('failed to start listener (unable to connect)')

    def start_listener_if_not_running(self, max_uptime: float = None, **kwargs) -> None:
        if self.is_alive():
            uptime = self.get_uptime()
            if not max_uptime or uptime <= max_uptime:
                return
            LOGGER.info('stopping listener, exceeded max uptime: %.3f > %.3f', uptime, max_uptime)
            self.stop()
        self.start_and_check_alive(**kwargs)


class DocConverterWrapper:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        port: int = 2003,
        enable_debug: bool = False,
        no_launch: bool = True,
        keep_listener_running: bool = True,
        process_timeout: Optional[float] = None,
        max_uptime: float = 10,
        stop_listener_on_error: bool = True
    ):
        self.port = port
        self.enable_debug = enable_debug
        self.no_launch = no_launch
        self.keep_listener_running = keep_listener_running
        self.process_timeout = process_timeout
        self.max_uptime = max_uptime
        self.stop_listener_on_error = stop_listener_on_error
        self._listener_process = ListenerProcess(port=port)
        self._lock = Lock()
        self._concurrent_count = 0

    def __repr__(self) -> str:
        return (
            '{type_name}('
            'port={self.port}'
            ', keep_listener_running={self.keep_listener_running}'
            ', _listener_process={self._listener_process}'
            ')'
        ).format(
            type_name=type(self).__name__,
            self=self
        )

    def start_listener_if_not_running(self) -> None:
        self._listener_process.start_listener_if_not_running(max_uptime=self.max_uptime)

    def stop_listener_if_running(self) -> None:
        self._listener_process.stop_if_running()

    def _do_convert(
        self,
        temp_source_filename: str,
        output_type: str = 'pdf',
        remove_line_no: bool = True,
        remove_header_footer: bool = True,
        remove_redline: bool = True
    ) -> str:
        if self.no_launch:
            self.start_listener_if_not_running()

        temp_target_filename = change_ext(
            temp_source_filename, None, '-output.%s' % output_type
        )

        args = []
        args.extend([
            'convert',
            '--format', output_type
        ])
        if remove_line_no:
            args.append('--remove-line-no')
        if remove_header_footer:
            args.append('--remove-header-footer')
        if remove_redline:
            args.append('--remove-redline')
        args.extend([
            '--port', str(self.port),
            '--output-file', str(temp_target_filename),
            temp_source_filename
        ])
        if self.no_launch:
            args.append('--no-launch')
        if self.keep_listener_running:
            args.append('--keep-listener-running')
        try:
            _exec_doc_converter(
                args,
                enable_debug=self.enable_debug,
                process_timeout=self.process_timeout
            )
        except UnoConnectionError:
            self.stop_listener_if_running()
            raise
        except Exception:
            if self.stop_listener_on_error:
                self.stop_listener_if_running()
            raise

        if not os.path.exists(temp_target_filename):
            raise RuntimeError('temp target file missing: %s' % temp_target_filename)
        return temp_target_filename

    def convert(self, *args, **kwargs) -> str:
        thread_id = current_thread().ident
        try:
            self._concurrent_count += 1
            LOGGER.debug(
                'attempting to aquire lock, thread id: %s, concurrent count: %s',
                thread_id, self._concurrent_count
            )
            with self._lock:
                LOGGER.debug(
                    'aquired lock, thread id: %s, concurrent count: %s',
                    thread_id, self._concurrent_count
                )
                return self._do_convert(*args, **kwargs)
        finally:
            self._concurrent_count -= 1
            LOGGER.debug(
                'exiting convert (released lock if it was aquired),'
                ' thread id: %s, concurrent count: %s',
                thread_id, self._concurrent_count
            )

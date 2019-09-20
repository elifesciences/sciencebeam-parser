import logging
import os
from threading import Lock, current_thread

from sciencebeam_utils.utils.file_path import (
    change_ext
)

from sciencebeam.utils.background_process import (
    CommandRestartableBackgroundProcess,
    exec_with_logging
)

from .office_scripts import get_office_script_directory
from .office_scripts.office_utils import find_pyuno_office, get_start_listener_command


LOGGER = logging.getLogger(__name__)


class UnoConnectionError(RuntimeError):
    pass


def _exec_pyuno_script(script_filename, args, process_timeout=None, daemon=False):
    if not os.path.exists(script_filename):
        from glob import glob
        LOGGER.info(
            '%s does not exist, found: %s',
            script_filename,
            list(glob('%s/**/*' % os.path.dirname(script_filename)))
        )
        raise RuntimeError('%s does not exist' % script_filename)
    office = find_pyuno_office()
    command = [
        office.python,
        script_filename
    ] + args
    LOGGER.info('executing: %s', command)
    p = exec_with_logging(
        command,
        'converter output: ',
        process_timeout=process_timeout,
        daemon=daemon
    )
    if not daemon:
        LOGGER.debug('converter return code: %s', p.returncode)
        if p.returncode == 9:
            raise UnoConnectionError('failed to connect to uno server: %s' % p.returncode)
        if p.returncode != 0:
            raise RuntimeError('failed to run converter: %s' % p.returncode)
    return p


def _exec_doc_converter(args, enable_debug=False, process_timeout=None, daemon=False):
    office_scripts_directory = get_office_script_directory()
    doc_converter_script_filename = os.path.abspath(os.path.join(
        office_scripts_directory,
        'doc_converter.py'
    ))
    if enable_debug:
        args = ['--debug'] + args
    return _exec_pyuno_script(
        doc_converter_script_filename,
        args,
        process_timeout=process_timeout,
        daemon=daemon
    )


class DocConverterWrapper:  # pylint: disable=too-many-instance-attributes
    def __init__(
            self, port=2003, enable_debug=False,
            no_launch=True,
            keep_listener_running=True,
            process_timeout=None):
        self.port = port
        self.enable_debug = enable_debug
        self.no_launch = no_launch
        self.keep_listener_running = keep_listener_running
        self.process_timeout = process_timeout
        self._listener_process = CommandRestartableBackgroundProcess(
            command=get_start_listener_command(port=port),
            name='listener on port %s' % port,
            logging_prefix='listener[port:%s]' % port,
            stop_at_exit=True
        )
        self._lock = Lock()
        self._concurrent_count = 0

    def start_listener_if_not_running(self):
        self._listener_process.start_if_not_running()

    def stop_listener_if_running(self):
        self._listener_process.stop_if_running()

    def _do_convert(
            self, temp_source_filename, output_type: str = 'pdf',
            remove_line_no: bool = True,
            remove_header_footer: bool = True,
            remove_redline: bool = True):
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

        if not os.path.exists(temp_target_filename):
            raise RuntimeError('temp target file missing: %s' % temp_target_filename)
        return temp_target_filename

    def convert(self, *args, **kwargs):
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

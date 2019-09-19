import logging
import subprocess
import os
import atexit
import signal
from threading import Thread, Timer, Lock
from functools import partial

from sciencebeam_utils.utils.file_path import (
    change_ext
)

from .office_scripts import get_office_script_directory
from .office_scripts.office_utils import find_pyuno_office


def get_logger():
    return logging.getLogger(__name__)


def stream_lines_to_logger(lines, logger, prefix=''):
    for line in lines:
        line = line.strip()
        if line:
            logger.info('%s%s', prefix, line)


def stop_process(process: subprocess.Popen):
    get_logger().info('sending SIGINT signal to process %s', process.pid)
    try:
        process.send_signal(signal.SIGINT)
    except (AttributeError, OSError):
        process.terminate()


def _exec_with_logging(command, logging_prefix, process_timeout=None, daemon=False):
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if not daemon:
        timer = None
        if process_timeout:
            timer = Timer(process_timeout, lambda: stop_process(p))
            timer.start()
        stream_lines_to_logger(p.stdout, get_logger(), logging_prefix)
        p.wait()
        if timer:
            timer.cancel()
        return p
    t = Thread(target=partial(
        stream_lines_to_logger,
        lines=p.stdout,
        logger=get_logger(),
        prefix=logging_prefix
    ))
    t.daemon = True
    t.start()
    return p


def _exec_pyuno_script(script_filename, args, process_timeout=None, daemon=False):
    if not os.path.exists(script_filename):
        from glob import glob
        get_logger().info(
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
    get_logger().info('executing: %s', command)
    p = _exec_with_logging(
        command,
        'converter output: ',
        process_timeout=process_timeout,
        daemon=daemon
    )
    if not daemon:
        get_logger().debug('converter return code: %s', p.returncode)
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


class DocConverterWrapper:
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
        self._listener_process = None
        self._lock = Lock()

    def start_listener(self):
        get_logger().info('starting listener on port %s', self.port)
        self._listener_process = _exec_doc_converter([
            'start-listener',
            '--port', str(self.port)
        ], enable_debug=self.enable_debug, daemon=True)
        atexit.register(self.stop_listener_if_running)

    def start_listener_if_not_running(self):
        if self._listener_process:
            self._listener_process.poll()
            if self._listener_process.returncode is not None:
                get_logger().info('listener has stopped: %s', self._listener_process.returncode)
        if not self._listener_process:
            self.start_listener()

    def stop_listener_if_running(self):
        if self._listener_process:
            get_logger().info('stopping listener')
            self._listener_process.send_signal(signal.SIGINT)

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
        _exec_doc_converter(
            args,
            enable_debug=self.enable_debug,
            process_timeout=self.process_timeout
        )

        if not os.path.exists(temp_target_filename):
            raise RuntimeError('temp target file missing: %s' % temp_target_filename)
        return temp_target_filename

    def convert(self, *args, **kwargs):
        with self._lock:
            return self._do_convert(*args, **kwargs)

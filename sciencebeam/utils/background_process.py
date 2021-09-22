import atexit
import logging
import signal
import subprocess
import time
from functools import partial
from threading import Timer, Thread
from typing import Union, List


LOGGER = logging.getLogger(__name__)


class ChildProcessReturnCodeError(ChildProcessError):
    def __init__(self, *args, returncode: int, process=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.returncode = returncode
        self.process = process


class ChildProcessTimeoutError(ChildProcessReturnCodeError):
    pass


class BackgroundProcess:
    def __init__(self, process: subprocess.Popen):
        self.process = process
        self._stopped_by_timeout = False
        self._created_time = time.monotonic()
        self._returncode = None

    def __repr__(self):
        return (
            '{type_name}('
            'pid={self.process.pid}'
            ', returncode={self.process.returncode}'
            ')'
        ).format(
            type_name=type(self).__name__,
            self=self
        )

    def is_running(self):
        self.process.poll()
        return self.returncode is None

    @property
    def returncode(self):
        if self.process.returncode != self._returncode:
            self._returncode = self.process.returncode
            LOGGER.debug('process(pid=%s).returncode: %s', self.process.pid, self._returncode)
        return self._returncode

    @property
    def pid(self):
        return self.process.pid

    def send_signal(self, sig):
        if self.process.returncode is not None:
            LOGGER.debug(
                'not sending signal %r, process has already stopped: %s',
                sig, self.process.pid
            )
            return
        LOGGER.info('sending %s to process %s', sig, self.process.pid)
        self.process.send_signal(sig)

    def terminate(self):
        self.send_signal(signal.SIGINT)

    def kill(self):
        self.send_signal(signal.SIGKILL)

    def kill_if_runing(self):
        if not self.is_running():
            return
        self.kill()

    def wait(self) -> int:
        self.process.wait()
        return self.returncode

    def get_uptime(self) -> float:
        return time.monotonic() - self._created_time

    def stop(self, wait: bool = True, kill_timeout: int = 60):
        self.terminate()
        if kill_timeout:
            Timer(kill_timeout, self.kill_if_runing).start()
        if wait:
            LOGGER.info('waiting for process(pid=%s) to stop', self.process.pid)
            self.wait()
            LOGGER.info(
                'process(pid=%s) has stopped with returncode: %s',
                self.process.pid, self.returncode
            )

    def stop_due_to_timeout(self, **kwargs):
        LOGGER.info('process timeout, stopping: %s', self.process.pid)
        self._stopped_by_timeout = True
        self.stop(**kwargs)

    def is_stopped_by_timeout(self):
        return self._stopped_by_timeout

    def check_returncode(self):
        returncode = self.process.returncode
        if returncode is None:
            return
        if self.is_stopped_by_timeout():
            LOGGER.debug('process stopped by timeout, return code: %s', returncode)
            raise ChildProcessTimeoutError(
                'process stopped by timeout, return code: %s' % returncode,
                returncode=returncode
            )
        if returncode != 0:
            LOGGER.debug('process failed with return code: %s', returncode)
            raise ChildProcessReturnCodeError(
                'process failed with return code: %s' % returncode,
                returncode=returncode
            )

    def stop_if_running(self, **kwargs):
        if not self.is_running():
            return
        self.stop(**kwargs)


def stream_lines_to_logger(lines, logger, prefix=''):
    for line in lines:
        line = line.strip()
        if line:
            logger.info('%s%s', prefix, line)


def exec_with_logging(
        command: Union[str, List[str]],
        logging_prefix: str = None,
        process_timeout: int = None,
        daemon: bool = False,
        check_returncode: bool = True,
        **kwargs) -> BackgroundProcess:
    p = BackgroundProcess(subprocess.Popen(  # pylint: disable=consider-using-with
        command,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        **kwargs
    ))
    if logging_prefix is None:
        logging_prefix = 'process'
    logging_prefix += '[pid:%s]: ' % p.process.pid
    if not daemon:
        timer = None
        if process_timeout:
            timer = Timer(process_timeout, p.stop_due_to_timeout)
            timer.start()
        stream_lines_to_logger(p.process.stdout, LOGGER, logging_prefix)
        p.wait()
        if timer:
            timer.cancel()
        if check_returncode:
            p.check_returncode()
        return p
    t = Thread(target=partial(
        stream_lines_to_logger,
        lines=p.process.stdout,
        logger=LOGGER,
        prefix=logging_prefix
    ))
    t.daemon = True
    t.start()
    return p


class CommandRestartableBackgroundProcess:
    def __init__(
            self,
            command: Union[str, List[str]],
            name: str = None,
            logging_prefix: str = None,
            stop_at_exit: bool = False):
        self.command = command
        self.name = name
        self.logging_prefix = logging_prefix
        self.process = None
        self.stop_at_exit = stop_at_exit
        self._atexit_registered = False

    def stop(self, wait: bool = True):
        if self.process:
            self.process.stop(wait=wait)

    def stop_if_running(self, wait: bool = True, **kwargs):
        if self.process:
            self.process.stop_if_running(wait=wait, **kwargs)

    def start(self, stop: bool = True):
        if stop:
            self.stop_if_running(wait=True)
        if self.stop_at_exit and not self._atexit_registered:
            atexit.register(self.stop_if_running)
            self._atexit_registered = True
        LOGGER.info('starting %s', self.name)
        LOGGER.debug('running background command: %s', self.command)
        self.process = exec_with_logging(
            self.command,
            logging_prefix=self.logging_prefix or self.name,
            daemon=True
        )

    def is_running(self):
        return self.process and self.process.is_running()

    def get_uptime(self) -> float:
        return self.process.get_uptime()

    def start_if_not_running(self):
        if not self.is_running():
            if self.process:
                LOGGER.info('process has stopped, restarting: %s', self.process.pid)
            self.start()

import atexit
import logging
import signal
import subprocess
from functools import partial
from threading import Timer, Thread
from typing import Union, List


LOGGER = logging.getLogger(__name__)


class BackgroundProcess:
    def __init__(self, process: subprocess.Popen):
        self.process = process

    def is_running(self):
        self.process.poll()
        LOGGER.debug('process.returncode: %s', self.process.returncode)
        return self.process.returncode is None

    @property
    def returncode(self):
        return self.process.returncode

    @property
    def pid(self):
        return self.process.pid

    def send_signal(self, sig):
        if self.process.returncode is not None:
            LOGGER.debug('not sending signal, process has already stopped: %s', self.process.pid)
            return
        LOGGER.info('sending %s to process %s', sig, self.process.pid)
        self.process.send_signal(sig)

    def terminate(self):
        self.send_signal(signal.SIGINT)

    def kill(self):
        self.send_signal(signal.SIGKILL)

    def wait(self):
        return self.process.wait()

    def stop(self, wait: bool = True, kill_timeout: int = 60):
        self.terminate()
        if kill_timeout:
            Timer(kill_timeout, self.kill).start()
        if wait:
            LOGGER.info('waiting for process to stop: %s', self.process.pid)
            self.wait()
            LOGGER.info('process has stopped: %s', self.process.pid)

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
        daemon: bool = False) -> BackgroundProcess:
    p = BackgroundProcess(subprocess.Popen(
        command,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ))
    if logging_prefix is None:
        logging_prefix = 'process'
    logging_prefix += '[pid:%s]: ' % p.process.pid
    if not daemon:
        timer = None
        if process_timeout:
            timer = Timer(process_timeout, p.stop)
            timer.start()
        stream_lines_to_logger(p.process.stdout, LOGGER, logging_prefix)
        p.wait()
        if timer:
            timer.cancel()
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

    def stop_if_running(self, **kwargs):
        self.stop(**kwargs)

    def start(self, stop: bool = True):
        if stop:
            self.stop(wait=True)
        if self.stop_at_exit and not self._atexit_registered:
            atexit.register(self.stop)
            self._atexit_registered = True
        LOGGER.info('starting %s', self.name)
        self.process = exec_with_logging(
            self.command,
            logging_prefix=self.logging_prefix or self.name,
            daemon=True
        )

    def is_running(self):
        return self.process and self.process.is_running()

    def start_if_not_running(self):
        if not self.is_running():
            if self.process:
                LOGGER.info('process has stopped, restarting: %s', self.process.pid)
            self.start()

import logging
from threading import Thread
from functools import partial
import shlex
import subprocess
from subprocess import PIPE
import atexit
import os
from zipfile import ZipFile
from shutil import rmtree
from urllib.request import urlretrieve

from sciencebeam_utils.utils.io import makedirs
from sciencebeam_utils.utils.zip import extract_all_with_executable_permission


def get_logger():
    return logging.getLogger(__name__)


def iter_read_lines(reader):
    while True:
        line = reader.readline()
        if not line:
            break
        yield line


def stream_lines_to_logger(lines, logger, prefix=''):
    for line in lines:
        line = line.strip()
        if line:
            logger.info('%s%s', prefix, line)


class GrobidServiceWrapper:
    def __init__(self):
        self.grobid_service_instance = None
        temp_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../../.temp'
        ))
        self.grobid_service_target_directory = os.path.join(
            temp_dir, 'grobid-service'
        )
        self.grobid_service_zip_filename = os.path.join(
            temp_dir, 'grobid-service.zip'
        )
        self.grobid_service_zip_url = (
            'https://storage.googleapis.com/elife-ml/artefacts/grobid-service.zip'
        )

    def stop_service_if_running(self):
        if self.grobid_service_instance is not None:
            get_logger().info('stopping instance: %s', self.grobid_service_instance)
            self.grobid_service_instance.kill()

    def download__grobid_service_zip_if_not_exist(self):
        if not os.path.isfile(self.grobid_service_zip_filename):
            get_logger().info(
                'downloading %s to %s',
                self.grobid_service_zip_url,
                self.grobid_service_zip_filename
            )

            makedirs(os.path.dirname(
                self.grobid_service_zip_filename
            ), exists_ok=True)

            temp_zip_filename = self.grobid_service_zip_filename + '.part'
            if os.path.isfile(temp_zip_filename):
                os.remove(temp_zip_filename)
            urlretrieve(self.grobid_service_zip_url, temp_zip_filename)
            os.rename(temp_zip_filename, self.grobid_service_zip_filename)

    def unzip_grobid_service_zip_if_target_directory_does_not_exist(self):
        if not os.path.isdir(self.grobid_service_target_directory):
            self.download__grobid_service_zip_if_not_exist()
            get_logger().info(
                'unzipping %s to %s',
                self.grobid_service_zip_filename,
                self.grobid_service_target_directory
            )
            temp_target_directory = self.grobid_service_target_directory + '.part'
            if os.path.isdir(temp_target_directory):
                rmtree(temp_target_directory)

            with ZipFile(self.grobid_service_zip_filename, 'r') as zf:
                extract_all_with_executable_permission(
                    zf, temp_target_directory
                )
                sub_dir = os.path.join(temp_target_directory, 'grobid-service')
                if os.path.isdir(sub_dir):
                    os.rename(sub_dir, self.grobid_service_target_directory)
                    rmtree(temp_target_directory)
                else:
                    os.rename(
                        temp_target_directory,
                        self.grobid_service_target_directory
                    )

    def start_service_if_not_running(self):
        get_logger().info('grobid_service_instance: %s', self.grobid_service_instance)
        if self.grobid_service_instance is None:
            self.unzip_grobid_service_zip_if_target_directory_does_not_exist()
            grobid_service_home = os.path.abspath(
                self.grobid_service_target_directory
            )
            cwd = grobid_service_home + '/bin'
            grobid_service_home_jar_dir = grobid_service_home + '/lib'
            class_name = 'org.grobid.service.main.GrobidServiceApplication'
            command_line = 'java -cp "{}/*" {}'.format(
                grobid_service_home_jar_dir, class_name
            )
            args = shlex.split(command_line)
            get_logger().info('command_line: %s', command_line)
            get_logger().info('args: %s', args)
            self.grobid_service_instance = subprocess.Popen(  # pylint: disable=consider-using-with
                args, cwd=cwd, stdout=PIPE, stderr=subprocess.STDOUT
            )
            if self.grobid_service_instance is None:
                raise RuntimeError('failed to start grobid service')
            atexit.register(self.stop_service_if_running)
            pstdout = self.grobid_service_instance.stdout
            out_prefix = 'stdout: '
            while True:
                line = pstdout.readline().strip()
                if line:
                    get_logger().info('%s%s', out_prefix, line)
                if 'jetty.server.Server: Started' in line:
                    get_logger().info('grobid service started successfully')
                    break
                if 'ERROR' in line or 'Error' in line:
                    raise RuntimeError(
                        'failed to start grobid service due to {}'.format(line)
                    )
            t = Thread(target=partial(
                stream_lines_to_logger,
                lines=iter_read_lines(pstdout),
                logger=get_logger(),
                prefix=out_prefix
            ))
            t.daemon = True
            t.start()


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    GrobidServiceWrapper().start_service_if_not_running()

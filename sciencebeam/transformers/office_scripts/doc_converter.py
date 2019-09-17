#!/usr/bin/env python3

# This script will run using the default Python 3 environment
# where LibreOffice's scripts are installed to (at least in Ubuntu).
# This converter is very similar to unoconv but has an option to remove
# line numbers, it is also simpler by being more tailored to the use-case.
# https://github.com/dagwieers/unoconv

# pylint: skip-file

from __future__ import absolute_import, print_function

import argparse
import os
import mimetypes
import logging
import subprocess
import sys
import atexit
from time import sleep
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue  # pylint: disable=import-error
from com.sun.star.connection import NoConnectException


from com.sun.star.document import RedlineDisplayType


LOGGER = logging.getLogger(__name__)


FILTER_NAME_BY_EXT = {
    'doc': 'MS Word 97',
    'docx': 'Office Open XML Text',
    'dotx': 'Office Open XML Text',
    'rtf': 'Rich Text Format',
    'pdf': 'writer_web_pdf_Export'
}

VALID_OUTPUT_FORMATS = sorted(FILTER_NAME_BY_EXT.keys())


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    convert_parser = subparsers.add_parser('convert')
    convert_parser.add_argument(
        '-f', '--format', type=str, required=True,
        choices=VALID_OUTPUT_FORMATS,
        help='Output format (ext)'
    )
    convert_parser.add_argument(
        '-p', '--port', type=int, default=2002,
        help='Port to the uno listener'
    )

    convert_parser.add_argument(
        'input_file', type=str, nargs='+',
        help='Input files (does not support pdf)'
    )

    convert_parser.add_argument(
        '--remove-line-no', action='store_true', default=False,
        help='remove line number'
    )

    convert_parser.add_argument(
        '--remove-header-footer', action='store_true', default=False,
        help='remove header and footer (including page number)'
    )

    convert_parser.add_argument(
        '--remove-redline', action='store_true', default=False,
        help='remove redlines (track changes, by accepting all changes)'
    )

    convert_parser.add_argument(
        '--keep-listener-running', action='store_true', default=False,
        help='keep listener running in the background'
    )
    convert_parser.add_argument(
        '-n', '--no-launch', action='store_true', default=False,
        help='fail if no listener is found (default: launch one)'
    )

    start_listener_parser = subparsers.add_parser('start-listener')
    start_listener_parser.add_argument(
        '-p', '--port', type=int, default=2002,
        help='Port to the uno listener'
    )

    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='enable debug output'
    )

    args = parser.parse_args(argv)

    if args.debug:
        logging.getLogger().setLevel('DEBUG')

    LOGGER.debug('args: %s', args)

    return args


def get_start_listener_command(port):
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


def get_resolver():
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    return resolver


def connect(resolver, port):
    return resolver.resolve(
        "uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext".format(
            port=port
        )
    )


def connect_with_timeout(resolver, port, timeout):
    delay = 0.5
    elapsed = 0.0
    while True:
        try:
            return connect(resolver, port)
        except NoConnectException as e:
            if elapsed >= timeout:
                LOGGER.debug(
                    'connection failed, timeout exceeded (%.1f >= %s)',
                    elapsed, timeout
                )
                raise e
            LOGGER.debug('connection failed, try again in %.1f (%.1f)', delay, elapsed)
            sleep(delay)
            elapsed += delay


def start_listener(port):
    LOGGER.debug('starting listener on port %d', port)
    return subprocess.Popen(
        get_start_listener_command(port)
    )


def stop_listener(listener_process):
    LOGGER.debug('stopping listener process with pid: %s', listener_process.pid)
    return listener_process.terminate()


@contextmanager
def managed_connection(resolver, port, no_launch, keep_listener_running):
    timeout = 10
    try:
        yield connect_with_timeout(resolver, port, timeout)
    except NoConnectException as e:
        if no_launch:
            raise e
        LOGGER.debug('failed to connect, try to start listener')
        listener_process = start_listener(port)
        try:
            yield connect_with_timeout(resolver, port, timeout)
        finally:
            if not keep_listener_running:
                stop_listener(listener_process)


@contextmanager
def managed_desktop(connection, keep_listener_running):
    desktop = connection.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", connection
    )
    try:
        yield desktop
    finally:
        try:
            if not keep_listener_running:
                LOGGER.debug('terminate desktop session')
                desktop.terminate()
        except Exception as e:
            LOGGER.warning('caught exception while terminating desktop: %s', e)


def create_property_value(name, value):
    property_value = PropertyValue()
    property_value.Name = name
    property_value.Value = value
    return property_value


def dict_to_property_values(d):
    return tuple([
        create_property_value(key, value)
        for key, value in d.items()
    ])


def property_set_to_dict(property_set):
    return {
        prop.Name: pageStyle.getPropertyValue(prop.Name)
        for prop in pageStyle.getPropertySetInfo().getProperties()
    }


def disable_document_header_footer(document):
    styleFamilies = document.getStyleFamilies()
    pageStyles = styleFamilies.getByName('PageStyles')
    if not styleFamilies.hasByName('PageStyles'):
        return
    for styleName in pageStyles.getElementNames():
        pageStyle = pageStyles.getByName(styleName)
        pageStyle.setPropertyValue('HeaderIsOn', False)
        pageStyle.setPropertyValue('FooterIsOn', False)


def convert_document_file(
        connection,
        desktop,
        input_file,
        output_file,
        output_ext,
        remove_line_no=False,
        remove_redline=False,
        remove_header_footer=False):
    output_filter_name = FILTER_NAME_BY_EXT[output_ext]

    input_file_url = uno.systemPathToFileUrl(os.path.realpath(input_file))
    document = desktop.loadComponentFromURL(
        input_file_url,
        "_blank", 0,
        dict_to_property_values({'Hidden': True, 'ReadOnly': True})
    )

    if not document:
        raise RuntimeError('failed to load document: %s' % input_file_url)

    if remove_line_no:
        document.getLineNumberingProperties().IsOn = False

    if remove_header_footer:
        disable_document_header_footer(document)

    if remove_redline:
        document.setPropertyValue('RedlineDisplayType', RedlineDisplayType.NONE)

    output_url = "file://" + os.path.abspath(output_file)
    LOGGER.debug("output_url: %s", output_url)
    document.storeToURL(
        output_url,
        dict_to_property_values({'FilterName': output_filter_name})
    )


def convert(connection, desktop, args):
    for input_filename in args.input_file:
        LOGGER.info(
            'processing: %s (%s)',
            input_filename,
            '{:,d}'.format(os.path.getsize(input_filename))
        )
        name, input_ext = os.path.splitext(input_filename)
        if input_ext.startswith('.'):
            input_ext = input_ext[1:]
        if input_ext == args.format:
            raise RuntimeError(
                'input and output format should not be the same: %s -> %s' % (
                    input_ext, args.format
                )
            )
        output_filename = name + '.' + args.format
        convert_document_file(
            connection,
            desktop,
            input_filename,
            output_filename,
            args.format,
            remove_line_no=args.remove_line_no,
            remove_header_footer=args.remove_header_footer,
            remove_redline=args.remove_redline
        )


def run(args):
    if args.command == 'convert':
        resolver = get_resolver()
        with managed_connection(
            resolver, args.port,
            no_launch=args.no_launch,
            keep_listener_running=args.keep_listener_running) as connection:

            with managed_desktop(connection, args.keep_listener_running) as desktop:
                convert(connection, desktop, args)
    elif args.command == 'start-listener':
        p = start_listener(args.port)
        atexit.register(
            lambda: stop_listener(p)
        )
        p.wait()
    else:
        raise RuntimeError('invalid command: %s' % args.command)


def main(argv=None):
    args = parse_args(argv)
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()

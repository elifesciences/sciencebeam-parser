import os

from six import text_type

from argparse import ArgumentParser


def add_batch_args(parser: ArgumentParser):
    parser.add_argument(
        '--data-path', type=str, required=True,
        help='base data path'
    )

    source_group = parser.add_argument_group('source')
    source_one_of_group = source_group.add_mutually_exclusive_group(
        required=True
    )
    source_one_of_group.add_argument(
        '--source-path', type=str, required=False,
        help='path to source file(s), relative to data-path'
    )
    source_one_of_group.add_argument(
        '--source-file-list', type=str, required=False,
        help='path to source csv/tsv file list'
    )
    source_group.add_argument(
        '--source-file-column', type=str, required=False, default='url',
        help='the column of the source file list to use'
    )

    parser.add_argument(
        '--limit', type=int, required=False,
        help='limit the number of file pairs to process'
    )

    output_group = parser.add_argument_group('output')
    output_group.add_argument(
        '--output-path', required=False,
        help='Output directory to write results to.'
    )
    output_group.add_argument(
        '--output-suffix', required=False, default='.xml',
        help='Output file suffix to add to the filename (excluding the file extension).'
    )

    parser.add_argument(
        '--resume', action='store_true', default=False,
        help='resume conversion (skip files that already have an output file)'
    )

    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='enable debug output'
    )


def process_batch_args(args):
    args.base_data_path = args.data_path.replace('/*/', '/')

    if not args.output_path:
        args.output_path = os.path.join(
            os.path.dirname(args.base_data_path),
            os.path.basename(args.base_data_path + '-results')
        )


def encode_if_text_type(data):
    return data.encode('utf-8') if isinstance(data, text_type) else data

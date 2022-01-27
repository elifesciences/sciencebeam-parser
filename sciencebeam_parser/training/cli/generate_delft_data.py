import argparse
import logging
import os
from glob import glob
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from lxml import etree

from sciencebeam_trainer_delft.sequence_labelling.reader import (
    load_data_crf_lines
)
from sciencebeam_trainer_delft.sequence_labelling.tag_formatter import (
    TagOutputFormats,
    iter_format_tag_result
)

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutToken
)

from sciencebeam_parser.models.data import DocumentFeaturesContext, ModelDataGenerator
from sciencebeam_parser.models.training_data import TrainingTeiParser

from sciencebeam_parser.resources.default_config import DEFAULT_CONFIG_FILE
from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.app.parser import ScienceBeamParser


LOGGER = logging.getLogger(__name__)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        'ScienceBeam Parser: Generate DELFT Training Data'
    )
    parser.add_argument(
        '--model-name',
        type=str,
        required=True
    )
    parser.add_argument(
        '--tei-source-path',
        type=str,
        required=True
    )
    parser.add_argument(
        '--raw-source-path',
        type=str,
        required=False
    )
    parser.add_argument(
        '--delft-output-path',
        type=str,
        required=True
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args(argv)


def get_raw_file_for_tei_file(
    tei_file: str,
    raw_source_path: str
) -> str:
    tei_suffix = '.tei.xml'
    assert tei_file.endswith(tei_suffix)
    return os.path.join(raw_source_path, os.path.basename(tei_file[:-len(tei_suffix)]))


def get_raw_file_list_for_tei_file_list(
    tei_file_list: Iterable[str],
    raw_source_path: str
) -> Sequence[str]:
    return [
        get_raw_file_for_tei_file(tei_file, raw_source_path=raw_source_path)
        for tei_file in tei_file_list
    ]


def get_training_tei_parser_for_model_name(
    model_name: str,
    sciencebeam_parser: ScienceBeamParser
) -> TrainingTeiParser:
    model = sciencebeam_parser.fulltext_models.get_sequence_model_by_name(model_name)
    try:
        training_tei_parser = model.get_training_tei_parser()
        assert training_tei_parser is not None
        return training_tei_parser
    except NotImplementedError as exc:
        training_tei_parser = None
        raise RuntimeError('unsupported model: %r' % model_name) from exc


def get_data_generator_for_model_name(
    model_name: str,
    sciencebeam_parser: ScienceBeamParser
) -> ModelDataGenerator:
    model = sciencebeam_parser.fulltext_models.get_sequence_model_by_name(model_name)
    return model.get_data_generator(
        document_features_context=DocumentFeaturesContext(
            app_features_context=sciencebeam_parser.app_features_context
        )
    )


def iter_generate_delft_training_data_lines_for_document(  # pylint: disable=too-many-locals
    tei_file: str,
    raw_file: Optional[str],
    training_tei_parser: TrainingTeiParser,
    data_generator: ModelDataGenerator
) -> Iterable[str]:
    tei_root = etree.parse(tei_file).getroot()
    tag_result = training_tei_parser.parse_training_tei_to_tag_result(
        tei_root
    )
    LOGGER.debug('tag_result: %r', tag_result)
    if raw_file:
        with open(raw_file, 'r', encoding='utf-8') as raw_fp:
            texts, features = load_data_crf_lines(
                raw_fp
            )
    else:
        texts = [
            [token_text for token_text, _tag in doc_tag_result]
            for doc_tag_result in tag_result
        ]
        layout_documents = [
            LayoutDocument.for_blocks([
                LayoutBlock.for_tokens([
                    LayoutToken(text=token_text)
                    for token_text in doc_texts
                ])
            ])
            for doc_texts in texts
        ]
        data_line_iterable = list(data_generator.iter_data_lines_for_layout_documents(
            layout_documents
        ))
        _texts, features = load_data_crf_lines(data_line_iterable)
    assert len(texts) == len(tag_result)
    for doc_tokens, doc_tag_result in zip(texts, tag_result):
        assert len(doc_tokens) == len(doc_tag_result)
    LOGGER.debug('features: %r', features)
    yield from iter_format_tag_result(
        tag_result=tag_result,
        output_format=TagOutputFormats.DATA,
        texts=None,
        features=features
    )


def generate_delft_training_data(
    model_name: str,
    tei_source_path: str,
    raw_source_path: str,
    delft_output_path: str,
    sciencebeam_parser: ScienceBeamParser
):
    training_tei_parser = get_training_tei_parser_for_model_name(
        model_name,
        sciencebeam_parser=sciencebeam_parser
    )
    data_generator = get_data_generator_for_model_name(
        model_name,
        sciencebeam_parser=sciencebeam_parser
    )
    LOGGER.debug('tei_source_path: %r', tei_source_path)
    tei_file_list = glob(tei_source_path)
    if not tei_file_list:
        raise RuntimeError('no files found for file pattern %r' % tei_source_path)
    LOGGER.info('tei_file_list: %r', tei_file_list)
    if raw_source_path:
        raw_file_list: Sequence[Optional[str]] = get_raw_file_list_for_tei_file_list(
            tei_file_list,
            raw_source_path=raw_source_path
        )
    else:
        raw_file_list = [None] * len(tei_file_list)
    LOGGER.info('raw_file_list: %r', raw_file_list)
    LOGGER.info('writing to : %r', delft_output_path)
    Path(delft_output_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(delft_output_path).open('w', encoding='utf-8') as data_fp:
        for document_index, (tei_file, raw_file) in enumerate(zip(tei_file_list, raw_file_list)):
            if document_index > 0:
                data_fp.write('\n\n')
            data_fp.writelines(iter_generate_delft_training_data_lines_for_document(
                tei_file=tei_file,
                raw_file=raw_file,
                training_tei_parser=training_tei_parser,
                data_generator=data_generator
            ))


def run(args: argparse.Namespace):
    LOGGER.info('args: %r', args)
    config = AppConfig.load_yaml(
        DEFAULT_CONFIG_FILE
    )
    sciencebeam_parser = ScienceBeamParser.from_config(config)
    generate_delft_training_data(
        model_name=args.model_name,
        tei_source_path=args.tei_source_path,
        raw_source_path=args.raw_source_path,
        delft_output_path=args.delft_output_path,
        sciencebeam_parser=sciencebeam_parser
    )


def main(argv: Optional[List[str]] = None):
    LOGGER.debug('argv: %r', argv)
    args = parse_args(argv)
    if args.debug:
        for name in [__name__, 'sciencebeam_parser', 'sciencebeam_trainer_delft']:
            logging.getLogger(name).setLevel('DEBUG')
    run(args)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()

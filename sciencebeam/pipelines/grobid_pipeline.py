import argparse
import logging
from configparser import ConfigParser
from typing import Dict, List, Optional

from sciencebeam.transformers.grobid_service import (
    grobid_service,
    GrobidApiPaths
)

from sciencebeam.transformers.xslt import xslt_transformer_from_file

from sciencebeam.utils.mime_type_constants import MimeTypes

from . import Pipeline, FunctionPipelineStep, FieldNames, StepDataProps


LOGGER = logging.getLogger(__name__)


DEFAULT_GROBID_ACTION = GrobidApiPaths.PROCESS_HEADER_DOCUMENT
DEFAULT_GROBID_XSLT_PATH = 'xslt/grobid-jats.xsl'

LOCAL_GROBID_API_URL = 'http://localhost:8080/api'

HEADER_FIELDS = {
    FieldNames.TITLE,
    FieldNames.ABSTRACT,
    FieldNames.AUTHORS,
    FieldNames.AFFILIATIONS
}


def has_only_header_fields(fields):
    return fields and not set(fields) - HEADER_FIELDS


def get_default_grobid_action_for_fields(fields):
    return (
        GrobidApiPaths.PROCESS_HEADER_DOCUMENT
        if has_only_header_fields(fields)
        else GrobidApiPaths.PROCESS_FULL_TEXT_DOCUMENT
    )


def get_xslt_template_parameters(config: ConfigParser) -> Dict[str, str]:
    return {
        key: value
        for key, value in config.items('xslt_template_parameters')
        if value
    }


class GrobidPipeline(Pipeline):
    def add_arguments(
        self,
        parser: argparse.ArgumentParser,
        config: ConfigParser,
        argv: Optional[List[str]] = None
    ):
        grobid_group = parser.add_argument_group('Grobid')
        grobid_group.add_argument(
            '--grobid-url', required=False, default=None,
            help='Base URL to the Grobid service'
        )
        grobid_group.add_argument(
            '--grobid-action', required=False,
            default=None,
            help='Name of the Grobid action'
            ' (by default determined depending on the requested fields)'
        )
        grobid_group.add_argument(
            '--no-grobid-xslt', action='store_true',
            help='Disable translation using XSLT'
        )
        grobid_group.add_argument(
            '--grobid-xslt-path', default=DEFAULT_GROBID_XSLT_PATH,
            help='Path to XSLT file translating results to JATS'
        )
        grobid_group.add_argument(
            '--no-grobid-pretty-print', action='store_true',
            help='Disable pretty print of XSLT output'
        )

    def get_steps(self, config, args):
        # type: (dict, object) -> list
        grobid_url = args.grobid_url
        if not grobid_url:
            grobid_url = LOCAL_GROBID_API_URL
            start_grobid_service = True
        else:
            start_grobid_service = False

        call_grobid = grobid_service(
            grobid_url, args.grobid_action, start_service=start_grobid_service
        )

        def convert_to_tei(pdf_filename, pdf_content, includes):
            return call_grobid(  # pylint: disable=redundant-keyword-arg
                (pdf_filename, pdf_content),
                path=args.grobid_action or get_default_grobid_action_for_fields(
                    includes
                )
            )[1]

        steps = [
            FunctionPipelineStep(lambda data, **_: {
                StepDataProps.CONTENT: convert_to_tei(
                    pdf_filename=data[StepDataProps.FILENAME],
                    pdf_content=data[StepDataProps.CONTENT],
                    includes=data.get(StepDataProps.INCLUDES)
                ),
                StepDataProps.TYPE: MimeTypes.TEI_XML
            }, {MimeTypes.PDF}, 'Convert to TEI')
        ]
        if not args.no_grobid_xslt:
            xslt_transformer = xslt_transformer_from_file(
                args.grobid_xslt_path,
                pretty_print=not args.no_grobid_pretty_print
            )
            xslt_template_parameters = get_xslt_template_parameters(config)
            LOGGER.info(
                'grobid_xslt_path=%r (xslt_template_parameters=%r)',
                args.grobid_xslt_path, xslt_template_parameters
            )
            steps.append(FunctionPipelineStep(lambda d, **_: {
                StepDataProps.CONTENT: xslt_transformer(
                    d[StepDataProps.CONTENT],
                    xslt_template_parameters=xslt_template_parameters
                ),
                StepDataProps.TYPE: MimeTypes.JATS_XML
            }, {MimeTypes.TEI_XML}, 'TEI to JATS'))
        return steps


PIPELINE = GrobidPipeline()

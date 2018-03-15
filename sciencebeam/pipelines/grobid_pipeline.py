from sciencebeam.transformers.grobid_service import (
  grobid_service,
  GrobidApiPaths
)

from . import Pipeline

class GrobidPipeline(Pipeline):
  def add_arguments(self, parser, config, argv=None):
    parser.add_argument(
      '--grobid-url',
      required=False,
      default=None,
      help='Base URL to the Grobid service')
    parser.add_argument(
      '--grobid-action',
      required=False,
      default=GrobidApiPaths.PROCESS_HEADER_DOCUMENT,
      help='Name of the Grobid action')

  def get_steps(self, config, args):
    grobid_url = args.grobid_url
    if not grobid_url:
      grobid_url = 'http://localhost:8080/api'
      start_grobid_service = True
    else:
      start_grobid_service = False

    call_grobid = grobid_service(
      grobid_url, args.grobid_action, start_service=start_grobid_service
    )

    convert_to_tei = lambda pdf_filename, pdf_content: call_grobid((pdf_filename, pdf_content))[1]

    return [
      lambda pdf_input: {
        'xml_content': convert_to_tei(
          pdf_filename=pdf_input['pdf_filename'],
          pdf_content=pdf_input['pdf_content']
        )
      }
    ]

PIPELINE = GrobidPipeline()

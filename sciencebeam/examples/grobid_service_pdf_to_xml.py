from __future__ import absolute_import

import argparse
from os.path import splitext

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from sciencebeam.beam_utils.fileio import ReadFileNamesAndContent, WriteToFile
from sciencebeam.beam_utils.core import MapKeys
from sciencebeam.transformers.grobid_service import (
  grobid_service,
  PROCESS_HEADER_DOCUMENT_PATH
)

def run(argv=None):
  """Main entry point; defines and runs the tfidf pipeline."""
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--input',
    required=True,
    help='Input file pattern to process.')
  parser.add_argument(
    '--output-suffix',
    required=False,
    default='.tei-header.xml',
    help='Output file suffix to add to the filename (excluding the file extension).')
  parser.add_argument(
    '--grobid-url',
    required=False,
    default='http://localhost:8080',
    help='Base URL to the Grobid service')
  parser.add_argument(
    '--grobid-action',
    required=False,
    default=PROCESS_HEADER_DOCUMENT_PATH,
    help='Name of the Grobid action')
  known_args, pipeline_args = parser.parse_known_args(argv)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = True

  with beam.Pipeline(options=pipeline_options) as p:
    # read the files and create a collection with filename, content tuples
    pcoll = p | ReadFileNamesAndContent(known_args.input)

    # map the pdf content to xml using Grobid
    # (grobid_service either accepts the content or tuples)
    output = pcoll | beam.Map(grobid_service(
      known_args.grobid_url, known_args.grobid_action
    ))

    # change the key (filename) from pdf to xml to reflect the new content
    output |= MapKeys(lambda k: splitext(k)[0] + known_args.output_suffix)

    # write the files, using the key as the filename
    output |= WriteToFile()

    # Execute the pipeline and wait until it is completed.


if __name__ == '__main__':
  import logging
  logging.getLogger().setLevel(logging.INFO)

  run()

# ScienceBeam

[![Build Status](https://travis-ci.org/elifesciences/sciencebeam.svg?branch=develop)](https://travis-ci.org/elifesciences/sciencebeam)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A set of tools to allow PDF to XML conversion, utilising [Apache Beam](https://beam.apache.org/) and other tools.

The aim of this project is to bring multiple tools together to generate a full XML document.

You might also be interested in the [ScienceBeam Gym](https://github.com/elifesciences/sciencebeam-gym), for the model training ground (the model is not yet integrated into the conversion pipeline).

## Status

This is in a very early status and may change significantly.

## Docker

Note: If you just want to use the API, you could make use of the [docker image](doc/Docker.md).

## Pre-requisites

- Python 2.7 ([currently Apache Beam doesn't support Python 3](https://issues.apache.org/jira/browse/BEAM-1373))
- [Apache Beam](https://beam.apache.org/get-started/quickstart-py/)
- [ScienceBeam Gym](https://github.com/elifesciences/sciencebeam-gym) project installed (e.g. by running `pip install -e .` after cloning it)

## Pipeline

The conversion pipeline could for example look as follows:

![Example Conversion Pipeline](doc/example-conversion-pipeline.png)

See below for current example implementations.

### Grobid Example Pipeline

This pipeline will run [Grobid](http://grobid.readthedocs.io/en/latest/) is used for the actual conversion.

To run the example conversion with the defaults:

```bash
python -m sciencebeam.examples.grobid_service_pdf_to_xml --input "/path/to/pdfs/*/*.pdf"
```

That will automatically download and run a [Grobid Service](https://grobid.readthedocs.io/en/latest/Grobid-service/) instance.

Or specify the Grobid URL and file suffix (in that case the Grobid Service is assumed to be running):

```bash
python -m sciencebeam.examples.grobid_service_pdf_to_xml --input "/path/to/pdfs/*/*.pdf" \
 --grobid-url http://localhost:8080 --output-suffix .tei-header.xml
```

Or specify an XSLT transformation, e.g. using [grobid-jats.xsl](https://github.com/kermitt2/grobid/blob/master/grobid-core/src/main/resources/xslt/grobid-jats.xsl):

```bash
python -m sciencebeam.examples.grobid_service_pdf_to_xml --input "/path/to/pdfs/*/*.pdf" \
 --xslt-path grobid-jats.xsl
```

Assuming you have already authenticated with [Google's Cloud SDK](https://cloud.google.com/sdk/) you can also work with buckets by specifying the URL:

```bash
python -m sciencebeam.examples.grobid_service_pdf_to_xml --input "gs://example_bucket/path/to/pdfs/*.pdf"
```

### ScienceBeam Conversion Pipeline

This pipeline is currently under development. It uses the CRF or computer vision model trained by
[ScienceBeam Gym](https://github.com/elifesciences/sciencebeam-gym).

What you need before you can proceed:

- At least one of:
  - Path to [CRF model](https://github.com/elifesciences/sciencebeam-gym#training-crf-model)
  - Path to [exported computer vision model](https://github.com/elifesciences/sciencebeam-gym#export-inference-model)
  - `--use-grobid` option
- PDF files, as file list csv/tsv or glob pattern

To use the CRF model together with the CV model, the CRF model will have to be trained with the CV predictions.

The following command will process files locally:

```bash
python -m sciencebeam.examples.conversion_pipeline \
  --data-path=./data \
  --pdf-file-list=./data/file-list-validation.tsv \
  --crf-model=path/to/crf-model.pkl \
  --cv-model-export-dir=./my-model/export \
  --output-path=./data-results \
  --pages=1 \
  --limit=100
```

The following command would process the first 100 files in the cloud using Dataflow:

```bash
python -m sciencebeam.examples.conversion_pipeline \
  --data-path=gs://my-bucket/data \
  --pdf-file-list=gs://my-bucket/data/file-list-validation.tsv \
  --crf-model=path/to/crf-model.pkl \
  --cv-model-export-dir=gs://mybucket/my-model/export \
  --output-path=gs://my-bucket/data-results \
  --pages=1 \
  --limit=100 \
  --cloud
```

You can also enable the post processing of the extracted authors and affiliations using Grobid by adding `--use-grobid`. In that case Grobid will be started automatically. To use an existing version also add `--grobid-url=<api url>` with the url to the Grobid API. If the `--use-grobid` option is used without a CRF or CV model, then it will use Grobid to translate the PDF to XML.

For a full list of parameters:

```bash
python -m sciencebeam.examples.conversion_pipeline --help
```

## Extending the Pipeline

You can use the [grobid_service_pdf_to_xml.py](sciencebeam/examples/grobid_service_pdf_to_xml.py) or
[conversion_pipeline.py](sciencebeam/examples/conversion_pipeline.py) example as a template and add your own steps.

## API Server

The [API](doc/API.md) server is currently available in combination with GROBID.

To start the GROBID run:

```bash
docker run -p 8070:8070 lfoppiano/grobid:0.5.1
```

To start the ScienceBeam server run:

```bash
./server.sh --host=0.0.0.0 --port=8075 --grobid-url http://localhost:8070/api
```

The [ScienceBeam API](doc/API.md) will be available on port _8075_.

## Tests

Unit tests are written using [pytest](https://docs.pytest.org/). Run for example `pytest` or `pytest-watch`.

## Contributing

See [CONTRIBUTIG](CONTRIBUTING.md)

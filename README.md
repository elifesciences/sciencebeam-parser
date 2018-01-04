# ScienceBeam

A set of tools to allow PDF to XML conversion, utilising [Apache Beam](https://beam.apache.org/) and other tools.

The aim of this project is to bring multiple tools together to generate a full XML document.

You might also be interested in the [ScienceBeam Gym](https://github.com/elifesciences/sciencebeam-gym), for the model training ground (the model is not yet integrated into the conversion pipeline).

## Status

This is in a very early status and may change significantly. The Pipeline may not currently run successfully in the Cloud.

## Pre-requisites

- Python 2.7 ([currently Apache Beam doesn't support Python 3](https://issues.apache.org/jira/browse/BEAM-1373))
- [Apache Beam](https://beam.apache.org/get-started/quickstart-py/)
- [ScienceBeam Gym](https://github.com/elifesciences/sciencebeam-gym) project installed (e.g. by running `pip install -e .` after cloning it)

## Pipeline

The conversion pipeline could for example look as follows:

![Example Conversion Pipeline](doc/example-conversion-pipeline.png)

Currently it only runs Grobid and XSLT (for meta data). It also assumes that Grobid is running as a service.

In the future we want to implement the TensorFlow model as well as integrate other tools.

## Run

There different example pipelines that you could run. To integrate new tools you'd modify an existing or add a new pipeline.

### Run Grobid Example Pipeline

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

### Run Computer Vision Pipeline

This pipeline is currently under development. It uses the computer vision model trained by
[ScienceBeam Gym](https://github.com/elifesciences/sciencebeam-gym).

What you need before you can go you proceed:

- Path to [exported computer vision model](https://github.com/elifesciences/sciencebeam-gym#export-inference-model)
- `color_map.conf` used to train the model (that will be embedded into the model in the future)
- PDF files, as file list csv/tsv or glob pattern

The following comman will process files locally:

```bash
python -m sciencebeam.examples.cv_conversion_pipeline \
  --data-path=./data \
  --pdf-file-list=./data/file-list-validation.tsv \
  --model-export-dir=./my-model/export \
  --output-path=./data-results \
  --pages=1 \
  --limit=100
```

The following command would process the first 100 files in the cloud using Dataflow:

```bash
python -m sciencebeam.examples.cv_conversion_pipeline \
  --data-path=gs://my-bucket/data \
  --pdf-file-list=gs://my-bucket/data/file-list-validation.tsv \
  --model-export-dir=gs://mybucket/my-model/export \
  --output-path=gs://my-bucket/data-results \
  --pages=1 \
  --limit=100 \
  --cloud
```

You can also enable the post processing of the extracted authors and affiliations using Grobid by adding `--use-grobid`. In that case Grobid will be started automatically. To use an existing version also add `--grobid-url=<api url>` with the url to the Grobid API.

For a full list of parameters:

```bash
python -m sciencebeam.examples.cv_conversion_pipeline --help
```

## Extending the Pipeline

You can use the [grobid_service_pdf_to_xml.py](sciencebeam/examples/grobid_service_pdf_to_xml.py) or
[cv_conversion_pipeline.py](sciencebeam/examples/cv_conversion_pipeline.py) example as a template and add your own steps.

## Tests

Unit tests are written using [pytest](https://docs.pytest.org/). Run for example `pytest` or `pytest-watch`.

## Contributing

See [CONTRIBUTIG](CONTRIBUTING.md)

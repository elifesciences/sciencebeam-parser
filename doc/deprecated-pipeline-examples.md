# Deprecated Pipeline Examples

The following example pipelines are currently deemed deprecated, in favour of the [Simple Pipeline](../README.md#simple-pipeline) (which can be run via [Apache Beam](../README.md#simple-pipeline) as well as the [API Server](../README.md#api-server).

The pipelines documented here can only be run via _Apache Beam_. However, for complex requirements this might be the right choice.

## Grobid Example Pipeline

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

## ScienceBeam Conversion Pipeline

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

## Extending the Pipeline (deprecated)

You can use the [grobid_service_pdf_to_xml.py](../sciencebeam/examples/grobid_service_pdf_to_xml.py) or
[conversion_pipeline.py](../sciencebeam/examples/conversion_pipeline.py) example as a template and add your own steps.

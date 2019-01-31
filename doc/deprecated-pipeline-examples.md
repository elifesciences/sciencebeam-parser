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

## Extending the Pipeline (deprecated)

You can use the [grobid_service_pdf_to_xml.py](../sciencebeam/examples/grobid_service_pdf_to_xml.py) example as a template and add your own steps.

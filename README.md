Science Beam
============

A set of tools to allow PDF to XML conversion, utilising [Apache Beam](https://beam.apache.org/) and other tools.

Currently [Grobid](http://grobid.readthedocs.io/en/latest/) is used for the actual conversion. But other tools are planned to be used in the future.

The aim of this project is to bring multiple tools together to generate a full XML document.

Status
------
This is in a very early status and may change significantly. The Pipeline may not currently run successfully in the Cloud.

Pre-requisites
--------------
- Python 2.7 ([currently Apache Beam doesn't support Python 3](https://issues.apache.org/jira/browse/BEAM-1373))
- [Apache Beam](https://beam.apache.org/get-started/quickstart-py/)
- [Grobid Service](https://grobid.readthedocs.io/en/latest/Grobid-service/)

Run
---

To run the example conversion with the defaults:

`python -m sciencebeam.examples.grobid_service_pdf_to_xml --input /path/to/pdfs/*/*.pdf`

Or specify the Grobid URL and file suffix:

`python -m sciencebeam.examples.grobid_service_pdf_to_xml --input /path/to/pdfs/*/*.pdf --grobid-url http://localhost:8080 --output-suffix .tei-header.xml`

Extending the Pipeline
----------------------
You can use the [grobid_service_pdf_to_xml](sciencebeam/examples/grobid_service_pdf_to_xml.py) as a template and add your own steps.

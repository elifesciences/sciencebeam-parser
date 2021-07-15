# General architecture

## Processing

The following gives an overview of the processing:

* PDF parsed using [pdfalto](https://github.com/kermitt2/pdfalto)
* [pdfalto](https://github.com/kermitt2/pdfalto) XML parsed into [Layout Document](pygrobid/document/layout_document.py)
* The layout document is re-tokenized
* [FullText Processor](pygrobid/processors/fulltext.py):
  * uses [models](pygrobid/models) to convert the [Layout Document](pygrobid/document/layout_document.py) to a [Semantic Document](pygrobid/document/semantic_document.py)
* the [Semantic Document](pygrobid/document/semantic_document.py) is converted to [TEI XML](pygrobid/document/tei_document.py)

## Models

Models will often consist of:

* Data Generator (`data.py`):
  * responsible for creating the layout features for the models
* Semantic Extractor (`extract.py`):
  * responsible for translating model output to Semantic Content elements
* Model Wrapper (`model.py`)
  * Provides model-specific implementation with common interface
  * Usually by providing constructurs for the data generator and semantic extractor

A model will not directly interact with another model. The [FullText Processor](pygrobid/processors/fulltext.py) will handle those interactions.

## Layout Document

The [Layout Document](pygrobid/document/layout_document.py) represents the parsed input document without layout information.

A layout document and all of it's classes should be treated as immutable.

A view may be created by constructing a layout document with a sub-set of the tokens (e.g. a layout document may be passed to the header model, containing only the tokens and blocks for the header).

## Semantic Document

The [Semantic Document](pygrobid/document/semantic_document.py)
represents the intermediate semantically extracted document.

This semantic document is mutable and may be changed during processing. The type class is the main *semantic label*.
For example `SemanticTitle` represents the title.

Semantic type classes may contain additional properties. For example `SemanticPageRange` contains a `from_page` and `to_page`. Whereas the *content* of `SemanticPageRange` is the content as it appeared in the original document.

Semantic content can be hierarchically. For example `SemanticTitle` within `SemanticFront` is the manuscript title, whereas `SemanticTitle` within `SemanticReference` would represent the title of the reference.

In general all of the text should preserved. Content without a known semantic meaning may use `SemanticNote`.

Some semantic content types denote partially parsed content. For example `SemanticRawAuthors` with be the output of the `header` model. Those can then be further parsed using downstream models.

The semantic content should aim to keep the order of the original document.

As the semantic content contains layout tokens, the original formatting can be preserved.

## TEI Document

The [TEI Document](pygrobid/document/tei_document.py) is used for the TEI XML output. It maps the [Semantic Document](pygrobid/document/semantic_document.py) to XML elements.

Currently it will aim to output every content that is represented in the semantic document, by default as a `note`.

Page coordinates are usually also added.

Formatting is preserved for most fields.

## Rest API

The [rest API](pygrobid/service/blueprints/api.py) is the general entry point for the document conversion.

Some of the end points:

| path | description |
| ---- | ----------- |
| `/api/processFulltextDocument` | The main mostly GROBID compatible end point |
| `/api/pdfalto` | Low level pdfalto conversion |
| `/api/models/<model-name>` | Model specific end point |

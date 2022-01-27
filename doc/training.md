# ScienceBeam Parser Model Training

ScienceBeam Parser uses machine learning models to parse documents.
Pre-trained models are provided and referenced by the configuration.
In order to get performance for the particular domain, it may be necessary to train
models with domain specific documents.

For the sequence model (`delft` etc) the general workflow looks like:

- Generate training data
- Annotate generated training data
- Train model (using `sciencebeam-trainer-delft`)
- Use and evaluate model:
  - Configure new model in `sciencebeam-parser`
  - Convert documents
  - Evaluate converted documents (using `sciencebeam-judge`)

## Generate training data

The training data for the sequential models follows the GROBID training data format.

### Generate `tei` training data for the sequence models

Currently training data will be generated for the following models:

- `segmentation`
- `header`
- `affiliation_address`
- `fulltext`
- `reference_segmenter`
- `citation` (references)
- `figure`
- `table`
- `name` (author names for `header` and `citations`)

```bash
python -m sciencebeam_parser.training.cli.generate_data \
    --source-path="test-data/*.pdf" \
    --output-path="./data/generated-training-data"
```

Using the configured models to pre-annotate the training data:

```bash
python -m sciencebeam_parser.training.cli.generate_data \
    --use-model \
    --source-path="test-data/*.pdf" \
    --output-path="./data/generated-training-data"
```

Note: as the models are hierachical, the parent model needs to be used
  in order to generate data for the child model.
  For example the `segmentation` model will be required for the `header` model.

The output could also be organised into a folder structure by model and type of file:

```bash
python -m sciencebeam_parser.training.cli.generate_data \
    --use-model \
    --use-directory-structure \
    --source-path="test-data/*.pdf" \
    --output-path="./data/generated-training-data"
```

### Annotating `tei` training data for the sequence models

After the `tei` training data has been generated, it should get reviewed and manually annotated.
Alternatively it can auto-annotated using [sciencebeam-trainer-grobid-tools](https://gitlab.coko.foundation/sciencebeam/sciencebeam-trainer-grobid-tools).

### Generate `delft` training data for the sequence models

From the annotated `tei` training data, we can generate the `delft` training data used for training.

It will do one of the following:

- For models with only `tei` XML files (no layout feature), it will parse the `tei` and generate data using the data generator.
- For models with additional layout data files, it will align the parsed `tei` with the layout data file and add the label to it.

```bash
python -m sciencebeam_parser.training.cli.generate_delft_data \
    --model-name="segmentation" \
    --tei-source-path="data/generated-training-data/segmentation/corpus/tei/*.tei.xml" \
    --raw-source-path="data/generated-training-data/segmentation/corpus/raw/" \
    --delft-output-path="./data/generated-training-data/delft/segmentation/corpus/segmentation.data"
```

Or:

```bash
python -m sciencebeam_parser.training.cli.generate_delft_data \
    --model-name="header" \
    --tei-source-path="data/generated-training-data/header/corpus/tei/*.tei.xml" \
    --raw-source-path="data/generated-training-data/header/corpus/raw/" \
    --delft-output-path="./data/generated-training-data/delft/header/corpus/header.data"
```

Or:

```bash
python -m sciencebeam_parser.training.cli.generate_delft_data \
    --model-name="affiliation_address" \
    --tei-source-path="data/generated-training-data/affiliation-address/corpus/*.tei.xml" \
    --delft-output-path \
    "./data/generated-training-data/delft/affiliation-address/corpus/affiliation-address.data"
```

Or:

```bash
python -m sciencebeam_parser.training.cli.generate_delft_data \
    --model-name="citation" \
    --tei-source-path="data/generated-training-data/citation/corpus/*.tei.xml" \
    --delft-output-path \
    "./data/generated-training-data/delft/citation/corpus/citation.data"
```

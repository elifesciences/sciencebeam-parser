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

### Generate training data for the sequence models

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

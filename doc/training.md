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

### Generate training data for the `segmentation` model

```bash
python -m sciencebeam_parser.training.generate_data \
    --model="segmentation" \
    --source-path="test-data/minimal-example.pdf" \
    --output-path="./data/generated-training-data"
```

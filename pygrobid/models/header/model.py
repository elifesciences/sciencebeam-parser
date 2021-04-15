from typing import Optional, Iterable, List

from sciencebeam_trainer_delft.sequence_labelling.wrapper import Sequence


class HeaderModel:
    def __init__(self, model_url: str):
        self.model_url = model_url
        self._model: Optional[Sequence] = None

    @property
    def model(self) -> Sequence:
        if self._model is not None:
            return self._model
        model = Sequence('dummy-model')
        model.load_from(self.model_url)
        self._model = model
        return model

    def predict_labels(
        self,
        texts: List[List[str]],
        features: List[List[List[str]]],
        output_format: Optional[str] = None
    ) -> Iterable[str]:
        model = self.model
        return model.tag(texts, features=features, output_format=output_format)

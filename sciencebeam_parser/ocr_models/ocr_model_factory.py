import functools

from sciencebeam_parser.ocr_models.ocr_model import (
    LazyOpticalCharacterRecognitionModel,
    OpticalCharacterRecognitionModel
)


class EngineNames:
    TESSEROCR = 'tesserocr'


def get_tesserocr_model(config: dict) -> OpticalCharacterRecognitionModel:
    from sciencebeam_parser.ocr_models.tesserocr_ocr_model import (  # noqa pylint: disable=import-outside-toplevel
        TesserComputerVisionModel
    )
    return TesserComputerVisionModel(config=config)


def get_engine_name_for_config(config: dict) -> str:
    engine_name = config.get('engine')
    if engine_name:
        return engine_name
    return EngineNames.TESSEROCR


def get_ocr_model_for_config(config: dict) -> OpticalCharacterRecognitionModel:
    engine_name = get_engine_name_for_config(config)
    if engine_name == EngineNames.TESSEROCR:
        return get_tesserocr_model(config=config)
    raise RuntimeError('invalid engine name: %r' % engine_name)


def get_lazy_ocr_model_for_config(config: dict) -> OpticalCharacterRecognitionModel:
    return LazyOpticalCharacterRecognitionModel(
        functools.partial(get_ocr_model_for_config, config)
    )

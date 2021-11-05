import dataclasses
import logging
from dataclasses import dataclass
from typing import (
    Any,
    Iterable,
    Optional,
    Type,
    TypeVar
)

from sciencebeam_parser.app.context import AppContext
from sciencebeam_parser.config.config import AppConfig
from sciencebeam_parser.models.model import Model
from sciencebeam_parser.models.model_impl_factory import get_model_impl_factory_for_config
from sciencebeam_parser.cv_models.cv_model_factory import get_lazy_cv_model_for_config
from sciencebeam_parser.cv_models.cv_model import ComputerVisionModel
from sciencebeam_parser.ocr_models.ocr_model_factory import get_lazy_ocr_model_for_config
from sciencebeam_parser.ocr_models.ocr_model import OpticalCharacterRecognitionModel

from sciencebeam_parser.models.segmentation.model import SegmentationModel
from sciencebeam_parser.models.header.model import HeaderModel
from sciencebeam_parser.models.name.model import NameModel
from sciencebeam_parser.models.affiliation_address.model import AffiliationAddressModel
from sciencebeam_parser.models.fulltext.model import FullTextModel
from sciencebeam_parser.models.figure.model import FigureModel
from sciencebeam_parser.models.table.model import TableModel
from sciencebeam_parser.models.reference_segmenter.model import ReferenceSegmenterModel
from sciencebeam_parser.models.citation.model import CitationModel
from sciencebeam_parser.processors.fulltext.config import FullTextProcessorConfig


LOGGER = logging.getLogger(__name__)


@dataclass
class FullTextModels:
    segmentation_model: SegmentationModel
    header_model: HeaderModel
    name_header_model: NameModel
    name_citation_model: NameModel
    affiliation_address_model: AffiliationAddressModel
    fulltext_model: FullTextModel
    figure_model: FigureModel
    table_model: TableModel
    reference_segmenter_model: ReferenceSegmenterModel
    citation_model: CitationModel
    cv_model: Optional[ComputerVisionModel] = None
    ocr_model: Optional[OpticalCharacterRecognitionModel] = None

    def _iter_models(self) -> Iterable[Any]:
        for field in dataclasses.fields(self):
            model = getattr(self, field.name)
            if model is not None:
                yield model

    def preload(self):
        LOGGER.info('preloading models...')
        models = list(self._iter_models())
        for model_index, model in enumerate(models):
            LOGGER.info('preloading: %d/%d: %r', 1 + model_index, len(models), model)
            try:
                model.preload()
            except AttributeError:
                pass
        LOGGER.info('preloaded models')


T_Model = TypeVar('T_Model', bound=Model)


def load_model(
    app_config: AppConfig,
    app_context: AppContext,
    model_name: str,
    model_class: Type[T_Model]
) -> T_Model:
    models_config = app_config['models']
    model_config = models_config[model_name]
    model = model_class(
        get_model_impl_factory_for_config(
            model_config,
            app_context=app_context
        ),
        model_config=model_config
    )
    return model


def get_cv_model_for_app_config(
    app_config: AppConfig,
    enabled: bool = True
) -> Optional[ComputerVisionModel]:
    cv_model_config = app_config.get('cv_models', {}).get('default')
    if enabled and cv_model_config:
        return get_lazy_cv_model_for_config(cv_model_config)
    return None


def get_ocr_model_for_app_config(
    app_config: AppConfig,
    enabled: bool = True
) -> Optional[OpticalCharacterRecognitionModel]:
    ocr_model_config = app_config.get('ocr_models', {}).get('default')
    if enabled and ocr_model_config:
        return get_lazy_ocr_model_for_config(ocr_model_config)
    return None


def load_models(
    app_config: AppConfig,
    app_context: AppContext,
    fulltext_processor_config: FullTextProcessorConfig
) -> FullTextModels:
    segmentation_model = load_model(
        app_config, app_context, 'segmentation', SegmentationModel
    )
    header_model = load_model(
        app_config, app_context, 'header', HeaderModel
    )
    name_header_model = load_model(
        app_config, app_context, 'name_header', NameModel
    )
    name_citation_model = load_model(
        app_config, app_context, 'name_citation', NameModel
    )
    affiliation_address_model = load_model(
        app_config, app_context, 'affiliation_address', AffiliationAddressModel
    )
    fulltext_model = load_model(
        app_config, app_context, 'fulltext', FullTextModel
    )
    figure_model = load_model(
        app_config, app_context, 'figure', FigureModel
    )
    table_model = load_model(
        app_config, app_context, 'table', TableModel
    )
    reference_segmenter_model = load_model(
        app_config, app_context, 'reference_segmenter', ReferenceSegmenterModel
    )
    citation_model = load_model(
        app_config, app_context, 'citation', CitationModel
    )
    cv_model = get_cv_model_for_app_config(
        app_config,
        enabled=fulltext_processor_config.use_cv_model
    )
    ocr_model = get_ocr_model_for_app_config(
        app_config,
        enabled=fulltext_processor_config.use_ocr_model
    )
    return FullTextModels(
        segmentation_model=segmentation_model,
        header_model=header_model,
        name_header_model=name_header_model,
        name_citation_model=name_citation_model,
        affiliation_address_model=affiliation_address_model,
        fulltext_model=fulltext_model,
        figure_model=figure_model,
        table_model=table_model,
        reference_segmenter_model=reference_segmenter_model,
        citation_model=citation_model,
        cv_model=cv_model,
        ocr_model=ocr_model
    )

import logging

from lxml import etree

from sciencebeam_parser.document.semantic_document import (
    SemanticAuthor,
    SemanticContentWrapper,
    SemanticDate,
    SemanticLabel,
    SemanticRawReference,
    SemanticRawReferenceText,
    SemanticReference,
    SemanticReferenceList,
    SemanticTitle
)
from sciencebeam_parser.document.tei.common import (
    TEI_E,
    TeiElementBuilder,
    create_tei_note_element
)
from sciencebeam_parser.document.tei.factory import (
    SingleElementTeiElementFactory,
    TeiElementFactoryContext
)
from sciencebeam_parser.document.tei.author import get_tei_author_for_semantic_author_element


LOGGER = logging.getLogger(__name__)


def _get_tei_raw_reference_element(
    semantic_raw_ref: SemanticRawReference,
    context: TeiElementFactoryContext
) -> etree.ElementBase:
    LOGGER.debug('semantic_raw_ref: %s', semantic_raw_ref)
    children = []
    for semantic_content in semantic_raw_ref:
        if isinstance(semantic_content, SemanticRawReferenceText):
            children.append(create_tei_note_element(
                'raw_reference', semantic_content.merged_block
            ))
            continue
        children.extend(context.get_tei_child_elements_for_semantic_content(semantic_content))
    tei_ref = TEI_E(
        'biblStruct',
        context.get_default_attributes_for_semantic_content(semantic_raw_ref),
        *children
    )
    return tei_ref


def get_tei_reference_element(  # pylint: disable=too-many-branches
    semantic_ref: SemanticReference,
    context: TeiElementFactoryContext
) -> etree.ElementBase:
    LOGGER.debug('semantic_ref: %s', semantic_ref)
    tei_ref = TeiElementBuilder(TEI_E(
        'biblStruct',
        context.get_default_attributes_for_semantic_content(semantic_ref)
    ))
    is_first_date = True
    for semantic_content in semantic_ref:
        parent_path = context.get_parent_path_for_semantic_content(
            semantic_content
        )
        tei_child_parent = tei_ref.get_or_create(parent_path)
        if isinstance(semantic_content, SemanticLabel):
            tei_child_parent.append(create_tei_note_element(
                'label', semantic_content.merged_block
            ))
            continue
        if isinstance(semantic_content, SemanticRawReferenceText):
            tei_child_parent.append(create_tei_note_element(
                'raw_reference', semantic_content.merged_block
            ))
            continue
        if isinstance(semantic_content, SemanticTitle):
            tei_child_parent.append(TEI_E(
                'title',
                {'level': 'a', 'type': 'main'},
                *context.iter_layout_block_tei_children(
                    semantic_content.merged_block
                )
            ))
            continue
        if isinstance(semantic_content, SemanticAuthor):
            tei_child_parent.append(get_tei_author_for_semantic_author_element(
                semantic_content,
                context=context
            ))
            continue
        if isinstance(semantic_content, SemanticDate):
            tei_child_parent = tei_ref.get_or_create(['monogr', 'imprint'])
            attrib = {}
            if is_first_date:
                # assume first date is published date (more or less matches GROBID)
                attrib['type'] = 'published'
            if semantic_content.year:
                attrib['when'] = str(semantic_content.year)
            tei_child_parent.append(TEI_E(
                'date', attrib,
                *context.iter_layout_block_tei_children(layout_block=semantic_content.merged_block)
            ))
            is_first_date = False
            continue
        tei_child_parent.extend(
            context.get_tei_child_elements_for_semantic_content(semantic_content)
        )
    return tei_ref.element


def get_tei_raw_reference_list_element(
    semantic_reference_list: SemanticReferenceList,
    context: TeiElementFactoryContext
) -> etree.ElementBase:
    tei_reference_list = TeiElementBuilder(TEI_E('listBibl'))
    for semantic_content in semantic_reference_list:
        if isinstance(semantic_content, SemanticRawReference):
            tei_reference_list.append(
                _get_tei_raw_reference_element(semantic_content, context=context)
            )
            continue
        if isinstance(semantic_content, SemanticReference):
            tei_reference_list.append(
                get_tei_reference_element(semantic_content, context=context)
            )
            continue
        tei_reference_list.extend(context.get_tei_child_elements_for_semantic_content(
            semantic_content
        ))
    return tei_reference_list.element


class SemanticReferenceListTeiElementFactory(SingleElementTeiElementFactory):
    def get_tei_element_for_semantic_content(
        self,
        semantic_content: SemanticContentWrapper,
        context: TeiElementFactoryContext
    ) -> etree.ElementBase:
        LOGGER.debug('semantic_content: %s', semantic_content)
        assert isinstance(semantic_content, SemanticReferenceList)
        semantic_reference_list = semantic_content
        return get_tei_raw_reference_list_element(
            semantic_reference_list=semantic_reference_list,
            context=context
        )

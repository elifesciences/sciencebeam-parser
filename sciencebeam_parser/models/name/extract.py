import logging
import re
from typing import Iterable, List, Mapping, Optional, Tuple, Type, Union, cast

from sciencebeam_parser.document.semantic_document import (
    SemanticAuthor,
    SemanticContentFactoryProtocol,
    SemanticContentWrapper,
    SemanticMarker,
    SemanticMiddleName,
    SemanticMixedContentWrapper,
    SemanticNamePart,
    SemanticNameSuffix,
    SemanticNameTitle,
    SemanticNote,
    SemanticGivenName,
    SemanticSurname,
    T_SemanticName
)
from sciencebeam_parser.document.layout_document import LayoutBlock, LayoutDocument, LayoutToken
from sciencebeam_parser.models.extract import SimpleModelSemanticExtractor


LOGGER = logging.getLogger(__name__)


SPLIT_ON_SECOND_ENTIY_NAME = {'<title>', '<forename>', '<surname>'}


SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG: Mapping[str, SemanticContentFactoryProtocol] = {
    '<title>': SemanticNameTitle,
    '<forename>': SemanticGivenName,
    '<middlename>': SemanticMiddleName,
    '<surname>': SemanticSurname,
    '<suffix>': SemanticNameSuffix
}


def tokenize_individual_characters(text: str) -> List[str]:
    return list(text)


def convert_two_letter_uppercase_given_name_to_given_middle_name(
    name: T_SemanticName
):
    given_names = list(name.iter_by_type(SemanticGivenName))
    middle_names = list(name.iter_by_type(SemanticMiddleName))
    if middle_names:
        LOGGER.debug('already has a middle name: %r', middle_names)
        return
    if len(given_names) != 1:
        LOGGER.debug('no or too many given names: %r', given_names)
        return
    given_name_text = given_names[0].get_text()
    if len(given_name_text) != 2 or not given_name_text.isupper():
        LOGGER.debug('not two uppercase characters: %r', given_name_text)
        return
    layout_document = LayoutDocument.for_blocks(list(given_names[0].iter_blocks()))
    retokenized_layout_document = layout_document.retokenize(
        tokenize_fn=tokenize_individual_characters
    )
    LOGGER.debug('retokenized_layout_document: %r', retokenized_layout_document)
    split_name_parts = [
        (
            SemanticGivenName(layout_block=LayoutBlock.for_tokens([token])) if index == 0
            else SemanticMiddleName(layout_block=LayoutBlock.for_tokens([token]))
        )
        for index, token in enumerate(retokenized_layout_document.iter_all_tokens())
    ]
    LOGGER.debug('split_name_parts: %r', split_name_parts)
    name.flat_map_inplace_by_type(
        SemanticGivenName,
        lambda _: split_name_parts
    )


def convert_name_parts_to_title_case(name: T_SemanticName):
    for semantic_content in name:
        if not isinstance(semantic_content, SemanticNamePart):
            continue
        semantic_content.value = semantic_content.get_text().title()


# based on:
# https://github.com/kermitt2/grobid/blob/0.6.2/grobid-core/src/main/java/org/grobid/core/data/Person.java#L375-L391
# and:
# https://github.com/kermitt2/grobid/blob/0.6.2/grobid-core/src/main/java/org/grobid/core/data/Person.java#L756-L775
def normalize_name_parts(name: T_SemanticName):
    if not list(name.iter_by_type(SemanticSurname)):
        return SemanticNote(
            layout_block=LayoutBlock.merge_blocks(name.iter_blocks()),
            note_type='invalid_author_name'
        )
    convert_two_letter_uppercase_given_name_to_given_middle_name(name)
    convert_name_parts_to_title_case(name)
    return name


def iter_semantic_markers_for_layout_block(
    layout_block: LayoutBlock
) -> Iterable[Union[SemanticMarker, SemanticContentWrapper]]:
    for text in re.split(r'(\D)', layout_block.text):
        if not text:
            continue
        local_block = LayoutBlock.for_tokens([
            LayoutToken(text, whitespace='')
        ])
        if text == ',' or text.isspace():
            yield SemanticNote(
                layout_block=local_block,
                note_type='marker_delimiter'
            )
            continue
        yield SemanticMarker(layout_block=local_block)


def append_semantic_markers_for_layout_block(
    parent_semantic_content: SemanticMixedContentWrapper,
    layout_block: LayoutBlock
) -> None:
    semantic_markers = list(iter_semantic_markers_for_layout_block(layout_block))
    for semantic_marker in semantic_markers:
        parent_semantic_content.add_content(semantic_marker)


class NameSemanticExtractor(SimpleModelSemanticExtractor):
    def __init__(self):
        super().__init__(semantic_content_class_by_tag=SIMPLE_SEMANTIC_CONTENT_CLASS_BY_TAG)

    def iter_semantic_content_for_entity_blocks(  # type: ignore  # pylint: disable=arguments-differ
        self,
        entity_tokens: Iterable[Tuple[str, LayoutBlock]],
        name_type: Optional[Type[T_SemanticName]] = None,
        **kwargs
    ) -> Iterable[T_SemanticName]:
        _name_type: Type[T_SemanticName] = cast(
            Type[T_SemanticName],
            name_type if name_type is not None else SemanticAuthor
        )
        entity_tokens = list(entity_tokens)
        LOGGER.debug('entity_tokens: %s', entity_tokens)
        semantic_name: Optional[T_SemanticName] = None
        seen_entity_tokens: List[Tuple[str, LayoutBlock]] = []
        seen_name_labels: List[str] = []
        has_tail_marker: bool = False
        for name, layout_block in entity_tokens:
            seen_entity_tokens.append((name, layout_block,))
            if name == '<marker>':
                if not semantic_name:
                    LOGGER.debug('new semantic_name with marker in the beginning')
                    semantic_name = _name_type()
                    append_semantic_markers_for_layout_block(semantic_name, layout_block)
                    continue
                if len(seen_entity_tokens) >= 2 and seen_name_labels and not has_tail_marker:
                    previous_layout_block = seen_entity_tokens[-2][1]
                    if previous_layout_block.text.strip().endswith(','):
                        LOGGER.debug(
                            'new semantic_name marker after comma, seen_name_labels=%s',
                            seen_name_labels
                        )
                        yield normalize_name_parts(semantic_name)
                        seen_name_labels = []
                        semantic_name = _name_type()
                        append_semantic_markers_for_layout_block(semantic_name, layout_block)
                        continue
                append_semantic_markers_for_layout_block(semantic_name, layout_block)
                has_tail_marker = True
                continue
            semantic_content = self.get_semantic_content_for_entity_name(
                name, layout_block
            )
            if semantic_name and name in SPLIT_ON_SECOND_ENTIY_NAME and name in seen_name_labels:
                LOGGER.debug(
                    'starting new semantic_name after having seen name part again, name=%r',
                    name
                )
                yield normalize_name_parts(semantic_name)
                seen_name_labels = []
                has_tail_marker = False
                semantic_name = None
            if not isinstance(semantic_content, SemanticNote):
                if has_tail_marker and semantic_name:
                    LOGGER.debug('starting new semantic_name after tail markers, name=%r', name)
                    yield normalize_name_parts(semantic_name)
                    seen_name_labels = []
                    has_tail_marker = False
                    semantic_name = None
                seen_name_labels.append(name)
            if not semantic_name:
                semantic_name = _name_type()
            semantic_name.add_content(semantic_content)
        if semantic_name:
            yield normalize_name_parts(semantic_name)

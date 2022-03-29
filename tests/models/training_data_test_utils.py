from typing import Sequence, Tuple

from sciencebeam_parser.document.layout_document import (
    LayoutBlock,
    LayoutDocument,
    LayoutLine,
    LayoutLineMeta
)
from sciencebeam_parser.models.data import (
    LabeledLayoutModelData,
    LayoutModelData,
    ModelDataGenerator
)


def get_model_data_list_for_layout_document(
    layout_document: LayoutDocument,
    data_generator: ModelDataGenerator
) -> Sequence[LayoutModelData]:
    return list(data_generator.iter_model_data_for_layout_document(
        layout_document
    ))


def get_label_with_prefix(label: str, index: int) -> str:
    if label[:2] in {'B-', 'I-'} or label == 'O':
        return label
    if index == 0:
        return 'B-' + label
    return 'I-' + label


def get_labeled_model_data_list(
    label_and_layout_line_list: Sequence[Tuple[str, LayoutLine]],
    data_generator: ModelDataGenerator
) -> Sequence[LabeledLayoutModelData]:
    labeled_model_data_list = []
    for label, layout_line in label_and_layout_line_list:
        layout_document = LayoutDocument.for_blocks([LayoutBlock(lines=[layout_line])])
        labeled_model_data_list.extend([
            LabeledLayoutModelData.from_model_data(
                model_data,
                label=get_label_with_prefix(label, index=index)
            )
            for index, model_data in enumerate(
                data_generator.iter_model_data_for_layout_document(
                    layout_document
                )
            )
        ])
    return labeled_model_data_list


def get_labeled_model_data_list_list(
    label_and_layout_line_list_list: Sequence[Sequence[Tuple[str, LayoutLine]]],
    data_generator: ModelDataGenerator
) -> Sequence[Sequence[LabeledLayoutModelData]]:
    return [
        get_labeled_model_data_list(
            label_and_layout_line_list,
            data_generator=data_generator
        )
        for label_and_layout_line_list in label_and_layout_line_list_list
    ]


def get_layout_line_for_text(text: str, line_id: int) -> LayoutLine:
    return LayoutLine.for_text(
        text,
        tail_whitespace='\n',
        line_meta=LayoutLineMeta(line_id=line_id)
    )


class ModuleState:
    line_id: int = 1


def get_next_layout_line_for_text(text: str) -> LayoutLine:
    line_id = ModuleState.line_id
    ModuleState.line_id += 1
    return get_layout_line_for_text(text, line_id=line_id)

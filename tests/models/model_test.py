from pygrobid.document.layout_document import (
    LayoutPage,
    get_layout_tokens_for_text,
    join_layout_tokens,
    LayoutDocument,
    LayoutBlock,
    LayoutLine
)
from pygrobid.models.model import LayoutDocumentLabelResult, LayoutModelLabel


TAG_1 = 'tag1'
TAG_2 = 'tag2'


class TestLayoutDocumentLabelResult:
    def test_should_filter_by_line_without_token(self):
        tagged_lines = [
            (TAG_1, LayoutLine.for_text('this is line 1')),
            (TAG_2, LayoutLine.for_text('this is line 2'))
        ]
        layout_model_labels = [
            LayoutModelLabel(
                label=tag,
                label_token_text=line.text,
                layout_line=line,
                layout_token=None
            )
            for tag, line in tagged_lines
            for token in line.tokens
        ]
        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            LayoutBlock(lines=[line for _, line in tagged_lines])
        ])])
        layout_document_label_result = LayoutDocumentLabelResult(
            layout_document,
            layout_model_labels
        )
        for tag, line in tagged_lines:
            assert (
                join_layout_tokens(
                    layout_document_label_result.get_filtered_document_by_label(tag)
                    .iter_all_tokens()
                ) == join_layout_tokens(line.tokens)
            )

    def test_should_filter_by_token_label(self):
        tagged_tokens = [
            (TAG_1, get_layout_tokens_for_text('this is line 1')),
            (TAG_2, get_layout_tokens_for_text('this is line 2'))
        ]
        line = LayoutLine([
            token
            for _, tokens in tagged_tokens
            for token in tokens
        ])
        layout_model_labels = [
            LayoutModelLabel(
                label=tag,
                label_token_text=token.text,
                layout_line=line,
                layout_token=token
            )
            for tag, tokens in tagged_tokens
            for token in tokens
        ]
        layout_document = LayoutDocument(pages=[LayoutPage(blocks=[
            LayoutBlock(lines=[line])
        ])])
        layout_document_label_result = LayoutDocumentLabelResult(
            layout_document,
            layout_model_labels
        )
        for tag, tokens in tagged_tokens:
            assert (
                join_layout_tokens(
                    layout_document_label_result.get_filtered_document_by_label(tag)
                    .iter_all_tokens()
                ) == join_layout_tokens(tokens)
            )

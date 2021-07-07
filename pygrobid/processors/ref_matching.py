import re
from abc import ABC, abstractmethod
from typing import Mapping, Optional


class ContentIdMatcher(ABC):
    @abstractmethod
    def get_id_by_text(self, text: str) -> Optional[str]:
        pass


def get_normalized_key_text(text: str):
    return re.sub(
        r'[^a-z0-9]',
        '',
        text.lower()
    )


def get_token_prefix_normalized_key_text(text: str):
    return ''.join([
        get_normalized_key_text(
            token if re.search(r'\d', token) else token[:1]
        )
        for token in text.split(' ')
    ])


class SimpleContentIdMatcher(ContentIdMatcher):
    def __init__(self, text_by_content_id: Mapping[str, str]):
        self.text_by_content_id = text_by_content_id
        self.content_id_by_text = {
            get_normalized_key_text(value): key
            for key, value in text_by_content_id.items()
        }
        self.content_id_by_token_prefix_text = {
            get_token_prefix_normalized_key_text(value): key
            for key, value in text_by_content_id.items()
        }

    def get_id_by_text(self, text: str) -> Optional[str]:
        content_id = self.content_id_by_text.get(get_normalized_key_text(text))
        if content_id:
            return content_id
        content_id = self.content_id_by_token_prefix_text.get(
            get_token_prefix_normalized_key_text(text)
        )
        return content_id

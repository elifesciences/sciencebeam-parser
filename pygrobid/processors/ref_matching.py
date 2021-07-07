import logging
import re
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from typing import Dict, List, Mapping, Optional

from pygrobid.utils.tokenizer import iter_tokenized_tokens


LOGGER = logging.getLogger(__name__)


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
        for token in re.split(r'\s', text)
    ])


def get_normalized_key_tokens(text: str):
    return [
        get_normalized_key_text(
            token if re.search(r'\d', token) else token[:1]
        )
        for token in iter_tokenized_tokens(text)
        if token.strip()
    ]


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


class PartialContentIdMatcher(SimpleContentIdMatcher):
    def __init__(self, text_by_content_id: Mapping[str, str]):
        super().__init__(text_by_content_id=text_by_content_id)
        self.content_ids_by_token_text: Dict[str, List[str]] = defaultdict(list)
        for content_id, text in text_by_content_id.items():
            for token in get_normalized_key_tokens(text):
                self.content_ids_by_token_text[token].append(content_id)

    def get_id_by_text(self, text: str) -> Optional[str]:
        content_id = super().get_id_by_text(text)
        if content_id:
            return content_id
        tokens = get_normalized_key_tokens(text)
        LOGGER.debug('tokens: %r', tokens)
        if not tokens:
            return None
        content_id_counts = Counter((
            content_id
            for token in tokens
            for content_id in self.content_ids_by_token_text.get(token, [])
        ))
        LOGGER.debug('content_id_counts: %s', content_id_counts)
        if not content_id_counts:
            return None
        keys = list(content_id_counts.keys())
        if (
            len(content_id_counts) >= 2
            and content_id_counts[keys[0]] == content_id_counts[keys[1]]
        ):
            return None
        return keys[0]

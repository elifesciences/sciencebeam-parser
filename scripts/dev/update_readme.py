import argparse
import logging
import os
from pathlib import Path
import re


LOGGER = logging.getLogger(__name__)


def strip_special_links(markdown: str) -> str:
    return '\n'.join([
        line.rstrip()
        for line in markdown.splitlines()
        if not line.startswith('[![')
    ])


def get_resolved_link(
    link: str,
    source_base_path: str,
    link_prefix: str
) -> str:
    if '://' in link:
        return link
    result = os.path.join(link_prefix, source_base_path, link)
    if source_base_path and '/' not in source_base_path:
        result = result.replace(f'/{source_base_path}/../', '/')
    return result


def get_markdown_with_resolved_links(
    markdown_content: str,
    source_base_path: str,
    link_prefix: str
) -> str:
    return re.sub(
        r'(\[.*\]\()(.*)(\))',
        lambda m: (
            m.group(1)
            + get_resolved_link(
                m.group(2),
                source_base_path=source_base_path,
                link_prefix=link_prefix
            )
            + m.group(3)
        ),
        markdown_content
    )


def update_readme_text(
    original_readme: str,
    source_base_path: str,
    link_prefix: str
) -> str:
    return get_markdown_with_resolved_links(
        strip_special_links(original_readme),
        source_base_path=source_base_path,
        link_prefix=link_prefix
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser('Update README')
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--source-base-path', required=True)
    parser.add_argument('--link-prefix', required=True)
    return parser.parse_args()


def run(
    source: str,
    target: str,
    source_base_path: str,
    link_prefix: str
):
    LOGGER.info('Updating readme: %r -> %r', source, target)
    original_readme = Path(source).read_text(encoding='utf-8')
    updated_readme = update_readme_text(
        original_readme,
        source_base_path=source_base_path,
        link_prefix=link_prefix
    )
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(updated_readme, encoding='utf-8')


def main():
    args = parse_args()
    run(
        source=args.source,
        target=args.target,
        source_base_path=args.source_base_path,
        link_prefix=args.link_prefix
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

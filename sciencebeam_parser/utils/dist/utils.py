import os
import re


def get_github_content_link_prefix(
    project_url: str,
    version: str,
    non_release_branch: str = 'develop'
) -> str:
    if 'dev' in version:
        return f'{project_url}/blob/{non_release_branch}'
    return f'{project_url}/blob/{version}'


def get_resolved_link(
    link: str,
    source_base_path: str,
    link_prefix: str
) -> str:
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
            + get_resolved_link(m.group(2), source_base_path, link_prefix)
            + m.group(3)
        ),
        markdown_content
    )

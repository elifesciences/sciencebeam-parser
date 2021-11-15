from setuptools import find_packages, setup

import sciencebeam_parser
from sciencebeam_parser.utils.dist.utils import (
    get_markdown_with_resolved_links,
    get_github_content_link_prefix
)


PROJECT_URL = 'https://github.com/elifesciences/sciencebeam-parser'
VERSION = sciencebeam_parser.__version__


with open('requirements.txt', 'r', encoding='utf-8') as f:
    REQUIRED_PACKAGES = f.readlines()


with open('doc/python_library.md', 'r', encoding='utf-8') as f:
    LONG_DESCRIPTION = get_markdown_with_resolved_links(
        '\n'.join([
            line.rstrip()
            for line in f
            if not line.startswith('[![')
        ]),
        source_base_path='doc',
        link_prefix=get_github_content_link_prefix(
            PROJECT_URL,
            version=VERSION
        )
    )


packages = find_packages(exclude=["tests", "tests.*"])

setup(
    name="sciencebeam_parser",
    version=VERSION,
    author="Daniel Ecer",
    url=PROJECT_URL,
    install_requires=REQUIRED_PACKAGES,
    packages=packages,
    include_package_data=True,
    description='ScienceBeam Parser, parse scientific documents.',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

from setuptools import find_packages, setup

import sciencebeam_parser


with open('requirements.txt', 'r', encoding='utf-8') as f:
    REQUIRED_PACKAGES = f.readlines()


with open('README.md', 'r', encoding='utf-8') as f:
    LONG_DESCRIPTION = '\n'.join([
        line.rstrip()
        for line in f
        if not line.startswith('[![')
    ])


packages = find_packages(exclude=["tests", "tests.*"])

setup(
    name="sciencebeam_parser",
    version=sciencebeam_parser.__version__,
    author="Daniel Ecer",
    url="https://github.com/elifesciences/sciencebeam-parser",
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

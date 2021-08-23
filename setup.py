from time import time

from setuptools import find_packages, setup


with open('requirements.txt', 'r', encoding='utf-8') as f:
    REQUIRED_PACKAGES = f.readlines()


with open('README.md', 'r', encoding='utf-8') as f:
    LONG_DESCRIPTION = '\n'.join([
        line.rstrip()
        for line in f
        if not line.startswith('[![')
    ])


def local_scheme(version):
    if not version.distance and not version.dirty:
        return ""
    return str(int(time()))


packages = find_packages(exclude=["tests", "tests.*"])

setup(
    name="sciencebeam_parser",
    use_scm_version={
        "local_scheme": local_scheme
    },
    setup_requires=['setuptools_scm'],
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

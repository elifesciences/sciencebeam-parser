import functools
from typing import cast

from sciencebeam_parser.models.model_impl import ModelImpl, T_ModelImplFactory


def get_delft_model_impl_for_path(path: str) -> ModelImpl:
    from sciencebeam_parser.models.delft_model_impl import (  # noqa pylint: disable=import-outside-toplevel
        DelftModelImpl
    )
    return DelftModelImpl(path)


def get_model_impl_for_config(config: dict):
    return get_delft_model_impl_for_path(config['path'])


def get_delft_model_impl_factory_for_path(path: str) -> T_ModelImplFactory:
    return cast(
        T_ModelImplFactory,
        functools.partial(get_delft_model_impl_for_path, path)
    )


def get_delft_model_impl_factory_for_config(config: dict) -> T_ModelImplFactory:
    return cast(
        T_ModelImplFactory,
        functools.partial(get_model_impl_for_config, config)
    )

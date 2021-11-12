import functools
from typing import cast

from sciencebeam_parser.app.context import AppContext
from sciencebeam_parser.models.model_impl import ModelImpl, T_ModelImplFactory


class EngineNames:
    DELFT = 'delft'
    WAPITI = 'wapiti'


def get_delft_model_impl_for_path(path: str, app_context: AppContext) -> ModelImpl:
    from sciencebeam_parser.models.delft_model_impl import (  # noqa pylint: disable=import-outside-toplevel
        DelftModelImpl
    )
    return DelftModelImpl(path, app_context=app_context)


def get_wapiti_model_impl_for_path(path: str, app_context: AppContext) -> ModelImpl:
    from sciencebeam_parser.models.wapiti_model_impl import (  # noqa pylint: disable=import-outside-toplevel
        WapitiModelImpl
    )
    return WapitiModelImpl(path, app_context=app_context)


def get_engine_name_for_config(config: dict) -> str:
    engine_name = config.get('engine')
    if engine_name:
        return engine_name
    return EngineNames.DELFT


def get_model_impl_for_config(config: dict, app_context: AppContext):
    path = config['path']
    engine_name = get_engine_name_for_config(config)
    if engine_name == EngineNames.WAPITI:
        return get_wapiti_model_impl_for_path(path, app_context=app_context)
    if engine_name == EngineNames.DELFT:
        return get_delft_model_impl_for_path(path, app_context=app_context)
    raise RuntimeError('invalid engine name: %r' % engine_name)


def get_model_impl_factory_for_config(
    config: dict,
    app_context: AppContext
) -> T_ModelImplFactory:
    return cast(
        T_ModelImplFactory,
        functools.partial(get_model_impl_for_config, config, app_context=app_context)
    )

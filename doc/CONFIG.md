# ScienceBeam Config

ScienceBeam can mainly be configured via an optional `app.cfg` and environment variables.

The [app-defaults.cfg](../app-defaults.cfg) file defines the default configuration and also documents some of the available options.

Those options can also be overridden using environment variables following the following naming convention (using double underscores):

`SCIENCEBEAM__<section name>__<parameter name>`.

The environment variable should be all upper case. Section names and parameter names are assumed to be lower case.

Some example configuration options:

| section | parameter name | environment variable name | description
| --------| -------------- | ------------------------- | -----------
| pipelines  | default | SCIENCEBEAM__PIPELINES__DEFAULT | the default pipeline, e.g. `grobid` |
| server  | max_concurrent_threads | SCIENCEBEAM__SERVER__MAX_CONCURRENT_THREADS | maximum of concurrent threads processed by the server |
| xslt_template_parameters  | acknowledgement_target | SCIENCEBEAM__XSLT_TEMPLATE_PARAMETERS__ACKNOWLEDGEMENT_TARGET | xslt parameter, defining where to output the acknowledgement section (e.g. `ack` or `body`) |
| xslt_template_parameters  | annex_target | SCIENCEBEAM__XSLT_TEMPLATE_PARAMETERS__ANNEX_TARGET | xslt parameter, defining where to output the annex section (e.g. `back`, `app` or `body`) |

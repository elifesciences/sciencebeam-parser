import logging

from apache_beam import coders, PTransform, Map
from apache_beam.io import filebasedsource, filebasedsink, Read
from apache_beam.io.filesystem import CompressionTypes
from apache_beam.io.filesystems import FileSystems

NAME = __name__


class _ReadFullFileSource(filebasedsource.FileBasedSource):
    def __init__(
            self,
            file_pattern,
            coder,
            compression_type,
            validate,
            output_filename=True,
            output_content=True,
            buffer_size=4096):

        super().__init__(
            file_pattern=file_pattern,
            compression_type=compression_type,
            splittable=False,
            validate=validate)
        self._coder = coder
        self.output_filename = output_filename
        self.output_content = output_content
        self.buffer_size = buffer_size

    def _read_all(self, file_handle):
        logger = logging.getLogger(NAME)
        result = None
        while True:
            buf = file_handle.read(self.buffer_size)
            logger.debug("read buffer: %s", len(buf) if buf else 'n/a')
            if buf is not None:
                if result is None:
                    result = buf
                else:
                    result += buf
            if buf is None or len(buf) < self.buffer_size:
                break
        logger.debug("read fully: %s", len(result))
        return result

    def read_records(self, file_name, offset_range_tracker):
        if offset_range_tracker.start_position():
            raise ValueError('Start position not 0:%s' %
                             offset_range_tracker.start_position())
        if self.output_filename and not self.output_content:
            yield file_name
        elif self.output_content:
            with self.open_file(file_name) as file_handle:
                content = self._read_all(file_handle)
                if self.output_filename:
                    yield file_name, content
                else:
                    yield content


class _ReadFullFile(PTransform):
    def __init__(
            self,
            file_pattern,
            coder=coders.BytesCoder(),
            compression_type=CompressionTypes.AUTO,
            validate=True,
            output_filename=True,
            output_content=True,
            **kwargs):
        super().__init__(**kwargs)
        self._source = _ReadFullFileSource(
            file_pattern, coder, compression_type,
            validate,
            output_filename=output_filename,
            output_content=output_content)

    def expand(self, pvalue):  # pylint: disable=arguments-differ,arguments-renamed
        return pvalue.pipeline | Read(self._source)


def ReadFileNames(*args, **kwargs):
    return _ReadFullFile(*args, output_filename=True, output_content=False, **kwargs)


def ReadFileContent(*args, **kwargs):
    return _ReadFullFile(*args, output_filename=False, output_content=True, **kwargs)


def ReadFileNamesAndContent(*args, **kwargs):
    return _ReadFullFile(*args, output_filename=True, output_content=True, **kwargs)


class _WriteFullFileSink(filebasedsink.FileBasedSink):
    def __init__(self, file_path_prefix, coder, file_name_suffix, num_shards,
                 shard_name_template, compression_type):
        super().__init__(
            file_path_prefix=file_path_prefix,
            coder=coder,
            file_name_suffix=file_name_suffix,
            num_shards=num_shards,
            shard_name_template=shard_name_template,
            mime_type='application/octet-stream',
            compression_type=compression_type)

    def write_full(self, file_name, value):
        logging.getLogger(NAME).info('writing to: %s', file_name)
        file_handle = FileSystems.create(
            file_name, self.mime_type, self.compression_type
        )
        try:
            file_handle.write(value)
        finally:
            if file_handle is not None:
                file_handle.close()
        return file_name, value


class WriteToFile(PTransform):
    def __init__(self,
                 coder=coders.BytesCoder(),
                 file_name_suffix='',
                 num_shards=0,
                 shard_name_template=None,
                 compression_type=CompressionTypes.AUTO,
                 **kwargs):
        super().__init__(**kwargs)
        self._sink = _WriteFullFileSink(
            'dummy', coder, file_name_suffix,
            num_shards, shard_name_template,
            compression_type)

    def expand(self, pcoll):  # pylint: disable=arguments-differ,arguments-renamed
        return pcoll | Map(lambda kv: self._sink.write_full(kv[0], kv[1]))

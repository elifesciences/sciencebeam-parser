# ScienceBeam API

## /api/convert

The currently the only API is _/api/convert_
e.g. [http://localhost:8075/api/convert](http://localhost:8075/api/convert).

It supports three modes of use.

### GET

A GET request will show a very simple submission form that allows the user to select a file which will be submitted to the API.

### POST PDF as data

The PDF can be posted as data to the API. The API will respond with the JATS XML.

e.g.

```bash
curl -X POST --show-error -H "Content-Type: application/pdf" \
  --data-binary @test.pdf \
  http://localhost:8075/api/convert?filename=test.pdf
```

The _filename_ parameter is optional.

### POST PDF as a file

The PDF can also be posted as a file. The effect will be the same as posting it as data.

e.g.

```bash
curl -X POST --show-error --form \
  "file=@test.pdf;filename=test.pdf" \
  http://localhost:8075/api/convert
```

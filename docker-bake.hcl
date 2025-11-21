target "runtime" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "runtime"
}

target "runtime-cv" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "runtime-cv"
}

target "dev" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "dev"
}

target "lint-flake8" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "lint-flake8"
}

target "lint-pylint" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "lint-pylint"
}

target "lint-mypy" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "lint-mypy"
}

target "pytest" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "pytest"
}

target "end-to-end-tests" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "end-to-end-tests"
}

target "python-dist" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "python-dist"
}

group "default" {
  targets = ["runtime", "runtime-cv"]
}

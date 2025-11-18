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

group "default" {
  targets = ["runtime", "runtime-cv"]
}

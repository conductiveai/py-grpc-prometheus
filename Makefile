.PHONY: initialize-development

# Initialize the project development environment.
initialize-development:
	@pip install --upgrade -r requirements.txt
	@pip install -U -r test_requirements.txt
	@pre-commit install

.PHONY: test
test:
	@black --check py_grpc_prometheus
	@mypy --show-error-codes py_grpc_prometheus
	@coverage run --source=py_grpc_prometheus -m pytest
	@coverage report -m

# Run pre-commit for all
pre-commit:
	@pre-commit run --all-files

run-test:
	@python -m unittest discover

# Fix the import path. Use pipe for sed to avoid the difference between Mac and GNU sed
compile-protos:
	@protoc \
      --python_out=tests/integration//hello_world  \
      --grpc_out=tests/integration//hello_world  \
      -I tests/integration/protos \
      tests/integration/protos/hello_world.proto

run-test-server:
	python -m tests.integration.hello_world.hello_world_server

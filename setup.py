#!/usr/bin/env python
from setuptools import find_packages
from setuptools import setup

import setuptools.command.build_py


class BuildPyCommand(setuptools.command.build_py.build_py):
    """Custom build command."""

    def run(self):
        print("Custom build: Generate protobuf python source file")
        from grpc_tools import protoc

        integration_dir = "tests/integration"
        ret = protoc.main(
            (
                "",
                f"-I{integration_dir}/protos",
                f"--python_out={integration_dir}/hello_world",
                f"--grpc_python_out={integration_dir}/hello_world",
                f"{integration_dir}/protos/hello_world.proto",
            )
        )
        assert ret == 0, "Fail to generate proto files"
        return super().run()


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="py_grpc_prometheus",
    version="0.7.0",
    description="Python gRPC Prometheus Interceptors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lin Chen",
    author_email="linchen04@gmail.com",
    install_requires=[
        "setuptools>=39.0.1",
        "grpcio>=1.10.0",
        "prometheus_client>=0.3.0",
        "grpc-stubs==1.24.11",
    ],
    url="https://github.com/conductive/py-grpc-prometheus",
    packages=find_packages(exclude=["tests.*", "tests"]),
    package_data={
        "py_grpc_prometheus": [
            "py.typed",
        ]
    },
)

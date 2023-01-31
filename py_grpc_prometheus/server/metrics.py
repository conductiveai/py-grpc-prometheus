from typing import Optional, Iterator

import grpc
from prometheus_client import Counter, Histogram
from prometheus_client.registry import CollectorRegistry


class Metrics:
    def __init__(self, registry: Optional[CollectorRegistry]) -> None:
        self.completed_rpc_counter = Counter(
            "grpc_server_handled_total",
            "Total number of RPCs completed on the server, regardless of success or failure.",
            ["grpc_type", "grpc_service", "grpc_method", "grpc_code"],
            registry=registry,
        )
        self.started_rpc_counter = Counter(
            "grpc_server_started_total",
            "Total number of RPCs started on the server.",
            ["grpc_type", "grpc_service", "grpc_method"],
            registry=registry,
        )
        self.stream_msg_received_counter = Counter(
            "grpc_server_msg_received_total",
            "Total number of RPC stream messages received on the server.",
            ["grpc_type", "grpc_service", "grpc_method"],
            registry=registry,
        )
        self.stream_msg_sent_counter = Counter(
            "grpc_server_msg_sent_total",
            "Total number of gRPC stream messages sent by the server.",
            ["grpc_type", "grpc_service", "grpc_method"],
            registry=registry,
        )
        self.response_latency_sec_histogram = Histogram(
            "grpc_server_handling_seconds",
            "Histogram of response latency (seconds) of gRPC that had been application-level handled by the server."
            "handled by the server.",
            ["grpc_type", "grpc_service", "grpc_method"],
            registry=registry,
        )

    def record_started_rpc(
        self, grpc_type: str, grpc_service: str, grpc_method: str
    ) -> None:
        self.started_rpc_counter.labels(
            grpc_type=grpc_type,
            grpc_service=grpc_service,
            grpc_method=grpc_method,
        ).inc()

    def record_completed_rpc(
        self, grpc_type: str, grpc_service: str, grpc_method: str, grpc_code: str
    ) -> None:
        self.completed_rpc_counter.labels(
            grpc_type=grpc_type,
            grpc_service=grpc_service,
            grpc_method=grpc_method,
            grpc_code=grpc_code,
        ).inc()

    def record_request_latency(
        self, grpc_type: str, grpc_service: str, grpc_method: str, latency: float
    ) -> None:
        self.response_latency_sec_histogram.labels(
            grpc_type=grpc_type,
            grpc_service=grpc_service,
            grpc_method=grpc_method,
        ).observe(max(latency, 0))

    def record_stream_msg_received(
        self,
        req_iterator: Iterator["grpc.TRequest"],
        grpc_type: str,
        grpc_service: str,
        grpc_method: str,
    ) -> Iterator["grpc.TRequest"]:
        for req_item in req_iterator:
            self.stream_msg_received_counter.labels(
                grpc_type=grpc_type,
                grpc_service=grpc_service,
                grpc_method=grpc_method,
            ).inc()
            yield req_item

    def record_stream_msg_sent(
        self,
        resp_iterator: Iterator["grpc.TResponse"],
        grpc_type: str,
        grpc_service: str,
        grpc_method: str,
    ) -> Iterator["grpc.TResponse"]:
        for resp_item in resp_iterator:
            self.stream_msg_sent_counter.labels(
                grpc_type=grpc_type,
                grpc_service=grpc_service,
                grpc_method=grpc_method,
            ).inc()
            yield resp_item

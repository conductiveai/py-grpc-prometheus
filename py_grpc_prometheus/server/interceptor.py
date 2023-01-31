"""Interceptor a client call with prometheus"""
from timeit import default_timer

import grpc
from prometheus_client.registry import REGISTRY, CollectorRegistry

from py_grpc_prometheus import grpc_utils
from py_grpc_prometheus.server.metrics import Metrics
from typing import Optional, Callable, Union, Iterator, cast


class PromServerInterceptor(grpc.ServerInterceptor):
    def __init__(self, registry: Optional[CollectorRegistry] = REGISTRY) -> None:
        self._metrics = Metrics(registry)

    def intercept_service(
        self, continuation, handler_call_details: grpc.HandlerCallDetails
    ):
        """
        Intercepts the server function calls.

        This implements referred to:
        https://github.com/census-instrumentation/opencensus-python/blob/master/opencensus/
        trace/ext/grpc/server_interceptor.py
        and
        https://grpc.io/grpc/python/grpc.html#service-side-interceptor
        """

        handler: Optional[grpc.RpcMethodHandler] = continuation(handler_call_details)
        if handler is None:
            return None

        if handler.request_streaming and handler.response_streaming:
            behavior_fn = handler.stream_stream
            handler_factory = grpc.stream_stream_rpc_method_handler
        elif handler.request_streaming and not handler.response_streaming:
            behavior_fn = handler.stream_unary
            handler_factory = grpc.stream_unary_rpc_method_handler
        elif not handler.request_streaming and handler.response_streaming:
            behavior_fn = handler.unary_stream
            handler_factory = grpc.unary_stream_rpc_method_handler
        else:
            behavior_fn = handler.unary_unary
            handler_factory = grpc.unary_unary_rpc_method_handler
        if behavior_fn is None or handler_factory is None:
            return None

        grpc_service_name, grpc_method_name, _ = grpc_utils.split_method_call(
            handler_call_details
        )
        grpc_type = grpc_utils.get_method_type(
            handler.request_streaming, handler.response_streaming
        )

        return handler_factory(
            self._metrics_wrapper(
                behavior_fn,
                grpc_service_name,
                grpc_method_name,
                grpc_type,
                handler.request_streaming,
                handler.response_streaming,
            ),
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def _metrics_wrapper(
        self,
        behavior: Callable[
            [Union["grpc.TRequest", Iterator["grpc.TRequest"]], grpc.ServicerContext],
            Union["grpc.TResponse", Iterator["grpc.TResponse"]],
        ],
        grpc_service: str,
        grpc_method: str,
        grpc_type: str,
        request_streaming: bool,
        response_streaming: bool,
    ) -> Callable[
        [Union["grpc.TRequest", Iterator["grpc.TRequest"]], grpc.ServicerContext],
        Union["grpc.TResponse", Iterator["grpc.TResponse"]],
    ]:
        def _wrap_behavior(
            request_or_iterator: Union["grpc.TRequest", Iterator["grpc.TRequest"]],
            servicer_context: grpc.ServicerContext,
        ):
            start = default_timer()
            try:
                if request_streaming:
                    request_or_iterator = self._metrics.record_stream_msg_received(
                        cast(Iterator["grpc.TRequest"], request_or_iterator),
                        grpc_type,
                        grpc_service,
                        grpc_method,
                    )
                else:
                    self._metrics.record_started_rpc(
                        grpc_type, grpc_service, grpc_method
                    )

                # Invoke the original rpc behavior.
                response_or_iterator = behavior(request_or_iterator, servicer_context)

                if response_streaming:
                    response_or_iterator = self._metrics.record_stream_msg_sent(
                        cast(Iterator["grpc.TResponse"], response_or_iterator),
                        grpc_type,
                        grpc_service,
                        grpc_method,
                    )
                else:
                    self._metrics.record_completed_rpc(
                        grpc_type,
                        grpc_service,
                        grpc_method,
                        self._compute_status_code(servicer_context).name,
                    )
                return response_or_iterator
            except grpc.RpcError as e:
                self._metrics.record_completed_rpc(
                    grpc_type,
                    grpc_service,
                    grpc_method,
                    self._compute_error_code(e).name,
                )
                raise e
            finally:
                if not response_streaming:
                    self._metrics.record_request_latency(
                        grpc_type, grpc_service, grpc_method, default_timer() - start
                    )

        return _wrap_behavior

    # pylint: disable=protected-access
    def _compute_status_code(
        self, servicer_context: grpc.ServicerContext
    ) -> grpc.StatusCode:
        if servicer_context._state.client == "cancelled":  # type: ignore
            return grpc.StatusCode.CANCELLED

        if servicer_context._state.code is None:  # type: ignore
            return grpc.StatusCode.OK

        return servicer_context._state.code  # type: ignore

    def _compute_error_code(self, grpc_exception: grpc.RpcError) -> grpc.StatusCode:
        if isinstance(grpc_exception, grpc.Call):
            return grpc_exception.code()

        return grpc.StatusCode.UNKNOWN

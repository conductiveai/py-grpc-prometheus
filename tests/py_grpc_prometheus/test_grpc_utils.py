from grpc import HandlerCallDetails

from py_grpc_prometheus.grpc_utils import split_method_call


def test_split_method_call():
    details = HandlerCallDetails()
    details.method = "ABC"
    assert split_method_call(details) == ("", "", False)

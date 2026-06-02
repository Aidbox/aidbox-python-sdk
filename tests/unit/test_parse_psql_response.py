import pytest

from aidbox_python_sdk.db import parse_psql_response
from aidbox_python_sdk.exceptions import AidboxDBException

# fmt: off
OLD_SUCCESS = [{"status": "success", "result": [{"last_value": 263052}], "duration": 1,   "query": "SELECT last_value from transaction_id_seq;"}]
OLD_ERROR   = [{"status": "error",   "error":  {"message": "oops"},                        "query": "SELECT 1;"}]
OLD_NONE    = [{"status": "success", "result": None}]
OLD_EXECUTE = [{"status": "success", "result": True,                     "duration": 0.0, "query": "select drop_before_all(100);"}]

NEW_SUCCESS = {"status": "success", "result": [{"type": "rset", "data": [{"last_value": 1608}]}], "duration": 0, "query": "SELECT last_value from transaction_id_seq;"}
NEW_ERROR   = {"status": "error",   "error":  {"message": "oops"},                                                "query": "SELECT 1;"}
NEW_NONE    = {"status": "success", "result": None}
NEW_EXECUTE        = {"status": "success", "result": [{"type": "rset", "data": [{"last_value": 4205}]}], "duration": 6, "query": "SELECT last_value from transaction_id_seq;"}
NEW_MULTI_EXECUTE  = {"status": "success", "result": [{"type": "rset", "data": [{"last_value": 1000}]}, {"type": "rset", "data": [{"last_value": 1000}]}], "duration": 4, "query": "SELECT last_value from transaction_id_seq;SELECT last_value from transaction_id_seq;"}
# fmt: on


def test_old_success_returns_rows():
    assert parse_psql_response(OLD_SUCCESS) == [[{"last_value": 263052}]]


def test_old_error_raises():
    with pytest.raises(AidboxDBException):
        parse_psql_response(OLD_ERROR)


def test_old_none_result():
    assert parse_psql_response(OLD_NONE) == [None]


def test_old_execute_wraps_true():
    assert parse_psql_response(OLD_EXECUTE) == [True]


def test_new_success_returns_rows():
    assert parse_psql_response(NEW_SUCCESS) == [[{"last_value": 1608}]]


def test_new_error_raises():
    with pytest.raises(AidboxDBException):
        parse_psql_response(NEW_ERROR)


def test_new_none_result():
    assert parse_psql_response(NEW_NONE) == [None]


def test_new_execute_returns_rows():
    assert parse_psql_response(NEW_EXECUTE) == [[{"last_value": 4205}]]


def test_new_multi_execute_returns_list_of_row_lists():
    assert parse_psql_response(NEW_MULTI_EXECUTE) == [
        [{"last_value": 1000}],
        [{"last_value": 1000}],
    ]

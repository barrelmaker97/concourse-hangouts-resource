#!/usr/bin/env python3
import copy
import json
import os
import random

import pytest
import requests

from assets import resource


# Test catalog:
# - Pure unit tests: test_get_bool_*
# - Contract success tests: test_send_*, test_run_resource_* (except explicit failures)
# - Contract failure tests: test_run_resource_out_http_error, test_run_resource_out_request_exception


@pytest.fixture
def mock_api_payload():
    return {
        "sender": {"name": "users/abc", "displayName": "Bot User"},
        "space": {
            "name": "spaces/xyz",
            "displayName": "Team Space",
            "type": "ROOM",
        },
        "thread": {"name": "spaces/xyz/threads/thread-1"},
        "createTime": "2025-01-01T00:00:00.000Z",
    }


@pytest.fixture
def mock_response(mock_api_payload):
    class MockResponse:
        status_code = 200
        text = json.dumps(mock_api_payload)

        @staticmethod
        def raise_for_status():
            return None

    return MockResponse()


@pytest.fixture
def mock_post(monkeypatch, mock_response):
    state = {"url": None, "json": None, "headers": None, "timeout": None}

    def fake_post(url, json=None, headers=None, timeout=None):
        state["url"] = url
        state["json"] = json
        state["headers"] = headers
        state["timeout"] = timeout
        return mock_response

    monkeypatch.setattr(resource.requests, "post", fake_post)
    return state


def test_send_no_thread(mock_post):
    test_message = str(random.getrandbits(128))
    code, message = resource.send("https://httpbin.org/post", test_message, False)
    assert code == 200
    assert test_message == mock_post["json"]["text"]
    assert "threadKey=concoursethreadkey" in mock_post["url"]
    assert mock_post["timeout"] == resource.REQUEST_TIMEOUT_SECONDS
    assert message


def test_send_thread(mock_post):
    test_message = str(random.getrandbits(128))
    code, _ = resource.send("https://httpbin.org/post", test_message, True)
    assert code == 200
    assert "threadKey=concoursethreadkey" not in mock_post["url"]
    assert mock_post["timeout"] == resource.REQUEST_TIMEOUT_SECONDS


def test_send_timeout(monkeypatch):
    def timeout_post(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(resource.requests, "post", timeout_post)

    with pytest.raises(requests.Timeout):
        resource.send("https://httpbin.org/post", "message", False)


def test_get_bool_true():
    assert resource.get_bool(True, True)


def test_get_bool_false():
    assert not resource.get_bool(False, True)


def test_get_bool_default():
    assert resource.get_bool("notaboolean", True)


def test_get_bool_failure():
    try:
        resource.get_bool(True, "notaboolean")
    except Exception as ex:
        print(ex)
        return
    assert False


def test_run_resource_check(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("check", data, "") == ([], True)


def test_run_resource_in(basic_input):
    data = json.dumps(basic_input)
    assert resource.run_resource("in", data, "") == ({"version": {}}, True)


def test_run_resource_out_basic(basic_input, basic_output, env_vars, mock_post):
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_thread(basic_input, basic_output, env_vars, mock_post):
    basic_input["params"]["create_thread"] = True
    basic_output["metadata"][4]["value"] = "True"
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)
    assert "threadKey=concoursethreadkey" not in mock_post["url"]


def test_run_resource_out_no_thread(basic_input, basic_output, env_vars, mock_post):
    basic_input["params"]["create_thread"] = False
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)
    assert "threadKey=concoursethreadkey" in mock_post["url"]


def test_run_resource_out_no_message(basic_input, basic_output, env_vars, mock_post):
    del basic_input["params"]["message"]
    basic_output["metadata"][1]["value"] = "None"
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_message_file(
    basic_input, basic_output, request, env_vars, mock_post
):
    basic_input["params"]["message_file"] = "message.txt"
    basic_output["metadata"][2]["value"] = "message.txt"
    data = json.dumps(basic_input)
    current_dir = request.fspath.dirname
    assert resource.run_resource("out", data, [current_dir]) == (basic_output, True)


def test_run_resource_out_missing_message_file(
    basic_input, basic_output, env_vars, mock_post
):
    basic_input["params"]["message_file"] = "not_a_message.txt"
    basic_output["metadata"][2]["value"] = "not_a_message.txt"
    data = json.dumps(basic_input)
    current_dir = os.getcwd()
    assert resource.run_resource("out", data, [current_dir]) == (basic_output, True)


def test_run_resource_out_add_info(basic_input, basic_output, env_vars, mock_post):
    basic_input["params"]["post_info"] = True
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_no_info(basic_input, basic_output, env_vars, mock_post):
    basic_input["params"]["post_info"] = False
    basic_output["metadata"][8]["value"] = "False"
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_add_url(basic_input, basic_output, env_vars, mock_post):
    basic_input["params"]["post_url"] = True
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_no_url(basic_input, basic_output, env_vars, mock_post):
    basic_input["params"]["post_url"] = False
    basic_output["metadata"][3]["value"] = ""
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)


def test_run_resource_out_webhook_with_params(
    basic_input, basic_output, env_vars, mock_post
):
    basic_input["source"]["webhook_url"] = "https://httpbin.org/post?test=test"
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (basic_output, True)
    assert "test=test" in mock_post["url"]


def test_run_resource_out_http_error(monkeypatch, basic_input, failure_output):
    class FailingResponse:
        status_code = 500
        text = "{}"

        @staticmethod
        def raise_for_status():
            raise requests.HTTPError("500 Server Error")

    monkeypatch.setattr(resource.requests, "post", lambda *args, **kwargs: FailingResponse())
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (failure_output, False)


def test_run_resource_out_request_exception(monkeypatch, basic_input, failure_output):
    def request_error(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(resource.requests, "post", request_error)
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (failure_output, False)


def test_run_resource_out_missing_webhook(basic_input, failure_output):
    del basic_input["source"]["webhook_url"]
    data = json.dumps(basic_input)
    assert resource.run_resource("out", data, "") == (failure_output, False)


@pytest.fixture
def env_vars():
    os.environ["BUILD_PIPELINE_NAME"] = "Test_Pipeline"
    os.environ["BUILD_JOB_NAME"] = "Test_Job"
    os.environ["BUILD_NAME"] = "1234"
    os.environ["BUILD_TEAM_NAME"] = "Test_Team"
    os.environ["ATC_EXTERNAL_URL"] = "https://not.a.site"
    yield True
    del os.environ["BUILD_PIPELINE_NAME"]
    del os.environ["BUILD_JOB_NAME"]
    del os.environ["BUILD_NAME"]
    del os.environ["BUILD_TEAM_NAME"]
    del os.environ["ATC_EXTERNAL_URL"]


@pytest.fixture
def basic_input():
    return {
        "source": {"webhook_url": "https://httpbin.org/post"},
        "params": {"message": "Test Message"},
    }


@pytest.fixture
def basic_output(mock_api_payload):
    url = "https://not.a.site/teams/Test_Team/pipelines/Test_Pipeline/jobs/Test_Job/builds/1234"
    output = {
        "version": {},
        "metadata": [
            {"name": "Status", "value": "Posted"},
            {"name": "Message", "value": "Test Message"},
            {"name": "Message File Name", "value": "None"},
            {"name": "Build URL", "value": url},
            {"name": "Thread Created", "value": "False"},
            {"name": "Pipeline Name", "value": "Test_Pipeline"},
            {"name": "Job Name", "value": "Test_Job"},
            {"name": "Build Number", "value": "1234"},
            {"name": "Info Sent", "value": "True"},
            {"name": "Sender Name", "value": mock_api_payload["sender"]["name"]},
            {
                "name": "Sender Display Name",
                "value": mock_api_payload["sender"]["displayName"],
            },
            {"name": "Space Name", "value": mock_api_payload["space"]["name"]},
            {
                "name": "Space Display Name",
                "value": mock_api_payload["space"]["displayName"],
            },
            {"name": "Space Type", "value": mock_api_payload["space"]["type"]},
            {"name": "Thread Name", "value": mock_api_payload["thread"]["name"]},
            {"name": "Time Created", "value": mock_api_payload["createTime"]},
        ],
    }
    return copy.deepcopy(output)


@pytest.fixture
def failure_output():
    return {"version": {}, "metadata": [{"name": "status", "value": "Failed"}]}

# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the Apache License 2.0 (the "License"). A copy of the
# License may be obtained with this software package or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Use of this file is prohibited except in compliance with the License.
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for results manager."""

from http.client import HTTPMessage
from unittest.mock import ANY, MagicMock, Mock, call

import pytest
import requests

from covalent._results_manager import wait
from covalent._results_manager.results_manager import (
    _get_result_from_dispatcher,
    cancel,
    get_result,
)
from covalent._shared_files.config import get_config


def test_get_result_unreachable_dispatcher(mocker):
    """
    Test that get_result returns None when
    the dispatcher server is unreachable.
    """
    mock_dispatch_id = "mock_dispatch_id"

    mocker.patch(
        "covalent._results_manager.results_manager._get_result_from_dispatcher",
        side_effect=requests.exceptions.ConnectionError,
    )

    assert get_result(mock_dispatch_id) is None


@pytest.mark.parametrize(
    "dispatcher_addr",
    [
        "http://" + get_config("dispatcher.address") + ":" + str(get_config("dispatcher.port")),
        "http://localhost:48008",
    ],
)
def test_get_result_from_dispatcher(mocker, dispatcher_addr):
    retries = 10
    getconn_mock = mocker.patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    mocker.patch("requests.Response.json", return_value=True)
    headers = HTTPMessage()
    headers.add_header("Retry-After", "2")

    mock_response = [Mock(status=503, msg=headers)] * (retries - 1)
    mock_response.append(Mock(status=200, msg=HTTPMessage()))
    getconn_mock.return_value.getresponse.side_effect = mock_response
    dispatch_id = "9d1b308b-4763-4990-ae7f-6a6e36d35893"
    _get_result_from_dispatcher(
        dispatch_id, wait=wait.LONG, dispatcher_addr=dispatcher_addr, status_only=False
    )
    assert (
        getconn_mock.return_value.request.mock_calls
        == [
            call(
                "GET",
                f"/api/result/{dispatch_id}?wait=True&status_only=False",
                body=None,
                headers=ANY,
            ),
        ]
        * retries
    )


def test_get_result_from_dispatcher_unreachable(mocker):
    """
    Test that _get_result_from_dispatcher raises an exception when
    the dispatcher server is unreachable.
    """

    # TODO: Will need to edit this once `_get_result_from_dispatcher` is fixed
    # to actually throw an exception when the dispatcher server is unreachable
    # instead of just hanging.

    mock_dispatcher_addr = "mock_dispatcher_addr"
    mock_dispatch_id = "mock_dispatch_id"

    message = f"The Covalent server cannot be reached at {mock_dispatcher_addr}. Local servers can be started using `covalent start` in the terminal. If you are using a remote Covalent server, contact your systems administrator to report an outage."

    mocker.patch("covalent._results_manager.results_manager.HTTPAdapter")
    mock_session = mocker.patch("covalent._results_manager.results_manager.requests.Session")
    mock_session.return_value.get.side_effect = requests.exceptions.ConnectionError

    mock_print = mocker.patch("covalent._results_manager.results_manager.print")

    with pytest.raises(requests.exceptions.ConnectionError):
        _get_result_from_dispatcher(
            mock_dispatch_id, wait=wait.LONG, dispatcher_addr=mock_dispatcher_addr
        )

    mock_print.assert_called_once_with(message)


def test_cancel_with_single_task_id(mocker):
    mock_get_config = mocker.patch("covalent._results_manager.results_manager.get_config")
    mock_request_post = mocker.patch(
        "covalent._results_manager.results_manager.requests.post", MagicMock()
    )

    cancel(dispatch_id="dispatch", task_ids=1)

    assert mock_get_config.call_count == 2
    mock_request_post.assert_called_once()
    mock_request_post.return_value.raise_for_status.assert_called_once()


def test_cancel_with_multiple_task_ids(mocker):
    mock_get_config = mocker.patch("covalent._results_manager.results_manager.get_config")
    mock_task_ids = [0, 1]

    mock_request_post = mocker.patch(
        "covalent._results_manager.results_manager.requests.post", MagicMock()
    )

    cancel(dispatch_id="dispatch", task_ids=[1, 2, 3])

    assert mock_get_config.call_count == 2
    mock_request_post.assert_called_once()
    mock_request_post.return_value.raise_for_status.assert_called_once()

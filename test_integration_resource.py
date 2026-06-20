#!/usr/bin/env python3
import os
import random

import pytest

from assets import resource


pytestmark = pytest.mark.integration


@pytest.fixture
def integration_webhook_url():
    url = os.getenv("INTEGRATION_WEBHOOK_URL")
    if not url:
        pytest.skip("Set INTEGRATION_WEBHOOK_URL to run integration tests.")
    return url


def test_send_no_thread_live(integration_webhook_url):
    test_message = str(random.getrandbits(128))
    code, message = resource.send(integration_webhook_url, test_message, False)
    assert code == 200
    assert message


def test_send_thread_live(integration_webhook_url):
    test_message = str(random.getrandbits(128))
    code, message = resource.send(integration_webhook_url, test_message, True)
    assert code == 200
    assert message

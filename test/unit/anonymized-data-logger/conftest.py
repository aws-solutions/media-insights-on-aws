# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/anonymized-data-logger/')

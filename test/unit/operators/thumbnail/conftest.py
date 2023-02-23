# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from botocore.stub import Stubber

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/operators/')
    monkeypatch.syspath_prepend('../../source/lib/MediaInsightsEngineLambdaHelper/')
    monkeypatch.syspath_prepend('./operators/')
    monkeypatch.setenv("botoConfig", '{"user_agent_extra": "AwsSolution/SO0163/vX.X.X"}')
    monkeypatch.setenv('AWS_XRAY_CONTEXT_MISSING', 'LOG_ERROR')
    monkeypatch.setenv('DATAPLANE_BUCKET', 'testDataplaneBucket')
    monkeypatch.setenv('mediaconvertRole', 'testMediaconvertRole')
    monkeypatch.setenv('AWS_REGION', 'us-west-2')
    monkeypatch.setenv('MEDIACONVERT_ENDPOINT', 'https://test.mediaconvert.endpoint')
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture()
def mediaconvert_start_stub():
    import thumbnail.start_thumbnail as app
    client = app.get_mediaconvert_client()
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture()
def mediaconvert_check_stub():
    import thumbnail.check_thumbnail as app
    client = app.get_mediaconvert_client()
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
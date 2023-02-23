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
    monkeypatch.setenv('DataplaneEndpoint', 'testDataplaneEndpoint')
    monkeypatch.setenv('comprehendRole', 'testComprehendRole10')
    monkeypatch.setenv('AWS_REGION', 'us-west-2')
    monkeypatch.setenv('KmsId', 'testKmsId')
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture
def comprehend_client_stub(mock_env_variables):
    import comprehend.entities.get_entity_detection as app
    with Stubber(app.comprehend) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def comprehend_start_entity(mock_env_variables):
    import comprehend.entities.start_entity_detection as app
    with Stubber(app.comprehend) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def s3_get_entity(mock_env_variables):
    import comprehend.entities.get_entity_detection as app
    with Stubber(app.s3_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def s3_start_entity(mock_env_variables):
    import comprehend.entities.start_entity_detection as app
    with Stubber(app.s3) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

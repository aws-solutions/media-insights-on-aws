# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from chalice.test import Client
from botocore.stub import Stubber
import boto3


@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/dataplaneapi/')
    monkeypatch.setenv("DATAPLANE_TABLE_NAME", "testDataplaneTableName")
    monkeypatch.setenv("DATAPLANE_BUCKET", "testDataplaneBucketName")
    monkeypatch.setenv("botoConfig", '{"user_agent_extra": "AwsSolution/SO0163/vX.X.X"}')
    monkeypatch.setenv("FRAMEWORK_VERSION", "v9.9.9")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "test")


@pytest.fixture
def test_client(mock_env_variables):
    from app import app
    with Client(app) as client:
        yield client


@pytest.fixture
def s3_client_stub(mock_env_variables):
    from app import s3_client
    with Stubber(s3_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def s3_resource_stub(mock_env_variables):
    from app import s3_resource
    with Stubber(s3_resource.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def ddb_resource_stub(mock_env_variables):
    from app import dynamo_resource
    with Stubber(dynamo_resource.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def ddb_client_stub(mock_env_variables):
    from app import dynamo_client
    with Stubber(dynamo_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

import pytest
import sys
from chalice.test import Client
from botocore.stub import Stubber

sys.path.append('source/dataplaneapi/')


@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.setenv("DATAPLANE_TABLE_NAME", "testDataplaneTableName")
    monkeypatch.setenv("DATAPLANE_BUCKET", "testDataplaneBucketName")


@pytest.fixture
def test_client(mock_env_variables):
    from app import app
    with Client(app) as client:
        yield client


@pytest.fixture(autouse=True)
def s3_client_stub(mock_env_variables):
    from app import s3_client
    with Stubber(s3_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture(autouse=True)
def ddb_resource_stub(mock_env_variables):
    from app import dynamo_resource
    with Stubber(dynamo_resource.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


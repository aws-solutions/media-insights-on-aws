import pytest
from chalice.test import Client
from botocore.stub import Stubber
from unittest import mock
import boto3
# import sys


@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/workflowapi/')
    monkeypatch.syspath_prepend('../../source/lib/MediaInsightsEngineLambdaHelper')
    monkeypatch.setenv("STACK_SHORT_UUID", "test1234")
    monkeypatch.setenv("SYSTEM_TABLE_NAME", "testSystemTable")
    monkeypatch.setenv("WORKFLOW_TABLE_NAME", "testWorkflowTable")
    monkeypatch.setenv("STAGE_TABLE_NAME", "testStageTable")
    monkeypatch.setenv("OPERATION_TABLE_NAME", "testOperationTable")
    monkeypatch.setenv("WORKFLOW_EXECUTION_TABLE_NAME", "testExecutionTable")
    monkeypatch.setenv("HISTORY_TABLE_NAME", "testHistoryTable")
    monkeypatch.setenv("STAGE_EXECUTION_QUEUE_URL", "testQueueUrl")
    monkeypatch.setenv("STAGE_EXECUTION_ROLE", "testExecutionRole/role")
    monkeypatch.setenv("STEP_FUNCTION_LOG_GROUP_ARN", "testExecutionSfnLogGroup")
    monkeypatch.setenv("COMPLETE_STAGE_LAMBDA_ARN", "testCompleteStageArn")
    monkeypatch.setenv("FILTER_OPERATION_LAMBDA_ARN", "testFilterLambdaArn")
    monkeypatch.setenv("OPERATOR_FAILED_LAMBDA_ARN", "testFailedLambdaArn")
    monkeypatch.setenv("WORKFLOW_SCHEDULER_LAMBDA_ARN", "testSchedulerArn")
    monkeypatch.setenv("DataplaneEndpoint", "testDataplaneEndpoint")
    monkeypatch.setenv("botoConfig", '{"user_agent_extra": "AwsSolution/SO0163/vX.X.X"}')
    monkeypatch.setenv("FRAMEWORK_VERSION", "v9.9.9")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture
def test_client(mock_env_variables):
    from app import app
    with Client(app) as client:
        yield client

@pytest.fixture
def ddb_resource_stub(mock_env_variables):
    from app import DYNAMO_RESOURCE
    with Stubber(DYNAMO_RESOURCE.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def sqs_client_stub(mock_env_variables):
    from app import SQS_CLIENT
    with Stubber(SQS_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def lambda_client_stub(mock_env_variables):
    from app import LAMBDA_CLIENT
    with Stubber(LAMBDA_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def iam_client_stub(mock_env_variables):
    from app import IAM_CLIENT
    with Stubber(IAM_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def sfn_client_stub(mock_env_variables):
    from app import SFN_CLIENT
    with Stubber(SFN_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def transcribe_client_stub(mock_env_variables):
    import app
    client = app.get_transcribe_client()
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def translate_client_stub(mock_env_variables):
    import app
    client = app.get_translate_client()
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

def create_asset():
    return {'AssetId': 'abcd-1234-efgh', 'S3Bucket': 'testBucket', 'S3Key': 'private/assets/abcd-1234-efgh/input/testFile.mp4'}

@pytest.fixture(autouse=True)
def mock_create_asset_response(monkeypatch, mock_env_variables):
    from app import DataPlane

    def get_mock(*args, **kwargs):
        return create_asset()

    monkeypatch.setattr(DataPlane, "create_asset", get_mock)


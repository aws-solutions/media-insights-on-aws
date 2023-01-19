import pytest
from botocore.stub import Stubber

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/workflow/')
    monkeypatch.syspath_prepend('../../source/lib/MediaInsightsEngineLambdaHelper')
    monkeypatch.setenv("botoConfig", '{"user_agent_extra": "AwsSolution/SO0163/vX.X.X"}')
    monkeypatch.setenv('StreamName', 'testStreamName')
    monkeypatch.setenv('AWS_XRAY_CONTEXT_MISSING', 'LOG_ERROR')
    monkeypatch.setenv('WORKFLOW_TABLE_NAME', 'testWorkflowTable')
    monkeypatch.setenv('STAGE_TABLE_NAME', 'testStageTable')
    monkeypatch.setenv('OPERATION_TABLE_NAME', 'testOperationTable')
    monkeypatch.setenv('WORKFLOW_EXECUTION_TABLE_NAME', 'testExecutionTable')
    monkeypatch.setenv('STAGE_EXECUTION_QUEUE_URL', 'testExecutionQueueUrl')
    monkeypatch.setenv('WORKFLOW_SCHEDULER_LAMBDA_ARN', 'testSchedulerLambdaArn')
    monkeypatch.setenv('SYSTEM_TABLE_NAME', 'testSystemTable')
    monkeypatch.setenv('DEFAULT_MAX_CONCURRENT_WORKFLOWS', '1')
    monkeypatch.setenv('ShortUUID', 'shortuuid')
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture
def dynamo_client_stub(mock_env_variables):
    from app import DYNAMO_CLIENT
    with Stubber(DYNAMO_CLIENT.meta.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def sqs_client_stub(mock_env_variables):
    from app import SQS_CLIENT
    with Stubber(SQS_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def sfn_client_stub(mock_env_variables):
    from app import SFN_CLIENT
    with Stubber(SFN_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def lambda_client_stub(mock_env_variables):
    from app import LAMBDA_CLIENT
    with Stubber(LAMBDA_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


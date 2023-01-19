import pytest
from botocore.stub import Stubber

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/workflowstream/')
    monkeypatch.setenv("botoConfig", '{"user_agent_extra": "AwsSolution/SO0163/vX.X.X"}')
    monkeypatch.setenv('StreamName', 'testStreamName')
    monkeypatch.setenv('AWS_XRAY_CONTEXT_MISSING', 'LOG_ERROR')
    monkeypatch.setenv('TOPIC_ARN', 'testTopicArn')
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture
def sns_client_stub(mock_env_variables):
    from workflowstream import sns
    with Stubber(sns) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

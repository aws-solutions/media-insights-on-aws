import pytest
from botocore.stub import Stubber

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/dataplanestream/')
    monkeypatch.setenv("botoConfig", '{"user_agent_extra": "AwsSolution/SO0163/vX.X.X"}')
    monkeypatch.setenv('StreamName', 'testStreamName')
    monkeypatch.setenv('AWS_XRAY_CONTEXT_MISSING', 'LOG_ERROR')

@pytest.fixture
def kinesis_client_stub(mock_env_variables):
    from stream import ks
    with Stubber(ks) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
    
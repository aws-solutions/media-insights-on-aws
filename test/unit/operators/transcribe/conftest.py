import pytest
from botocore.stub import Stubber

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/operators/')
    monkeypatch.syspath_prepend('../../source/lib/MediaInsightsEngineLambdaHelper/')
    monkeypatch.syspath_prepend('./operators/')
    monkeypatch.setenv("botoConfig", '{"user_agent_extra": "AwsSolution/SO0163/vX.X.X"}')
    monkeypatch.setenv('AWS_XRAY_CONTEXT_MISSING', 'LOG_ERROR')
    monkeypatch.setenv('AWS_REGION', 'us-west-2')
    monkeypatch.setenv('DataplaneEndpoint', 'testDataplaneEndpoint')

@pytest.fixture()
def transcribe_start_stub():
    import transcribe.start_transcribe as app
    with Stubber(app.transcribe) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture()
def transcribe_get_stub():
    import transcribe.get_transcribe as app
    with Stubber(app.transcribe) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture()
def s3_client_stub():
    import transcribe.get_transcribe as app
    with Stubber(app.s3) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
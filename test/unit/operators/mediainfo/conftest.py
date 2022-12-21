import pytest
from botocore.stub import Stubber

@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.syspath_prepend('../../source/operators/')
    monkeypatch.syspath_prepend('../../source/lib/MediaInsightsEngineLambdaHelper/')
    monkeypatch.syspath_prepend('./operators/')
    monkeypatch.setenv('DataplaneEndpoint', 'testDataplaneEndpoint')
    monkeypatch.setenv('AWS_XRAY_CONTEXT_MISSING', 'LOG_ERROR')
    monkeypatch.setenv('AWS_REGION', 'us-west-2')

@pytest.fixture
def s3_client_stub(mock_env_variables):
    import mediainfo.mediainfo as app
    client = app.get_s3_client()
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

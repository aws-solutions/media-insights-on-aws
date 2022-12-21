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

@pytest.fixture
def mediaconvert_start_stub(mock_env_variables):
    import mediaconvert.start_media_convert as app
    client = app.get_mediaconvert_client()
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def mediaconvert_get_stub(mock_env_variables):
    import mediaconvert.get_media_convert as app
    client = app.get_mediaconvert_client()
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

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
    monkeypatch.setenv('DataplaneEndpoint', 'testDataplaneEndpoint')
    monkeypatch.setenv('MEDIACONVERT_ENDPOINT', 'https://test.mediaconvert.endpoint')

@pytest.fixture
def translate_client_stub(mock_env_variables):
    import translate.start_translate as app
    with Stubber(app.translate_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def s3_client_stub(mock_env_variables):
    import translate.start_translate as app
    with Stubber(app.s3) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()

@pytest.fixture
def translate_client_stub(mock_env_variables):
    import translate.start_translate as app
    with Stubber(app.translate_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
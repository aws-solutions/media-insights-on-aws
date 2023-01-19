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
    monkeypatch.setenv('OPERATOR_NAME', 'testOperatorName')
    monkeypatch.setenv('DataplaneEndpoint', 'testDataplaneEndpoint')
    monkeypatch.setenv('REKOGNITION_SNS_TOPIC_ARN', 'testRekognitionSNSTopicArn')
    monkeypatch.setenv('REKOGNITION_ROLE_ARN', 'testRekognitionRoleArn')
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

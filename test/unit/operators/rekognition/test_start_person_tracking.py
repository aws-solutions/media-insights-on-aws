import pytest
from botocore.stub import Stubber


def test_empty_event_status():
    import rekognition.start_rekognition as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(metadata={})

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.start_person_tracking(input_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['PersonTrackingError'] == 'No valid inputs'


def test_image():
    import rekognition.start_rekognition as lambda_function
    import helper

    input_parameter = helper.get_operator_parameter(
        metadata={},
        input={
            'Media': {
                'Image': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key.png'
                }
            }
        }
    )

    response = lambda_function.start_person_tracking(input_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'


def test_video():
    import rekognition.start_rekognition as lambda_function
    import helper

    input_parameter = helper.get_operator_parameter(
        metadata={},
        input={
            'Media': {
                'Video': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key.mp4'
                }
            }
        }
    )

    with Stubber(lambda_function.rek) as stubber:
        stubber.assert_no_pending_responses()
        stubber.add_response(
            'start_person_tracking',
            expected_params={
                'Video': {
                    'S3Object': {
                        'Bucket': 'test_bucket',
                        'Name': 'test_key.mp4'
                    }
                },
                'NotificationChannel': {
                    'SNSTopicArn': 'testRekognitionSNSTopicArn',
                    'RoleArn': 'testRekognitionRoleArn'
                }
            },
            service_response={
                'JobId': 'testJobId'
            }
        )

        response = lambda_function.start_person_tracking(input_parameter, {})
        assert response['Status'] == 'Executing'
        assert response['MetaData']['JobId'] == 'testJobId'
        assert response['MetaData']['AssetId'] == 'testAssetId'
        assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'

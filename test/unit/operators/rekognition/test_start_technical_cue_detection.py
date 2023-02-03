import pytest
from botocore.stub import Stubber


def test_empty_event_status():
    import rekognition.start_rekognition as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(metadata={})

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.start_technical_cue_detection(input_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TechnicalCueDetectionError'] == 'No valid inputs'


def test_error_handling():
    import rekognition.start_rekognition as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = helper.get_operator_parameter(
        metadata={},
        input={
            'Media': {
                'Video': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key.png'
                }
            }
        }
    )

    with Stubber(lambda_function.rek) as stubber:
        stubber.assert_no_pending_responses()
        stubber.add_client_error('start_segment_detection')
        with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
            lambda_function.start_technical_cue_detection(input_parameter, {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['TechnicalCueDetectionError'] == 'Not a valid file type'


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
            'start_segment_detection',
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
                },
                'SegmentTypes': ['TECHNICAL_CUE']
            },
            service_response={
                'JobId': 'testJobId'
            }
        )

        response = lambda_function.start_technical_cue_detection(input_parameter, {})
        assert response['Status'] == 'Executing'
        assert response['MetaData']['JobId'] == 'testJobId'
        assert response['MetaData']['AssetId'] == 'testAssetId'
        assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'

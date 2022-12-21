import pytest, json
from pymediainfo import MediaInfo
from unittest.mock import MagicMock

def test_input_validation():
    import mediainfo.mediainfo as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper
    
    operator_parameters = []
    # Missing S3Bucket for Video Input
    operator_parameters.append({
        'key': 'S3Bucket',
        'value': helper.get_operator_parameter(
            input = {
                'Media': {
                    'Video': {
                        'S3Key': 'test_key'
                    }
                }
            }
        )
    })
    # Missing S3Key for Video Input
    operator_parameters.append({
        'key': 'S3Key',
        'value': helper.get_operator_parameter(
            input = {
                'Media': {
                    'Video': {
                        'S3Bucket': 'test_bucket'
                    }
                }
            }
        )
    })
    # Missing S3Bucket for Image Input
    operator_parameters.append({
        'key': 'S3Bucket',
        'value': helper.get_operator_parameter(
            input = {
                'Media': {
                    'Image': {
                        'S3Key': 'test_key'
                    }
                }
            }
        )
    })
    # Missing S3Key for Image Input
    operator_parameters.append({
        'key': 'S3Key',
        'value': helper.get_operator_parameter(
            input = {
                'Media': {
                    'Image': {
                        'S3Bucket': 'test_bucket'
                    }
                }
            }
        )
    })
    for parameter in operator_parameters:
        with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
            lambda_function.lambda_handler(parameter['value'], {})
        assert err.value.args[0]['Status'] == 'Error'
        assert err.value.args[0]['MetaData']['MediaconvertError'] == "Missing a required metadata key '{e}'".format(e=parameter['key'])

class MediaInfoRespose():
    def __init__(self, value = None):
        self.value = value

    def to_json(self):
        if self.value is None:
            return json.dumps({
                'tracks': [{
                    'track_type': 'Audio'
                }]
            })
        return json.dumps(self.value)

def test_mediainfo_invalid_results():
    import mediainfo.mediainfo as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    # mock mediainfo parse
    original_function = MediaInfo.parse
    MediaInfo.parse = MagicMock(return_value = MediaInfoRespose({
        'tracks': [{
            'track_type': 'invalid_type'
        }]
    }))

    operator_parameter = helper.get_operator_parameter(
        metadata={},
        media={},
        input = {
            'Media': {
                'Image': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert "Unable to get Mediainfo results." in err.value.args[0]['MetaData']['MediainfoError']

    # revert mocks
    MediaInfo.parse = original_function


def test_mediainfo_error():
    import mediainfo.mediainfo as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    # mock mediainfo parse
    original_function = MediaInfo.parse
    MediaInfo.parse = MagicMock(side_effect=RuntimeError('testError'))

    operator_parameter = helper.get_operator_parameter(
        metadata={},
        media={},
        input = {
            'Media': {
                'Image': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['MediainfoError'] == 'File does not contain valid video, audio, image, or text content'

    # revert mocks
    MediaInfo.parse = original_function

def test_completed_job():
    import mediainfo.mediainfo as lambda_function
    import helper

    # mock mediainfo parse
    original_function = MediaInfo.parse
    MediaInfo.parse = MagicMock(return_value = MediaInfoRespose())
    
    #mock dataplane store_asset_metadata
    original_dataplane = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
            'Status': 'Success'
        }
    )

    operator_parameter = helper.get_operator_parameter(
        metadata={},
        media={},
        input = {
            'Media': {
                'Image': {
                    'S3Bucket': 'test_bucket',
                    'S3Key': 'test_key'
                }
            }
        }
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['MetaData']['Mediainfo_num_audio_tracks'] == '1'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'
    assert MediaInfo.parse.call_count == 1
    assert 'https://s3.us-west-2.amazonaws.com/test_bucket/test_key' in MediaInfo.parse.call_args[0][0]
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {'tracks': [{'track_type': 'Audio'}]}

    # revert mocks
    MediaInfo.parse = original_function
    lambda_function.DataPlane.store_asset_metadata = original_dataplane

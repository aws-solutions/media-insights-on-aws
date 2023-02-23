# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest, json
from unittest.mock import MagicMock

class HTTPResponseMock:
    def __init__(self) -> None:
        self.data = json.dumps({
            'results': {
                'transcripts': [{
                    'transcript': ['test_', 'transcript_', 'result']
                }]
            }
        }).encode('utf-8')

def test_workflow_zero_audio_tracks():
    import transcribe.get_transcribe as lambda_function
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '0'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )
    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'

def test_workflow_empty_job_id():
    import transcribe.get_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={}
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranscribeError'] == "Missing a required metadata key 'TranscribeJobId'"

def test_workflow_empty_language_code_from_job_response(transcribe_get_stub):
    import transcribe.get_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={
            'TranscribeJobId': 'testJobId'
        }
    )

    transcribe_get_stub.add_response(
        'get_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'testJobId'
        },
        service_response = {

        }
    )

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranscribeError'] == "'TranscriptionJob'"
    assert err.value.args[0]['MetaData']['TranscribeJobId'] == 'testJobId'

def test_workflow_in_progress(transcribe_get_stub):
    import transcribe.get_transcribe as lambda_function
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={
            'TranscribeJobId': 'testJobId'
        }
    )

    transcribe_get_stub.add_response(
        'get_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'testJobId'
        },
        service_response = {
            'TranscriptionJob': {
                'LanguageCode': 'en',
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        }
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['TranscribeJobId'] == 'testJobId'
    assert response['MetaData']['AssetId'] == 'testAssetId'
    assert response['MetaData']['WorkflowExecutionId'] == 'testWorkflowId'

def test_workflow_failed(transcribe_get_stub):
    import transcribe.get_transcribe as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata={
            'TranscribeJobId': 'testJobId'
        }
    )

    transcribe_get_stub.add_response(
        'get_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'testJobId'
        },
        service_response = {
            'TranscriptionJob': {
                'LanguageCode': 'en',
                'TranscriptionJobStatus': 'FAILED',
                'FailureReason': 'test_failed_message'
            }
        }
    )

    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['TranscribeJobId'] == 'testJobId'
    assert err.value.args[0]['MetaData']['TranscribeError'] == 'test_failed_message'

def test_workflow_completed(transcribe_get_stub, s3_client_stub):
    import transcribe.get_transcribe as lambda_function
    import helper
    import urllib3

    input_parameter = {
        'Media': {
            'ProxyEncode': {
                'S3Bucket': 'test_bucket',
                'S3Key': 'test_key.mp4'
            }
        },
        'MetaData': {
            'Mediainfo_num_audio_tracks': '1'
        }
    }
    operator_parameter = helper.get_operator_parameter(
        input = input_parameter,
        metadata = {
            'TranscribeJobId': 'testJobId'
        },
        media = {}
    )

    original_function = urllib3.PoolManager.request
    urllib3.PoolManager.request = MagicMock(
        return_value = HTTPResponseMock()
    )

    original_dataplane_generate = lambda_function.DataPlane.generate_media_storage_path
    lambda_function.DataPlane.generate_media_storage_path = MagicMock(
        return_value = {
            'S3Bucket': 'test_bucket',
            'S3Key': 'test_key_'
        }
    )

    original_dataplane_store = lambda_function.DataPlane.store_asset_metadata
    lambda_function.DataPlane.store_asset_metadata = MagicMock(
        return_value = {
            'Status': 'Success',
            'Bucket': 'result_bucket',
            'Key': 'result_key'
        }
    )

    transcribe_get_stub.add_response(
        'get_transcription_job',
        expected_params = {
            'TranscriptionJobName': 'testJobId'
        },
        service_response = {
            'TranscriptionJob': {
                'LanguageCode': 'en',
                'TranscriptionJobStatus': 'COMPLETED',
                'Transcript': {
                    'TranscriptFileUri': 'test_uri'
                }
            }
        }
    )

    s3_client_stub.add_response(
        'put_object',
        expected_params = {
            'Bucket': 'test_bucket',
            'Key': 'test_key_transcript.txt',
            'Body': 'test_transcript_result'
        },
        service_response = {}
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['MetaData']['TranscribeJobId'] == 'testJobId'
    assert response['MetaData']['TranscribeSourceLanguage'] == 'en'
    assert lambda_function.DataPlane.generate_media_storage_path.call_count == 1
    assert lambda_function.DataPlane.generate_media_storage_path.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.generate_media_storage_path.call_args[0][1] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_count == 1
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][0] == 'testAssetId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][1] == 'testName'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][2] == 'testWorkflowId'
    assert lambda_function.DataPlane.store_asset_metadata.call_args[0][3] == {'TextTranscriptUri': {'S3Bucket': 'test_bucket', 'S3Key': 'test_key_transcript.txt'}, 'results': {'transcripts': [{'transcript': ['test_', 'transcript_', 'result']}]}}

    urllib3.PoolManager.request = original_function
    lambda_function.DataPlane.generate_media_storage_path = original_dataplane_generate
    lambda_function.DataPlane.store_asset_metadata = original_dataplane_store
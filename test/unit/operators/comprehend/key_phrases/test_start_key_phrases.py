# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest, json
from unittest.mock import MagicMock
from botocore.response import StreamingBody
from io import BytesIO
from botocore.stub import ANY

def test_input_parameter():
    import comprehend.key_phrases.start_key_phrases as lambda_function
    import helper
    
    operator_parameter = helper.get_operator_parameter({
        'comprehend_entity_job_id': 'comprehend_entity_job_id'
    })
    del operator_parameter['WorkflowExecutionId']
    
    with pytest.raises(KeyError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0] == 'WorkflowExecutionId'

def test_empty_input():
    import comprehend.key_phrases.start_key_phrases as lambda_function
    import MediaInsightsEngineLambdaHelper
    import helper

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                }
            }
        }
    )
    with pytest.raises(MediaInsightsEngineLambdaHelper.MasExecutionError) as err:
        lambda_function.lambda_handler(operator_parameter, {})
    assert err.value.args[0]['Status'] == 'Error'
    assert err.value.args[0]['MetaData']['comprehend_error'] == 'No valid inputs'

def test_for_empty_s3_object(s3_start_key_phrases):
    import comprehend.key_phrases.start_key_phrases as lambda_function
    import helper

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': 'test_bucket_name',
                    'S3Key': 'test_key_name'
                }
            }
        }
    )

    s3_start_key_phrases.add_response(
        'head_object',
        expected_params = {
            'Bucket': 'test_bucket_name',
            'Key': 'test_key_name'
        },
        service_response = {
            'ContentLength': 0
        }
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Complete'
    assert response['MetaData']['comprehend_phrases_job_id'] == 'Empty input --> empty output.'

def test_getting_mediafile_from_s3_and_start_process(s3_start_key_phrases, comprehend_start_key_phrases):
    import comprehend.key_phrases.start_key_phrases as lambda_function
    import helper

    test_bucket_name = 'test_bucket_name'
    test_key_name = 'test_key_name.json'

    original_func = lambda_function.DataPlane.generate_media_storage_path
    lambda_function.DataPlane.generate_media_storage_path = MagicMock()

    operator_parameter = helper.get_operator_parameter(
        input = {
            'Media': {
                'Text': {
                    'S3Bucket': test_bucket_name,
                    'S3Key': test_key_name
                }
            }
        }
    )

    s3_response_json = {
        'TextTranscriptUri': {
            'S3Bucket': test_bucket_name,
            'S3Key': test_key_name
        }
    }

    s3_start_key_phrases.add_response(
        'get_object',
        expected_params = {
            'Bucket': test_bucket_name,
            'Key': test_key_name
        },
        service_response = {
            'Body': StreamingBody(
                BytesIO(json.dumps(s3_response_json).encode('utf-8')),
                len(json.dumps(s3_response_json))
            )
        }
    )

    s3_start_key_phrases.add_response(
        'head_object',
        expected_params = {
            'Bucket': test_bucket_name,
            'Key': test_key_name
        },
        service_response = {
            'ContentLength': len(json.dumps(s3_response_json))
        }
    )

    comprehend_start_key_phrases.add_response(
        'start_key_phrases_detection_job',
        expected_params = {
            'InputDataConfig': {
                "S3Uri": 's3://' + test_bucket_name + '/' + test_key_name,
                "InputFormat": "ONE_DOC_PER_FILE"
            },
            'OutputDataConfig': {
                "S3Uri": ANY,
                "KmsKeyId": 'testKmsId'
            },
            'DataAccessRoleArn': 'testComprehendRole10',
            'VolumeKmsKeyId': 'testKmsId',
            'JobName': 'testWorkflowId',
            'LanguageCode': "en"
        },
        service_response = {}
    )

    response = lambda_function.lambda_handler(operator_parameter, {})
    assert response['Status'] == 'Executing'
    assert response['MetaData']['comprehend_phrases_job_id'] == 'testWorkflowId'

    lambda_function.DataPlane.generate_media_storage_path = original_func